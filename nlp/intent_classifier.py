"""
Query Intent Classifier.
Combines TF-IDF classification and rule heuristics to determine SQL statement topology.
"""
from __future__ import annotations

from enum import Enum
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression


class QueryIntent(str, Enum):
    SIMPLE_SELECT = "SIMPLE_SELECT"
    FILTERED_SELECT = "FILTERED_SELECT"
    AGGREGATE = "AGGREGATE"
    JOIN_QUERY = "JOIN_QUERY"
    GROUP_BY_AGGREGATE = "GROUP_BY_AGGREGATE"
    ORDERED_SELECT = "ORDERED_SELECT"


# Training corpus for intent classification
INTENT_TRAINING_CORPUS = [
    ("show all students", QueryIntent.SIMPLE_SELECT),
    ("display all departments", QueryIntent.SIMPLE_SELECT),
    ("list instructors", QueryIntent.SIMPLE_SELECT),
    ("get courses", QueryIntent.SIMPLE_SELECT),
    ("find students belonging to CSE", QueryIntent.FILTERED_SELECT),
    ("students who scored more than 80", QueryIntent.FILTERED_SELECT),
    ("instructors with salary greater than 85000", QueryIntent.FILTERED_SELECT),
    ("courses with 4 credits", QueryIntent.FILTERED_SELECT),
    ("what is the average marks in DBMS", QueryIntent.AGGREGATE),
    ("find maximum salary of instructors", QueryIntent.AGGREGATE),
    ("count total number of students", QueryIntent.AGGREGATE),
    ("minimum marks in Mathematics", QueryIntent.AGGREGATE),
    ("show names of students who scored more than 80 marks in DBMS", QueryIntent.JOIN_QUERY),
    ("find students enrolled in Operating Systems", QueryIntent.JOIN_QUERY),
    ("display course titles taught by Dr Sharma", QueryIntent.JOIN_QUERY),
    ("count number of students in each department", QueryIntent.GROUP_BY_AGGREGATE),
    ("average marks for each subject", QueryIntent.GROUP_BY_AGGREGATE),
    ("total budget per department", QueryIntent.GROUP_BY_AGGREGATE),
    ("display top 5 students based on cgpa", QueryIntent.ORDERED_SELECT),
    ("show students ordered by admission year", QueryIntent.ORDERED_SELECT),
    ("lowest scoring students in OS", QueryIntent.ORDERED_SELECT),
]


class IntentClassifier:
    """Classifies user natural language query intent."""

    def __init__(self):
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2))
        self.model = LogisticRegression(max_iter=200)
        self._train()

    def _train(self):
        texts = [item[0] for item in INTENT_TRAINING_CORPUS]
        labels = [item[1].value for item in INTENT_TRAINING_CORPUS]
        X = self.vectorizer.fit_transform(texts)
        self.model.fit(X, labels)

    def classify(self, text: str) -> QueryIntent:
        """Predicts query intent using ML with rule-based verification."""
        lower = text.lower()

        # Rule overrides for high-confidence indicators
        if any(w in lower for w in ["each", "every", "per"]) and any(w in lower for w in ["count", "avg", "average", "total", "sum", "number of"]):
            return QueryIntent.GROUP_BY_AGGREGATE
        if any(w in lower for w in ["top", "first", "highest", "lowest", "bottom", "sort", "order by"]):
            return QueryIntent.ORDERED_SELECT

        X = self.vectorizer.transform([text])
        pred = self.model.predict(X)[0]
        return QueryIntent(pred)

