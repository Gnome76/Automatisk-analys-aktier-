import streamlit as st
import pandas as pd
from database import init_db, save_company, load_companies, delete_company
from finance import fetch_data
import yfinance as yf

# Initiera databasen
init_db()

st.set_page_config(page_title="Målkurs 2027 – Aktieanalys", layout="wide")
st.title("📊 Målkurs 2027 – Aktieanalys per ticker")

# ➕ Lägg till bolag
with st.sidebar:
    st.header("➕ Lägg till bolag")
    ticker_input = st.text_input("Ange ticker-symbol (t.ex. AAPL, SOUN, EMBRAC.ST)")
    if st.button("Lägg till"):
        if ticker_input:
            try:
                data = fetch_data(ticker_input)
                save_company(data)
                st.success(f"{data['name']} ({data['ticker']}) tillagd! Ladda om sidan.")
            except Exception as e:
                st.error(f"Kunde inte hämta data: {e}")
        else:
            st.warning("Ange en giltig ticker-symbol.")

# 🔄 Uppdatera alla bolag
st.markdown("### 🔄 Uppdatera samtliga bolag")
if st.button("Uppdatera alla"):
    companies = load_companies()
    for _, row in companies.iterrows():
        try:
            updated = fetch_data(row["ticker"])
            save_company(updated)
        except Exception as e:
            st.warning(f"Kunde inte uppdatera {row['ticker']}: {e}")
    st.success("Alla bolag uppdaterade! Ladda om sidan.")

# 📈 Visa alla bolag
df = load_companies()

if df.empty:
    st.info("Inga bolag tillagda ännu.")
else:
    st.subheader("📈 Sammanställning")

    tickers = list(df["ticker"])
    prices = {}

    try:
        if len(tickers) == 1:
            raw = yf.download(tickers=tickers[0], period="1d", progress=False)
            if "Adj Close" in raw.columns:
                prices[tickers[0]] = raw["Adj Close"].iloc[-1]
        else:
            raw = yf.download(tickers=tickers, period="1d", group_by="ticker", progress=False)
            for ticker in tickers:
                try:
                    prices[ticker] = raw[ticker]["Adj Close"].iloc[-1]
                except:
                    continue
    except Exception as e:
        st.error(f"Fel vid prisinhämtning: {e}")

    df["current_price"] = df["ticker"].map(prices)

    if df["current_price"].isna().any():
        st.warning("⚠️ Vissa priser kunde inte hämtas. Kontrollera ticker-symbolerna.")

    df["undervaluation_%"] = ((df["target_price_base"] - df["current_price"]) / df["current_price"]) * 100
    df.sort_values(by="undervaluation_%", ascending=False, inplace=True)

    def color_row(row):
        if row["undervaluation_%"] > 30:
            return ["background-color: lightgreen"] * len(row)
        elif row["undervaluation_%"] < 0:
            return ["background-color: salmon"] * len(row)
        else:
            return [""] * len(row)

    styled_df = df[[
        "ticker", "name", "currency", "revenue_ttm", "ps_avg", "revenue_2027",
        "target_price_low", "target_price_base", "target_price_high",
        "current_price", "undervaluation_%"
    ]].style.format({
        "revenue_ttm": "{:,.0f}",
        "revenue_2027": "{:,.0f}",
        "ps_avg": "{:.2f}",
        "target_price_low": "{:.2f}",
        "target_price_base": "{:.2f}",
        "target_price_high": "{:.2f}",
        "current_price": "{:.2f}",
        "undervaluation_%": "{:.1f} %"
    }).apply(color_row, axis=1)

    st.dataframe(styled_df, use_container_width=True)

    # 🗑 Ta bort bolag
    st.subheader("🗑 Ta bort bolag")
    selected = st.selectbox("Välj ticker att ta bort", df["ticker"])
    if st.button("Ta bort"):
        delete_company(selected)
        st.success(f"{selected} borttagen. Ladda om sidan.")
