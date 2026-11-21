"""
Entity Extraction and Dynamic Schema Linking Module.
Maps natural language tokens to database tables and columns using lexical matching,
relational keyword awareness, domain synonyms, and similarity-based string distance.
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


# Domain synonym dictionaries for relational concepts
DOMAIN_SYNONYMS: dict[str, list[tuple[str, Optional[str]]]] = {
    "student": [("students", None)],
    "students": [("students", None)],
    "instructor": [("instructors", None)],
    "instructors": [("instructors", None)],
    "teacher": [("instructors", None)],
    "professor": [("instructors", None)],
    "faculty": [("instructors", None)],
    "department": [("departments", None)],
    "departments": [("departments", None)],
    "dept": [("departments", None)],
    "course": [("courses", None)],
    "courses": [("courses", None)],
    "classroom": [("classrooms", None)],
    "enrollment": [("enrollments", None)],
    "enrollments": [("enrollments", None)],
    "name": [("students", "student_name"), ("departments", "dept_name"), ("instructors", "name"), ("courses", "course_title")],
    "names": [("students", "student_name"), ("departments", "dept_name"), ("instructors", "name"), ("courses", "course_title")],
    "cgpa": [("students", "cgpa")],
    "gpa": [("students", "cgpa")],
    "salary": [("instructors", "salary")],
    "marks": [("marks", "marks")],
    "mark": [("marks", "marks")],
    "score": [("marks", "marks")],
    "scores": [("marks", "marks")],
    "subject": [("marks", "subject")],
    "credit": [("courses", "credits")],
    "credits": [("courses", "credits")],
}


class SchemaLinker:
    """Grounds question tokens to relational schema elements across arbitrary databases."""

    def __init__(self, schema: DatabaseSchema, similarity_threshold: float = 0.80):
        self.schema = schema
        self.similarity_threshold = similarity_threshold

    def _normalize(self, word: str) -> str:
        w = word.lower().replace("_", "").strip()
        if w.endswith("s") and len(w) > 3:
            return w[:-1]
        return w

    def link(self, tokens: list[str]) -> list[LinkedEntity]:
        """Maps query tokens to discovered schema tables and columns."""
        linked: list[LinkedEntity] = []
        seen: set[tuple[str, Optional[str]]] = set()
        table_names = self.schema.get_table_names()

        # Step 1: Check Domain Synonyms for explicit targets in current schema
        for token in tokens:
            t_lower = token.lower()
            if t_lower in DOMAIN_SYNONYMS:
                for target_tbl, target_col in DOMAIN_SYNONYMS[t_lower]:
                    if target_tbl in self.schema.tables:
                        if target_col is None or target_col in self.schema.tables[target_tbl].columns:
                            key = (target_tbl, target_col)
                            if key not in seen:
                                seen.add(key)
                                linked.append(LinkedEntity(
                                    entity_type="column" if target_col else "table",
                                    matched_text=token,
                                    target_table=target_tbl,
                                    target_column=target_col,
                                    confidence=0.95
                                ))

        # Step 2: Direct Table Name Matching (exact or singular/plural)
        for token in tokens:
            t_norm = self._normalize(token)
            for table_name in table_names:
                if t_norm == self._normalize(table_name) or token.lower() == table_name.lower():
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

        # Step 3: Direct Column Name Matching
        for token in tokens:
            t_lower = token.lower()
            t_norm = self._normalize(token)
            # Avoid overly generic stop-tokens matching ID fields
            if t_lower in ("in", "for", "of", "to", "at", "by", "is", "a", "an", "the"):
                continue

            for table_name, table in self.schema.tables.items():
                for col_name in table.columns:
                    col_lower = col_name.lower()
                    if t_lower == col_lower or t_norm == self._normalize(col_name):
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

        # Step 4: Fuzzy String Similarity (difflib) for arbitrary schemas
        for token in tokens:
            t_lower = token.lower()
            if len(t_lower) < 4 or t_lower in ("show", "find", "list", "display", "select", "each", "every", "more", "less", "than"):
                continue

            for table_name in table_names:
                ratio = difflib.SequenceMatcher(None, t_lower, table_name.lower()).ratio()
                if ratio >= self.similarity_threshold:
                    key = (table_name, None)
                    if key not in seen:
                        seen.add(key)
                        linked.append(LinkedEntity(
                            entity_type="table",
                            matched_text=token,
                            target_table=table_name,
                            target_column=None,
                            confidence=round(ratio, 2)
                        ))

            for table_name, table in self.schema.tables.items():
                for col_name in table.columns:
                    ratio = difflib.SequenceMatcher(None, t_lower, col_name.lower()).ratio()
                    if ratio >= self.similarity_threshold:
                        key = (table_name, col_name)
                        if key not in seen:
                            seen.add(key)
                            linked.append(LinkedEntity(
                                entity_type="column",
                                matched_text=token,
                                target_table=table_name,
                                target_column=col_name,
                                confidence=round(ratio, 2)
                            ))

        return linked
