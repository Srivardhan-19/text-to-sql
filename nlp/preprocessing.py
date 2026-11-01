"""
NLP Preprocessing Module.
Performs text normalization, tokenization, relational-aware stopword filtering, and lemmatization.
"""
from __future__ import annotations

import re
import string
from dataclasses import dataclass
from typing import Optional

try:
    import nltk
    from nltk.corpus import stopwords
    from nltk.stem import WordNetLemmatizer
    from nltk.tokenize import word_tokenize
    _STOPWORDS = set(stopwords.words("english"))
    _LEMMATIZER = WordNetLemmatizer()
except Exception:
    _STOPWORDS = {
        "a", "an", "the", "and", "or", "of", "to", "is", "are", "was", "were",
        "it", "this", "that", "these", "those", "for", "with", "as"
    }
    _LEMMATIZER = None

# Relational keywords that must NEVER be stripped as stopwords
PRESERVED_KEYWORDS = {
    "more", "less", "greater", "fewer", "than", "above", "below", "equal",
    "top", "bottom", "highest", "lowest", "first", "last", "average", "avg",
    "sum", "total", "count", "number", "minimum", "min", "maximum", "max",
    "each", "every", "per", "group", "having", "between", "not", "order", "sort"
}

# Common contractions expansion
CONTRACTIONS = {
    r"won\'t": "will not",
    r"can\'t": "can not",
    r"n\'t": " not",
    r"\'re": " are",
    r"\'s": " is",
    r"\'d": " would",
    r"\'ll": " will",
    r"\'t": " not",
    r"\'ve": " have",
    r"\'m": " am",
}


@dataclass
class PreprocessedText:
    raw_text: str
    normalized_text: str
    tokens: list[str]
    filtered_tokens: list[str]
    lemmas: list[str]


class TextPreprocessor:
    """Preprocesses natural language queries for schema linking and SQL intent analysis."""

    def __init__(self):
        self.stopwords = _STOPWORDS - PRESERVED_KEYWORDS
        self.lemmatizer = _LEMMATIZER

    def normalize(self, text: str) -> str:
        """Lowercases, expands contractions, and normalizes whitespace."""
        normalized = text.lower().strip()
        for pattern, replacement in CONTRACTIONS.items():
            normalized = re.sub(pattern, replacement, normalized)
        # Remove trailing question mark or period
        normalized = re.sub(r"[?!.]+$", "", normalized).strip()
        return normalized

    def tokenize(self, text: str) -> list[str]:
        """Tokenizes text using NLTK or whitespace regex fallback."""
        try:
            return word_tokenize(text)
        except Exception:
            return re.findall(r"\b\w+(?:[-']\w+)?\b|[><=]+", text)

    def lemmatize(self, token: str) -> str:
        """Lemmatizes token with noun and verb fallback."""
        if self.lemmatizer:
            try:
                lemma = self.lemmatizer.lemmatize(token, pos="v")
                if lemma == token:
                    lemma = self.lemmatizer.lemmatize(token, pos="n")
                return lemma
            except Exception:
                pass
        return token

    def preprocess(self, text: str) -> PreprocessedText:
        normalized = self.normalize(text)
        tokens = self.tokenize(normalized)
        filtered = [t for t in tokens if t not in self.stopwords and t not in string.punctuation]
        lemmas = [self.lemmatize(t) for t in filtered]

        return PreprocessedText(
            raw_text=text,
            normalized_text=normalized,
            tokens=tokens,
            filtered_tokens=filtered,
            lemmas=lemmas
        )

