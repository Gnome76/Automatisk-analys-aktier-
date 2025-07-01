import sqlite3
import os
import pandas as pd

# Se till att mappen finns
DB_PATH = "/mnt/data/database.db"
os.makedirs("/mnt/data", exist_ok=True)

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS companies (
            ticker TEXT PRIMARY KEY,
            name TEXT,
            currency TEXT,
            revenue_ttm REAL,
            growth_2025 REAL,
            growth_2026 REAL,
            growth_2027 REAL,
            revenue_2027 REAL,
            ps_avg REAL,
            target_price_base REAL
        )
    """)
    conn.commit()
    conn.close()

def save_company(data):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT OR REPLACE INTO companies VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data["ticker"], data["name"], data["currency"], data["revenue_ttm"],
        data["growth_2025"], data["growth_2026"], data["growth_2027"],
        data["revenue_2027"], data["ps_avg"], data["target_price_base"]
    ))
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
