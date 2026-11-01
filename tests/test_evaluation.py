"""Tests for Evaluation Dataset, Exact Match Normalization, Execution Accuracy, and Benchmark Suite."""
import pytest
from sqlalchemy import create_engine
from sample_database.setup_db import init_database
from database.schema_detector import SchemaDetector
from evaluation.dataset_loader import DatasetLoader
from evaluation.exact_match import compute_exact_match, normalize_sql
from evaluation.execution_accuracy import compute_execution_accuracy
from evaluation.evaluate import run_benchmark_suite


@pytest.fixture(scope="module")
def sqlite_test_db(tmp_path_factory):
    db_file = tmp_path_factory.mktemp("db") / "eval_college.sqlite"
    engine = create_engine(f"sqlite:///{db_file}")
    init_database(engine, is_sqlite=True)
    yield engine
    engine.dispose()


def test_dataset_loader():
    items = DatasetLoader.load(split="test")
    assert len(items) >= 10
    difficulties = {item.difficulty for item in items}
    assert any("Level 1" in d for d in difficulties)
    assert any("Level 3" in d for d in difficulties)


def test_exact_match_normalization():
    sql1 = "SELECT student_name FROM students WHERE cgpa > 8.5;"
    sql2 = "select student_name from students where cgpa > 8.5"
    assert compute_exact_match(sql1, sql2) is True

    sql_diff = "SELECT student_name FROM students WHERE cgpa < 7.0;"
    assert compute_exact_match(sql1, sql_diff) is False


def test_execution_accuracy(sqlite_test_db):
    sql1 = "SELECT student_name FROM students WHERE cgpa > 9.0;"
    # Alternative query with table alias producing identical records
    sql2 = "SELECT s.student_name FROM students s WHERE s.cgpa > 9.0;"
    assert compute_execution_accuracy(sql1, sql2, sqlite_test_db) is True


def test_benchmark_suite_execution(sqlite_test_db):
    schema = SchemaDetector(sqlite_test_db).detect()
    summary_df, detailed_df = run_benchmark_suite(schema, sqlite_test_db)

    assert not summary_df.empty
    assert "Execution Accuracy (EX %)" in summary_df.columns
    assert len(detailed_df) >= 20  # Baseline + LLM across items
