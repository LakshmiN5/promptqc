"""Configuration loading for promptqc.

Supports loading settings from:
1. promptqc.toml (project root)
2. pyproject.toml [tool.promptqc] section
3. Inline comments in prompt files: # promptqc-disable PQ001
"""

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set


@dataclass
class PromptQCConfig:
    """Configuration for promptqc analysis."""

    # Rules to disable globally (e.g., ["PQ003", "PQ004"])
    disable_rules: List[str] = field(default_factory=list)

    # Severity overrides (e.g., {"PQ005": "warning"})
    severity_overrides: Dict[str, str] = field(default_factory=dict)

    # LLM Judge settings
    judge_model: Optional[str] = None  # e.g., "groq/llama3-8b-8192", "gpt-4o-mini"

    # Token settings
    token_model: str = "gpt-4o"
    token_budget: Optional[int] = None

    # Thresholds
    redundancy_threshold: float = 0.88
    contradiction_min_similarity: float = 0.35
    contradiction_max_similarity: float = 0.85

    # Template variable settings
    template_syntax: str = "auto"  # "auto", "python", "jinja2", "none"

    # Custom rule classes to load (dotted Python paths)
    # e.g., ["my_team.rules.BrandRule", "my_team.rules.ComplianceRule"]
    custom_rules: List[str] = field(default_factory=list)

    @property
    def disabled_rule_set(self) -> Set[str]:
        return set(self.disable_rules)


def _load_toml(path: Path) -> dict:
    """Load a TOML file, using tomllib (3.11+) or tomli."""
    if sys.version_info >= (3, 11):
        import tomllib
    else:
        try:
            import tomli as tomllib
        except ImportError:
            return {}

    try:
        with open(path, "rb") as f:
            return tomllib.load(f)
    except (FileNotFoundError, Exception):
        return {}


def load_config(directory: Optional[str] = None) -> PromptQCConfig:
    """
    Load configuration from the nearest config file.

    Search order:
    1. promptqc.toml in the given directory
    2. pyproject.toml [tool.promptqc] in the given directory
    3. Walk up parent directories for either file
    4. Fall back to defaults

    Args:
        directory: Starting directory to search (defaults to cwd)

    Returns:
        PromptQCConfig with loaded settings
    """
    search_dir = Path(directory) if directory else Path.cwd()
    config_data = {}

    # Search upward for config files
    for parent in [search_dir] + list(search_dir.parents):
        # Check promptqc.toml first
        promptqc_toml = parent / "promptqc.toml"
        if promptqc_toml.exists():
            config_data = _load_toml(promptqc_toml)
            break

        # Check pyproject.toml [tool.promptqc]
        pyproject_toml = parent / "pyproject.toml"
        if pyproject_toml.exists():
            data = _load_toml(pyproject_toml)
            tool_config = data.get("tool", {}).get("promptqc", {})
            if tool_config:
                config_data = tool_config
                break

    return _dict_to_config(config_data)


def _dict_to_config(data: dict) -> PromptQCConfig:
    """Convert a dictionary to a PromptQCConfig with error handling."""
    config = PromptQCConfig()

    def _safe_set(field_name, converter, value):
        """Apply a converter to a config value, raising a clear error on failure."""
        try:
            return converter(value)
        except (TypeError, ValueError) as e:
            raise ValueError(
                f"Invalid value for '{field_name}' in promptqc config: "
                f"got {value!r} — {e}"
            )

    if "disable_rules" in data:
        config.disable_rules = _safe_set("disable_rules", list, data["disable_rules"])
    if "severity_overrides" in data:
        config.severity_overrides = _safe_set("severity_overrides", dict, data["severity_overrides"])
    if "judge_model" in data:
        config.judge_model = data["judge_model"]
    if "token_model" in data:
        config.token_model = str(data["token_model"])
    if "token_budget" in data:
        config.token_budget = _safe_set("token_budget", int, data["token_budget"])
    if "template_syntax" in data:
        valid = ("auto", "python", "jinja2", "none")
        val = str(data["template_syntax"])
        if val not in valid:
            raise ValueError(
                f"Invalid 'template_syntax' in promptqc config: got {val!r}, "
                f"must be one of {valid}"
            )
        config.template_syntax = val
    if "custom_rules" in data:
        config.custom_rules = _safe_set("custom_rules", list, data["custom_rules"])

    # Thresholds
    thresholds = data.get("thresholds", {})
    if "redundancy" in thresholds:
        config.redundancy_threshold = _safe_set(
            "thresholds.redundancy", float, thresholds["redundancy"]
        )
    if "contradiction_min" in thresholds:
        config.contradiction_min_similarity = _safe_set(
            "thresholds.contradiction_min", float, thresholds["contradiction_min"]
        )
    if "contradiction_max" in thresholds:
        config.contradiction_max_similarity = _safe_set(
            "thresholds.contradiction_max", float, thresholds["contradiction_max"]
        )

    return config


# ── Inline suppression parsing ──────────────────────────────────────

INLINE_DISABLE_PATTERNS = [
    "# promptqc-disable",       # Python-style comment
    "// promptqc-disable",      # C-style comment
    "<!-- promptqc-disable",    # HTML/XML comment
]


def parse_inline_disables(text: str) -> Dict[int, Set[str]]:
    """
    Parse inline disable comments from prompt text.

    Supports:
        # promptqc-disable PQ001
        # promptqc-disable PQ001 PQ003
        # promptqc-disable-next-line PQ001
        // promptqc-disable PQ001
        <!-- promptqc-disable PQ001 -->

    Returns:
        Dict mapping line numbers to sets of disabled rule IDs.
        A special key 0 means "disable globally for the file".
    """
    disables: Dict[int, Set[str]] = {}
    lines = text.split("\n")

    for i, line in enumerate(lines):
        line_num = i + 1
        stripped = line.strip()

        for prefix in INLINE_DISABLE_PATTERNS:
            if prefix in stripped:
                # Extract the part after the prefix
                idx = stripped.index(prefix) + len(prefix)
                rest = stripped[idx:].strip()

                # Clean up trailing comment markers
                rest = rest.replace("-->", "").strip()

                if rest.startswith("-next-line"):
                    # Applies to the next line
                    rest = rest[len("-next-line"):].strip()
                    rule_ids = _extract_rule_ids(rest)
                    if rule_ids:
                        disables.setdefault(line_num + 1, set()).update(rule_ids)
                else:
                    rule_ids = _extract_rule_ids(rest)
                    if rule_ids:
                        disables.setdefault(line_num, set()).update(rule_ids)
                    else:
                        # No specific rules = disable all on this line
                        disables.setdefault(line_num, set()).add("*")
                break

    return disables


def _extract_rule_ids(text: str) -> Set[str]:
    """Extract PQ### rule IDs from a string."""
    import re
    return set(re.findall(r"PQ\d{3}", text))
