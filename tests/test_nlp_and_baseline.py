"""Tests for NLP Preprocessing, Keyword Extraction, Intent Classification, and Baseline Generation."""
import pytest
from sqlalchemy import create_engine
from sample_database.setup_db import init_database
from database.schema_detector import SchemaDetector
from nlp.preprocessing import TextPreprocessor
from nlp.keyword_extraction import KeywordExtractor
from nlp.entity_extractor import SchemaLinker
from nlp.intent_classifier import IntentClassifier, QueryIntent
from generation.baseline_generator import BaselineSQLGenerator


@pytest.fixture(scope="module")
def sqlite_test_db(tmp_path_factory):
    db_file = tmp_path_factory.mktemp("db") / "nlp_college.sqlite"
    engine = create_engine(f"sqlite:///{db_file}")
    init_database(engine, is_sqlite=True)
    yield engine
    engine.dispose()


def test_text_preprocessor():
    prep = TextPreprocessor()
    res = prep.preprocess("Show students who scored more than 80 marks?")
    assert "more" in res.filtered_tokens  # relational keyword preserved
    assert "than" in res.filtered_tokens
    assert "?" not in res.normalized_text


def test_keyword_extractor():
    extractor = KeywordExtractor()
    kw = extractor.extract("Show top 5 students who scored more than 80 marks in DBMS")
    assert kw.limit == 5
    assert kw.order_by_direction == "DESC"
    assert any(c.operator == ">" and c.value == "80" for c in kw.conditions)
    assert any(c.operator == "=" and c.value == "DBMS" for c in kw.conditions)


def test_intent_classifier():
    classifier = IntentClassifier()
    assert classifier.classify("show all students") == QueryIntent.SIMPLE_SELECT
    assert classifier.classify("what is the average marks in DBMS") == QueryIntent.AGGREGATE
    assert classifier.classify("count students in each department") == QueryIntent.GROUP_BY_AGGREGATE
    assert classifier.classify("top 5 students based on cgpa") == QueryIntent.ORDERED_SELECT


def test_baseline_generator_motivating_query(sqlite_test_db):
    """
    Test the user's example:
    'Show the names of students who scored more than 80 marks in DBMS.'
    """
    schema = SchemaDetector(sqlite_test_db).detect()
    generator = BaselineSQLGenerator(schema)
    res = generator.generate("Show the names of students who scored more than 80 marks in DBMS")

    assert "students" in res.linked_tables
    assert "marks" in res.linked_tables
    assert "SELECT" in res.sql
    assert "JOIN marks" in res.sql or "JOIN students" in res.sql
    assert "marks > 80" in res.sql
    assert "subject = 'DBMS'" in res.sql

