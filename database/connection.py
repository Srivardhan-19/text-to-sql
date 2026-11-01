"""
Database Connection Manager.
Handles engine creation, connection validation, and safe credential handling.
"""
from __future__ import annotations

import logging
from typing import Optional
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from config.settings import DatabaseSettings, get_settings

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages SQLAlchemy database connections for MySQL and SQLite."""

    def __init__(self, settings: Optional[DatabaseSettings] = None):
        self.settings = settings or get_settings().db
        self._engine: Optional[Engine] = None

    def get_engine(self, custom_url: Optional[str] = None) -> Engine:
        """Returns active engine, creating one if not initialized."""
        if custom_url:
            return create_engine(custom_url, pool_pre_ping=True)
        if self._engine is None:
            url = self.settings.get_connection_url()
            self._engine = create_engine(url, pool_pre_ping=True)
        return self._engine

    def test_connection(self, url: Optional[str] = None) -> tuple[bool, str]:
        """
        Validates database connectivity.
        Returns: (success: bool, message: str)
        """
        target_url = url or self.settings.get_connection_url()
        try:
            temp_engine = create_engine(target_url, pool_pre_ping=True)
            with temp_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            temp_engine.dispose()
            return True, "Connection successful."
        except Exception as e:
            logger.warning(f"Connection test failed: {e}")
            return False, str(e)

    def close(self):
        """Disposes active engine."""
        if self._engine:
            self._engine.dispose()
            self._engine = None

