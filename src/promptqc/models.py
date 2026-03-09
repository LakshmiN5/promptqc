"""Data models for promptqc analysis results."""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict


class Severity(Enum):
    """Issue severity levels."""
    ERROR = "error"        # Must fix — will cause real problems
    WARNING = "warning"    # Should fix — likely causing issues
    SUGGESTION = "suggestion"  # Consider fixing — room for improvement
    INFO = "info"          # Informational — no action needed


@dataclass
class Issue:
    """A single quality issue found in a prompt."""
    rule_id: str           # e.g., "PQ001"
    severity: Severity
    message: str           # Human-readable description
    line: int              # 1-indexed line number
    line_content: str      # The actual line text
    suggestion: Optional[str] = None  # How to fix it
    end_line: Optional[int] = None    # For multi-line issues
    related_line: Optional[int] = None  # e.g., the contradicting line
    related_content: Optional[str] = None
    category: str = ""     # e.g., "contradiction", "injection"

    @property
    def severity_icon(self) -> str:
        return {
            Severity.ERROR: "🔴",
            Severity.WARNING: "⚠️ ",
            Severity.SUGGESTION: "💡",
            Severity.INFO: "ℹ️ ",
        }[self.severity]


@dataclass
class TokenBudget:
    """Token usage analysis for a prompt."""
    total_tokens: int
    model_name: str
    context_window: int
    tokens_remaining: int
    usage_percent: float
    section_tokens: Dict[str, int] = field(default_factory=dict)


@dataclass
class QualityScore:
    """Overall quality score for a prompt."""
    total: int             # 0-100
    breakdown: Dict[str, int] = field(default_factory=dict)
    # e.g., {"structure": 90, "clarity": 75, "safety": 60, "efficiency": 85}

    @property
    def grade(self) -> str:
        if self.total >= 90:
            return "A"
        elif self.total >= 80:
            return "B"
        elif self.total >= 70:
            return "C"
        elif self.total >= 60:
            return "D"
        return "F"


@dataclass
class Report:
    """Complete analysis report for a prompt."""
    prompt_text: str
    issues: List[Issue]
    token_budget: Optional[TokenBudget] = None
    quality_score: Optional[QualityScore] = None

    @property
    def errors(self) -> List[Issue]:
        return [i for i in self.issues if i.severity == Severity.ERROR]

    @property
    def warnings(self) -> List[Issue]:
        return [i for i in self.issues if i.severity == Severity.WARNING]

    @property
    def suggestions(self) -> List[Issue]:
        return [i for i in self.issues if i.severity == Severity.SUGGESTION]

    @property
    def infos(self) -> List[Issue]:
        return [i for i in self.issues if i.severity == Severity.INFO]

    @property
    def has_issues(self) -> bool:
        return len(self.errors) > 0 or len(self.warnings) > 0

    def summary_counts(self) -> Dict[str, int]:
        return {
            "errors": len(self.errors),
            "warnings": len(self.warnings),
            "suggestions": len(self.suggestions),
            "info": len(self.infos),
            "total": len(self.issues),
        }

    def to_dict(self) -> Dict:
        """Serialize report to dictionary."""
        result = {
            "issues": [
                {
                    "rule_id": i.rule_id,
                    "severity": i.severity.value,
                    "message": i.message,
                    "line": i.line,
                    "line_content": i.line_content,
                    "suggestion": i.suggestion,
                    "category": i.category,
                    "related_line": i.related_line,
                }
                for i in self.issues
            ],
            "summary": self.summary_counts(),
        }
        if self.token_budget:
            result["token_budget"] = {
                "total_tokens": self.token_budget.total_tokens,
                "model": self.token_budget.model_name,
                "context_window": self.token_budget.context_window,
                "tokens_remaining": self.token_budget.tokens_remaining,
                "usage_percent": round(self.token_budget.usage_percent, 2),
            }
        if self.quality_score:
            result["quality_score"] = {
                "total": self.quality_score.total,
                "grade": self.quality_score.grade,
                "breakdown": self.quality_score.breakdown,
            }
        return result
