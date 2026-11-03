import os
import sqlite3
from contextlib import contextmanager

DB_NAME = os.environ.get("WORLDBANK_DB", "worldbank.db")


class DuplicateRecordError(Exception):
    """A record with the same country, indicator and year already exists."""


def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def connection():
    """Open a connection and always close it, even if an error occurs."""
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    with connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS indicators (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                country_code TEXT NOT NULL,
                country_name TEXT NOT NULL,
                indicator_name TEXT NOT NULL,
                value REAL NOT NULL,
                year INTEGER NOT NULL
            )
            """
        )
        # Uniqueness is enforced by the database itself, so duplicates are
        # impossible even with concurrent requests or PATCH updates.
        try:
            conn.execute(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_indicator
                ON indicators (country_code, indicator_name, year)
                """
            )
        except sqlite3.IntegrityError:
            print(
                "WARNING: worldbank.db already contains duplicate records, "
                "so the unique index was not created. Remove the duplicates "
                "and restart the app."
            )
        conn.commit()


def get_all_indicators(search_query=None):
    with connection() as conn:
        if search_query:
            pattern = f"%{search_query}%"
            rows = conn.execute(
                """
                SELECT * FROM indicators
                WHERE country_name LIKE ?
                   OR country_code LIKE ?
                   OR indicator_name LIKE ?
                ORDER BY year DESC
                """,
                (pattern, pattern, pattern),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM indicators ORDER BY year DESC"
            ).fetchall()
    return [dict(row) for row in rows]


def get_indicator_by_id(item_id):
    with connection() as conn:
        row = conn.execute(
            "SELECT * FROM indicators WHERE id = ?", (item_id,)
        ).fetchone()
    return dict(row) if row else None


def is_indicator_saved(country_code, indicator_name, year):
    with connection() as conn:
        row = conn.execute(
            """
            SELECT 1 FROM indicators
            WHERE country_code = ? AND indicator_name = ? AND year = ?
            LIMIT 1
            """,
            (country_code, indicator_name, year),
        ).fetchone()
    return row is not None


def get_saved_keys(indicator_name):
    """Return a set of (country_code, year) pairs saved for one indicator.

    One query instead of one query per row of the external API response.
    """
    with connection() as conn:
        rows = conn.execute(
            "SELECT country_code, year FROM indicators WHERE indicator_name = ?",
            (indicator_name,),
        ).fetchall()
    return {(row["country_code"], row["year"]) for row in rows}


def add_indicator(country_code, country_name, indicator_name, value, year):
    """Insert a record and return its id.

    Raises DuplicateRecordError if the record already exists.
    """
    with connection() as conn:
        try:
            cursor = conn.execute(
                """
                INSERT INTO indicators
                    (country_code, country_name, indicator_name, value, year)
                VALUES (?, ?, ?, ?, ?)
                """,
                (country_code, country_name, indicator_name, value, year),
            )
            conn.commit()
        except sqlite3.IntegrityError as exc:
            raise DuplicateRecordError from exc
        return cursor.lastrowid


def update_indicator(
    item_id,
    country_code=None,
    country_name=None,
    indicator_name=None,
    value=None,
    year=None,
):
    """Update the given fields of a record.

    Returns False if the record does not exist.
    Raises DuplicateRecordError if the update would create a duplicate.
    """
    existing = get_indicator_by_id(item_id)
    if not existing:
        return False

    updated = (
        country_code if country_code is not None else existing["country_code"],
        country_name if country_name is not None else existing["country_name"],
        indicator_name if indicator_name is not None else existing["indicator_name"],
        value if value is not None else existing["value"],
        year if year is not None else existing["year"],
        item_id,
    )

    with connection() as conn:
        try:
            conn.execute(
                """
                UPDATE indicators
                SET country_code = ?, country_name = ?, indicator_name = ?,
                    value = ?, year = ?
                WHERE id = ?
                """,
                updated,
            )
            conn.commit()
        except sqlite3.IntegrityError as exc:
            raise DuplicateRecordError from exc
    return True


def delete_indicator(item_id):
    with connection() as conn:
        cursor = conn.execute("DELETE FROM indicators WHERE id = ?", (item_id,))
        conn.commit()
        return cursor.rowcount > 0