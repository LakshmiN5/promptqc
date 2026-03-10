"""Core analysis engine for promptqc."""

from typing import List, Optional, Set

from promptqc.models import Issue, Report, QualityScore, Severity
from promptqc.parser import parse_prompt, ParsedPrompt
from promptqc.rules.base import BaseRule
from promptqc.rules import get_default_rules, get_fast_rules, get_judge_rules
from promptqc.config import PromptQCConfig, parse_inline_disables, load_config


class PromptAnalyzer:
    """
    Main analyzer that runs quality checks on prompts.

    Usage:
        # Fast mode (instant, heuristic-only)
        analyzer = PromptAnalyzer(fast_mode=True)
        report = analyzer.analyze("You are a helpful assistant...")

        # Full mode (includes semantic embedding analysis)
        analyzer = PromptAnalyzer()
        report = analyzer.analyze("You are a helpful assistant...")

        # Judge mode (uses LLM for deep analysis)
        analyzer = PromptAnalyzer(judge_model="groq/llama3-8b-8192")
        report = analyzer.analyze("You are a helpful assistant...")
    """

    def __init__(
        self,
        rules: Optional[List[BaseRule]] = None,
        model_name: str = "all-MiniLM-L6-v2",
        token_model: str = "gpt-4o",
        token_budget: Optional[int] = None,
        fast_mode: bool = False,
        judge_model: Optional[str] = None,
        config: Optional[PromptQCConfig] = None,
    ):
        """
        Initialize the analyzer.

        Args:
            rules: Custom list of rules (uses defaults if None)
            model_name: Sentence transformer model for semantic analysis
            token_model: Model name for token counting (e.g., "gpt-4o")
            token_budget: Optional explicit token budget to enforce
            fast_mode: If True, skip embedding-based rules for instant results
            judge_model: LiteLLM model identifier for LLM judge mode
                         (e.g., "groq/llama3-8b-8192", "ollama/phi3", "gpt-4o-mini")
            config: Optional PromptQCConfig (loaded from file if None)
        """
        self._model_name = model_name
        self._embedding_model = None
        self._token_budget = None  # Set by TokenBudgetRule during analysis
        self.token_model = token_model
        self.judge_model = judge_model

        # Load config
        self.config = config or load_config()

        # Apply config overrides
        if self.config.judge_model and judge_model is None:
            self.judge_model = self.config.judge_model

        # Load custom rules from config (if any)
        custom = self.config.custom_rules or None

        if rules is not None:
            self.rules = rules
        elif self.judge_model:
            self.rules = get_judge_rules(
                model=token_model,
                budget=token_budget,
                judge_model=self.judge_model,
                custom=custom,
            )
        elif fast_mode:
            self.rules = get_fast_rules(model=token_model, budget=token_budget, custom=custom)
        else:
            self.rules = get_default_rules(model=token_model, budget=token_budget, custom=custom)

    @property
    def embedding_model(self):
        """Lazy-load the sentence transformer model with user-visible progress."""
        if self._embedding_model is None:
            from sentence_transformers import SentenceTransformer
            from rich.console import Console
            with Console(stderr=True).status(
                f"[dim]Downloading semantic model ({self._model_name})…[/dim]",
                spinner="dots",
            ):
                self._embedding_model = SentenceTransformer(self._model_name)
        return self._embedding_model

    def analyze(self, prompt_text: str) -> Report:
        """
        Run all quality checks on a prompt.

        Args:
            prompt_text: The system prompt text to analyze

        Returns:
            Report with all issues, token budget, and quality score
        """
        # Parse the prompt
        parsed = parse_prompt(prompt_text)

        # Parse inline disable comments
        inline_disables = parse_inline_disables(prompt_text)

        # Get globally disabled rules from config
        disabled_rules = self.config.disabled_rule_set

        # Run all rules
        all_issues: List[Issue] = []
        for rule in self.rules:
            # Skip globally disabled rules
            if rule.rule_id in disabled_rules:
                continue

            try:
                issues = rule.check(parsed, self)

                # Filter out inline-disabled issues
                for issue in issues:
                    line_disables = inline_disables.get(issue.line, set())
                    if "*" in line_disables or issue.rule_id in line_disables:
                        continue  # Suppressed by inline comment
                    all_issues.append(issue)

            except Exception as e:
                # Don't crash on individual rule failures
                all_issues.append(Issue(
                    rule_id=rule.rule_id,
                    severity=Severity.INFO,
                    message=f"Rule {rule.name} failed: {str(e)}",
                    line=1,
                    line_content=parsed.get_line_text(1),
                    category="internal",
                ))

        # Sort issues by line number, then severity
        severity_order = {
            Severity.ERROR: 0,
            Severity.WARNING: 1,
            Severity.SUGGESTION: 2,
            Severity.INFO: 3,
        }
        all_issues.sort(key=lambda i: (i.line, severity_order.get(i.severity, 99)))

        # Compute quality score
        quality_score = self._compute_quality_score(all_issues, parsed)

        return Report(
            prompt_text=prompt_text,
            issues=all_issues,
            token_budget=self._token_budget,
            quality_score=quality_score,
        )

    def _compute_quality_score(
        self,
        issues: List[Issue],
        parsed: ParsedPrompt,
    ) -> QualityScore:
        """
        Compute an overall quality score based on issues found.

        Scoring:
        - Start at 100
        - Deduct points based on issue severity and category
        - Minimum score is 0
        """
        score = 100

        # Category-specific sub-scores start at 100
        categories = {
            "structure": 100,
            "clarity": 100,
            "security": 100,
            "efficiency": 100,
            "consistency": 100,
        }

        # Map rule categories to score categories
        category_map = {
            "contradiction": "consistency",
            "redundancy": "efficiency",
            "anti-pattern": "clarity",
            "clarity": "clarity",
            "efficiency": "efficiency",
            "security": "security",
            "structure": "structure",
            "semantic": "consistency",
            "internal": "structure",
        }

        # Deduction amounts by severity
        deductions = {
            Severity.ERROR: 15,
            Severity.WARNING: 8,
            Severity.SUGGESTION: 3,
            Severity.INFO: 0,
        }

        for issue in issues:
            deduction = deductions.get(issue.severity, 0)
            score = max(0, score - deduction)

            # Apply to sub-category
            cat = category_map.get(issue.category, "clarity")
            if cat in categories:
                categories[cat] = max(0, categories[cat] - deduction * 2)

        return QualityScore(
            total=score,
            breakdown=categories,
        )
