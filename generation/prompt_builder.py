"""
Prompt Builder for Schema-Aware LLM SQL Generation.
Constructs in-context prompts with schema DDL, foreign key relationships, few-shot examples, and MySQL guidelines.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Optional
from database.schema_detector import DatabaseSchema
from database.schema_formatter import SchemaFormatter

FEW_SHOT_EXAMPLES = [
    {
        "question": "Show all students enrolled in the Computer Science department.",
        "sql": "SELECT s.student_name FROM students s JOIN departments d ON s.dept_id = d.dept_id WHERE d.dept_name = 'Computer Science';",
        "explanation": "Joins students and departments on dept_id, filtering for 'Computer Science' to retrieve student names.",
        "tables_used": ["students", "departments"],
        "columns_used": ["students.student_name", "students.dept_id", "departments.dept_id", "departments.dept_name"],
        "assumptions": ["Assumes exact department name matching"],
        "needs_clarification": False
    },
    {
        "question": "What is the average salary of instructors in each department?",
        "sql": "SELECT d.dept_name, AVG(i.salary) AS avg_salary FROM instructors i JOIN departments d ON i.dept_id = d.dept_id GROUP BY d.dept_name;",
        "explanation": "Joins instructors and departments, groups by department name, and calculates average instructor salary.",
        "tables_used": ["instructors", "departments"],
        "columns_used": ["instructors.salary", "instructors.dept_id", "departments.dept_id", "departments.dept_name"],
        "assumptions": [],
        "needs_clarification": False
    },
    {
        "question": "Show the names of students who scored more than 80 marks in DBMS.",
        "sql": "SELECT s.student_name FROM students s JOIN marks m ON s.student_id = m.student_id WHERE m.subject = 'DBMS' AND m.marks > 80;",
        "explanation": "Joins students and marks on student_id, filters by subject 'DBMS' and marks > 80.",
        "tables_used": ["students", "marks"],
        "columns_used": ["students.student_name", "students.student_id", "marks.student_id", "marks.subject", "marks.marks"],
        "assumptions": ["Assumes 'DBMS' is stored in marks.subject"],
        "needs_clarification": False
    }
]


class PromptBuilder:
    """Builds prompt payloads for LLM Text-to-SQL tasks."""

    def __init__(self, schema: DatabaseSchema):
        self.schema = schema

    def build_system_prompt(self) -> str:
        schema_text = SchemaFormatter.to_prompt_string(self.schema)
        return f"""You are an expert NLP-to-MySQL database query generator.
Your role is to translate natural language user questions into valid, safe, and efficient MySQL queries.

### DATABASE SCHEMA:
{schema_text}

### RULES & CONSTRAINTS:
1. DIALECT: Output standard MySQL 8.0 compatible SQL.
2. PERMITTED OPERATIONS: Only generate SELECT queries. NEVER generate INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, or CREATE statements.
3. SINGLE STATEMENT: Generate exactly one SQL statement ending with a semicolon.
4. TABLE & COLUMN REFERENCES: Use only tables and columns explicitly present in the provided schema.
5. JOINS: Join tables using proper primary key and foreign key relationships.
6. STRING COMPARISONS: Use single quotes for string literals.
7. AMBIGUITY: If the question is ambiguous or lacks necessary schema information, set needs_clarification to true and explain in assumptions.
8. OUTPUT FORMAT: Respond ONLY with a valid JSON object matching this exact JSON schema:
{{
  "sql": "SELECT ...;",
  "explanation": "Simple English explanation of the SQL logic clause by clause",
  "tables_used": ["table1", "table2"],
  "columns_used": ["table1.col1", "table2.col2"],
  "assumptions": ["Assumption 1", "Assumption 2"],
  "needs_clarification": false
}}"""

    def build_user_prompt(self, question: str, conversation_history: Optional[list[dict[str, str]]] = None) -> str:
        prompt_parts = []

        # Add few-shot examples
        prompt_parts.append("### FEW-SHOT EXAMPLES:")
        for ex in FEW_SHOT_EXAMPLES:
            prompt_parts.append(f"Question: {ex['question']}")
            prompt_parts.append(f"Response: {json.dumps(ex)}")
            prompt_parts.append("")

        # Add conversation history for conversational context
        if conversation_history:
            prompt_parts.append("### CONVERSATION CONTEXT:")
            for turn in conversation_history:
                prompt_parts.append(f"Previous Question: {turn.get('question', '')}")
                prompt_parts.append(f"Previous SQL: {turn.get('sql', '')}")
            prompt_parts.append("")

        prompt_parts.append(f"### CURRENT QUESTION:\n{question}")
        prompt_parts.append("\nReturn strictly JSON without markdown code fences.")

        return "\n".join(prompt_parts)

