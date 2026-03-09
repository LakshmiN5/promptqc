"""Base class for all quality check rules."""

from abc import ABC, abstractmethod
from typing import List, TYPE_CHECKING

from promptqc.models import Issue

if TYPE_CHECKING:
    from promptqc.parser import ParsedPrompt
    from promptqc.analyzer import PromptAnalyzer


class BaseRule(ABC):
    """Base class for prompt quality rules."""

    rule_id: str = ""          # e.g., "PQ001"
    name: str = ""             # e.g., "contradiction-detection"
    category: str = ""         # e.g., "contradiction"
    description: str = ""      # Human-readable description
    needs_embeddings: bool = False  # Whether this rule requires the embedding model

    @abstractmethod
    def check(self, parsed: "ParsedPrompt", analyzer: "PromptAnalyzer") -> List[Issue]:
        """
        Run this rule against a parsed prompt.

        Args:
            parsed: The parsed prompt structure
            analyzer: The analyzer instance (provides access to embedding model)

        Returns:
            List of issues found
        """
        ...
