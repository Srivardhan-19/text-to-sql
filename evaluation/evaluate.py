"""
Benchmark Evaluation Harness.
Orchestrates systematic evaluation of the Traditional NLP & Rule-Based Text-to-SQL system.
Evaluates Exact Match (EM), Execution Accuracy (EX), SQL Validity, and Latency.
"""
from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any
import pandas as pd
from sqlalchemy.engine import Engine

from database.schema_detector import DatabaseSchema
from evaluation.dataset_loader import BenchmarkItem, DatasetLoader
from evaluation.exact_match import compute_exact_match
from evaluation.execution_accuracy import compute_execution_accuracy
from generation.baseline_generator import BaselineSQLGenerator
from validation.sql_validator import SQLValidator

logger = logging.getLogger(__name__)


def evaluate_approach(
    approach_name: str,
    generator_func,
    items: list[BenchmarkItem],
    engine: Engine,
    validator: SQLValidator
) -> list[dict[str, Any]]:
    """Evaluates a generation approach across benchmark items."""
    results = []

    for item in items:
        start_gen = time.perf_counter()
        try:
            gen_res = generator_func(item.question)
            pred_sql = getattr(gen_res, "sql", str(gen_res)).strip()
        except Exception as e:
            pred_sql = ""
        gen_time_ms = (time.perf_counter() - start_gen) * 1000

        # Validate SQL
        val_res = validator.validate(pred_sql)
        is_valid = val_res.is_valid

        # Compute Exact Match (EM)
        em = compute_exact_match(pred_sql, item.gold_sql)

        # Compute Execution Accuracy (EX)
        ex = compute_execution_accuracy(pred_sql, item.gold_sql, engine) if is_valid else False

        results.append({
            "id": item.id,
            "approach": approach_name,
            "difficulty": item.difficulty,
            "question": item.question,
            "gold_sql": item.gold_sql,
            "predicted_sql": pred_sql,
            "is_valid": is_valid,
            "exact_match": em,
            "execution_accuracy": ex,
            "gen_time_ms": round(gen_time_ms, 2)
        })

    return results


def run_benchmark_suite(
    schema: DatabaseSchema,
    engine: Engine
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Runs complete benchmark suite on the Traditional NLP pipeline."""
    items = DatasetLoader.load(split="test")
    validator = SQLValidator()

    # Traditional NLP & Rule-Based Pipeline
    baseline_gen = BaselineSQLGenerator(schema)
    records = evaluate_approach(
        "Traditional NLP & Rule-Based Pipeline",
        baseline_gen.generate,
        items,
        engine,
        validator
    )

    detailed_df = pd.DataFrame(records)

    # Compute Summary Metrics
    total = len(detailed_df)
    val_pct = (detailed_df["is_valid"].sum() / total) * 100 if total else 0.0
    em_pct = (detailed_df["exact_match"].sum() / total) * 100 if total else 0.0
    ex_pct = (detailed_df["execution_accuracy"].sum() / total) * 100 if total else 0.0
    avg_gen_time = detailed_df["gen_time_ms"].mean() if total else 0.0

    summary_data = [{
        "Approach": "Traditional NLP Pipeline",
        "Total Evaluated": total,
        "SQL Validity (%)": round(val_pct, 1),
        "Exact Match (EM %)": round(em_pct, 1),
        "Execution Accuracy (EX %)": round(ex_pct, 1),
        "Avg Latency (ms)": round(avg_gen_time, 1)
    }]

    summary_df = pd.DataFrame(summary_data)
    return summary_df, detailed_df


if __name__ == "__main__":
    from database.connection import ConnectionManager
    from database.schema_detector import SchemaDetector
    mgr = ConnectionManager()
    eng = mgr.get_engine()
    schema = SchemaDetector(eng).detect()
    summary, _ = run_benchmark_suite(schema, eng)
    print("\n=== BENCHMARK SUMMARY ===")
    print(summary.to_string(index=False))
