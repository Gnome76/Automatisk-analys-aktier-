import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import json
import yfinance as yf
import pandas as pd

# Kontroll: visa filer i /mnt/data/
import os
st.write("📁 Innehåll i /mnt/data/:", os.listdir("/mnt/data/"))

# Google Sheets-inställningar
scope = ["https://www.googleapis.com/auth/spreadsheets"]
credentials_dict = json.loads(st.secrets["GOOGLE_CREDENTIALS"])
credentials = Credentials.from_service_account_info(credentials_dict, scopes=scope)
gc = gspread.authorize(credentials)

# Sheet-ID (justera vid behov)
SHEET_ID = "1-IGWQacBAGo2nIDhTrCWZ9c3tJgm_oY0vRsWIzjG5Yo"  # din sheet
sh = gc.open_by_key(SHEET_ID)
worksheet = sh.sheet1

st.title("📊 Automatisk analys av aktier")

# Enkel funktion för att lägga till ett bolag
ticker = st.text_input("Ange en ticker (t.ex. AAPL eller MSFT)")
tillvaxt_2027 = st.number_input("Förväntad tillväxt 2027 (%)", value=10.0)

if st.button("Analysera bolag"):
    if ticker:
        try:
            info = yf.Ticker(ticker).info
            namn = info.get("shortName", "")
            valuta = info.get("currency", "")
            aktier = info.get("sharesOutstanding", 1)
            marketcap = info.get("marketCap", 0)
            oms_ttm = info.get("totalRevenue", 0)
            ps_tal = round(marketcap / oms_ttm, 2) if oms_ttm else 0
            oms_2027 = oms_ttm * ((1 + tillvaxt_2027 / 100) ** 2)
            kurs_2027 = round((oms_2027 / aktier) * ps_tal, 2) if aktier else 0

            # Visa resultat
            st.subheader(namn)
            st.write(f"Valuta: {valuta}")
            st.write(f"P/S-tal: {ps_tal}")
            st.write(f"Beräknad omsättning 2027: {oms_2027:,.0f} {valuta}")
            st.write(f"Beräknad kurs 2027: {kurs_2027} {valuta}")

            # Spara till Google Sheet
            worksheet.append_row([
                ticker, namn, valuta, ps_tal, tillvaxt_2027, round(oms_2027), kurs_2027
            ])
            st.success("✅ Datan har sparats till Google Sheet.")
        except Exception as e:
            st.error(f"Något gick fel: {e}")
    else:
        st.warning("⚠️ Skriv in en ticker först.")

# Visa befintlig data
st.divider()
st.subheader("📋 Tidigare analyserade bolag")
df = pd.DataFrame(worksheet.get_all_records())
st.dataframe(df)
