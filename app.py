import streamlit as st
import yfinance as yf
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import os

# 📁 Kontrollera om credentials.json finns
data_folder = "/mnt/data/"
st.write("📁 Innehåll i /mnt/data/:", os.listdir(data_folder))

if "credentials.json" not in os.listdir(data_folder):
    uploaded_file = st.file_uploader("⬆️ Ladda upp credentials.json", type="json")
    if uploaded_file:
        with open(os.path.join(data_folder, "credentials.json"), "wb") as f:
            f.write(uploaded_file.read())
        st.success("✅ Filen är uppladdad! Starta om appen.")
        st.stop()
    else:
        st.warning("⚠️ Ladda upp credentials.json för att fortsätta.")
        st.stop()

# 🔐 Ladda in credentials
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = Credentials.from_service_account_file(
    os.path.join(data_folder, "credentials.json"),
    scopes=scope
)
gc = gspread.authorize(credentials)

# 📄 Anslut till Google Sheet
SHEET_ID = "1-IGWQacBAGo2nIDhTrCWZ9c3tJgm_oY0vRsWIzjG5Yo"
worksheet = gc.open_by_key(SHEET_ID).sheet1

# 🧾 Hämta befintlig data
data = worksheet.get_all_records()
df = pd.DataFrame(data)

# 🧠 Appens titel
st.title("📊 Automatisk aktieanalys – Målkurs 2027")
st.markdown("Analyserar bolag automatiskt med tillväxt och P/S TTM.")

# ➕ Formulär för nytt bolag
st.header("Lägg till nytt bolag")
ticker = st.text_input("Ticker (ex. AAPL)")
growth_2027 = st.number_input("Förväntad tillväxt 2027 (%)", step=1.0)

if st.button("Analysera och lägg till"):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        name = info.get("shortName", "")
        price = info.get("currentPrice", None)
        currency = info.get("currency", "USD")
        shares = info.get("sharesOutstanding", None)
        revenue_ttm = info.get("totalRevenue", None)
        ps_ratio = info.get("priceToSalesTrailing12Months", None)

        if None in [price, shares, revenue_ttm, ps_ratio]:
            st.error("❌ Kunde inte hämta fullständig data för bolaget.")
        else:
            growth_factor = 1 + (growth_2027 / 100)
            est_revenue_2027 = revenue_ttm * growth_factor
            target_price_2027 = (est_revenue_2027 / shares) * ps_ratio
            undervaluation = ((target_price_2027 - price) / price) * 100

            new_row = [ticker, name, price, ps_ratio, revenue_ttm, shares, growth_2027,
                       est_revenue_2027, target_price_2027, undervaluation, currency]
            worksheet.append_row(new_row)

            st.success(f"✅ {ticker} analyserat och sparat!")
    except Exception as e:
        st.error(f"Något gick fel: {e}")

# 📊 Visa existerande data
st.header("📃 Analyserade bolag")
if not df.empty:
    df_sorted = df.sort_values(by="Undervaluation (%)", ascending=False)
    st.dataframe(df_sorted)
else:
    st.info("Inga bolag analyserade ännu.")
