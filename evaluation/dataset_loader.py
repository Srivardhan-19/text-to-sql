"""
Evaluation Dataset Loader Module.
Loads benchmark questions, reference SQL queries, and metadata.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

DATASET_FILE = Path(__file__).resolve().parent.parent / "datasets" / "custom_questions.json"


@dataclass
class BenchmarkItem:
    id: int
    difficulty: str
    question: str
    gold_sql: str
    expected_tables: list[str]
    split: str = "test"


class DatasetLoader:
    """Loads and filters benchmark question-SQL pairs."""

    @staticmethod
    def load(split: Optional[str] = None, difficulty: Optional[str] = None) -> list[BenchmarkItem]:
        if not DATASET_FILE.exists():
            return []

        with open(DATASET_FILE, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        items = []
        for d in raw_data:
            if split and d.get("split") != split:
                continue
            if difficulty and d.get("difficulty") != difficulty:
                continue
            items.append(BenchmarkItem(
                id=d["id"],
                difficulty=d["difficulty"],
                question=d["question"],
                gold_sql=d["sql"],
                expected_tables=d.get("expected_tables", []),
                split=d.get("split", "test")
            ))
        return items

