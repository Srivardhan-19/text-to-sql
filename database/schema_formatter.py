"""
Schema Formatter Module.
Converts DatabaseSchema into structured prompt strings, markdown summaries, and graph representations.
"""
from __future__ import annotations

from typing import Any
from database.schema_detector import DatabaseSchema


class SchemaFormatter:
    """Formats DatabaseSchema into representations for LLM prompts and UI display."""

    @staticmethod
    def to_prompt_string(schema: DatabaseSchema) -> str:
        """Generates compact DDL-like schema description for LLM in-context prompts."""
        lines = [f"Database Dialect: MySQL\nDatabase: {schema.database_name}\nSchema:"]

        for table_name, table in schema.tables.items():
            cols = []
            for col in table.columns.values():
                col_def = f"{col.name} ({col.data_type})"
                if col.is_primary_key:
                    col_def += " PRIMARY KEY"
                if col.is_foreign_key and col.foreign_key_target:
                    col_def += f" REFERENCES {col.foreign_key_target}"
                cols.append(col_def)
            lines.append(f"Table {table_name}: [ {', '.join(cols)} ]")

        if schema.relationships:
            lines.append("\nForeign Key Relationships:")
            for rel in schema.relationships:
                lines.append(f"  - {rel.source_table}.{rel.source_column} -> {rel.target_table}.{rel.target_column}")

        return "\n".join(lines)

    @staticmethod
    def to_markdown_summary(schema: DatabaseSchema) -> str:
        """Generates rich markdown summary for UI Database Explorer."""
        sections = [f"### Database: `{schema.database_name}`\n"]
        for table_name, table in schema.tables.items():
            sections.append(f"#### Table: `{table_name}`")
            sections.append("| Column | Data Type | Nullable | Primary Key | Foreign Key Target |")
            sections.append("| :--- | :--- | :---: | :---: | :--- |")
            for col in table.columns.values():
                pk_badge = "Yes" if col.is_primary_key else "No"
                null_badge = "Yes" if col.nullable else "No"
                fk_target = f"`{col.foreign_key_target}`" if col.foreign_key_target else "-"
                sections.append(f"| `{col.name}` | `{col.data_type}` | {null_badge} | {pk_badge} | {fk_target} |")
            sections.append("")

        if schema.relationships:
            sections.append("#### Foreign Key Constraints")
            for rel in schema.relationships:
                sections.append(f"- `{rel.source_table}.{rel.source_column}` ➔ `{rel.target_table}.{rel.target_column}`")

        return "\n".join(sections)

    @staticmethod
    def to_dict(schema: DatabaseSchema) -> dict[str, Any]:
        """Serializes schema to dictionary for schema linking and caching."""
        return {
            "database_name": schema.database_name,
            "tables": {
                name: {
                    "columns": {c_name: c.data_type for c_name, c in tbl.columns.items()},
                    "primary_keys": tbl.primary_keys,
                    "foreign_keys": [
                        {"column": r.source_column, "target": f"{r.target_table}.{r.target_column}"}
                        for r in schema.relationships if r.source_table == name
                    ]
                }
                for name, tbl in schema.tables.items()
            },
            "relationships": [
                {
                    "source": f"{r.source_table}.{r.source_column}",
                    "target": f"{r.target_table}.{r.target_column}"
                }
                for r in schema.relationships
            ]
        }

