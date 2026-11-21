"""
Traditional NLP / Rule-Based SQL Generator.
Constructs safe, structured MySQL queries using dynamic schema linking, intent classification,
BFS foreign-key JOIN traversal, and deterministic SQL templates.
No LLMs or external generative AI are used.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional
from database.schema_detector import DatabaseSchema, Relationship
from nlp.entity_extractor import LinkedEntity, SchemaLinker
from nlp.intent_classifier import IntentClassifier, QueryIntent
from nlp.keyword_extraction import ExtractedKeywords, KeywordExtractor
from nlp.preprocessing import TextPreprocessor


@dataclass
class BaselineGenerationResult:
    sql: str
    intent: QueryIntent
    explanation: str
    linked_tables: list[str]
    linked_columns: list[str]
    confidence: float
    approach: str = "Traditional NLP & Rule-Based Generator"


class BaselineSQLGenerator:
    """Deterministic, transparent rule-based SQL generator driven by traditional NLP."""

    def __init__(self, schema: DatabaseSchema):
        self.schema = schema
        self.preprocessor = TextPreprocessor()
        self.keyword_extractor = KeywordExtractor()
        self.intent_classifier = IntentClassifier()
        self.linker = SchemaLinker(schema)

    def generate(self, question: str) -> BaselineGenerationResult:
        prep = self.preprocessor.preprocess(question)
        keywords = self.keyword_extractor.extract(question)
        intent = self.intent_classifier.classify(question)
        entities = self.linker.link(prep.tokens + prep.lemmas)

        # 1. Resolve tables and columns
        linked_tables: list[str] = list(dict.fromkeys([e.target_table for e in entities]))
        linked_columns: list[str] = list(dict.fromkeys(
            [f"{e.target_table}.{e.target_column}" for e in entities if e.target_column]
        ))

        all_tables = self.schema.get_table_names()
        if not all_tables:
            return BaselineGenerationResult(
                sql="-- Error: No tables detected in database schema.",
                intent=intent,
                explanation="Unable to generate query because connected database has 0 tables.",
                linked_tables=[],
                linked_columns=[],
                confidence=0.0
            )

        if not linked_tables:
            linked_tables = [all_tables[0]]

        primary_table = linked_tables[0]

        # Generate unique short aliases for tables
        alias_map: dict[str, str] = {}
        used_aliases: set[str] = set()
        for tbl in all_tables:
            prefix = tbl[0].lower()
            if prefix not in used_aliases:
                alias_map[tbl] = prefix
                used_aliases.add(prefix)
            else:
                for k in range(2, len(tbl) + 1):
                    cand = tbl[:k].lower()
                    if cand not in used_aliases:
                        alias_map[tbl] = cand
                        used_aliases.add(cand)
                        break
                if tbl not in alias_map:
                    alias_map[tbl] = f"{tbl[:1]}_{len(used_aliases)}"
                    used_aliases.add(alias_map[tbl])

        # 2. Build FROM & JOIN clauses using BFS shortest path
        from_clause = f"{primary_table} {alias_map[primary_table]}"
        joins: list[str] = []
        joined_tables: set[str] = {primary_table}

        for other_table in linked_tables[1:]:
            if other_table not in joined_tables:
                path = self.schema.find_join_path(primary_table, other_table)
                for rel in path:
                    target_tbl = rel.target_table if rel.source_table in joined_tables else rel.source_table
                    if target_tbl not in joined_tables:
                        join_cond = rel.to_join_clause(alias_map)
                        joins.append(f"JOIN {target_tbl} {alias_map.get(target_tbl, target_tbl)} ON {join_cond}")
                        joined_tables.add(target_tbl)

        # 3. Build SELECT projection clause
        select_cols: list[str] = []
        distinct_prefix = "DISTINCT " if keywords.distinct else ""

        if intent == QueryIntent.AGGREGATE and keywords.aggregates:
            agg = keywords.aggregates[0]
            target_col = None
            for lc in linked_columns:
                tbl, col = lc.split(".")
                col_type = self.schema.tables[tbl].columns[col].data_type.lower()
                if any(t in col_type for t in ("int", "decimal", "float", "double", "numeric")):
                    target_col = f"{alias_map[tbl]}.{col}"
                    break
            if not target_col:
                target_col = "*" if agg == "COUNT" else f"{alias_map[primary_table]}.*"
            select_cols.append(f"{agg}({target_col})")

        elif intent == QueryIntent.GROUP_BY_AGGREGATE:
            group_col = None
            if linked_columns:
                tbl, col = linked_columns[0].split(".")
                group_col = f"{alias_map[tbl]}.{col}"
            else:
                first_col = list(self.schema.tables[primary_table].columns.keys())[0]
                group_col = f"{alias_map[primary_table]}.{first_col}"

            agg = keywords.aggregates[0] if keywords.aggregates else "COUNT"
            select_cols.append(group_col)
            select_cols.append(f"{agg}(*)")

        else:
            # Filter projected columns only to relevant non-FK identifier/name columns
            if linked_columns:
                for lc in linked_columns:
                    tbl, col = lc.split(".")
                    if tbl in joined_tables and not col.endswith("_id"):
                        select_cols.append(f"{alias_map[tbl]}.{col}")
            # If nothing specific or only IDs matched, select first descriptive column or table.*
            if not select_cols:
                if linked_columns:
                    tbl, col = linked_columns[0].split(".")
                    select_cols.append(f"{alias_map[tbl]}.{col}")
                else:
                    select_cols.append(f"{alias_map[primary_table]}.*")

        # 4. Build WHERE filtering clause
        where_clauses: list[str] = []

        for cond in keywords.conditions:
            if cond.is_numeric:
                val_num = float(cond.value)
                val_is_float = "." in cond.value
                assigned = False

                # Search joined tables for suitable column matching condition magnitude
                # Priority: search for exact metric matches first (marks, salary, cgpa, credits)
                for tbl in joined_tables:
                    for col_name, col_meta in self.schema.tables[tbl].columns.items():
                        # Exclude primary/foreign keys from numeric threshold filtering
                        if col_name.endswith("_id") or col_name == "id":
                            continue

                        col_type = col_meta.data_type.lower()
                        if any(t in col_type for t in ("int", "decimal", "float", "double")):
                            if ("cgpa" in col_name.lower() or "gpa" in col_name.lower()) and val_num <= 10.0:
                                where_clauses.append(f"{alias_map[tbl]}.{col_name} {cond.operator} {cond.value}")
                                assigned = True
                                break
                            elif ("salary" in col_name.lower() or "budget" in col_name.lower()) and val_num >= 1000:
                                where_clauses.append(f"{alias_map[tbl]}.{col_name} {cond.operator} {cond.value}")
                                assigned = True
                                break
                            elif ("mark" in col_name.lower() or "score" in col_name.lower()) and val_num <= 100:
                                where_clauses.append(f"{alias_map[tbl]}.{col_name} {cond.operator} {cond.value}")
                                assigned = True
                                break
                            elif "credit" in col_name.lower() and val_num <= 10:
                                where_clauses.append(f"{alias_map[tbl]}.{col_name} {cond.operator} {cond.value}")
                                assigned = True
                                break
                    if assigned:
                        break

                if not assigned:
                    for tbl in joined_tables:
                        for col_name, col_meta in self.schema.tables[tbl].columns.items():
                            if not col_name.endswith("_id") and any(t in col_meta.data_type.lower() for t in ("int", "decimal", "float", "double")):
                                where_clauses.append(f"{alias_map[tbl]}.{col_name} {cond.operator} {cond.value}")
                                assigned = True
                                break
                        if assigned:
                            break
            else:
                # String condition (e.g. subject = 'DBMS', dept_name = 'CSE')
                str_assigned = False
                # First check exact context hint in question (e.g., if question mentions marks or score, prioritize marks.subject)
                priority_terms = ["subject", "course", "dept", "title", "name"]
                if "mark" in question.lower() or "score" in question.lower():
                    priority_terms = ["subject", "course_title", "dept_name", "title", "name"]
                elif "dept" in question.lower() or "department" in question.lower():
                    priority_terms = ["dept_name", "department", "subject", "title", "name"]

                for term in priority_terms:
                    for tbl in joined_tables:
                        for col_name, col_meta in self.schema.tables[tbl].columns.items():
                            if term == col_name.lower() or term in col_name.lower():
                                if any(t in col_meta.data_type.lower() for t in ("char", "varchar", "text")):
                                    where_clauses.append(f"{alias_map[tbl]}.{col_name} = '{cond.value}'")
                                    str_assigned = True
                                    break
                        if str_assigned:
                            break
                    if str_assigned:
                        break

        # 5. Assemble Query
        query_parts = [
            f"SELECT {distinct_prefix}{', '.join(select_cols)}",
            f"FROM {from_clause}"
        ]
        if joins:
            query_parts.extend(joins)
        if where_clauses:
            query_parts.append(f"WHERE {' AND '.join(where_clauses)}")
        if intent == QueryIntent.GROUP_BY_AGGREGATE:
            query_parts.append(f"GROUP BY {select_cols[0]}")
        if keywords.order_by_direction:
            order_col = select_cols[0]
            query_parts.append(f"ORDER BY {order_col} {keywords.order_by_direction}")
        if keywords.limit:
            query_parts.append(f"LIMIT {keywords.limit}")

        sql = " ".join(query_parts) + ";"

        explanation = (
            f"Generated via Traditional NLP & Rule-Based Pipeline:\n"
            f"• Classified Intent: {intent.value}\n"
            f"• Linked Entities: Tables [{', '.join(linked_tables)}], Columns [{', '.join(linked_columns) if linked_columns else 'Wildcard/Derived'}]\n"
            f"• Extracted Filters: {', '.join(where_clauses) if where_clauses else 'None'}\n"
            f"• Relationships Traversed: {len(joins)} JOIN path(s)"
        )

        return BaselineGenerationResult(
            sql=sql,
            intent=intent,
            explanation=explanation,
            linked_tables=linked_tables,
            linked_columns=linked_columns,
            confidence=0.85 if linked_tables and (select_cols or where_clauses) else 0.50
        )
