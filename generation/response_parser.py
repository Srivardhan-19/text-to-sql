"""
Response Parser Module.
Parses, sanitizes, and normalizes structured LLM JSON responses.
"""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ParsedLLMResponse:
    sql: str
    explanation: str
    tables_used: list[str] = field(default_factory=list)
    columns_used: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    needs_clarification: bool = False
    raw_response: str = ""
    is_valid_json: bool = True


class ResponseParser:
    """Extracts structured fields from raw LLM output text."""

    @staticmethod
    def clean_markdown_fences(text: str) -> str:
        """Removes ```json ... ``` or ```sql ... ``` code block delimiters."""
        cleaned = text.strip()
        # Strip leading ```json or ```
        cleaned = re.sub(r"^```(?:json|sql)?\s*", "", cleaned, flags=re.IGNORECASE)
        # Strip trailing ```
        cleaned = re.sub(r"\s*```$", "", cleaned)
        return cleaned.strip()

    @classmethod
    def parse(cls, raw_text: str) -> ParsedLLMResponse:
        cleaned = cls.clean_markdown_fences(raw_text)

        # 1. Try standard JSON parsing
        try:
            data = json.loads(cleaned)
            return ParsedLLMResponse(
                sql=data.get("sql", "").strip(),
                explanation=data.get("explanation", "").strip(),
                tables_used=data.get("tables_used", []),
                columns_used=data.get("columns_used", []),
                assumptions=data.get("assumptions", []),
                needs_clarification=bool(data.get("needs_clarification", False)),
                raw_response=raw_text,
                is_valid_json=True
            )
        except json.JSONDecodeError:
            logger.warning("Direct JSON decode failed, attempting JSON regex search...")

        # 2. Try regex extraction of JSON object
        json_match = re.search(r"\{[\s\S]*\}", cleaned)
        if json_match:
            try:
                data = json.loads(json_match.group(0))
                return ParsedLLMResponse(
                    sql=data.get("sql", "").strip(),
                    explanation=data.get("explanation", "").strip(),
                    tables_used=data.get("tables_used", []),
                    columns_used=data.get("columns_used", []),
                    assumptions=data.get("assumptions", []),
                    needs_clarification=bool(data.get("needs_clarification", False)),
                    raw_response=raw_text,
                    is_valid_json=True
                )
            except Exception:
                pass

        # 3. Fallback: Extract SELECT statement directly using regex
        sql_match = re.search(r"(SELECT\s+[\s\S]+?;)", raw_text, flags=re.IGNORECASE)
        if not sql_match:
            sql_match = re.search(r"(SELECT\s+[^.\n]+)", raw_text, flags=re.IGNORECASE)
        sql = sql_match.group(1).strip() if sql_match else ""
        if sql and not sql.endswith(";"):
            sql += ";"

        return ParsedLLMResponse(
            sql=sql,
            explanation="Extracted directly from raw text via regex fallback.",
            tables_used=[],
            columns_used=[],
            assumptions=["JSON formatting was malformed; raw query extracted."],
            needs_clarification=False,
            raw_response=raw_text,
            is_valid_json=False
        )
