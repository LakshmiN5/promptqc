"""Semantic rules — contradiction and redundancy detection using embeddings."""

from typing import List, Tuple
import numpy as np

from promptqc.rules.base import BaseRule
from promptqc.models import Issue, Severity
from promptqc.parser import ParsedPrompt


# Pairs of words/phrases that often indicate contradictory intent
OPPOSING_TERMS = [
    ({"concise", "brief", "short", "succinct", "terse", "minimal"},
     {"detailed", "thorough", "comprehensive", "extensive", "elaborate", "verbose", "in-depth"}),
    ({"formal", "professional", "corporate"},
     {"casual", "informal", "relaxed", "conversational", "friendly"}),
    ({"always", "must", "required", "mandatory"},
     {"never", "must not", "forbidden", "prohibited", "do not"}),
    ({"can", "allowed", "permitted", "able to", "may"},
     {"cannot", "can not", "not allowed", "unable", "must not", "may not"}),
    ({"include", "add", "provide", "show"},
     {"exclude", "omit", "hide", "remove", "skip"}),
    ({"strict", "rigid", "exact", "precise"},
     {"flexible", "lenient", "approximate", "loose"}),
    ({"fast", "quick", "rapid", "immediate"},
     {"slow", "careful", "deliberate", "thorough"}),
    ({"simple", "basic", "plain"},
     {"complex", "advanced", "sophisticated"}),
]


def _has_opposing_terms(text1: str, text2: str) -> bool:
    """Check if two texts contain known opposing term pairs."""
    t1_lower = text1.lower()
    t2_lower = text2.lower()
    for group_a, group_b in OPPOSING_TERMS:
        a_in_1 = any(term in t1_lower for term in group_a)
        b_in_2 = any(term in t2_lower for term in group_b)
        a_in_2 = any(term in t2_lower for term in group_a)
        b_in_1 = any(term in t1_lower for term in group_b)
        if (a_in_1 and b_in_2) or (a_in_2 and b_in_1):
            return True
    return False


def _compute_pairwise_similarities(
    instructions: List[Tuple[int, str]],
    analyzer,
) -> List[Tuple[int, int, float]]:
    """Compute pairwise cosine similarities between instructions."""
    if len(instructions) < 2:
        return []

    texts = [text for _, text in instructions]
    embeddings = analyzer.embedding_model.encode(texts, show_progress_bar=False)
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1, norms)  # avoid division by zero
    normalized = embeddings / norms
    similarity_matrix = np.dot(normalized, normalized.T)

    results = []
    for i in range(len(instructions)):
        for j in range(i + 1, len(instructions)):
            results.append((i, j, float(similarity_matrix[i, j])))
    return results


class ContradictionRule(BaseRule):
    """
    PQ001: Detect contradictory instructions within the prompt.

    Finds instruction pairs that are semantically related (share a topic)
    but contain opposing directives, which causes inconsistent LLM behavior.
    """

    rule_id = "PQ001"
    name = "contradiction-detection"
    category = "contradiction"
    description = "Detects contradictory instructions that cause inconsistent behavior"
    needs_embeddings = True

    # Similarity thresholds
    MIN_TOPIC_SIMILARITY = 0.35  # Must share some topic
    MAX_TOPIC_SIMILARITY = 0.85  # If too similar, it's redundancy not contradiction

    def check(self, parsed: ParsedPrompt, analyzer) -> List[Issue]:
        issues = []
        instructions = parsed.all_instructions

        if len(instructions) < 2:
            return issues

        similarities = _compute_pairwise_similarities(instructions, analyzer)

        for i, j, sim in similarities:
            line_i, text_i = instructions[i]
            line_j, text_j = instructions[j]

            # Look for instructions that share a topic but have opposing terms
            if (self.MIN_TOPIC_SIMILARITY <= sim <= self.MAX_TOPIC_SIMILARITY
                    and _has_opposing_terms(text_i, text_j)):
                issues.append(Issue(
                    rule_id=self.rule_id,
                    severity=Severity.WARNING,
                    message=f'Potential contradiction: "{text_i[:60]}..." conflicts with "{text_j[:60]}..."',
                    line=line_i,
                    line_content=parsed.get_line_text(line_i),
                    suggestion=(
                        "Resolve the conflict by choosing one directive, or add context "
                        "to clarify when each applies."
                    ),
                    related_line=line_j,
                    related_content=parsed.get_line_text(line_j),
                    category=self.category,
                ))

        return issues


class RedundancyRule(BaseRule):
    """
    PQ002: Detect redundant instructions that waste tokens.

    Finds instruction pairs that say essentially the same thing in different
    words. Removing duplicates reduces token usage without losing meaning.
    """

    rule_id = "PQ002"
    name = "redundancy-detection"
    category = "redundancy"
    description = "Detects redundant instructions that waste tokens"
    needs_embeddings = True

    REDUNDANCY_THRESHOLD = 0.88  # Above this = semantically redundant

    def check(self, parsed: ParsedPrompt, analyzer) -> List[Issue]:
        issues = []
        instructions = parsed.all_instructions

        if len(instructions) < 2:
            return issues

        similarities = _compute_pairwise_similarities(instructions, analyzer)

        # Track which pairs we've already flagged to avoid duplicate reports
        flagged = set()

        for i, j, sim in similarities:
            line_i, text_i = instructions[i]
            line_j, text_j = instructions[j]

            # Skip if exact same line
            if line_i == line_j:
                continue

            # Skip exact duplicates (handled separately if needed)
            if text_i.strip().lower() == text_j.strip().lower():
                issues.append(Issue(
                    rule_id=self.rule_id,
                    severity=Severity.WARNING,
                    message=f'Exact duplicate instruction found',
                    line=line_j,
                    line_content=parsed.get_line_text(line_j),
                    suggestion=f"Remove this line — it's identical to line {line_i}.",
                    related_line=line_i,
                    related_content=parsed.get_line_text(line_i),
                    category=self.category,
                ))
                flagged.add((i, j))
                continue

            if sim >= self.REDUNDANCY_THRESHOLD and (i, j) not in flagged:
                issues.append(Issue(
                    rule_id=self.rule_id,
                    severity=Severity.SUGGESTION,
                    message=(
                        f'Redundant instructions ({sim:.0%} similar): '
                        f'"{text_i[:50]}..." ≈ "{text_j[:50]}..."'
                    ),
                    line=line_j,
                    line_content=parsed.get_line_text(line_j),
                    suggestion=(
                        f"Consider merging with line {line_i} to save tokens. "
                        f"Keep the more specific version."
                    ),
                    related_line=line_i,
                    related_content=parsed.get_line_text(line_i),
                    category=self.category,
                ))
                flagged.add((i, j))

        return issues
