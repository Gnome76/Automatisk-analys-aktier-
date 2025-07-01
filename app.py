import streamlit as st
import pandas as pd
import yfinance as yf
import time
from datetime import timedelta

st.set_page_config(page_title="Målkurs 2027", layout="wide")
st.title("📊 Målkurs 2027 – Analys med verkligt P/S-snitt")

if "companies" not in st.session_state:
    st.session_state.companies = []

def fetch_data(ticker, g25, g26, g27):
    stock = yf.Ticker(ticker)
    info = stock.info
    name = info.get("longName", ticker)
    currency = info.get("currency", "USD")
    shares = info.get("sharesOutstanding") or 1
    revenue_ttm = info.get("totalRevenue") or 0

    # 🔢 1. Manuell tillväxt
    revenue_2025 = revenue_ttm * (1 + g25 / 100)
    revenue_2026 = revenue_2025 * (1 + g26 / 100)
    revenue_2027 = revenue_2026 * (1 + g27 / 100)

    # 📊 2. Hämta kvartalsvisa omsättningar (senaste 4)
    try:
        financials = stock.quarterly_financials.T
        revenues = financials["Total Revenue"].dropna().head(4)
    except:
        revenues = pd.Series([revenue_ttm / 4] * 4)

    # 💵 3. Hämta kurs vid kvartalsdatum
    ps_values = []
    for date, revenue in revenues.items():
        try:
            start = date - timedelta(days=3)
            end = date + timedelta(days=3)
            hist = stock.history(start=start, end=end)
            price = hist["Close"].mean()
            market_cap = price * shares
            ps = market_cap / revenue if revenue > 0 else None
            if ps:
                ps_values.append(ps)
        except:
            pass
        time.sleep(0.3)

    # 📈 4. Snitt av 4 senaste P/S
    ps_avg = sum(ps_values) / len(ps_values) if ps_values else 5

    # 🎯 5. Målkurs
    target_price = (revenue_2027 / shares) * ps_avg

    # 💰 6. Aktuell kurs
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

# ➕ Sidopanel
with st.sidebar:
    st.header("Lägg till bolag")
    ticker = st.text_input("Ticker (ex: NVDA)").upper()
    g25 = st.number_input("Förväntad tillväxt 2025 (%)", min_value=0.0, max_value=500.0, value=30.0)
    g26 = st.number_input("Förväntad tillväxt 2026 (%)", min_value=0.0, max_value=500.0, value=30.0)
    g27 = st.number_input("Förväntad tillväxt 2027 (%)", min_value=0.0, max_value=500.0, value=30.0)

    if st.button("Analysera"):
        if ticker:
            try:
                data = fetch_data(ticker, g25, g26, g27)
                st.session_state.companies.append(data)
                st.success(f"{data['name']} tillagd.")
            except Exception as e:
                st.error(f"Kunde inte hämta data: {e}")
        else:
            st.warning("Ange en giltig ticker.")

# 📈 Resultattabell
if st.session_state.companies:
    df = pd.DataFrame(st.session_state.companies)
    df["undervaluation"] = df["undervaluation"].map(lambda x: f"{x:.1f} %" if x is not None else "-")
    df["target_price"] = df["target_price"].map(lambda x: f"{x:.2f}" if x is not None else "-")
    df["current_price"] = df["current_price"].map(lambda x: f"{x:.2f}" if x is not None else "-")

    st.subheader("🔍 Analysresultat")
    st.dataframe(df[[
        "ticker", "name", "currency", "revenue_ttm", "growth_2025", "growth_2026", "growth_2027",
        "revenue_2027", "ps_avg", "target_price", "current_price", "undervaluation"
    ]], use_container_width=True)
else:
    st.info("Inga analyserade bolag ännu.")
