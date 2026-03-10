"""Rule registry — collects and exposes all available rules."""

import importlib
from typing import List, Dict, Optional, Type

from promptqc.rules.base import BaseRule
from promptqc.rules.semantic import ContradictionRule, RedundancyRule
from promptqc.rules.patterns import AntiPatternRule, TokenWasteRule, InjectionRiskRule
from promptqc.rules.structure import CompletenessRule
from promptqc.rules.tokens import TokenBudgetRule
from promptqc.rules.variables import TemplateVariableRule, VariableSandboxRule


# All available rule classes
ALL_RULE_CLASSES: Dict[str, Type[BaseRule]] = {
    "contradiction": ContradictionRule,
    "redundancy": RedundancyRule,
    "anti-pattern": AntiPatternRule,
    "token-waste": TokenWasteRule,
    "injection": InjectionRiskRule,
    "completeness": CompletenessRule,
    "token-budget": TokenBudgetRule,
    "template-variable": TemplateVariableRule,
    "variable-sandbox": VariableSandboxRule,
}


def load_custom_rules(dotted_paths: List[str]) -> List[BaseRule]:
    """
    Dynamically load custom rule classes from dotted Python paths.

    Each path should point to a class that inherits from BaseRule.
    Example: "my_team.rules.BrandRule" will import BrandRule from my_team.rules.

    Args:
        dotted_paths: List of fully-qualified class names.

    Returns:
        List of instantiated custom rule objects.
    """
    rules = []
    for path in dotted_paths:
        module_path, _, class_name = path.rpartition(".")
        if not module_path:
            raise ValueError(
                f"Invalid custom rule path: {path!r} — "
                f"expected format: 'my_package.my_module.MyRuleClass'"
            )
        try:
            module = importlib.import_module(module_path)
            cls = getattr(module, class_name)
        except (ImportError, AttributeError) as e:
            raise ValueError(f"Cannot load custom rule {path!r}: {e}")

        if not (isinstance(cls, type) and issubclass(cls, BaseRule)):
            raise ValueError(
                f"Custom rule {path!r} must be a class that inherits from "
                f"promptqc.rules.base.BaseRule"
            )
        rules.append(cls())
    return rules


def get_default_rules(
    model: str = "gpt-4o",
    budget: int = None,
    custom: Optional[List[str]] = None,
) -> List[BaseRule]:
    """Get default set of all rules (including semantic analysis)."""
    rules: List[BaseRule] = [
        ContradictionRule(),
        RedundancyRule(),
        AntiPatternRule(),
        TokenWasteRule(),
        InjectionRiskRule(),
        CompletenessRule(),
        TemplateVariableRule(),
        VariableSandboxRule(),
        TokenBudgetRule(model=model, budget=budget),
    ]
    if custom:
        rules.extend(load_custom_rules(custom))
    return rules


def get_fast_rules(
    model: str = "gpt-4o",
    budget: int = None,
    custom: Optional[List[str]] = None,
) -> List[BaseRule]:
    """Get only pattern-based rules (no embeddings, instant execution)."""
    rules = [
        AntiPatternRule(),
        TokenWasteRule(),
        InjectionRiskRule(),
        CompletenessRule(),
        TemplateVariableRule(),
        VariableSandboxRule(),
        TokenBudgetRule(model=model, budget=budget),
    ]
    if custom:
        rules.extend(load_custom_rules(custom))
    return rules


def get_judge_rules(
    model: str = "gpt-4o",
    budget: int = None,
    judge_model: str = "groq/llama3-8b-8192",
    custom: Optional[List[str]] = None,
) -> List[BaseRule]:
    """Get rules including LLM-as-a-Judge (replaces embedding-based semantic rules)."""
    from promptqc.rules.llm_judge import LLMJudgeRule

    rules = [
        # Fast heuristic rules (always run)
        AntiPatternRule(),
        TokenWasteRule(),
        InjectionRiskRule(),
        CompletenessRule(),
        TemplateVariableRule(),
        VariableSandboxRule(),
        TokenBudgetRule(model=model, budget=budget),
        # LLM Judge (replaces ContradictionRule + RedundancyRule)
        LLMJudgeRule(model=judge_model),
    ]
    if custom:
        rules.extend(load_custom_rules(custom))
    return rules
