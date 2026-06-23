import pymysql
import pymysql.cursors
import streamlit as st
from decimal import Decimal


@st.cache_resource
def get_connection():
    """
    Returns a cached MySQL connection using PyMySQL.

    Switched from mysql-connector-python because it has an internal bug:
    when a connection attempt fails, the library crashes while trying to
    FORMAT its own error message ("%u format: a real number is required,
    not str"), which hides the actual underlying error completely. PyMySQL
    is a simpler, pure-Python driver that doesn't have this problem and
    gives clean, readable error messages instead.

    Credentials come from .streamlit/secrets.toml locally, or the "Secrets"
    panel on Streamlit Cloud when deployed.
    """
    return pymysql.connect(
        host=st.secrets["mysql"]["host"],
        port=int(st.secrets["mysql"].get("port", 3306)),
        user=st.secrets["mysql"]["user"],
        password=st.secrets["mysql"]["password"],
        database=st.secrets["mysql"]["database"],
        autocommit=False,
        cursorclass=pymysql.cursors.DictCursor,
        ssl={"ssl": True},  # Aiven requires SSL — this enables it
        connect_timeout=10,
    )


def get_live_connection():
    """
    Always returns a WORKING connection. The cached connection from
    get_connection() can go stale if MySQL closes it server-side after a
    timeout (Aiven's free tier also auto-powers-off the database after
    inactivity) — Streamlit's cache doesn't know that happened, so it keeps
    handing out the dead connection.

    This pings the cached connection first; if the ping fails, it clears
    the cache and creates a fresh connection instead of crashing.
    """
    conn = get_connection()
    try:
        conn.ping(reconnect=True)
    except pymysql.Error:
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

    PyMySQL uses %s placeholders same as mysql-connector, so all existing
    queries in queries.py work unchanged.
    """
    conn = get_live_connection()
    with conn.cursor() as cursor:
        cursor.execute(query, params or ())
        rows = cursor.fetchall() if fetch else None

    if rows:
        for row in rows:
            for key, value in row.items():
                if isinstance(value, Decimal):
                    row[key] = float(value)
    return rows


def run_write(query, params=None):
    """Run an INSERT / UPDATE / DELETE and commit."""
    conn = get_live_connection()
    with conn.cursor() as cursor:
        cursor.execute(query, params or ())
        conn.commit()
        last_id = cursor.lastrowid
    return last_id
