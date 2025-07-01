import streamlit as st
import pandas as pd
from database import init_db, save_company, load_companies, delete_company
from finance import fetch_data
import yfinance as yf

init_db()
st.set_page_config(page_title="Målkurs 2027", layout="wide")
st.title("📊 Målkurs 2027 – Aktieanalys")

with st.sidebar:
    st.header("➕ Lägg till bolag")
    ticker = st.text_input("Ticker-symbol (ex: NVDA, AAPL, TSLA)")
    growth_2027 = st.number_input("Förväntad tillväxt 2027 (%)", min_value=0.0, max_value=500.0, step=1.0)
    if st.button("Lägg till"):
        if ticker:
            try:
                data = fetch_data(ticker, growth_2027)
                save_company(data)
                st.success(f"{data['name']} tillagd!")
            except Exception as e:
                st.error(f"Kunde inte lägga till: {e}")
        else:
            st.warning("Ange en giltig ticker.")

st.markdown("### 🔄 Uppdatera alla bolag")
if st.button("Uppdatera samtliga"):
    df = load_companies()
    for _, row in df.iterrows():
        try:
            data = fetch_data(row["ticker"], row["growth_2027"])
            save_company(data)
        except Exception as e:
            st.warning(f"Kunde inte uppdatera {row['ticker']}: {e}")
    st.success("Alla uppdaterade.")

df = load_companies()
if df.empty:
    st.info("Inga bolag tillagda.")
else:
    st.subheader("📈 Sammanställning")
    prices = {}
    for ticker in df["ticker"]:
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="1d")
            if not hist.empty:
                prices[ticker] = hist["Close"].iloc[-1]
        except:
            continue

    df["current_price"] = df["ticker"].map(prices)
    df["undervaluation_%"] = ((df["target_price_base"] - df["current_price"]) / df["current_price"]) * 100
    df.sort_values(by="undervaluation_%", ascending=False, inplace=True)

    st.dataframe(df[[
        "ticker", "name", "currency", "revenue_ttm", "growth_2025", "growth_2026", "growth_2027",
        "revenue_2027", "ps_avg", "target_price_base", "current_price", "undervaluation_%"
    ]].style.format({
        "revenue_ttm": "{:,.0f}", "revenue_2027": "{:,.0f}",
        "ps_avg": "{:.2f}", "target_price_base": "{:.2f}",
        "current_price": "{:.2f}", "undervaluation_%": "{:.1f} %"
    }), use_container_width=True)

    st.subheader("🗑 Ta bort bolag")
    val = st.selectbox("Välj bolag", df["ticker"])
    if st.button("Ta bort"):
        delete_company(val)
        st.success(f"{val} borttaget.")
