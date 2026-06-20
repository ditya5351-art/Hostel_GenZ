import mysql.connector
import streamlit as st


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
        port=st.secrets["mysql"].get("port", 3306),
        user=st.secrets["mysql"]["user"],
        password=st.secrets["mysql"]["password"],
        database=st.secrets["mysql"]["database"],
        autocommit=False,
        use_pure=True,
        ssl_disabled=False,
    )


def run_query(query, params=None, fetch=True):
    """Run a SELECT and return rows as list of dicts."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(query, params or ())
    rows = cursor.fetchall() if fetch else None
    cursor.close()
    return rows


def run_write(query, params=None):
    """Run an INSERT / UPDATE / DELETE and commit."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query, params or ())
    conn.commit()
    last_id = cursor.lastrowid
    cursor.close()
    return last_id
