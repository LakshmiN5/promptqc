"""Token budget analysis using tiktoken."""

from typing import List, Optional, Dict

from promptqc.rules.base import BaseRule
from promptqc.models import Issue, Severity, TokenBudget
from promptqc.parser import ParsedPrompt


# Context window sizes for popular models
MODEL_CONTEXT_WINDOWS: Dict[str, int] = {
    "gpt-4o": 128_000,
    "gpt-4o-mini": 128_000,
    "gpt-4-turbo": 128_000,
    "gpt-4": 8_192,
    "gpt-3.5-turbo": 16_385,
    "claude-3.5-sonnet": 200_000,
    "claude-3-opus": 200_000,
    "claude-3-haiku": 200_000,
    "gemini-1.5-pro": 2_000_000,
    "gemini-1.5-flash": 1_000_000,
    "gemini-2.0-flash": 1_000_000,
    "llama-3-8b": 8_192,
    "llama-3-70b": 8_192,
    "llama-3.1-8b": 128_000,
    "llama-3.1-70b": 128_000,
    "mistral-7b": 32_768,
    "mixtral-8x7b": 32_768,
    "MiniMax-M2.5": 204_000,
}

# Model name to tiktoken encoding mapping
MODEL_ENCODINGS: Dict[str, str] = {
    "gpt-4o": "o200k_base",
    "gpt-4o-mini": "o200k_base",
    "gpt-4-turbo": "cl100k_base",
    "gpt-4": "cl100k_base",
    "gpt-3.5-turbo": "cl100k_base",
}


def count_tokens(text: str, model: str = "gpt-4o") -> int:
    """Count tokens for a given text and model."""
    try:
        import tiktoken

        # Try to get encoding for specific model
        encoding_name = MODEL_ENCODINGS.get(model)
        if encoding_name:
            enc = tiktoken.get_encoding(encoding_name)
        else:
            # Default to cl100k_base (good approximation for most models)
            enc = tiktoken.get_encoding("cl100k_base")

        return len(enc.encode(text))
    except ImportError:
        # Rough estimate: ~4 chars per token
        return len(text) // 4


def compute_token_budget(
    parsed: ParsedPrompt,
    model: str = "gpt-4o",
) -> TokenBudget:
    """Compute token usage for a prompt."""
    total_tokens = count_tokens(parsed.raw_text, model)
    context_window = MODEL_CONTEXT_WINDOWS.get(model, 128_000)
    tokens_remaining = context_window - total_tokens
    usage_percent = (total_tokens / context_window) * 100

    # Per-section breakdown
    section_tokens = {}
    for section in parsed.sections:
        section_text = "\n".join(line.text for line in section.lines)
        section_tokens[section.name] = count_tokens(section_text, model)

    return TokenBudget(
        total_tokens=total_tokens,
        model_name=model,
        context_window=context_window,
        tokens_remaining=tokens_remaining,
        usage_percent=usage_percent,
        section_tokens=section_tokens,
    )


class TokenBudgetRule(BaseRule):
    """
    PQ011: Analyze token budget and flag excessive usage.

    Reports:
    - Total token count per model
    - Percentage of context window consumed
    - Per-section token breakdown
    - Warnings if system prompt is too large
    """

    rule_id = "PQ011"
    name = "token-budget-analysis"
    category = "efficiency"
    description = "Analyzes token usage and flags budget concerns"
    needs_embeddings = False

    # If system prompt uses more than this % of context window, warn
    WARNING_THRESHOLD_PERCENT = 25.0
    ERROR_THRESHOLD_PERCENT = 50.0

    def __init__(self, model: str = "gpt-4o", budget: Optional[int] = None):
        """
        Args:
            model: Model name for token counting
            budget: Optional explicit token budget (overrides percentage-based checks)
        """
        self.model = model
        self.budget = budget

    def check(self, parsed: ParsedPrompt, analyzer) -> List[Issue]:
        issues = []
        budget = compute_token_budget(parsed, self.model)

        # Store on analyzer for the report
        analyzer._token_budget = budget

        # Check against explicit budget
        if self.budget and budget.total_tokens > self.budget:
            over = budget.total_tokens - self.budget
            issues.append(Issue(
                rule_id=self.rule_id,
                severity=Severity.ERROR,
                message=f"Prompt exceeds token budget: {budget.total_tokens:,} tokens (budget: {self.budget:,}, over by {over:,})",
                line=1,
                line_content=parsed.get_line_text(1),
                suggestion=f"Reduce prompt by ~{over:,} tokens. Use the per-section breakdown to identify what to trim.",
                category=self.category,
            ))

        # Check percentage of context window
        elif budget.usage_percent >= self.ERROR_THRESHOLD_PERCENT:
            issues.append(Issue(
                rule_id=self.rule_id,
                severity=Severity.WARNING,
                message=(
                    f"System prompt uses {budget.usage_percent:.1f}% of {self.model}'s context window "
                    f"({budget.total_tokens:,}/{budget.context_window:,} tokens) — "
                    f"very little room for conversation"
                ),
                line=1,
                line_content=parsed.get_line_text(1),
                suggestion="Consider reducing the system prompt or using a model with a larger context window.",
                category=self.category,
            ))
        elif budget.usage_percent >= self.WARNING_THRESHOLD_PERCENT:
            issues.append(Issue(
                rule_id=self.rule_id,
                severity=Severity.SUGGESTION,
                message=(
                    f"System prompt uses {budget.usage_percent:.1f}% of {self.model}'s context window "
                    f"({budget.total_tokens:,}/{budget.context_window:,} tokens)"
                ),
                line=1,
                line_content=parsed.get_line_text(1),
                suggestion="Consider trimming verbose sections to leave more room for conversation context.",
                category=self.category,
            ))

        # Find largest section
        if budget.section_tokens and len(budget.section_tokens) > 1:
            largest = max(budget.section_tokens.items(), key=lambda x: x[1])
            total = budget.total_tokens if budget.total_tokens > 0 else 1
            pct = (largest[1] / total) * 100
            if pct > 50 and largest[1] > 200:
                issues.append(Issue(
                    rule_id=self.rule_id,
                    severity=Severity.INFO,
                    message=f'Section "{largest[0]}" uses {pct:.0f}% of total tokens ({largest[1]:,} tokens)',
                    line=1,
                    line_content=parsed.get_line_text(1),
                    suggestion="This section dominates the prompt. Consider whether all of it is necessary.",
                    category=self.category,
                ))

        return issues
