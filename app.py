import streamlit as st
import pandas as pd
import yfinance as yf
import time
from datetime import timedelta

st.set_page_config(page_title="Målkurs 2027", layout="wide")
st.title("📊 Målkurs 2027 – Ett bolag i taget")

if "companies" not in st.session_state:
    st.session_state.companies = []

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
        time.sleep(0.3)

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

# ➕ Lägg till bolag
with st.sidebar:
    st.header("Lägg till nytt bolag")
    ticker = st.text_input("Ticker (ex: NVDA)").upper()
    g25 = st.number_input("Tillväxt 2025 (%)", 0.0, 500.0, 30.0)
    g26 = st.number_input("Tillväxt 2026 (%)", 0.0, 500.0, 30.0)
    g27 = st.number_input("Tillväxt 2027 (%)", 0.0, 500.0, 30.0)

    if st.button("Analysera"):
        if ticker:
            try:
                data = fetch_data(ticker, g25, g26, g27)
                st.session_state.companies.append(data)
                st.success(f"{data['name']} tillagd.")
            except Exception as e:
                st.error(f"Kunde inte hämta data: {e}")
        else:
            st.warning("Ange en ticker.")

# 📊 Visa ett bolag i taget
if st.session_state.companies:
    sorted_companies = sorted(
        st.session_state.companies,
        key=lambda x: x["undervaluation"] if x["undervaluation"] is not None else -float("inf"),
        reverse=True
    )

    tickers = [c["ticker"] for c in sorted_companies]
    selected_ticker = st.selectbox("Välj bolag att visa (mest undervärderad först):", tickers)
    company = next((c for c in sorted_companies if c["ticker"] == selected_ticker), None)

    if company:
        st.markdown(f"### {company['ticker']} – {company['name']} ({company['currency']})")

        col1, col2, col3 = st.columns(3)
        with col1:
            g25 = st.number_input("Tillväxt 2025 (%)", value=company["growth_2025"], key="g25")
        with col2:
            g26 = st.number_input("Tillväxt 2026 (%)", value=company["growth_2026"], key="g26")
        with col3:
            g27 = st.number_input("Tillväxt 2027 (%)", value=company["growth_2027"], key="g27")

        col4, col5 = st.columns(2)
        with col4:
            if st.button("🔄 Uppdatera bolaget"):
                try:
                    updated = fetch_data(company["ticker"], g25, g26, g27)
                    index = st.session_state.companies.index(next(c for c in st.session_state.companies if c["ticker"] == company["ticker"]))
                    st.session_state.companies[index] = updated
                    st.success("Bolaget uppdaterat.")
                except Exception as e:
                    st.error(f"Fel vid uppdatering: {e}")
        with col5:
            if st.button("🗑️ Ta bort bolaget"):
                index = st.session_state.companies.index(next(c for c in st.session_state.companies if c["ticker"] == company["ticker"]))
                st.session_state.companies.pop(index)
                st.experimental_rerun()

        st.markdown(f"""
        **Aktuell kurs:** {company['current_price']:.2f} {company['currency']}  
        **Målkurs 2027:** {company['target_price']:.2f} {company['currency']}  
        **Undervärdering:** {company['undervaluation']:.1f}%  
        **P/S TTM-snitt:** {company['ps_avg']:.2f}
        """)
else:
    st.info("Inga bolag tillagda ännu.")
