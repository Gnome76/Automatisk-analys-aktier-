import sqlite3
import pandas as pd

# Korrekt sökväg för Streamlit Cloud (med permanent lagring)
DB_PATH = "/mnt/data/database.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS companies (
            ticker TEXT PRIMARY KEY,
            name TEXT,
            currency TEXT,
            market_cap REAL,
            revenue_ttm REAL,
            shares_outstanding REAL,
            ps_avg REAL,
            revenue_2027 REAL,
            target_price_low REAL,
            target_price_base REAL,
            target_price_high REAL,
            last_updated TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_company(data):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT OR REPLACE INTO companies VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
    """, tuple(data.values()))
    conn.commit()
    conn.close()

def load_companies():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM companies", conn)
    conn.close()
    return df

def delete_company(ticker):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM companies WHERE ticker = ?", (ticker,))
    conn.commit()
    conn.close()
