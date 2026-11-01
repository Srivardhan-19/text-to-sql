"""
Entity Extraction and Schema Linking Module.
Maps natural language tokens to database tables and columns using lexical and semantic grounding.
"""
from __future__ import annotations

import difflib
from dataclasses import dataclass
from typing import Optional
from database.schema_detector import DatabaseSchema


@dataclass
class LinkedEntity:
    entity_type: str  # "table" or "column"
    matched_text: str
    target_table: str
    target_column: Optional[str] = None
    confidence: float = 1.0


# Domain synonym dictionaries for academic/college schemas
SYNONYMS = {
    "student": ("students", None),
    "students": ("students", None),
    "pupil": ("students", None),
    "instructor": ("instructors", None),
    "instructors": ("instructors", None),
    "teacher": ("instructors", None),
    "faculty": ("instructors", None),
    "professor": ("instructors", None),
    "department": ("departments", None),
    "departments": ("departments", None),
    "dept": ("departments", None),
    "branch": ("departments", None),
    "course": ("courses", None),
    "courses": ("courses", None),
    "subject": ("marks", "subject"),
    "marks": ("marks", "marks"),
    "score": ("marks", "marks"),
    "scores": ("marks", "marks"),
    "mark": ("marks", "marks"),
    "cgpa": ("students", "cgpa"),
    "gpa": ("students", "cgpa"),
    "salary": ("instructors", "salary"),
    "name": ("students", "student_name"),
    "names": ("students", "student_name"),
    "credit": ("courses", "credits"),
    "credits": ("courses", "credits"),
}


class SchemaLinker:
    """Grounds question tokens to relational schema elements."""

    def __init__(self, schema: DatabaseSchema):
        self.schema = schema

    def link(self, tokens: list[str]) -> list[LinkedEntity]:
        linked: list[LinkedEntity] = []
        seen = set()

        # 1. Synonym matching
        for token in tokens:
            lower = token.lower()
            if lower in SYNONYMS:
                table, col = SYNONYMS[lower]
                if table in self.schema.tables:
                    key = (table, col)
                    if key not in seen:
                        seen.add(key)
                        linked.append(LinkedEntity(
                            entity_type="column" if col else "table",
                            matched_text=token,
                            target_table=table,
                            target_column=col,
                            confidence=0.95
                        ))

        # 2. Exact and singular matching against actual schema tables
        for table_name in self.schema.tables:
            table_singular = table_name.rstrip("s")
            for token in tokens:
                lower = token.lower()
                if lower == table_name or lower == table_singular:
                    key = (table_name, None)
                    if key not in seen:
                        seen.add(key)
                        linked.append(LinkedEntity(
                            entity_type="table",
                            matched_text=token,
                            target_table=table_name,
                            target_column=None,
                            confidence=1.0
                        ))

        # 3. Exact matching against columns
        for table_name, table in self.schema.tables.items():
            for col_name in table.columns:
                for token in tokens:
                    lower = token.lower()
                    if lower == col_name or lower == col_name.replace("_", ""):
                        key = (table_name, col_name)
                        if key not in seen:
                            seen.add(key)
                            linked.append(LinkedEntity(
                                entity_type="column",
                                matched_text=token,
                                target_table=table_name,
                                target_column=col_name,
                                confidence=1.0
                            ))

        return linked

