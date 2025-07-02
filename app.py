import streamlit as st
import yfinance as yf
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import json

# Google Sheets-autentisering via secrets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials_dict = st.secrets["GOOGLE_CREDENTIALS"]
credentials = Credentials.from_service_account_info(credentials_dict, scopes=scope)
gc = gspread.authorize(credentials)

# ID till ditt Google Sheet
SHEET_ID = "1-IGWQacBAGo2nIDhTrCWZ9c3tJgm_oY0vRsWIzjG5Yo"

# Öppna kalkylarket och första bladet
sh = gc.open_by_key(SHEET_ID)
worksheet = sh.sheet1

# Ladda in data från Google Sheet till dataframe
data = worksheet.get_all_records()
df = pd.DataFrame(data)

st.title("📊 Automatisk aktieanalys")

# Inmatning för nytt bolag
st.header("Lägg till nytt bolag")
ticker = st.text_input("Ticker (t.ex. AAPL)")

growth_2027 = st.number_input("Förväntad tillväxt 2027 (%)", step=1.0)

if st.button("Analysera bolag"):
    if ticker:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            # Hämta nuvarande data
            current_price = info.get("currentPrice")
            shares_outstanding = info.get("sharesOutstanding")
            currency = info.get("currency", "USD")

            # Hämta TTM-omsättning
            quarterly_revenue = stock.quarterly_financials.loc["Total Revenue"]
            ttm_revenue = quarterly_revenue[:4].sum()

            # Hämta P/S för senaste 4 kvartal (baserat på TTM)
            history = stock.history(period="1y", interval="3mo")
            ps_values = []
            for i in range(len(history)):
                try:
                    price = history['Close'][i]
                    ps = (price * shares_outstanding) / ttm_revenue
                    ps_values.append(ps)
                except:
                    continue

            average_ps = sum(ps_values) / len(ps_values) if ps_values else 0

            # Tillväxtberäkningar
            revenue_2027 = ttm_revenue * ((1 + growth_2027 / 100) ** 3)
            potential_price_2027 = (revenue_2027 / shares_outstanding) * average_ps

            # Lägg till i dataframe och spara i Google Sheet
            new_row = {
                "Ticker": ticker,
                "Valuta": currency,
                "Nuvarande kurs": current_price,
                "Omsättning TTM": ttm_revenue,
                "Antal aktier": shares_outstanding,
                "P/S TTM-snitt": round(average_ps, 2),
                "Tillväxt 2027 (%)": growth_2027,
                "Potentiell kurs 2027": round(potential_price_2027, 2)
            }

            worksheet.append_row(list(new_row.values()))
            st.success(f"{ticker} tillagd med målkurs {round(potential_price_2027, 2)} {currency}")
        except Exception as e:
            st.error(f"Något gick fel: {e}")
    else:
        st.warning("Ange en giltig ticker!")

# Visa existerande data
st.header("📈 Analyserade bolag")
st.dataframe(df)
