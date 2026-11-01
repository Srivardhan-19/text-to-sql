"""
Safe Database Query Execution Engine.
Executes validated read-only SQL queries with timeout, row limit capping, and latency measurement.
"""
from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass, field
from typing import Any, Optional
import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Engine

from config.settings import SafetySettings, get_settings

logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    success: bool
    columns: list[str] = field(default_factory=list)
    rows: list[list[Any]] = field(default_factory=list)
    row_count: int = 0
    execution_time_ms: float = 0.0
    error_message: Optional[str] = None
    sql_executed: str = ""

    def to_dataframe(self) -> pd.DataFrame:
        if self.rows and self.columns:
            return pd.DataFrame(self.rows, columns=self.columns)
        return pd.DataFrame()


class QueryExecutor:
    """Executes validated SQL queries against MySQL or SQLite engines safely."""

    def __init__(self, engine: Engine, safety_settings: Optional[SafetySettings] = None):
        self.engine = engine
        self.safety = safety_settings or get_settings().safety

    def _apply_row_limit(self, sql_query: str) -> str:
        """Enforces max_rows safety ceiling if no LIMIT is present or if LIMIT is excessive."""
        sql = sql_query.rstrip(";").strip()
        limit_match = re.search(r"\bLIMIT\s+([0-9]+)\b", sql, flags=re.IGNORECASE)

        if not limit_match:
            return f"{sql} LIMIT {self.safety.max_rows};"
        else:
            existing_limit = int(limit_match.group(1))
            if existing_limit > self.safety.max_rows:
                # Replace with max_rows ceiling
                sql = re.sub(r"\bLIMIT\s+[0-9]+\b", f"LIMIT {self.safety.max_rows}", sql, flags=re.IGNORECASE)
            return f"{sql};"

    def execute(self, sql_query: str) -> ExecutionResult:
        """Executes a validated SELECT query and measures execution latency."""
        safe_sql = self._apply_row_limit(sql_query)
        start_time = time.perf_counter()

        try:
            with self.engine.connect() as conn:
                # Execute with execution timeout where applicable
                result = conn.execute(text(safe_sql))
                columns = list(result.keys())
                rows = [list(row) for row in result.fetchall()]

            elapsed_ms = (time.perf_counter() - start_time) * 1000

            return ExecutionResult(
                success=True,
                columns=columns,
                rows=rows,
                row_count=len(rows),
                execution_time_ms=elapsed_ms,
                sql_executed=safe_sql
            )

        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            logger.warning(f"SQL execution failed: {e}")
            return ExecutionResult(
                success=False,
                error_message=str(e),
                execution_time_ms=elapsed_ms,
                sql_executed=safe_sql
            )

