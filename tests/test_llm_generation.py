"""Tests for Schema-Aware Prompt Building, Response Parsing, and LLM Generator Fallbacks."""
import pytest
from sqlalchemy import create_engine
from sample_database.setup_db import init_database
from database.schema_detector import SchemaDetector
from generation.prompt_builder import PromptBuilder
from generation.response_parser import ResponseParser
from generation.llm_generator import LLMGenerator


@pytest.fixture(scope="module")
def sqlite_test_db(tmp_path_factory):
    db_file = tmp_path_factory.mktemp("db") / "llm_college.sqlite"
    engine = create_engine(f"sqlite:///{db_file}")
    init_database(engine, is_sqlite=True)
    yield engine
    engine.dispose()


def test_prompt_builder_structure(sqlite_test_db):
    schema = SchemaDetector(sqlite_test_db).detect()
    builder = PromptBuilder(schema)

    sys_prompt = builder.build_system_prompt()
    assert "DATABASE SCHEMA:" in sys_prompt
    assert "Table students:" in sys_prompt
    assert "Only generate SELECT queries" in sys_prompt

    user_prompt = builder.build_user_prompt("Find the average marks in DBMS.")
    assert "### FEW-SHOT EXAMPLES:" in user_prompt
    assert "Find the average marks in DBMS." in user_prompt


def test_response_parser_markdown_and_json():
    # Valid JSON enclosed in markdown fences
    raw = """```json
    {
        "sql": "SELECT student_name FROM students WHERE cgpa > 9.0;",
        "explanation": "Selects student names with CGPA exceeding 9.0.",
        "tables_used": ["students"],
        "columns_used": ["students.student_name", "students.cgpa"],
        "assumptions": [],
        "needs_clarification": false
    }
    ```"""
    parsed = ResponseParser.parse(raw)
    assert parsed.is_valid_json is True
    assert parsed.sql == "SELECT student_name FROM students WHERE cgpa > 9.0;"
    assert parsed.tables_used == ["students"]
    assert parsed.needs_clarification is False


def test_response_parser_regex_fallback():
    # Malformed text containing raw SQL
    raw = "Here is the query you requested: SELECT dept_name, budget FROM departments; Enjoy!"
    parsed = ResponseParser.parse(raw)
    assert parsed.is_valid_json is False
    assert parsed.sql == "SELECT dept_name, budget FROM departments;"


def test_llm_generator_offline_fallback(sqlite_test_db):
    schema = SchemaDetector(sqlite_test_db).detect()
    generator = LLMGenerator(schema)

    # Force offline mode
    res = generator.generate("Show students who scored more than 80 marks in DBMS", force_provider="offline")
    assert res.sql.startswith("SELECT")
    assert "marks" in res.tables_used
    assert res.provider == "offline-baseline"
    assert res.generation_time_ms >= 0.0

