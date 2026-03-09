"""Structural completeness checks for prompt quality."""

import re
from typing import List

from promptqc.rules.base import BaseRule
from promptqc.models import Issue, Severity
from promptqc.parser import ParsedPrompt


class CompletenessRule(BaseRule):
    """
    PQ008: Check structural completeness of the prompt.

    Well-structured prompts typically include:
    - Role definition ("You are...")
    - Clear instructions/task description
    - Output format specification
    - Constraints or boundaries
    - Examples (for complex tasks)

    Research shows prompts with explicit structure produce 40%+ more
    consistent outputs.
    """

    rule_id = "PQ008"
    name = "completeness-check"
    category = "structure"
    description = "Checks for essential prompt components"
    needs_embeddings = False

    def check(self, parsed: ParsedPrompt, analyzer) -> List[Issue]:
        issues = []
        full_text = parsed.raw_text
        full_lower = full_text.lower()

        # 1. Check for role definition
        has_role = bool(re.search(
            r"\byou\s+are\s+(a|an|the)\b|\bact\s+as\b|\byour\s+role\s+is\b|\bas\s+(a|an)\s+\w+,?\s+you\b",
            full_lower,
        ))
        if not has_role:
            issues.append(Issue(
                rule_id=self.rule_id,
                severity=Severity.SUGGESTION,
                message='No role definition found — prompts with explicit roles produce more consistent behavior',
                line=1,
                line_content=parsed.get_line_text(1),
                suggestion='Start with a role definition like "You are a [specific role] specialized in [domain]."',
                category=self.category,
            ))

        # 2. Check for output format
        has_format = bool(re.search(
            r"\b(output|response|answer|reply|format|respond)\b.*\b(format|json|markdown|xml|bullet|numbered|structured|table)\b"
            r"|\b(format|structure)\b.*\b(output|response)\b"
            r"|\breturn\s+(as|in|a)\b.*\b(json|xml|yaml|markdown|list|csv)\b",
            full_lower,
        ))
        # Also check section headers
        format_sections = any(
            re.search(r"\b(output|format|response\s+format|structure)\b", s.name.lower())
            for s in parsed.sections
        )
        if not has_format and not format_sections:
            issues.append(Issue(
                rule_id=self.rule_id,
                severity=Severity.SUGGESTION,
                message="No output format specification found — can lead to inconsistent response formats",
                line=1,
                line_content=parsed.get_line_text(1),
                suggestion='Add an output format section, e.g., "## Output Format\\nRespond in JSON with keys: ..."',
                category=self.category,
            ))

        # 3. Check for constraints/boundaries
        has_constraints = bool(re.search(
            r"\b(constraint|boundar|limitation|restrict|must\s+not|never|do\s+not|forbidden|prohibited|scope|off.?limit)\b",
            full_lower,
        ))
        constraint_sections = any(
            re.search(r"\b(constraint|rule|boundar|limit|safety|guard)\b", s.name.lower())
            for s in parsed.sections
        )
        if not has_constraints and not constraint_sections:
            issues.append(Issue(
                rule_id=self.rule_id,
                severity=Severity.SUGGESTION,
                message="No constraints or boundaries defined — the LLM may act outside intended scope",
                line=1,
                line_content=parsed.get_line_text(1),
                suggestion='Add constraints, e.g., "## Constraints\\n- Only answer questions about [topic]\\n- Never provide [restricted info]"',
                category=self.category,
            ))

        # 4. Check if prompt is too short for its complexity
        section_count = len(parsed.sections)
        instruction_count = len(parsed.all_instructions)

        if instruction_count > 10 and section_count <= 1:
            issues.append(Issue(
                rule_id="PQ009",
                severity=Severity.SUGGESTION,
                message=f"Prompt has {instruction_count} instructions but no section headers — consider organizing with ## headings",
                line=1,
                line_content=parsed.get_line_text(1),
                suggestion="Break the prompt into sections (e.g., ## Role, ## Instructions, ## Output Format, ## Constraints)",
                category=self.category,
            ))

        # 5. Check for examples in complex prompts
        has_examples = bool(re.search(
            r"\b(example|e\.g\.|for\s+instance|sample|such\s+as|here\s+is)\b",
            full_lower,
        ))
        example_sections = any(
            re.search(r"\b(example|sample|demo)\b", s.name.lower())
            for s in parsed.sections
        )
        if instruction_count > 8 and not has_examples and not example_sections:
            issues.append(Issue(
                rule_id="PQ010",
                severity=Severity.INFO,
                message="Complex prompt with no examples — few-shot examples can significantly improve output consistency",
                line=1,
                line_content=parsed.get_line_text(1),
                suggestion='Add an "## Examples" section with 1-3 input/output pairs',
                category=self.category,
            ))

        return issues
