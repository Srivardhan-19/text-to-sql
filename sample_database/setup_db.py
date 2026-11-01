"""
Database Initialization Script for College Management System.
Supports populating both live MySQL and local SQLite instances for testing.
"""
from __future__ import annotations

import argparse
import logging
import re
import sys
from pathlib import Path

# Ensure repository root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sqlalchemy import create_engine, text

from config.settings import get_settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

CURRENT_DIR = Path(__file__).resolve().parent
SCHEMA_FILE = CURRENT_DIR / "schema.sql"
DATA_FILE = CURRENT_DIR / "sample_data.sql"


def adapt_sql_for_sqlite(sql_content: str) -> str:
    """Adapts MySQL DDL statements for SQLite compatibility."""
    # Replace AUTO_INCREMENT with AUTOINCREMENT (in SQLite, INTEGER PRIMARY KEY AUTOINCREMENT)
    sql = re.sub(r'INT\s+AUTO_INCREMENT\s+PRIMARY\s+KEY', 'INTEGER PRIMARY KEY AUTOINCREMENT', sql_content, flags=re.IGNORECASE)
    sql = re.sub(r'INT\s+AUTO_INCREMENT', 'INTEGER PRIMARY KEY AUTOINCREMENT', sql, flags=re.IGNORECASE)
    # Remove ENGINE=InnoDB
    sql = re.sub(r'ENGINE\s*=\s*InnoDB;?', ';', sql, flags=re.IGNORECASE)
    return sql


def split_sql_statements(sql_content: str) -> list[str]:
    """Splits SQL string into individual runnable statements, skipping comments."""
    statements = []
    current: list[str] = []
    
    for line in sql_content.splitlines():
        trimmed = line.strip()
        if not trimmed or trimmed.startswith("--") or trimmed.startswith("/*"):
            continue
        current.append(line)
        if trimmed.endswith(";"):
            stmt = "\n".join(current).strip()
            if stmt:
                statements.append(stmt)
            current = []
    return statements


def init_database(engine, is_sqlite: bool = False) -> None:
    """Executes schema creation and seeds sample data."""
    with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
        schema_raw = f.read()
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data_raw = f.read()

    if is_sqlite:
        schema_raw = adapt_sql_for_sqlite(schema_raw)

    schema_statements = split_sql_statements(schema_raw)
    data_statements = split_sql_statements(data_raw)

    with engine.begin() as conn:
        logger.info(f"Executing {len(schema_statements)} schema statements...")
        for stmt in schema_statements:
            conn.execute(text(stmt))

        logger.info(f"Executing {len(data_statements)} data seed statements...")
        for stmt in data_statements:
            conn.execute(text(stmt))

    logger.info("Database initialized and seeded successfully.")


def main():
    parser = argparse.ArgumentParser(description="Initialize College Management DB")
    parser.add_argument("--sqlite", action="store_true", help="Initialize SQLite DB for testing")
    parser.add_argument("--sqlite-path", default="college_db.sqlite", help="SQLite database path")
    args = parser.parse_args()

    settings = get_settings()

    if args.sqlite:
        db_path = Path(args.sqlite_path)
        if db_path.exists():
            db_path.unlink()
        engine = create_engine(f"sqlite:///{db_path}")
        logger.info(f"Target: SQLite file '{db_path}'")
        init_database(engine, is_sqlite=True)
    else:
        # MySQL mode
        try:
            # First connect without database to create DB if not exists
            server_url = settings.db.get_connection_url(database="")
            server_engine = create_engine(server_url)
            with server_engine.connect() as conn:
                conn.execute(text(f"CREATE DATABASE IF NOT EXISTS `{settings.db.database}`"))
            logger.info(f"Ensured database '{settings.db.database}' exists.")

            target_engine = create_engine(settings.db.get_connection_url())
            init_database(target_engine, is_sqlite=False)
        except Exception as e:
            logger.error(f"MySQL connection error: {e}")
            logger.info("Tip: You can use --sqlite flag for a local self-contained test environment.")
            sys.exit(1)


if __name__ == "__main__":
    main()
