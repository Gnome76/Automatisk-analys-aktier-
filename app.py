import streamlit as st
import pandas as pd
import yfinance as yf

st.set_page_config(page_title="Målkurs 2027", layout="wide")
st.title("📊 Målkurs 2027 – Direktanalys utan databas")

if "companies" not in st.session_state:
    st.session_state.companies = []

def fetch_data(ticker, growth_2027):
    stock = yf.Ticker(ticker)
    info = stock.info
    name = info.get("longName", ticker)
    currency = info.get("currency", "USD")
    shares = info.get("sharesOutstanding", 1)
    revenue_ttm = info.get("totalRevenue", 0)

    # Analyst-estimat från Yahoo Finance
    growth_2025 = None
    growth_2026 = None

    try:
        analysis = stock.analysis
        if "Revenue Estimate" in analysis.index:
            if "2025" in analysis.columns:
                rev_2025 = analysis.loc["Revenue Estimate", "2025"]
                growth_2025 = ((rev_2025 - revenue_ttm) / revenue_ttm) * 100
            if "2026" in analysis.columns:
                rev_2026 = analysis.loc["Revenue Estimate", "2026"]
                growth_2026 = ((rev_2026 - rev_2025) / rev_2025) * 100 if rev_2025 else None
    except:
        pass

    # Fallback om inget finns
    growth_2025 = growth_2025 or 20.0
    growth_2026 = growth_2026 or 20.0

    # Beräkna framtida omsättning
    revenue_2025 = revenue_ttm * (1 + growth_2025 / 100)
    revenue_2026 = revenue_2025 * (1 + growth_2026 / 100)
    revenue_2027 = revenue_2026 * (1 + growth_2027 / 100)

    ps_avg = info.get("trailingPegRatio", 5)
    target_price = (revenue_2027 / shares) * ps_avg

    # Försök hämta aktuell kurs
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
        "growth_2025": growth_2025,
        "growth_2026": growth_2026,
        "growth_2027": growth_2027,
        "revenue_2027": revenue_2027,
        "ps_avg": ps_avg,
        "target_price": target_price,
        "current_price": current_price,
        "undervaluation": undervaluation
    }

with st.sidebar:
    st.header("➕ Lägg till bolag")
    ticker = st.text_input("Ticker (ex: NVDA)")
    growth_2027 = st.number_input("Förväntad tillväxt 2027 (%)", min_value=0.0, max_value=500.0, value=30.0)
    if st.button("Analysera"):
        if ticker:
            try:
                data = fetch_data(ticker, growth_2027)
                st.session_state.companies.append(data)
                st.success(f"{data['name']} tillagd.")
            except Exception as e:
                st.error(f"Kunde inte hämta data: {e}")
        else:
            st.warning("Ange en giltig ticker.")

if st.session_state.companies:
    df = pd.DataFrame(st.session_state.companies)
    df["undervaluation"] = df["undervaluation"].map(lambda x: f"{x:.1f} %" if x else "-")
    df["target_price"] = df["target_price"].map(lambda x: f"{x:.2f}")
    df["current_price"] = df["current_price"].map(lambda x: f"{x:.2f}" if x else "-")
    st.subheader("📈 Analysresultat")
    st.dataframe(df[[
        "ticker", "name", "currency", "revenue_ttm", "growth_2025", "growth_2026", "growth_2027",
        "revenue_2027", "ps_avg", "target_price", "current_price", "undervaluation"
    ]], use_container_width=True)
else:
    st.info("Inga analyserade bolag ännu.")
