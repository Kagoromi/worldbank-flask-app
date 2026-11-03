import sqlite3

DB_NAME = "worldbank.db"


def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
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
    conn.commit()
    conn.close()


def get_all_indicators(search_query=None):
    conn = get_connection()
    cursor = conn.cursor()
    if search_query:
        query = """
            SELECT * FROM indicators 
            WHERE country_name LIKE ? OR country_code LIKE ? 
            ORDER BY year DESC
        """
        pattern = f"%{search_query}%"
        cursor.execute(query, (pattern, pattern))
    else:
        query = "SELECT * FROM indicators ORDER BY year DESC"
        cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_indicator_by_id(item_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM indicators WHERE id = ?", (item_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def is_indicator_saved(country_code, indicator_name, year):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT 1 FROM indicators 
        WHERE country_code = ? AND indicator_name = ? AND year = ?
        LIMIT 1
    """,
        (country_code, indicator_name, year),
    )
    row = cursor.fetchone()
    conn.close()
    return row is not None


def add_indicator(country_code, country_name, indicator_name, value, year):
    # Перевірка на дублікати перед збереженням
    if is_indicator_saved(country_code, indicator_name, year):
        return None

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO indicators (country_code, country_name, indicator_name, value, year)
        VALUES (?, ?, ?, ?, ?)
    """,
        (country_code, country_name, indicator_name, value, year),
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id


def update_indicator(
    item_id,
    country_code=None,
    country_name=None,
    indicator_name=None,
    value=None,
    year=None,
):
    existing = get_indicator_by_id(item_id)
    if not existing:
        return False

    updated_code = (
        country_code if country_code is not None else existing["country_code"]
    )
    updated_cname = (
        country_name if country_name is not None else existing["country_name"]
    )
    updated_iname = (
        indicator_name
        if indicator_name is not None
        else existing["indicator_name"]
    )
    updated_val = value if value is not None else existing["value"]
    updated_year = year if year is not None else existing["year"]

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE indicators
        SET country_code = ?, country_name = ?, indicator_name = ?, value = ?, year = ?
        WHERE id = ?
    """,
        (
            updated_code,
            updated_cname,
            updated_iname,
            updated_val,
            updated_year,
            item_id,
        ),
    )
    conn.commit()
    conn.close()
    return True


def delete_indicator(item_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM indicators WHERE id = ?", (item_id,))
    conn.commit()
    affected = cursor.rowcount
    conn.close()
    return affected > 0