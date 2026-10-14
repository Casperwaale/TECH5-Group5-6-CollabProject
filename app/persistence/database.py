"""Database connection and lifecycle manager for SQLite persistence.

This module provides thread-safe connection pooling, transaction management,
foreign-key enforcement, and schema initialization for TECH5.
"""

import contextlib
import pathlib
import sqlite3
from collections.abc import Iterator
from typing import Any

from app import config


class DatabaseManager:
    """Manages SQLite database connections and transactions."""

    def __init__(self, db_path: pathlib.Path | str | None = None) -> None:
        """Initializes the database manager with target file path.

        Args:
            db_path: Optional custom path to SQLite database file.
        """
        if db_path is None:
            self.db_path = config.Config.DATABASE_PATH
        elif isinstance(db_path, str):
            self.db_path = pathlib.Path(db_path)
        else:
            self.db_path = db_path

        # Ensure parent directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def get_connection(self) -> sqlite3.Connection:
        """Creates and configures a new SQLite connection.

        Returns:
            An active SQLite Connection configured with Row factory and FKs.
        """
        conn = sqlite3.connect(
            str(self.db_path),
            timeout=30.0,
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
        )
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA journal_mode = WAL;")
        return conn

    @contextlib.contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        """Context manager yielding a managed connection with transaction.

        Yields:
            An active sqlite3.Connection.
        """
        conn = self.get_connection()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def initialize_schema(self) -> None:
        """Executes the DDL schema script to establish tables and indexes."""
        schema_path = pathlib.Path(__file__).parent / "schema.sql"
        with open(schema_path, mode="r", encoding="utf-8") as f:
            ddl_script = f.read()

        with self.connection() as conn:
            conn.executescript(ddl_script)

    def execute_query(
        self,
        query: str,
        params: dict[str, Any] | tuple[Any, ...] | None = None,
    ) -> list[sqlite3.Row]:
        """Executes a parameterized SELECT query and returns all rows.

        Args:
            query: The SQL query text.
            params: Parameters for SQL substitution.

        Returns:
            List of sqlite3.Row objects.
        """
        with self.connection() as conn:
            cursor = conn.cursor()
            if params is None:
                cursor.execute(query)
            else:
                cursor.execute(query, params)
            return cursor.fetchall()

    def execute_statement(
        self,
        statement: str,
        params: dict[str, Any] | tuple[Any, ...] | None = None,
    ) -> int:
        """Executes an INSERT, UPDATE, or DELETE statement.

        Args:
            statement: The SQL statement text.
            params: Parameters for SQL substitution.

        Returns:
            The rowcount of modified records.
        """
        with self.connection() as conn:
            cursor = conn.cursor()
            if params is None:
                cursor.execute(statement)
            else:
                cursor.execute(statement, params)
            return cursor.rowcount


# Singleton default instance
db_manager = DatabaseManager()
