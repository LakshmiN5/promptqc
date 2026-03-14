"""LLM-as-a-Judge rule — deep semantic analysis using LiteLLM.

Uses any LLM provider (Groq, Ollama, OpenAI, Anthropic, etc.) via LiteLLM
to perform deep semantic analysis that regex and embeddings can't handle:
- Contextual contradiction detection
- Variable safety assessment
- Prompt clarity and effectiveness evaluation

Usage:
    # Free/local options:
    export GROQ_API_KEY="gsk_..."       # Groq (free tier, fast)
    promptqc check prompt.txt --judge groq/llama3-8b-8192

    ollama pull phi3                    # Local Ollama
    promptqc check prompt.txt --judge ollama/phi3

    # Premium options:
    export OPENAI_API_KEY="sk-..."
    promptqc check prompt.txt --judge gpt-4o-mini
"""

import os
import logging

# Suppress LiteLLM verbose logging
os.environ["LITELLM_LOG"] = "ERROR"
logging.getLogger("LiteLLM").setLevel(logging.ERROR)

import json
from typing import List, Optional

from promptqc.rules.base import BaseRule
from promptqc.models import Issue, Severity
from promptqc.parser import ParsedPrompt


JUDGE_SYSTEM_PROMPT = """You are PromptQC Judge — an expert prompt engineering analyzer.

Your job is to analyze a system prompt and find REAL issues. Be precise and avoid false positives.

Analyze the prompt for:
1. **Contradictions**: Instructions that genuinely conflict (not just different aspects of behavior)
   - **Cross-instruction**: Conflicting instructions on different lines
   - **Intra-sentence**: Contradictions within a single sentence (e.g., "Be brief, but include all details")
2. **Injection Vulnerabilities**: Template variables containing user data without XML sandboxing
3. **Ambiguity**: Instructions so vague the LLM will interpret them inconsistently
4. **Missing Critical Elements**: Important missing pieces for the prompt's stated purpose
5. **Token Inefficiency**: Verbose phrasing, excessive lists of synonyms, or wordy instructions that add no new semantic value but waste tokens

Rules:
- STRICTLY ONLY report GENUINE issues, not stylistic preferences or opinions on ambiguity.
- DO NOT flag standard instruction language (e.g. "extract main points", "explain why", "summarize") as ambiguous. LLMs understand these perfectly well.
- DO NOT flag correcting grammar/spelling/formatting as a contradiction to "do not add new information". Fixing errors is not adding information.
- DO NOT flag instructions about conciseness vs detail if they apply to different parts of the output.
- Each issue must have a specific line reference and actionable fix.
- Do NOT flag things that are clearly intentional design choices.
- Be extremely conservative: when in doubt, do NOT report it. Only flag absolute, undeniable errors.
- Pay special attention to intra-sentence contradictions joined by "but", "however", "yet", "although".

Respond ONLY with valid JSON matching this exact schema (no markdown, no explanation):
{
  "issues": [
    {
      "rule_id": "PQ020",
      "severity": "error|warning|suggestion",
      "line": <1-indexed line number>,
      "message": "<clear description of the issue>",
      "suggestion": "<specific fix, ideally with rewritten text>"
    }
  ]
}

Rule ID assignments:
- PQ020: Contextual contradiction (instructions that genuinely conflict in practice)
- PQ021: Variable injection risk (template variables not properly sandboxed)
- PQ022: Ambiguous instruction (will cause inconsistent LLM behavior)
- PQ023: Missing critical element (important gap for the prompt's purpose)
- PQ024: Other significant issue
- PQ025: Token waste/Verbosity (excessive synonyms, rambling instructions, or filler phrases)

Severity guide:
- error: Will definitely cause problems in production
- warning: Likely to cause issues, should be addressed
- suggestion: Could be improved but not critical

If no real issues are found, return: {"issues": []}"""


def _build_user_message(prompt_text: str) -> str:
    """Build the user message with the prompt to analyze."""
    # Add line numbers for reference
    numbered_lines = []
    for i, line in enumerate(prompt_text.split("\n"), 1):
        numbered_lines.append(f"L{i:>3}: {line}")
    numbered_text = "\n".join(numbered_lines)

    return f"""Analyze this system prompt for quality issues:

```
{numbered_text}
```

Remember: Respond with JSON only. Be precise and conservative — only flag genuine issues."""


def _parse_judge_response(response_text: str) -> List[dict]:
    """Parse the LLM judge's JSON response, handling common formatting issues."""
    text = response_text.strip()

    # Strip markdown code fences if present
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines)

    try:
        data = json.loads(text)
        if isinstance(data, dict) and "issues" in data:
            return data["issues"]
        return []
    except json.JSONDecodeError:
        # Try to find JSON in the response
        import re
        json_match = re.search(r'\{[\s\S]*"issues"[\s\S]*\}', text)
        if json_match:
            try:
                data = json.loads(json_match.group())
                return data.get("issues", [])
            except json.JSONDecodeError:
                pass
        return []


SEVERITY_MAP = {
    "error": Severity.ERROR,
    "warning": Severity.WARNING,
    "suggestion": Severity.SUGGESTION,
    "info": Severity.INFO,
}


class LLMJudgeRule(BaseRule):
    """
    PQ020-PQ024: Deep semantic analysis using an LLM judge.

    Uses LiteLLM to send the prompt to any LLM provider for expert-level
    quality analysis that goes far beyond what regex or embeddings can detect.

    Supported providers (via LiteLLM):
    - Groq: groq/llama3-8b-8192 (free tier available)
    - Ollama: ollama/phi3, ollama/llama3 (local, private)
    - OpenAI: gpt-4o-mini, gpt-4o (premium)
    - Anthropic: claude-3-haiku-20240307 (premium)
    - And 100+ more via LiteLLM
    """

    rule_id = "PQ020"
    name = "llm-judge-analysis"
    category = "semantic"
    description = "Deep semantic analysis using LLM-as-a-Judge"
    needs_embeddings = False

    def __init__(self, model: str = "groq/qwen/qwen3-32b"):
        """
        Args:
            model: LiteLLM model identifier (e.g., "groq/qwen/qwen3-32b",
                   "ollama/phi3", "gpt-4o-mini")
        """
        self.model = model

    def check(self, parsed: ParsedPrompt, analyzer) -> List[Issue]:
        """Run LLM judge analysis on the prompt."""
        try:
            from litellm import completion
        except ImportError:
            return [Issue(
                rule_id=self.rule_id,
                severity=Severity.INFO,
                message=(
                    "LLM Judge requires litellm. "
                    "Install with: pip install promptqc[llm]"
                ),
                line=1,
                line_content=parsed.get_line_text(1),
                category="internal",
            )]

        # Call the LLM
        try:
            messages = [
                {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
                {"role": "user", "content": _build_user_message(parsed.raw_text)},
            ]
            base_kwargs = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.1,  # Low temperature for consistent analysis
                "max_tokens": 2000,
            }

            # Try with structured JSON output first (supported by OpenAI, Groq, etc.)
            # Fall back gracefully for providers that don't support it.
            try:
                response = completion(
                    **base_kwargs,
                    response_format={"type": "json_object"},
                )
            except Exception:
                # Provider doesn't support response_format — fall back to
                # prompt-only JSON enforcement (the system prompt already
                # instructs JSON output, and _parse_judge_response handles
                # markdown fences and other common formatting issues).
                response = completion(**base_kwargs)

            response_text = response.choices[0].message.content
            judge_issues = _parse_judge_response(response_text)

            # Convert to Issue objects
            issues = []
            for ji in judge_issues:
                line = ji.get("line", 1)
                severity_str = ji.get("severity", "suggestion").lower()
                severity = SEVERITY_MAP.get(severity_str, Severity.SUGGESTION)

                issues.append(Issue(
                    rule_id=ji.get("rule_id", "PQ020"),
                    severity=severity,
                    message=ji.get("message", "Issue detected by LLM judge"),
                    line=line,
                    line_content=parsed.get_line_text(line),
                    suggestion=ji.get("suggestion"),
                    category="semantic",
                ))

            return issues

        except Exception as e:
            error_msg = str(e)

            # Provide helpful error messages for common issues
            if "api_key" in error_msg.lower() or "auth" in error_msg.lower():
                hint = (
                    f"Set the API key for {self.model}. Examples:\n"
                    f"  export GROQ_API_KEY='gsk_...'      (free: groq/qwen/qwen3-32b)\n"
                    f"  export OPENAI_API_KEY='sk-...'      (gpt-4o-mini)\n"
                    f"  ollama pull phi3                     (local: ollama/phi3)"
                )
            elif "connection" in error_msg.lower() or "refused" in error_msg.lower():
                hint = (
                    f"Cannot connect to {self.model}. "
                    f"If using Ollama, ensure it's running: ollama serve"
                )
            else:
                hint = f"LLM Judge error ({self.model}): {error_msg}"

            return [Issue(
                rule_id=self.rule_id,
                severity=Severity.INFO,
                message=f"LLM Judge unavailable: {hint}",
                line=1,
                line_content=parsed.get_line_text(1),
                category="internal",
            )]
