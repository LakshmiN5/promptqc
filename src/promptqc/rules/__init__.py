"""Rule registry — collects and exposes all available rules."""

from typing import List, Dict, Type

from promptqc.rules.base import BaseRule
from promptqc.rules.semantic import ContradictionRule, RedundancyRule
from promptqc.rules.patterns import AntiPatternRule, TokenWasteRule, InjectionRiskRule
from promptqc.rules.structure import CompletenessRule
from promptqc.rules.tokens import TokenBudgetRule


# All available rule classes
ALL_RULE_CLASSES: Dict[str, Type[BaseRule]] = {
    "contradiction": ContradictionRule,
    "redundancy": RedundancyRule,
    "anti-pattern": AntiPatternRule,
    "token-waste": TokenWasteRule,
    "injection": InjectionRiskRule,
    "completeness": CompletenessRule,
    "token-budget": TokenBudgetRule,
}


def get_default_rules(model: str = "gpt-4o", budget: int = None) -> List[BaseRule]:
    """Get default set of all rules."""
    rules: List[BaseRule] = [
        ContradictionRule(),
        RedundancyRule(),
        AntiPatternRule(),
        TokenWasteRule(),
        InjectionRiskRule(),
        CompletenessRule(),
        TokenBudgetRule(model=model, budget=budget),
    ]
    return rules


def get_fast_rules(model: str = "gpt-4o", budget: int = None) -> List[BaseRule]:
    """Get only pattern-based rules (no embeddings, instant execution)."""
    return [
        AntiPatternRule(),
        TokenWasteRule(),
        InjectionRiskRule(),
        CompletenessRule(),
        TokenBudgetRule(model=model, budget=budget),
    ]
