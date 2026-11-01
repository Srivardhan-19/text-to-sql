"""Tests for Dynamic Schema Detection, Graph Navigation, and Formatting."""
import pytest
from pathlib import Path
from sqlalchemy import create_engine
from sample_database.setup_db import init_database
from database.connection import ConnectionManager
from database.schema_detector import SchemaDetector
from database.schema_formatter import SchemaFormatter


@pytest.fixture(scope="module")
def sqlite_test_db(tmp_path_factory):
    """Initializes a temporary SQLite database with college management schema."""
    db_file = tmp_path_factory.mktemp("db") / "college_test.sqlite"
    engine = create_engine(f"sqlite:///{db_file}")
    init_database(engine, is_sqlite=True)
    yield engine
    engine.dispose()


def test_connection_manager_sqlite(sqlite_test_db):
    """Test connection testing logic."""
    mgr = ConnectionManager()
    success, msg = mgr.test_connection(str(sqlite_test_db.url))
    assert success is True
    assert "successful" in msg.lower()


def test_schema_detector_tables_and_columns(sqlite_test_db):
    """Verify tables, columns, and data types are introspected dynamically."""
    detector = SchemaDetector(sqlite_test_db)
    schema = detector.detect()

    expected_tables = {"departments", "instructors", "students", "courses", "enrollments", "marks", "classrooms"}
    assert set(schema.get_table_names()) == expected_tables

    student_cols = set(schema.get_column_names("students"))
    assert {"student_id", "student_name", "gender", "dept_id", "admission_year", "cgpa"}.issubset(student_cols)

    # Check primary keys
    assert schema.tables["students"].primary_keys == ["student_id"]
    assert schema.tables["marks"].primary_keys == ["mark_id"]


def test_join_path_discovery(sqlite_test_db):
    """Verify graph BFS finds valid JOIN paths between tables."""
    detector = SchemaDetector(sqlite_test_db)
    schema = detector.detect()

    # Direct 1-hop path: students -> marks
    path = schema.find_join_path("students", "marks")
    assert len(path) == 1
    assert (path[0].source_table, path[0].target_table) in [("students", "marks"), ("marks", "students")]

    # Multi-hop path: students -> departments
    path_dept = schema.find_join_path("students", "departments")
    assert len(path_dept) == 1

    # Multi-hop path: students -> instructors (students -> departments -> instructors)
    path_inst = schema.find_join_path("students", "instructors")
    assert len(path_inst) == 2


def test_schema_formatter_outputs(sqlite_test_db):
    """Verify prompt formatting and markdown summary generation."""
    detector = SchemaDetector(sqlite_test_db)
    schema = detector.detect()

    prompt_str = SchemaFormatter.to_prompt_string(schema)
    assert "Database Dialect: MySQL" in prompt_str
    assert "Table students:" in prompt_str
    assert "student_name" in prompt_str

    md_summary = SchemaFormatter.to_markdown_summary(schema)
    assert "#### Table: `students`" in md_summary
    assert "| Column | Data Type |" in md_summary

    schema_dict = SchemaFormatter.to_dict(schema)
    assert "students" in schema_dict["tables"]
    assert "marks" in schema_dict["tables"]

