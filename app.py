import streamlit as st
import yfinance as yf
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import os

# Tillfällig felsökning – visar filer i /mnt/data/
st.write("Filer i /mnt/data/:", os.listdir("/mnt/data/"))

# Autentisering för Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = Credentials.from_service_account_file(
    "/mnt/data/credentials.json",
    scopes=scope
)
gc = gspread.authorize(credentials)

# Google Sheet ID
SHEET_ID = "1-IGWQacBAGo2nIDhTrCWZ9c3tJgm_oY0vRsWIzjG5Yo"
SHEET_NAME = "Ark1"

# Hämta eller skapa Google Sheet
try:
    sh = gc.open_by_key(SHEET_ID)
    worksheet = sh.worksheet(SHEET_NAME)
    data = worksheet.get_all_records()
    df = pd.DataFrame(data)
except Exception as e:
    st.error(f"Kunde inte läsa Google Sheet: {e}")
    df = pd.DataFrame(columns=[
        "Ticker", "Namn", "Valuta", "TTM Omsättning", "Börsvärde",
        "Antal aktier", "Genomsnitt P/S", "Nuvarande kurs",
        "Tillväxt 2025 (%)", "Tillväxt 2026 (%)", "Tillväxt 2027 (%)",
        "Omsättning 2027", "Målkurs 2027", "Undervärdering (%)"
    ])

# Ny analys
st.header("Lägg till bolag för analys")
ticker = st.text_input("Ticker (t.ex. AAPL)")
growth_2027 = st.number_input("Förväntad tillväxt 2027 (%)", value=10.0)

if st.button("Analysera bolag"):
    if not ticker:
        st.warning("Fyll i en ticker")
    else:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            hist = stock.history(period="1y", interval="3mo")

            # Validera historik
            if hist.empty or len(hist) < 4:
                raise ValueError("Otillräcklig kvartalsdata")

            # Rullande TTM-omsättning för varje kvartal
            quarterly = stock.quarterly_financials.T
            quarterly_rev = quarterly["Total Revenue"]
            quarterly_rev = quarterly_rev.sort_index(ascending=False)
            rolling_revenue = quarterly_rev.rolling(4).sum().dropna()

            # P/S per kvartal = Börsvärde / TTM Revenue
            market_cap = info.get("marketCap")
            ps_values = market_cap / rolling_revenue
            avg_ps = ps_values.mean()

            currency = info.get("currency", "USD")
            name = info.get("shortName", "")
            shares = info.get("sharesOutstanding", 0)
            current_price = info.get("currentPrice", 0)
            ttm_revenue = quarterly_rev.head(4).sum()

            # Tillväxtprognoser i %
            growth_2025 = info.get("earningsQuarterlyGrowth", 0.10) * 100
            growth_2026 = info.get("revenueGrowth", 0.10) * 100

            # Omvandla tillväxt till decimal
            g25 = growth_2025 / 100
            g26 = growth_2026 / 100
            g27 = growth_2027 / 100

            oms_2027 = ttm_revenue * (1 + g25) * (1 + g26) * (1 + g27)
            target_price = (oms_2027 / shares) * avg_ps
            undervaluation = ((target_price - current_price) / current_price) * 100

            df = pd.concat([df, pd.DataFrame([{
                "Ticker": ticker,
                "Namn": name,
                "Valuta": currency,
                "TTM Omsättning": ttm_revenue,
                "Börsvärde": market_cap,
                "Antal aktier": shares,
                "Genomsnitt P/S": round(avg_ps, 2),
                "Nuvarande kurs": current_price,
                "Tillväxt 2025 (%)": round(growth_2025, 1),
                "Tillväxt 2026 (%)": round(growth_2026, 1),
                "Tillväxt 2027 (%)": round(growth_2027, 1),
                "Omsättning 2027": round(oms_2027, 2),
                "Målkurs 2027": round(target_price, 2),
                "Undervärdering (%)": round(undervaluation, 1)
            }])], ignore_index=True)

            # Spara till Google Sheet
            try:
                worksheet.clear()
                worksheet.update([df.columns.values.tolist()] + df.values.tolist())
            except Exception as e:
                st.error(f"Kunde inte spara till Google Sheet: {e}")

        except Exception as e:
            st.error(f"Kunde inte hämta data: {e}")

# Sortering
if not df.empty:
    df = df.sort_values(by="Undervärdering (%)", ascending=False)
    st.header("Analysresultat")

    # Bläddring
    if "index" not in st.session_state:
        st.session_state.index = 0

    bolag = df.iloc[st.session_state.index]

    st.subheader(f"{bolag['Namn']} ({bolag['Ticker']})")
    st.write(f"Nuvarande kurs: {bolag['Nuvarande kurs']} {bolag['Valuta']}")
    st.write(f"Målkurs 2027: {bolag['Målkurs 2027']} {bolag['Valuta']}")
    st.write(f"Undervärdering: {bolag['Undervärdering (%)']} %")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ Föregående") and st.session_state.index > 0:
            st.session_state.index -= 1
    with col2:
        if st.button("Nästa ➡️") and st.session_state.index < len(df) - 1:
            st.session_state.index += 1
