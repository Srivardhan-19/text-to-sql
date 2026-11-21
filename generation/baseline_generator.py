"""
Traditional NLP / Rule-Based SQL Generator.
Constructs safe, accurate, minimal-JOIN MySQL queries using dynamic schema linking,
intent classification, BFS foreign-key pathfinding, and deterministic SQL assembly.
"""
from __future__ import annotations

import re
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

        # 1. Identify explicitly mentioned tables vs column-derived tables
        explicit_tables: list[str] = [e.target_table for e in entities if e.entity_type == "table"]
        column_entities: list[LinkedEntity] = [e for e in entities if e.entity_type == "column" and e.target_column]

        # Determine primary focus table
        if explicit_tables:
            primary_table = explicit_tables[0]
        elif column_entities:
            primary_table = column_entities[0].target_table
        else:
            primary_table = all_tables[0]

        # 2. Filter column entities: keep columns that belong to primary table or explicitly referenced tables
        relevant_columns: list[LinkedEntity] = []
        for ce in column_entities:
            # If "name" was linked across 4 tables, prefer the one from primary_table!
            if ce.target_table == primary_table:
                relevant_columns.append(ce)
            elif ce.target_table in explicit_tables:
                relevant_columns.append(ce)

        if not relevant_columns and column_entities:
            relevant_columns = [column_entities[0]]

        # Determine the set of required tables (minimal set)
        required_tables: list[str] = [primary_table]
        for tbl in explicit_tables:
            if tbl not in required_tables:
                required_tables.append(tbl)
        for rc in relevant_columns:
            if rc.target_table not in required_tables:
                required_tables.append(rc.target_table)

        # Check if conditions require additional tables (e.g., condition on subject requires 'marks')
        for cond in keywords.conditions:
            if not cond.is_numeric:
                for tbl in all_tables:
                    for col_name in self.schema.tables[tbl].columns:
                        if "subject" in col_name or "course" in col_name or "dept" in col_name or "title" in col_name:
                            if tbl not in required_tables:
                                required_tables.append(tbl)
                            break

        # Generate unique table aliases
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

        # 3. Build FROM & Minimal JOIN paths
        from_clause = f"{primary_table} {alias_map[primary_table]}"
        joins: list[str] = []
        joined_tables: set[str] = {primary_table}

        for target_table in required_tables[1:]:
            if target_table not in joined_tables:
                path = self.schema.find_join_path(primary_table, target_table)
                for rel in path:
                    tbl_to_join = rel.target_table if rel.source_table in joined_tables else rel.source_table
                    if tbl_to_join not in joined_tables:
                        join_cond = rel.to_join_clause(alias_map)
                        joins.append(f"JOIN {tbl_to_join} {alias_map.get(tbl_to_join, tbl_to_join)} ON {join_cond}")
                        joined_tables.add(tbl_to_join)

        # 4. Build SELECT Projection Clause
        select_cols: list[str] = []
        distinct_prefix = "DISTINCT " if keywords.distinct else ""

        if intent == QueryIntent.AGGREGATE and keywords.aggregates:
            agg = keywords.aggregates[0]
            target_col = None
            for rc in relevant_columns:
                col_type = self.schema.tables[rc.target_table].columns[rc.target_column].data_type.lower()
                if any(t in col_type for t in ("int", "decimal", "float", "double", "numeric")):
                    target_col = f"{alias_map[rc.target_table]}.{rc.target_column}"
                    break
            if not target_col:
                # Find first numeric column in joined tables
                for tbl in joined_tables:
                    for col_name, col_meta in self.schema.tables[tbl].columns.items():
                        if not col_name.endswith("_id") and any(t in col_meta.data_type.lower() for t in ("int", "decimal", "float", "double")):
                            target_col = f"{alias_map[tbl]}.{col_name}"
                            break
                    if target_col:
                        break
            if not target_col:
                target_col = "*"
            select_cols.append(f"{agg}({target_col})")

        elif intent == QueryIntent.GROUP_BY_AGGREGATE:
            # Determine grouping column (e.g. dept_name or dept_id)
            group_col = None
            for tbl in joined_tables:
                for col_name in self.schema.tables[tbl].columns:
                    if "dept_name" in col_name or "name" in col_name or "department" in col_name:
                        group_col = f"{alias_map[tbl]}.{col_name}"
                        break
                if group_col:
                    break
            if not group_col:
                first_col = list(self.schema.tables[primary_table].columns.keys())[0]
                group_col = f"{alias_map[primary_table]}.{first_col}"

            agg = keywords.aggregates[0] if keywords.aggregates else "COUNT"
            # Target for aggregate
            agg_target = "*"
            if agg in ("AVG", "SUM", "MIN", "MAX"):
                for tbl in joined_tables:
                    for col_name, col_meta in self.schema.tables[tbl].columns.items():
                        if not col_name.endswith("_id") and any(t in col_meta.data_type.lower() for t in ("int", "decimal", "float", "double")):
                            agg_target = f"{alias_map[tbl]}.{col_name}"
                            break
                    if agg_target != "*":
                        break

            select_cols.append(group_col)
            select_cols.append(f"{agg}({agg_target})")

        else:
            # Simple select or filtered select
            # If the user asked specifically for columns (e.g. "names", "cgpa", "salary")
            if relevant_columns:
                for rc in relevant_columns:
                    col_ref = f"{alias_map[rc.target_table]}.{rc.target_column}"
                    if col_ref not in select_cols:
                        select_cols.append(col_ref)
            # If user said "show all students" or no specific column requested, select table.*
            if not select_cols:
                select_cols.append(f"{alias_map[primary_table]}.*")

        # 5. Build WHERE Clause
        where_clauses: list[str] = []

        for cond in keywords.conditions:
            if cond.is_numeric:
                val_num = float(cond.value)
                assigned = False

                for tbl in joined_tables:
                    for col_name, col_meta in self.schema.tables[tbl].columns.items():
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
                str_assigned = False
                priority_terms = ["subject", "course_title", "dept_name", "title", "name"]
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

        # 6. Assemble SQL
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
            # If order target column hinted, find it
            for tbl in joined_tables:
                for col_name in self.schema.tables[tbl].columns:
                    if "cgpa" in question.lower() and "cgpa" in col_name.lower():
                        order_col = f"{alias_map[tbl]}.{col_name}"
                        break
                    elif "salary" in question.lower() and "salary" in col_name.lower():
                        order_col = f"{alias_map[tbl]}.{col_name}"
                        break
            query_parts.append(f"ORDER BY {order_col} {keywords.order_by_direction}")
        if keywords.limit:
            query_parts.append(f"LIMIT {keywords.limit}")

        sql = " ".join(query_parts) + ";"

        explanation = (
            f"Generated via Traditional NLP & Rule-Based Pipeline:\n"
            f"• Classified Intent: {intent.value}\n"
            f"• Primary Table: {primary_table}\n"
            f"• Extracted Projections: {', '.join(select_cols)}\n"
            f"• Applied Filters: {', '.join(where_clauses) if where_clauses else 'None'}\n"
            f"• Relationships: {len(joins)} JOIN(s)"
        )

        return BaselineGenerationResult(
            sql=sql,
            intent=intent,
            explanation=explanation,
            linked_tables=list(joined_tables),
            linked_columns=[c.target_column for c in relevant_columns if c.target_column],
            confidence=0.88 if select_cols else 0.50
        )
