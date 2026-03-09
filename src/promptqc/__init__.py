"""
PromptQC — Quality assessment and improvement suggestions for LLM system prompts.

Analyzes system prompts for contradictions, redundancy, anti-patterns,
injection vulnerabilities, structural completeness, and token efficiency.

Usage:
    from promptqc import analyze

    report = analyze("You are a helpful assistant...")
    print(report.quality_score.grade)  # "A", "B", etc.

    for issue in report.issues:
        print(f"L{issue.line}: [{issue.severity.value}] {issue.message}")
"""

__version__ = "0.1.0"

from promptqc.analyzer import PromptAnalyzer
from promptqc.models import Issue, Report, Severity, TokenBudget, QualityScore
from promptqc.parser import parse_prompt, ParsedPrompt

__all__ = [
    "analyze",
    "analyze_fast",
    "PromptAnalyzer",
    "Issue",
    "Report",
    "Severity",
    "TokenBudget",
    "QualityScore",
    "parse_prompt",
    "ParsedPrompt",
]


# Module-level cached analyzer instance
_default_analyzer = None
_fast_analyzer = None


def analyze(
    prompt: str,
    token_model: str = "gpt-4o",
    token_budget: int = None,
) -> Report:
    """
    Analyze a prompt with full quality checks (including semantic analysis).

    This is the main entry point. It loads a ~80MB sentence-transformers model
    on first call (cached for subsequent calls).

    Args:
        prompt: The system prompt text to analyze
        token_model: Model name for token counting (e.g., "gpt-4o", "claude-3.5-sonnet")
        token_budget: Optional explicit token budget to enforce

    Returns:
        Report with issues, quality score, and token budget

    Example:
        >>> report = analyze("You are a helpful assistant. Be concise.")
        >>> print(report.quality_score.grade)
        >>> for issue in report.issues:
        ...     print(f"L{issue.line}: {issue.message}")
    """
    global _default_analyzer
    if _default_analyzer is None or _default_analyzer.token_model != token_model:
        _default_analyzer = PromptAnalyzer(
            token_model=token_model,
            token_budget=token_budget,
        )
    return _default_analyzer.analyze(prompt)


def analyze_fast(
    prompt: str,
    token_model: str = "gpt-4o",
    token_budget: int = None,
) -> Report:
    """
    Analyze a prompt with fast, pattern-based checks only.

    Skips semantic analysis (no model download needed). Runs in milliseconds.
    Covers: anti-patterns, injection risks, completeness, token budget.

    Args:
        prompt: The system prompt text to analyze
        token_model: Model name for token counting
        token_budget: Optional explicit token budget

    Returns:
        Report with issues (no contradiction/redundancy detection)

    Example:
        >>> report = analyze_fast("You are a helpful assistant.")
        >>> print(f"Score: {report.quality_score.total}/100")
    """
    global _fast_analyzer
    if _fast_analyzer is None or _fast_analyzer.token_model != token_model:
        _fast_analyzer = PromptAnalyzer(
            fast_mode=True,
            token_model=token_model,
            token_budget=token_budget,
        )
    return _fast_analyzer.analyze(prompt)
