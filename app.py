import streamlit as st
import os

# Tillfällig filuppladdning (visas bara om credentials.json saknas i /mnt/data/)
if "credentials.json" not in os.listdir("/mnt/data/"):
    uploaded_file = st.file_uploader("⬆️ Ladda upp credentials.json", type="json")
    if uploaded_file:
        with open("/mnt/data/credentials.json", "wb") as f:
            f.write(uploaded_file.read())
        st.success("✅ Filen är nu uppladdad! Starta om appen.")
        st.stop()
        import streamlit as st
import os
import pandas as pd
import yfinance as yf
import gspread
from google.oauth2.service_account import Credentials

# 🔍 Temporär kontrollrad – visar filer i mnt/data/
st.write("📁 Innehåll i /mnt/data/:", os.listdir("/mnt/data/"))

# 🛡️ Autentisering för Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = Credentials.from_service_account_file(
    "/mnt/data/credentials.json",  # Säkerställ att filnamnet stämmer
    scopes=scope
)
gc = gspread.authorize(credentials)

# 🔑 Ange ditt Google Sheet-ID här
SHEET_ID = "1-IGWQacBAGo2nIDhTrCWZ9c3tJgm_oY0vRsWIzjG5Yo"
SHEET_NAME = "Sheet1"  # Ändra om du döpt om fliken i arket

# 🔄 Försök läsa datan från arket
try:
    sh = gc.open_by_key(SHEET_ID)
    worksheet = sh.worksheet(SHEET_NAME)
    data = worksheet.get_all_records()
    df = pd.DataFrame(data)
except Exception as e:
    st.error(f"Kunde inte läsa från Google Sheet: {e}")
    df = pd.DataFrame(columns=[
        "Ticker", "Tillväxt 2025 (%)", "Tillväxt 2026 (%)", "Tillväxt 2027 (%)",
        "Omsättning TTM", "P/S TTM", "Aktuell kurs", "Beräknad omsättning 2027",
        "Målkurs 2027", "Undervärdering (%)"
    ])

# 📥 Formulär för nytt bolag
with st.form("Lägg till bolag"):
    ticker = st.text_input("Ticker (t.ex. AAPL)").upper()
    growth_2027 = st.number_input("Förväntad tillväxt 2027 (%)", value=10.0)
    submitted = st.form_submit_button("Analysera")

    if submitted and ticker:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            current_price = info.get("currentPrice")

            # Hämta TTM-omsättning
            ttm_rev = info.get("totalRevenue")

            # Hämta kvartalsdata för att beräkna TTM P/S
            q = stock.quarterly_financials
            if q.empty or ttm_rev is None or current_price is None:
                st.warning("Kunde inte hämta komplett data.")
            else:
                market_cap = info.get("marketCap")
                ps_ttm = market_cap / ttm_rev if market_cap and ttm_rev else None

                # Förväntad tillväxt 2025 och 2026 (om möjligt)
                growth_2025 = info.get("earningsGrowth") or 0.1
                growth_2026 = growth_2025  # om du vill använda samma

                # Räkna ut framtida omsättning
                oms_2027 = ttm_rev * (1 + growth_2025) * (1 + growth_2026) * (1 + growth_2027 / 100)
                target_price = oms_2027 * ps_ttm / info.get("sharesOutstanding", 1)
                undervaluation = ((target_price - current_price) / current_price * 100) if current_price else None

                ny_rad = {
                    "Ticker": ticker,
                    "Tillväxt 2025 (%)": round(growth_2025 * 100, 2),
                    "Tillväxt 2026 (%)": round(growth_2026 * 100, 2),
                    "Tillväxt 2027 (%)": round(growth_2027, 2),
                    "Omsättning TTM": round(ttm_rev / 1e9, 2),
                    "P/S TTM": round(ps_ttm, 2),
                    "Aktuell kurs": round(current_price, 2),
                    "Beräknad omsättning 2027": round(oms_2027 / 1e9, 2),
                    "Målkurs 2027": round(target_price, 2),
                    "Undervärdering (%)": round(undervaluation, 2),
                }

                # Lägg till i DataFrame och spara
                df = pd.concat([df, pd.DataFrame([ny_rad])], ignore_index=True)
                worksheet.update([df.columns.values.tolist()] + df.values.tolist())
                st.success(f"{ticker} har lagts till i analysen.")
        except Exception as e:
            st.error(f"Kunde inte hämta data: {e}")

# 📊 Visa analysdata
if not df.empty:
    df_sorted = df.sort_values(by="Undervärdering (%)", ascending=False).reset_index(drop=True)

    st.subheader("📈 Aktieanalys – Mest undervärderad först")
    index = st.number_input("Bläddra mellan bolag", min_value=0, max_value=len(df_sorted) - 1, step=1)
    st.write(df_sorted.iloc[index])
else:
    st.info("Inga bolag har lagts till ännu.")
