import sqlite3
import pandas as pd
import os

# 🟩 Se till att mappen finns
os.makedirs("/mnt/data", exist_ok=True)

# ✅ Korrekt databasväg
DB_PATH = "/mnt/data/database.db"

def init_db():
    try:
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
    except Exception as e:
        raise RuntimeError(f"Kunde inte initiera databasen: {e}")

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
