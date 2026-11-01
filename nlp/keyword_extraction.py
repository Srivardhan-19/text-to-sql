"""
Keyword, Condition, and Operator Extraction Module.
Detects numeric conditions, comparison operators, aggregate terms, and limit clauses.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class ConditionClause:
    column_hint: Optional[str]
    operator: str
    value: str
    raw_span: str


@dataclass
class ExtractedKeywords:
    aggregates: list[str]  # e.g. ["AVG", "COUNT"]
    conditions: list[ConditionClause]
    order_by_direction: Optional[str]  # "ASC", "DESC"
    limit: Optional[int]
    group_by_terms: list[str]


class KeywordExtractor:
    """Extracts SQL-relevant syntactic constructs from natural language text."""

    AGG_MAP = {
        "average": "AVG", "avg": "AVG", "mean": "AVG",
        "count": "COUNT", "number of": "COUNT", "how many": "COUNT", "total number": "COUNT",
        "sum": "SUM", "total": "SUM",
        "maximum": "MAX", "max": "MAX", "highest": "MAX", "greatest": "MAX", "top": "MAX",
        "minimum": "MIN", "min": "MIN", "lowest": "MIN", "least": "MIN", "bottom": "MIN"
    }

    OPERATOR_PATTERNS = [
        (r"(?:more\s+than|greater\s+than|above|exceeding)\s+([0-9]+(?:\.[0-9]+)?)", ">"),
        (r"(?:less\s+than|fewer\s+than|below|under)\s+([0-9]+(?:\.[0-9]+)?)", "<"),
        (r"(?:at\s+least|greater\s+than\s+or\s+equal\s+to|>=)\s+([0-9]+(?:\.[0-9]+)?)", ">="),
        (r"(?:at\s+most|less\s+than\s+or\s+equal\s+to|<=)\s+([0-9]+(?:\.[0-9]+)?)", "<="),
        (r"(?:equal\s+to|equals|=)\s+([0-9]+(?:\.[0-9]+)?)", "="),
    ]

    STRING_CONDITION_PATTERNS = [
        (r"(?:in|for|of|department|dept|subject)\s+['\"]?([A-Za-z0-9_-]+)['\"]?", "="),
        (r"(?:named|called)\s+['\"]?([A-Za-z\s]+)['\"]?", "="),
    ]

    def extract_aggregates(self, text: str) -> list[str]:
        lower = text.lower()
        aggs = []
        for phrase, agg in self.AGG_MAP.items():
            if re.search(r"\b" + re.escape(phrase) + r"\b", lower):
                if agg not in aggs:
                    aggs.append(agg)
        return aggs

    def extract_conditions(self, text: str) -> list[ConditionClause]:
        conditions: list[ConditionClause] = []
        lower = text.lower()

        # Numeric comparisons
        for pattern, op in self.OPERATOR_PATTERNS:
            for match in re.finditer(pattern, lower):
                val = match.group(1)
                conditions.append(ConditionClause(
                    column_hint=None,
                    operator=op,
                    value=val,
                    raw_span=match.group(0)
                ))

        # String conditions (e.g. in DBMS, for CSE)
        # Match common subject / department filter patterns
        subj_match = re.search(r"\b(?:in|subject|course)\s+['\"]?([A-Za-z0-9_-]{2,})['\"]?", lower)
        if subj_match:
            val = subj_match.group(1).upper()
            if val not in ("THE", "EACH", "EVERY", "ALL", "ORDER"):
                conditions.append(ConditionClause(
                    column_hint="subject",
                    operator="=",
                    value=val,
                    raw_span=subj_match.group(0)
                ))

        return conditions

    def extract_limit_and_order(self, text: str) -> tuple[Optional[int], Optional[str]]:
        lower = text.lower()
        limit = None
        direction = None

        # Detect top N
        top_match = re.search(r"\b(?:top|first)\s+([0-9]+)\b", lower)
        if top_match:
            limit = int(top_match.group(1))
            direction = "DESC"

        # Detect bottom N
        bot_match = re.search(r"\b(?:bottom|lowest)\s+([0-9]+)\b", lower)
        if bot_match:
            limit = int(bot_match.group(1))
            direction = "ASC"

        # Explicit order terms
        if not direction:
            if any(k in lower for k in ["highest", "descending", "best", "greatest"]):
                direction = "DESC"
            elif any(k in lower for k in ["lowest", "ascending", "least"]):
                direction = "ASC"

        return limit, direction

    def extract(self, text: str) -> ExtractedKeywords:
        aggs = self.extract_aggregates(text)
        conditions = self.extract_conditions(text)
        limit, direction = self.extract_limit_and_order(text)

        # Detect grouping hints
        lower = text.lower()
        group_terms = []
        if re.search(r"\b(?:each|every|per|by)\s+([a-z_]+)\b", lower):
            for match in re.finditer(r"\b(?:each|every|per|by)\s+([a-z_]+)\b", lower):
                group_terms.append(match.group(1))

        return ExtractedKeywords(
            aggregates=aggs,
            conditions=conditions,
            order_by_direction=direction,
            limit=limit,
            group_by_terms=group_terms
        )

