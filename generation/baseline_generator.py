"""
Traditional NLP / ML Baseline SQL Generator (Approach 1).
Translates natural language questions to SQL using slot-filling, intent templates, and schema linking.
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
    approach: str = "Traditional NLP/ML Baseline"


class BaselineSQLGenerator:
    """Rule-based and slot-filling baseline SQL generator."""

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

        # Separate linked tables and columns
        linked_tables = list(dict.fromkeys([e.target_table for e in entities]))
        linked_columns = list(dict.fromkeys([f"{e.target_table}.{e.target_column}" for e in entities if e.target_column]))

        # Fallback table if none identified
        if not linked_tables:
            linked_tables = ["students"] if "students" in self.schema.tables else [self.schema.get_table_names()[0]]

        primary_table = linked_tables[0]
        alias_map = {tbl: tbl[0] if tbl[0] not in [t[0] for t in linked_tables[:i]] else f"{tbl[:2]}" for i, tbl in enumerate(linked_tables)}

        # Build SELECT clause
        select_cols = []
        if intent == QueryIntent.AGGREGATE and keywords.aggregates:
            agg = keywords.aggregates[0]
            # Identify target column for agg
            target_col = None
            for lc in linked_columns:
                tbl, col = lc.split(".")
                if self.schema.tables[tbl].columns[col].data_type.lower() in ("int", "decimal", "float"):
                    target_col = f"{alias_map[tbl]}.{col}"
                    break
            if not target_col:
                target_col = "*"
            select_cols.append(f"{agg}({target_col})")
        elif intent == QueryIntent.GROUP_BY_AGGREGATE:
            # Grouping column + aggregate
            group_col = None
            if linked_columns:
                group_col = f"{alias_map[linked_columns[0].split('.')[0]]}.{linked_columns[0].split('.')[1]}"
            else:
                group_col = f"{alias_map[primary_table]}.{primary_table.rstrip('s')}_id"
            agg = keywords.aggregates[0] if keywords.aggregates else "COUNT"
            select_cols.append(group_col)
            select_cols.append(f"{agg}(*)")
        else:
            # Project specific columns or table alias.*
            for lc in linked_columns:
                tbl, col = lc.split(".")
                select_cols.append(f"{alias_map[tbl]}.{col}")
            if not select_cols:
                select_cols.append(f"{alias_map[primary_table]}.*")

        # Build FROM & JOIN clauses
        from_clause = f"{primary_table} {alias_map[primary_table]}"
        joins: list[str] = []
        joined_tables = {primary_table}

        for other_table in linked_tables[1:]:
            if other_table not in joined_tables:
                path = self.schema.find_join_path(primary_table, other_table)
                for rel in path:
                    target_tbl = rel.target_table if rel.source_table in joined_tables else rel.source_table
                    if target_tbl not in joined_tables:
                        join_cond = rel.to_join_clause(alias_map)
                        joins.append(f"JOIN {target_tbl} {alias_map.get(target_tbl, target_tbl)} ON {join_cond}")
                        joined_tables.add(target_tbl)

        # Build WHERE clause
        where_clauses: list[str] = []
        for cond in keywords.conditions:
            if cond.column_hint == "subject" and "marks" in joined_tables:
                where_clauses.append(f"{alias_map['marks']}.subject = '{cond.value}'")
            elif cond.column_hint == "department" and "departments" in joined_tables:
                where_clauses.append(f"{alias_map['departments']}.dept_name = '{cond.value}'")
            else:
                # Assign numeric condition to appropriate column (e.g. marks > 80, salary > 85000, cgpa > 8)
                val_is_float = "." in cond.value
                val_num = float(cond.value)
                assigned = False
                for tbl in joined_tables:
                    for col_name in self.schema.tables[tbl].columns:
                        if "marks" in col_name and val_num > 10:
                            where_clauses.append(f"{alias_map[tbl]}.{col_name} {cond.operator} {cond.value}")
                            assigned = True
                            break
                        elif "salary" in col_name and val_num > 1000:
                            where_clauses.append(f"{alias_map[tbl]}.{col_name} {cond.operator} {cond.value}")
                            assigned = True
                            break
                        elif "cgpa" in col_name and val_is_float:
                            where_clauses.append(f"{alias_map[tbl]}.{col_name} {cond.operator} {cond.value}")
                            assigned = True
                            break
                    if assigned:
                        break

        # Assemble SQL
        query_parts = [f"SELECT {', '.join(select_cols)}", f"FROM {from_clause}"]
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

        # Explanation
        explanation = (
            f"Approach: Traditional NLP Baseline.\n"
            f"- Identified intent as {intent.value}.\n"
            f"- Mapped entities to tables: {', '.join(linked_tables)}.\n"
            f"- Formulated query filtering on: {', '.join(where_clauses) if where_clauses else 'No filters'}."
        )

        return BaselineGenerationResult(
            sql=sql,
            intent=intent,
            explanation=explanation,
            linked_tables=linked_tables,
            linked_columns=linked_columns,
            confidence=0.75 if linked_tables else 0.40
        )

