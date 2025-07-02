import os
st.write("Filer i /mnt/data/:", os.listdir("/mnt/data/"))
import streamlit as st
import pandas as pd
import yfinance as yf
import gspread
from google.oauth2.service_account import Credentials

# ===== Google Sheet-konfiguration =====
SHEET_ID = "1-IGWQacBAGo2nIDhTrCWZ9c3tJgm_oY0vRsWIzjG5Yo"
SHEET_NAME = "Data"  # Valfritt namn – byt till ditt kalkylbladsfliknamn om det är annat

scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

credentials = Credentials.from_service_account_file(
    "/mnt/data/credentials.json",
    scopes=scope
)

gc = gspread.authorize(credentials)
sh = gc.open_by_key(SHEET_ID)
worksheet = sh.worksheet(SHEET_NAME)

# ===== Funktioner =====

def read_data():
    try:
        data = worksheet.get_all_records()
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Kunde inte läsa Google Sheet: {e}")
        return pd.DataFrame()

def save_data(df):
    try:
        worksheet.clear()
        worksheet.update([df.columns.values.tolist()] + df.values.tolist())
    except Exception as e:
        st.error(f"Kunde inte spara till Google Sheet: {e}")

def calculate_ps_ttm(ticker):
    try:
        ticker_data = yf.Ticker(ticker)
        info = ticker_data.info
        shares_out = info.get("sharesOutstanding")
        market_cap = info.get("marketCap")
        quarterly_rev = ticker_data.quarterly_financials.loc["Total Revenue"]
        rev_ttm = quarterly_rev.iloc[:4].sum()
        ps_ttm = market_cap / rev_ttm if rev_ttm and shares_out else None
        return ps_ttm, rev_ttm, market_cap, shares_out
    except:
        return None, None, None, None

def calculate_target_price(rev_2027, shares, avg_ps):
    try:
        return (rev_2027 / shares) * avg_ps
    except:
        return None

# ===== Gränssnitt =====

st.title("📈 Automatisk Aktievärdering – 2027 P/S-analys")

df = read_data()

# === Formulär för nytt bolag ===
with st.expander("➕ Lägg till nytt bolag"):
    with st.form("add_company"):
        ticker = st.text_input("Ticker (t.ex. AAPL)")
        growth_2025 = st.number_input("Förväntad tillväxt 2025 (%)", value=10.0)
        growth_2026 = st.number_input("Förväntad tillväxt 2026 (%)", value=10.0)
        growth_2027 = st.number_input("Förväntad tillväxt 2027 (%)", value=10.0)
        submit = st.form_submit_button("Lägg till")

    if submit and ticker:
        avg_ps, rev_ttm, market_cap, shares_out = calculate_ps_ttm(ticker)
        if not all([avg_ps, rev_ttm, market_cap, shares_out]):
            st.warning("Kunde inte hämta data från Yahoo Finance.")
        else:
            rev_2025 = rev_ttm * (1 + growth_2025 / 100)
            rev_2026 = rev_2025 * (1 + growth_2026 / 100)
            rev_2027 = rev_2026 * (1 + growth_2027 / 100)
            target_price = calculate_target_price(rev_2027, shares_out, avg_ps)

            new_row = {
                "Ticker": ticker,
                "Tillväxt 2025 (%)": growth_2025,
                "Tillväxt 2026 (%)": growth_2026,
                "Tillväxt 2027 (%)": growth_2027,
                "Omsättning TTM": rev_ttm,
                "Antal aktier": shares_out,
                "P/S TTM": round(avg_ps, 2),
                "Målkurs 2027": round(target_price, 2)
            }

            df = df.append(new_row, ignore_index=True)
            save_data(df)
            st.success("Bolag tillagt!")

# === Visa ett bolag i taget ===
if not df.empty:
    df["Undervärdering (%)"] = df["Målkurs 2027"] / yf.download(df["Ticker"].tolist(), period="1d")["Adj Close"].iloc[-1].values * 100 - 100
    df = df.sort_values(by="Undervärdering (%)", ascending=False).reset_index(drop=True)

    if "index" not in st.session_state:
        st.session_state.index = 0

    i = st.session_state.index
    bolag = df.iloc[i]

    st.markdown(f"### {bolag['Ticker']}")
    st.metric("Målkurs 2027", f"{bolag['Målkurs 2027']:.2f}")
    st.metric("P/S TTM", f"{bolag['P/S TTM']:.2f}")
    st.metric("Tillväxt 2025–2027 (%)", f"{bolag['Tillväxt 2025 (%)']} / {bolag['Tillväxt 2026 (%)']} / {bolag['Tillväxt 2027 (%)']}")
    st.metric("Undervärdering (%)", f"{bolag['Undervärdering (%)']:.1f} %")

    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("⬅️ Föregående") and i > 0:
            st.session_state.index -= 1
    with col2:
        if st.button("➡️ Nästa") and i < len(df) - 1:
            st.session_state.index += 1

else:
    st.info("Inga bolag tillagda ännu.")
