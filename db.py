import mysql.connector
import streamlit as st


@st.cache_resource
def get_connection():
    """
    Returns a cached MySQL connection.
    Credentials come from .streamlit/secrets.toml (never hardcode passwords in code
    that you might push to GitHub).
    """
    return mysql.connector.connect(
        host=st.secrets["mysql"]["host"],
        user=st.secrets["mysql"]["user"],
        password=st.secrets["mysql"]["password"],
        database=st.secrets["mysql"]["database"],
        autocommit=False,
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
