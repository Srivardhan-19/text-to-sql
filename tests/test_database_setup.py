"""Tests for College Management Database Schema and Seed Data."""
import pytest
from pathlib import Path
from sqlalchemy import create_engine, inspect, text
from sample_database.setup_db import init_database

EXPECTED_TABLES = {
    "departments",
    "instructors",
    "students",
    "courses",
    "enrollments",
    "marks",
    "classrooms",
}


@pytest.fixture(scope="module")
def sqlite_test_engine(tmp_path_factory):
    """Creates a temporary in-memory or file-based SQLite database for testing."""
    db_file = tmp_path_factory.mktemp("db") / "test_college.sqlite"
    engine = create_engine(f"sqlite:///{db_file}")
    init_database(engine, is_sqlite=True)
    yield engine
    engine.dispose()


def test_tables_created(sqlite_test_engine):
    """Verify all 7 expected tables are created."""
    inspector = inspect(sqlite_test_engine)
    tables = set(inspector.get_table_names())
    assert EXPECTED_TABLES.issubset(tables), f"Missing tables: {EXPECTED_TABLES - tables}"


def test_sample_query_execution(sqlite_test_engine):
    """
    Verify the user's motivating query executes and produces valid results:
    'Show the names of students who scored more than 80 marks in DBMS.'
    """
    query = """
    SELECT s.student_name
    FROM students s
    JOIN marks m ON s.student_id = m.student_id
    WHERE m.subject = 'DBMS'
    AND m.marks > 80
    ORDER BY s.student_name;
    """
    with sqlite_test_engine.connect() as conn:
        result = conn.execute(text(query)).fetchall()
        student_names = [row[0] for row in result]
        assert len(student_names) == 3
        assert student_names == ["Aarav Patel", "Ananya Iyer", "Diya Sen"]


def test_foreign_key_relationships(sqlite_test_engine):
    """Verify foreign keys are registered properly."""
    inspector = inspect(sqlite_test_engine)
    fks = inspector.get_foreign_keys("marks")
    referred_tables = {fk["referred_table"] for fk in fks}
    assert "students" in referred_tables
    assert "courses" in referred_tables

