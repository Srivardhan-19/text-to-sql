"""
SQL Validation and AST Security Module.
Uses SQLGlot (MySQL dialect) to enforce strict read-only SELECT permissions and parse validity.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional
import sqlglot
from sqlglot import exp

logger = logging.getLogger(__name__)

# Forbidden AST statement types that modify data or schema
FORBIDDEN_EXPRESSIONS = (
    exp.Insert,
    exp.Update,
    exp.Delete,
    exp.Drop,
    exp.Alter,
    exp.Create,
    exp.TruncateTable,
    exp.Command,
    exp.Pragma,
)


@dataclass
class SQLValidationResult:
    is_valid: bool
    error_message: Optional[str] = None
    ast: Optional[exp.Expression] = None
    tables_referenced: list[str] = field(default_factory=list)
    columns_referenced: list[str] = field(default_factory=list)


class SQLValidator:
    """Validates SQL query syntax and safety using SQLGlot AST traversal."""

    def __init__(self, dialect: str = "mysql"):
        self.dialect = dialect

    def validate(self, sql_query: str) -> SQLValidationResult:
        trimmed = sql_query.strip()
        if not trimmed:
            return SQLValidationResult(is_valid=False, error_message="Empty SQL query provided.")

        # 1. Parse using SQLGlot
        try:
            parsed_expressions = sqlglot.parse(trimmed, read=self.dialect)
        except Exception as e:
            return SQLValidationResult(is_valid=False, error_message=f"SQL syntax error: {e}")

        # 2. Enforce single statement
        if not parsed_expressions:
            return SQLValidationResult(is_valid=False, error_message="Failed to parse any valid SQL statement.")
        if len(parsed_expressions) > 1:
            return SQLValidationResult(
                is_valid=False,
                error_message="Multiple SQL statements detected. Multi-statement execution is strictly disallowed."
            )

        root = parsed_expressions[0]

        # 3. Check for forbidden mutation AST nodes anywhere in AST
        for node in root.walk():
            if isinstance(node, FORBIDDEN_EXPRESSIONS):
                node_name = node.__class__.__name__
                return SQLValidationResult(
                    is_valid=False,
                    error_message=f"Security violation: Forbidden SQL operation '{node_name}' detected. Only read-only SELECT queries are allowed."
                )

        # 4. Enforce that root statement is a SELECT or UNION
        if not isinstance(root, (exp.Select, exp.Union)):
            return SQLValidationResult(
                is_valid=False,
                error_message=f"Only SELECT queries are permitted (got {root.__class__.__name__})."
            )

        # 5. Extract referenced tables and columns
        tables = []
        for table_node in root.find_all(exp.Table):
            t_name = table_node.name.strip("`'\"")
            if t_name and t_name not in tables:
                tables.append(t_name)

        columns = []
        for col_node in root.find_all(exp.Column):
            c_name = col_node.name.strip("`'\"")
            if c_name and c_name not in columns:
                columns.append(c_name)

        return SQLValidationResult(
            is_valid=True,
            ast=root,
            tables_referenced=tables,
            columns_referenced=columns
        )
