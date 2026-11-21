"""Initial setup and configuration test (Traditional NLP)."""
import pytest
from config.settings import get_settings


def test_settings_loaded():
    """Verify settings load properly from .env."""
    settings = get_settings()
    assert settings is not None
    assert settings.db.port == 3306
    assert settings.safety.max_rows == 100
    assert settings.safety.allow_write is False
    assert settings.app_env in ("development", "production", "test")


def test_core_dependencies():
    """Verify all critical libraries are importable and available."""
    import sqlalchemy
    import pymysql
    import sqlglot
    import streamlit
    import sklearn
    import nltk
    import pandas
    import numpy
    
    assert sqlalchemy.__version__ is not None
    assert pymysql.__version__ is not None
    assert sqlglot.__version__ is not None
    assert streamlit.__version__ is not None
    assert sklearn.__version__ is not None
    assert nltk.__version__ is not None
    assert pandas.__version__ is not None
    assert numpy.__version__ is not None
