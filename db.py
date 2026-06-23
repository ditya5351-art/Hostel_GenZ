import mysql.connector
import streamlit as st
from decimal import Decimal


@st.cache_resource
def get_connection():
    """
    Returns a cached MySQL connection.
    Credentials come from .streamlit/secrets.toml locally, or the "Secrets"
    panel on Streamlit Cloud when deployed (never hardcode passwords in code
    that you might push to GitHub).

    `port` is optional in secrets — defaults to 3306 (MySQL's standard port).
    Aiven and some other managed-MySQL providers use a custom port instead
    of 3306, so make sure to set it in secrets if your provider gave you one.

    `use_pure=True` forces the pure-Python implementation of the connector
    instead of its C extension. The C extension has caused low-level crashes
    ("malloc_consolidate(): invalid chunk size") on some Streamlit Cloud
    container environments — pure Python avoids that at a small performance
    cost that's irrelevant for an app this size.
    """
    return mysql.connector.connect(
        host=st.secrets["mysql"]["host"],
        port=st.secrets["mysql"].get(port, 3306),
        user=st.secrets["mysql"]["user"],
        password=st.secrets["mysql"]["password"],
        database=st.secrets["mysql"]["database"],
        autocommit=False,
        use_pure=True,
        ssl_disabled=False,
    )


def get_live_connection():
    """
    Always returns a WORKING connection. The cached connection from
    get_connection() can go stale if MySQL closes it server-side after a
    timeout (Aiven's free tier also auto-powers-off the database after
    inactivity) — Streamlit's cache doesn't know that happened, so it keeps
    handing out the dead connection, causing "MySQL Connection not available".

    This pings the cached connection first; if the ping fails, it clears
    the cache and creates a fresh connection instead of crashing.
    """
    conn = get_connection()
    try:
        conn.ping(reconnect=True, attempts=3, delay=1)
    except mysql.connector.Error:
        get_connection.clear()  # drop the dead cached connection
        conn = get_connection()  # cache_resource will create a brand new one
    return conn


def run_query(query, params=None, fetch=True):
    """
    Run a SELECT and return rows as list of dicts.

    MySQL returns DECIMAL columns (rent, amounts, etc.) as Python Decimal
    objects. Decimal mixed with None has been known to crash pandas/pyarrow's
    native conversion code (the "double free or corruption" crash seen when
    st.dataframe() tries to render such rows) on some platform/version
    combinations — converting to plain float here sidesteps that entirely
    and is precise enough for a rent/deposit amount.
    """
    conn = get_live_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(query, params or ())
    rows = cursor.fetchall() if fetch else None
    cursor.close()

    if rows:
        for row in rows:
            for key, value in row.items():
                if isinstance(value, Decimal):
                    row[key] = float(value)
    return rows


def run_write(query, params=None):
    """Run an INSERT / UPDATE / DELETE and commit."""
    conn = get_live_connection()
    cursor = conn.cursor()
    cursor.execute(query, params or ())
    conn.commit()
    last_id = cursor.lastrowid
    cursor.close()
    return last_id
