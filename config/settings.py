"""
Application Configuration and Settings Module.
Loads environment variables safely and provides strongly-typed configuration objects.
Strictly traditional NLP architecture (no LLMs or external generative APIs).
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Optional

# Attempt to load python-dotenv if present
try:
    from dotenv import load_dotenv
    BASE_DIR = Path(__file__).resolve().parent.parent
    env_file = BASE_DIR / ".env"
    if env_file.exists():
        load_dotenv(dotenv_path=env_file)
except ImportError:
    BASE_DIR = Path(__file__).resolve().parent.parent
    env_file = BASE_DIR / ".env"
    if env_file.exists():
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    key = key.strip()
                    val = val.strip().strip("'\"")
                    if key not in os.environ:
                        os.environ[key] = val


from urllib.parse import quote_plus

@dataclass
class DatabaseSettings:
    """MySQL Database connection configuration."""
    host: str = field(default_factory=lambda: os.getenv("MYSQL_HOST", "localhost"))
    port: int = field(default_factory=lambda: int(os.getenv("MYSQL_PORT", "3306")))
    user: str = field(default_factory=lambda: os.getenv("MYSQL_USER", "root"))
    password: str = field(default_factory=lambda: os.getenv("MYSQL_PASSWORD", ""))
    database: str = field(default_factory=lambda: os.getenv("MYSQL_DATABASE", "college_db"))
    
    def get_connection_url(self, masked: bool = False, database: Optional[str] = None) -> str:
        """Returns SQLAlchemy connection string with PyMySQL driver."""
        db_target = database if database is not None else self.database
        db_suffix = f"/{db_target}" if db_target else ""
        if masked:
            pwd = "••••••" if self.password else ""
        else:
            pwd = quote_plus(self.password) if self.password else ""
            
        if pwd:
            return f"mysql+pymysql://{quote_plus(self.user)}:{pwd}@{self.host}:{self.port}{db_suffix}"
        return f"mysql+pymysql://{quote_plus(self.user)}@{self.host}:{self.port}{db_suffix}"


@dataclass
class SafetySettings:
    """SQL Parsing & Execution safety constraints."""
    execution_timeout: int = field(default_factory=lambda: int(os.getenv("SQL_EXECUTION_TIMEOUT", "10")))
    max_rows: int = field(default_factory=lambda: int(os.getenv("SQL_MAX_ROWS", "100")))
    allow_write: bool = field(default_factory=lambda: os.getenv("SQL_ALLOW_WRITE", "false").lower() in ("true", "1", "yes"))


@dataclass
class Settings:
    """Consolidated application settings container (Traditional NLP only)."""
    db: DatabaseSettings = field(default_factory=DatabaseSettings)
    safety: SafetySettings = field(default_factory=SafetySettings)
    app_env: str = field(default_factory=lambda: os.getenv("APP_ENV", "development"))
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    base_dir: Path = field(default_factory=lambda: BASE_DIR)


@lru_cache()
def get_settings() -> Settings:
    """Singleton getter for application settings."""
    return Settings()
