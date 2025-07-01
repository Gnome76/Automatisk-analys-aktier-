import streamlit as st
import pandas as pd
import yfinance as yf
import gspread
from gspread_dataframe import set_with_dataframe, get_as_dataframe
import time
from datetime import timedelta

# Google Sheet URL och öppna arket
SHEET_URL = "https://docs.google.com/spreadsheets/d/1-IGWQacBAGo2nIDhTrCWZ9c3tJgm_oY0vRsWIzjG5Yo/edit"
SHEET_NAME = "Ark1"  # eller det blad du har

gc = gspread.service_account(filename="credentials.json")  # kräver att vi kör lokalt med nyckel – tas bort i cloud
sh = gc.open_by_url(SHEET_URL)
worksheet = sh.worksheet(SHEET_NAME)

def load_sheet_data():
    try:
        df = get_as_dataframe(worksheet).dropna(subset=["ticker"])
        return df
    except:
        return pd.DataFrame(columns=["ticker", "growth_2025", "growth_2026", "growth_2027"])

def save_sheet_data(df):
    worksheet.clear()
    set_with_dataframe(worksheet, df)

def fetch_data(ticker, g25, g26, g27):
    stock = yf.Ticker(ticker)
    info = stock.info
    name = info.get("longName", ticker)
    currency = info.get("currency", "USD")
    shares = info.get("sharesOutstanding") or 1
    revenue_ttm = info.get("totalRevenue") or 0

    revenue_2025 = revenue_ttm * (1 + g25 / 100)
    revenue_2026 = revenue_2025 * (1 + g26 / 100)
    revenue_2027 = revenue_2026 * (1 + g27 / 100)

    try:
        financials = stock.quarterly_financials.T
        revenues = financials["Total Revenue"].dropna().head(8)
    except:
        revenues = pd.Series([revenue_ttm / 4] * 8)

    ps_values = []
    dates = revenues.index
    for i in range(len(revenues) - 3):
        ttm_revenue = revenues.iloc[i:i+4].sum()
        date = dates[i]
        try:
            start = date - timedelta(days=3)
            end = date + timedelta(days=3)
            hist = stock.history(start=start, end=end)
            price = hist["Close"].mean()
            market_cap = price * shares
            ps = market_cap / ttm_revenue if ttm_revenue > 0 else None
            if ps:
                ps_values.append(ps)
        except:
            pass
        time.sleep(0.2)

    ps_avg = sum(ps_values) / len(ps_values) if ps_values else 5
    target_price = (revenue_2027 / shares) * ps_avg

    current_price = None
    try:
        hist = stock.history(period="1d")
        if not hist.empty:
            current_price = hist["Close"].iloc[-1]
    except:
        pass

    undervaluation = None
    if current_price:
        undervaluation = ((target_price - current_price) / current_price) * 100

    return {
        "ticker": ticker,
        "name": name,
        "currency": currency,
        "revenue_ttm": revenue_ttm,
        "growth_2025": g25,
        "growth_2026": g26,
        "growth_2027": g27,
        "revenue_2027": revenue_2027,
        "ps_avg": ps_avg,
        "target_price": target_price,
        "current_price": current_price,
        "undervaluation": undervaluation
    }

# ------------------------ APP UI ------------------------

st.title("📊 Aktieanalys med Google Sheets")

df = load_sheet_data()

# Lägg till nytt bolag
with st.sidebar:
    st.header("Lägg till bolag")
    ticker = st.text_input("Ticker").upper()
    g25 = st.number_input("Tillväxt 2025 (%)", 0.0, 500.0, 30.0)
    g26 = st.number_input("Tillväxt 2026 (%)", 0.0, 500.0, 30.0)
    g27 = st.number_input("Tillväxt 2027 (%)", 0.0, 500.0, 30.0)
    if st.button("Lägg till"):
        df = df.append({"ticker": ticker, "growth_2025": g25, "growth_2026": g26, "growth_2027": g27}, ignore_index=True)
        save_sheet_data(df)
        st.success("Bolag tillagt!")

# Uppdatera data
if st.button("🔄 Uppdatera alla bolag"):
    updated_rows = []
    for _, row in df.iterrows():
        try:
            data = fetch_data(row["ticker"], row["growth_2025"], row["growth_2026"], row["growth_2027"])
            updated_rows.append(data)
        except:
            st.warning(f"Kunde inte hämta data för {row['ticker']}")
    if updated_rows:
        df_updated = pd.DataFrame(updated_rows)
        save_sheet_data(df_updated)
        st.success("Alla bolag uppdaterade.")
        df = df_updated

# Visa resultat sorterat
if not df.empty and "target_price" in df.columns:
    df_sorted = df.sort_values(by="undervaluation", ascending=False)
    st.dataframe(df_sorted.style.background_gradient(subset=["undervaluation"], cmap="RdYlGn"))
else:
    st.info("Inga uppgifter att visa ännu.")
