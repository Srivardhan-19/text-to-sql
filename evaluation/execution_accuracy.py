"""
Execution Accuracy (EX) Evaluation Metric.
Executes predicted and gold SQL against the database state and verifies multiset record equivalence.
"""
from __future__ import annotations

import logging
from typing import Any
from sqlalchemy import text
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)


def compute_execution_accuracy(predicted_sql: str, gold_sql: str, engine: Engine) -> bool:
    """
    Executes predicted and reference SQL against the same database engine.
    Returns True if both produce identical result sets.
    """
    if not predicted_sql or not gold_sql:
        return False

    try:
        with engine.connect() as conn:
            gold_res = conn.execute(text(gold_sql)).fetchall()
            pred_res = conn.execute(text(predicted_sql)).fetchall()

        # Convert rows to comparable tuples
        gold_tuples = [tuple(row) for row in gold_res]
        pred_tuples = [tuple(row) for row in pred_res]

        # If ORDER BY is in gold SQL, test sequence order
        if "order by" in gold_sql.lower():
            return gold_tuples == pred_tuples

        # Otherwise compare as multiset / unordered frequency
        return sorted(str(t) for t in gold_tuples) == sorted(str(t) for t in pred_tuples)

    except Exception as e:
        logger.debug(f"Execution accuracy evaluation failed: {e}")
        return False

