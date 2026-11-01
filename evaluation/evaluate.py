"""
Benchmark Evaluation Harness.
Orchestrates comparative evaluation of Traditional Baseline vs. Schema-Aware LLM approach.
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
from generation.llm_generator import LLMGenerator
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
    """Runs complete benchmark suite comparing Baseline and LLM approaches."""
    items = DatasetLoader.load(split="test")
    validator = SQLValidator()

    # 1. Baseline Approach
    baseline_gen = BaselineSQLGenerator(schema)
    baseline_records = evaluate_approach(
        "Approach 1: Traditional Baseline",
        baseline_gen.generate,
        items,
        engine,
        validator
    )

    # 2. LLM Approach (with graceful fallback)
    llm_gen = LLMGenerator(schema)
    llm_records = evaluate_approach(
        "Approach 2: Schema-Aware LLM",
        llm_gen.generate,
        items,
        engine,
        validator
    )

    all_records = baseline_records + llm_records
    detailed_df = pd.DataFrame(all_records)

    # Compute Summary Metrics per Approach
    summary_data = []
    for app_name in detailed_df["approach"].unique():
        sub = detailed_df[detailed_df["approach"] == app_name]
        total = len(sub)
        val_pct = (sub["is_valid"].sum() / total) * 100 if total else 0.0
        em_pct = (sub["exact_match"].sum() / total) * 100 if total else 0.0
        ex_pct = (sub["execution_accuracy"].sum() / total) * 100 if total else 0.0
        avg_gen_time = sub["gen_time_ms"].mean() if total else 0.0

        summary_data.append({
            "Approach": app_name,
            "Total Evaluated": total,
            "SQL Validity (%)": round(val_pct, 1),
            "Exact Match (EM %)": round(em_pct, 1),
            "Execution Accuracy (EX %)": round(ex_pct, 1),
            "Avg Latency (ms)": round(avg_gen_time, 1)
        })

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
