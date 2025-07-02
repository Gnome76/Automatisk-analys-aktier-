import streamlit as st
import pandas as pd
import yfinance as yf
import gspread
import json
from google.oauth2.service_account import Credentials
import datetime

st.set_page_config(page_title="Automatisk Aktieanalys", layout="wide")

# 📌 Autentisering
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

credentials_dict = st.secrets["GOOGLE_CREDENTIALS"]
credentials = Credentials.from_service_account_info(credentials_dict, scopes=scope)
gc = gspread.authorize(credentials)

# 🔑 Google Sheets-ID och kalkylblad
SHEET_ID = "1-IGWQacBAGo2nIDhTrCWZ9c3tJgm_oY0vRsWIzjG5Yo"
SHEET_NAME = "Data"

try:
    sh = gc.open_by_key(SHEET_ID)
    worksheet = sh.worksheet(SHEET_NAME)
    df = pd.DataFrame(worksheet.get_all_records())
except Exception as e:
    st.error(f"Kunde inte läsa Google Sheet: {e}")
    df = pd.DataFrame()

st.title("📈 Automatisk analys av aktier (med målkurs 2027)")

with st.form("ticker_form"):
    ticker = st.text_input("Ange ticker (t.ex. AAPL, MSFT, NVDA):").upper()
    tillväxt_2027 = st.number_input("Förväntad tillväxt 2027 (%)", value=15.0)
    submitted = st.form_submit_button("Analysera")

if submitted and ticker:
    try:
        stock = yf.Ticker(ticker)

        info = stock.info
        currency = info.get("currency", "USD")
        shares_outstanding = info.get("sharesOutstanding")
        market_cap = info.get("marketCap")

        if shares_outstanding is None or market_cap is None:
            st.error("Kunde inte hämta aktiedata.")
        else:
            revenue_ttm = info.get("totalRevenue", None)
            if revenue_ttm is None:
                st.error("Kunde inte hämta TTM-omsättning.")
            else:
                ps_now = market_cap / revenue_ttm

                # Hämta kvartalsvis omsättning
                try:
                    q_income = stock.quarterly_financials.loc["Total Revenue"]
                    q_income = q_income.sort_index(ascending=False)
                    q_income_values = q_income.values

                    if len(q_income_values) >= 4:
                        ps_ttm_values = []
                        for i in range(4):
                            if i + 4 <= len(q_income_values):
                                rolling_revenue = sum(q_income_values[i:i+4])
                                price = stock.history(period="1d")["Close"][-1]
                                ps = (price * shares_outstanding) / rolling_revenue
                                ps_ttm_values.append(ps)

                        ps_avg = sum(ps_ttm_values) / len(ps_ttm_values)
                    else:
                        ps_avg = ps_now  # fallback
                except Exception as e:
                    ps_avg = ps_now

                # Hämta prognoser för 2025–2026 från 'earnings_trend'
                try:
                    growth_2025 = info.get("earningsGrowth", 0.1)  # fallback 10%
                    growth_2026 = growth_2025  # approximera samma tillväxt
                except:
                    growth_2025 = growth_2026 = 0.1

                # Tillväxtfaktorer
                faktor_2025 = 1 + growth_2025
                faktor_2026 = 1 + growth_2026
                faktor_2027 = 1 + (tillväxt_2027 / 100)

                revenue_2027 = revenue_ttm * faktor_2025 * faktor_2026 * faktor_2027
                potential_price_2027 = (revenue_2027 / shares_outstanding) * ps_avg

                st.subheader(f"💰 Potentiell målkurs för {ticker} år 2027:")
                st.metric(label="Målkurs", value=f"{potential_price_2027:,.2f} {currency}")

                # Spara till Google Sheet
                new_row = {
                    "Ticker": ticker,
                    "Datum": datetime.date.today().isoformat(),
                    "Nuvarande kurs": round(stock.history(period="1d")["Close"][-1], 2),
                    "Valuta": currency,
                    "Omsättning TTM": int(revenue_ttm),
                    "Tillväxt 2025 (%)": round(growth_2025 * 100, 1),
                    "Tillväxt 2026 (%)": round(growth_2026 * 100, 1),
                    "Tillväxt 2027 (%)": tillväxt_2027,
                    "Målkurs 2027": round(potential_price_2027, 2),
                }

                if df.empty:
                    df = pd.DataFrame([new_row])
                else:
                    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

                worksheet.clear()
                worksheet.update([df.columns.values.tolist()] + df.values.tolist())
                st.success("✅ Analysen har sparats!")
    except Exception as e:
        st.error(f"Något gick fel under analysen: {e}")

# Visa sparade analyser
if not df.empty:
    st.subheader("📊 Sparade analyser")
    st.dataframe(df.sort_values(by="Målkurs 2027", ascending=False), use_container_width=True)
