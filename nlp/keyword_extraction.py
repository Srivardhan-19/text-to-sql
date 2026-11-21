"""
Keyword, Condition, and Operator Extraction Module.
Detects numeric conditions, string filters, comparison operators, aggregate terms, limit clauses, and ordering.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ConditionClause:
    column_hint: Optional[str]
    operator: str
    value: str
    raw_span: str
    is_numeric: bool = True


@dataclass
class ExtractedKeywords:
    aggregates: list[str]  # e.g. ["AVG", "COUNT"]
    conditions: list[ConditionClause]
    order_by_direction: Optional[str]  # "ASC", "DESC"
    order_by_keyword: Optional[str] = None  # e.g. "cgpa", "salary"
    limit: Optional[int] = None
    group_by_terms: list[str] = field(default_factory=list)
    distinct: bool = False


class KeywordExtractor:
    """Extracts SQL-relevant syntactic constructs from natural language text."""

    AGG_MAP = {
        "average": "AVG", "avg": "AVG", "mean": "AVG",
        "count": "COUNT", "number of": "COUNT", "how many": "COUNT", "total number": "COUNT",
        "sum": "SUM", "total": "SUM",
        "maximum": "MAX", "max": "MAX", "highest": "MAX", "greatest": "MAX",
        "minimum": "MIN", "min": "MIN", "lowest": "MIN", "least": "MIN"
    }

    OPERATOR_PATTERNS = [
        (r"(?:more\s+than|greater\s+than|above|exceeding)\s+([0-9]+(?:\.[0-9]+)?)", ">"),
        (r"(?:less\s+than|fewer\s+than|below|under)\s+([0-9]+(?:\.[0-9]+)?)", "<"),
        (r"(?:at\s+least|greater\s+than\s+or\s+equal\s+to|>=)\s+([0-9]+(?:\.[0-9]+)?)", ">="),
        (r"(?:at\s+most|less\s+than\s+or\s+equal\s+to|<=)\s+([0-9]+(?:\.[0-9]+)?)", "<="),
        (r"(?:equal\s+to|equals|=)\s+([0-9]+(?:\.[0-9]+)?)", "="),
    ]

    STRING_FILTER_PATTERNS = [
        (r"(?:in|for|of|department|dept|subject|course|named)\s+['\"]([A-Za-z0-9_\s-]+)['\"]", "="),
        (r"\b(?:in|of)\s+([A-Z]{2,6})\b", "="),  # Acronyms like CSE, ECE, DBMS, OS
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
                    raw_span=match.group(0),
                    is_numeric=True
                ))

        # String / Literal filters (e.g. 'DBMS', 'Computer Science', CSE)
        for pattern, op in self.STRING_FILTER_PATTERNS:
            for match in re.finditer(pattern, text):
                val = match.group(1).strip()
                # Exclude SQL stopwords
                if val.lower() not in ("each", "every", "the", "a", "all", "students", "courses", "instructors"):
                    conditions.append(ConditionClause(
                        column_hint=None,
                        operator=op,
                        value=val,
                        raw_span=match.group(0),
                        is_numeric=False
                    ))

        return conditions

    def extract_order_by(self, text: str) -> tuple[Optional[str], Optional[str]]:
        """Returns (direction, target_hint) if an ordering request is found."""
        lower = text.lower()
        if re.search(r"\b(top|highest|greatest|maximum|max|best|descending|desc)\b", lower):
            return "DESC", None
        if re.search(r"\b(bottom|lowest|least|minimum|min|worst|ascending|asc)\b", lower):
            return "ASC", None
        if re.search(r"\b(ordered\s+by|sorted\s+by|order\s+by|sort\s+by)\b", lower):
            return "ASC", None
        return None, None

    def extract_limit(self, text: str) -> Optional[int]:
        match = re.search(r"\b(?:top|first|limit)\s+([0-9]+)\b", text, flags=re.IGNORECASE)
        if match:
            return int(match.group(1))
        return None

    def extract_distinct(self, text: str) -> bool:
        return bool(re.search(r"\b(distinct|unique|different)\b", text, flags=re.IGNORECASE))

    def extract(self, text: str) -> ExtractedKeywords:
        direction, hint = self.extract_order_by(text)
        return ExtractedKeywords(
            aggregates=self.extract_aggregates(text),
            conditions=self.extract_conditions(text),
            order_by_direction=direction,
            order_by_keyword=hint,
            limit=self.extract_limit(text),
            distinct=self.extract_distinct(text)
        )
