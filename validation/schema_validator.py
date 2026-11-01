"""
Schema Reference Validator Module.
Ensures that all tables and columns referenced in the parsed SQL AST exist in the active DatabaseSchema.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional
from database.schema_detector import DatabaseSchema
from validation.sql_validator import SQLValidationResult

logger = logging.getLogger(__name__)


@dataclass
class SchemaValidationResult:
    is_valid: bool
    error_message: Optional[str] = None
    unknown_tables: list[str] = field(default_factory=list)
    unknown_columns: list[str] = field(default_factory=list)


class SchemaValidator:
    """Whitelists referenced AST elements against the introspected database schema."""

    def __init__(self, schema: DatabaseSchema):
        self.schema = schema
        self.schema_tables = set(schema.get_table_names())
        self.schema_columns: dict[str, set[str]] = {
            t_name: set(schema.get_column_names(t_name))
            for t_name in self.schema_tables
        }
        self.all_columns: set[str] = set()
        for cols in self.schema_columns.values():
            self.all_columns.update(cols)

    def validate(self, sql_res: SQLValidationResult) -> SchemaValidationResult:
        if not sql_res.is_valid:
            return SchemaValidationResult(is_valid=False, error_message=sql_res.error_message)

        # 1. Validate tables
        unknown_tables = [t for t in sql_res.tables_referenced if t.lower() not in [st.lower() for st in self.schema_tables]]
        if unknown_tables:
            return SchemaValidationResult(
                is_valid=False,
                error_message=f"Schema violation: Table(s) {unknown_tables} do not exist in database '{self.schema.database_name}'.",
                unknown_tables=unknown_tables
            )

        # 2. Validate columns (where column is not '*' or SQL alias)
        unknown_columns = []
        for c in sql_res.columns_referenced:
            c_clean = c.lower()
            if c_clean in ("*", ""):
                continue
            # Check if column exists in any of the referenced tables or general schema
            found = False
            for t in sql_res.tables_referenced:
                # Resolve actual table name
                matched_t = next((st for st in self.schema_tables if st.lower() == t.lower()), None)
                if matched_t and c_clean in [sc.lower() for sc in self.schema_columns[matched_t]]:
                    found = True
                    break
            if not found and c_clean not in [ac.lower() for ac in self.all_columns]:
                unknown_columns.append(c)

        if unknown_columns:
            return SchemaValidationResult(
                is_valid=False,
                error_message=f"Schema violation: Column(s) {unknown_columns} do not exist in referenced table(s).",
                unknown_columns=unknown_columns
            )

        return SchemaValidationResult(is_valid=True)

