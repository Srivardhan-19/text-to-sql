"""
Exact Match (EM) Evaluation Metric.
Normalizes SQL statements via SQLGlot AST canonicalization for invariant structural comparison.
"""
from __future__ import annotations

import sqlglot


def normalize_sql(sql: str, dialect: str = "mysql") -> str:
    """Normalizes SQL syntax, aliases, and formatting for invariant comparison."""
    try:
        parsed = sqlglot.parse_one(sql.strip().rstrip(";"), read=dialect)
        # Transpile into normalized lowercase without extraneous whitespace
        return parsed.sql(dialect=dialect, pretty=False, comments=False).lower()
    except Exception:
        # Fallback to string normalization
        return " ".join(sql.lower().replace(";", "").split())


def compute_exact_match(predicted_sql: str, gold_sql: str, dialect: str = "mysql") -> bool:
    """Returns True if the normalized AST representation of both queries matches."""
    if not predicted_sql or not gold_sql:
        return False
    norm_pred = normalize_sql(predicted_sql, dialect)
    norm_gold = normalize_sql(gold_sql, dialect)
    return norm_pred == norm_gold

