"""
Dynamic Database Schema Detector.
Inspects tables, columns, data types, primary keys, and foreign-key relationships.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Any, Optional
from sqlalchemy import inspect
from sqlalchemy.engine import Engine


@dataclass
class ColumnSchema:
    name: str
    data_type: str
    nullable: bool = True
    is_primary_key: bool = False
    is_foreign_key: bool = False
    foreign_key_target: Optional[str] = None


@dataclass
class Relationship:
    source_table: str
    source_column: str
    target_table: str
    target_column: str

    def to_join_clause(self, alias_map: Optional[dict[str, str]] = None) -> str:
        s_alias = alias_map.get(self.source_table, self.source_table) if alias_map else self.source_table
        t_alias = alias_map.get(self.target_table, self.target_table) if alias_map else self.target_table
        return f"{s_alias}.{self.source_column} = {t_alias}.{self.target_column}"


@dataclass
class TableSchema:
    name: str
    columns: dict[str, ColumnSchema] = field(default_factory=dict)
    primary_keys: list[str] = field(default_factory=list)
    foreign_keys: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class DatabaseSchema:
    database_name: str
    tables: dict[str, TableSchema] = field(default_factory=dict)
    relationships: list[Relationship] = field(default_factory=list)

    def get_table_names(self) -> list[str]:
        return list(self.tables.keys())

    def get_column_names(self, table_name: str) -> list[str]:
        table = self.tables.get(table_name)
        return list(table.columns.keys()) if table else []

    def find_join_path(self, start_table: str, end_table: str) -> list[Relationship]:
        """BFS shortest path to discover JOIN relationships between two tables."""
        if start_table == end_table:
            return []

        # Build adjacency graph
        adj: dict[str, list[tuple[str, Relationship]]] = {}
        for rel in self.relationships:
            adj.setdefault(rel.source_table, []).append((rel.target_table, rel))
            # Reverse edge for undirected traversal
            rev_rel = Relationship(rel.target_table, rel.target_column, rel.source_table, rel.source_column)
            adj.setdefault(rel.target_table, []).append((rel.source_table, rev_rel))

        queue = deque([(start_table, [])])
        visited = {start_table}

        while queue:
            current, path = queue.popleft()
            if current == end_table:
                return path

            for neighbor, rel in adj.get(current, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [rel]))

        return []


class SchemaDetector:
    """Introspects relational database schemas dynamically via SQLAlchemy metadata."""

    def __init__(self, engine: Engine):
        self.engine = engine

    def detect(self) -> DatabaseSchema:
        inspector = inspect(self.engine)
        db_name = self.engine.url.database or "default"
        table_names = inspector.get_table_names()

        tables: dict[str, TableSchema] = {}
        relationships: list[Relationship] = []

        for table_name in table_names:
            pk_constraint = inspector.get_pk_constraint(table_name)
            pks = set(pk_constraint.get("constrained_columns", []) if pk_constraint else [])
            fks = inspector.get_foreign_keys(table_name)

            fk_map: dict[str, str] = {}
            for fk in fks:
                ref_table = fk["referred_table"]
                for col, ref_col in zip(fk["constrained_columns"], fk["referred_columns"]):
                    fk_map[col] = f"{ref_table}.{ref_col}"
                    relationships.append(Relationship(
                        source_table=table_name,
                        source_column=col,
                        target_table=ref_table,
                        target_column=ref_col
                    ))

            columns: dict[str, ColumnSchema] = {}
            for col_meta in inspector.get_columns(table_name):
                col_name = col_meta["name"]
                columns[col_name] = ColumnSchema(
                    name=col_name,
                    data_type=str(col_meta["type"]),
                    nullable=bool(col_meta.get("nullable", True)),
                    is_primary_key=(col_name in pks),
                    is_foreign_key=(col_name in fk_map),
                    foreign_key_target=fk_map.get(col_name)
                )

            tables[table_name] = TableSchema(
                name=table_name,
                columns=columns,
                primary_keys=list(pks),
                foreign_keys=fks
            )

        return DatabaseSchema(database_name=db_name, tables=tables, relationships=relationships)

