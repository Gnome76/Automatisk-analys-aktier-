import streamlit as st
import yfinance as yf
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# 🟩 Anslut till Google Sheets
SHEET_ID = "1-IGWQacBAGo2nIDhTrCWZ9c3tJgm_oY0vRsWIzjG5Yo"
gc = gspread.service_account(filename="credentials.json")
sh = gc.open_by_key(SHEET_ID)
worksheet = sh.sheet1

# 🟩 Läs existerande data från arket
@st.cache_data(ttl=60)
def read_data():
    try:
        data = worksheet.get_all_records()
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Kunde inte läsa Google Sheet: {e}")
        return pd.DataFrame()

# 🟩 Spara ny rad till arket
def append_data_to_sheet(row_dict):
    try:
        worksheet.append_row(list(row_dict.values()))
    except Exception as e:
        st.error(f"Kunde inte spara till Google Sheet: {e}")

# 🟩 Räkna ut framtida omsättning och målkurs
def calculate_values(ticker, growth_2025, growth_2026, growth_2027):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        # Valuta
        currency = info.get("currency", "USD")

        # Antal aktier
        shares = info.get("sharesOutstanding")

        # Hämta TTM Revenue
        ttm = stock.financials.loc["Total Revenue"].iloc[:4].sum()
        if pd.isna(ttm) or ttm == 0:
            raise ValueError("Kunde inte hämta TTM-omsättning.")

        # Hämta aktuell pris
        current_price = info.get("currentPrice", None)

        # Beräkna framtida omsättning
        oms_2025 = ttm * (1 + growth_2025 / 100)
        oms_2026 = oms_2025 * (1 + growth_2026 / 100)
        oms_2027 = oms_2026 * (1 + growth_2027 / 100)

        # Hämta senaste kvartalens revenue för TTM P/S
        quarterly = stock.quarterly_financials.loc["Total Revenue"]
        ttm_quarters = quarterly.iloc[:4].sum()
        ps_ratio = (current_price * shares) / ttm_quarters if shares and ttm_quarters else None

        # Målkurs
        target_price_2027 = (oms_2027 / shares) * ps_ratio if ps_ratio and shares else None

        # Undervärdering
        undervaluation = ((target_price_2027 - current_price) / current_price * 100) if target_price_2027 and current_price else None

        return {
            "Ticker": ticker,
            "Currency": currency,
            "Current Price": round(current_price, 2) if current_price else "N/A",
            "PS Ratio TTM": round(ps_ratio, 2) if ps_ratio else "N/A",
            "Target Price 2027": round(target_price_2027, 2) if target_price_2027 else "N/A",
            "Undervaluation %": round(undervaluation, 1) if undervaluation else "N/A",
            "Growth 2025 %": growth_2025,
            "Growth 2026 %": growth_2026,
            "Growth 2027 %": growth_2027,
        }

    except Exception as e:
        st.error(f"Kunde inte hämta data: {e}")
        return None

# 🟩 Streamlit-gränssnitt
st.title("📈 Automatiserad Aktieanalys (Google Sheets)")

with st.form("add_form"):
    st.subheader("Lägg till bolag")
    ticker = st.text_input("Ticker (t.ex. AAPL, MSFT)").upper()
    growth_2025 = st.number_input("Förväntad tillväxt 2025 (%)", value=10.0)
    growth_2026 = st.number_input("Förväntad tillväxt 2026 (%)", value=10.0)
    growth_2027 = st.number_input("Förväntad tillväxt 2027 (%)", value=10.0)
    submitted = st.form_submit_button("Analysera och spara")

    if submitted and ticker:
        result = calculate_values(ticker, growth_2025, growth_2026, growth_2027)
        if result:
            append_data_to_sheet(result)
            st.success(f"{ticker} sparades!")

# 🟩 Visa sparad data
df = read_data()
if not df.empty:
    st.subheader("📊 Analysresultat")
    df_sorted = df.sort_values("Undervaluation %", ascending=False)
    st.dataframe(df_sorted, use_container_width=True)
else:
    st.info("Inga bolag har analyserats ännu.")
