"""Tests for SQLGlot AST Validation, Schema Whitelisting, and Safe Query Execution."""
import pytest
from sqlalchemy import create_engine
from sample_database.setup_db import init_database
from database.schema_detector import SchemaDetector
from database.query_executor import QueryExecutor
from validation.sql_validator import SQLValidator
from validation.schema_validator import SchemaValidator


@pytest.fixture(scope="module")
def sqlite_test_db(tmp_path_factory):
    db_file = tmp_path_factory.mktemp("db") / "val_college.sqlite"
    engine = create_engine(f"sqlite:///{db_file}")
    init_database(engine, is_sqlite=True)
    yield engine
    engine.dispose()


def test_sql_validator_valid_select():
    validator = SQLValidator()
    res = validator.validate("SELECT s.student_name, m.marks FROM students s JOIN marks m ON s.student_id = m.student_id;")
    assert res.is_valid is True
    assert "students" in res.tables_referenced
    assert "marks" in res.tables_referenced


def test_sql_validator_mutation_rejection():
    validator = SQLValidator()

    # Rejection of DROP TABLE
    drop_res = validator.validate("DROP TABLE students;")
    assert drop_res.is_valid is False
    assert "Forbidden SQL operation 'Drop'" in drop_res.error_message

    # Rejection of DELETE
    delete_res = validator.validate("DELETE FROM students WHERE student_id = 1;")
    assert delete_res.is_valid is False
    assert "Forbidden SQL operation 'Delete'" in delete_res.error_message

    # Rejection of INSERT
    insert_res = validator.validate("INSERT INTO students (student_name) VALUES ('Hacker');")
    assert insert_res.is_valid is False

    # Rejection of multi-statement SQL injection
    multi_res = validator.validate("SELECT * FROM students; DROP TABLE marks;")
    assert multi_res.is_valid is False
    assert "Multiple SQL statements detected" in multi_res.error_message


def test_schema_validator(sqlite_test_db):
    schema = SchemaDetector(sqlite_test_db).detect()
    sql_val = SQLValidator()
    schema_val = SchemaValidator(schema)

    # Valid schema references
    res_valid = sql_val.validate("SELECT student_name, cgpa FROM students;")
    schema_check = schema_val.validate(res_valid)
    assert schema_check.is_valid is True

    # Invalid table reference
    res_invalid_tbl = sql_val.validate("SELECT * FROM unauthorized_payroll_table;")
    tbl_check = schema_val.validate(res_invalid_tbl)
    assert tbl_check.is_valid is False
    assert "unauthorized_payroll_table" in tbl_check.error_message

    # Invalid column reference
    res_invalid_col = sql_val.validate("SELECT secret_ssn FROM students;")
    col_check = schema_val.validate(res_invalid_col)
    assert col_check.is_valid is False
    assert "secret_ssn" in col_check.error_message


def test_query_executor(sqlite_test_db):
    executor = QueryExecutor(sqlite_test_db)
    query = "SELECT student_name, cgpa FROM students WHERE cgpa > 8.5 ORDER BY cgpa DESC"
    result = executor.execute(query)

    assert result.success is True
    assert result.row_count > 0
    assert result.columns == ["student_name", "cgpa"]
    assert result.execution_time_ms > 0
    assert "LIMIT 100" in result.sql_executed

    # Verify DataFrame conversion
    df = result.to_dataframe()
    assert not df.empty
    assert "student_name" in df.columns

