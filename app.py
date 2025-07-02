import streamlit as st
import pandas as pd
import yfinance as yf
import gspread
from google.oauth2.service_account import Credentials
import os

# Google Sheet-ID
SHEET_ID = "1-IGWQacBAGo2nIDhTrCWZ9c3tJgm_oY0vRsWIzjG5Yo"
SHEET_NAME = "Sheet1"

# Autentisering till Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = Credentials.from_service_account_file(
    "/mnt/data/credentials.json",
    scopes=scope
)
gc = gspread.authorize(credentials)
sh = gc.open_by_key(SHEET_ID)
worksheet = sh.worksheet(SHEET_NAME)

# Läs in datan
try:
    df = pd.DataFrame(worksheet.get_all_records())
except Exception as e:
    st.error(f"Kunde inte läsa Google Sheet: {e}")
    df = pd.DataFrame(columns=[
        "Ticker", "Bolagsnamn", "Tillväxt_2025", "Tillväxt_2026", "Tillväxt_2027",
        "Aktuell kurs", "Genomsnittligt P/S", "Omsättning 2024", "Omsättning 2025",
        "Omsättning 2026", "Omsättning 2027", "Målkurs 2027", "Undervärdering (%)"
    ])

st.title("📈 Automatisk aktieanalys – P/S 2027")

# Formulär för att lägga till nytt bolag
with st.form("add_company"):
    st.subheader("➕ Lägg till nytt bolag")
    ticker = st.text_input("Ticker (t.ex. AAPL)")
    tillvaxt_2027 = st.number_input("Förväntad tillväxt 2027 (%)", value=10.0)
    submitted = st.form_submit_button("Lägg till")
    
    if submitted and ticker:
        try:
            info = yf.Ticker(ticker).info
            name = info.get("shortName", ticker)

            # Hämta tillväxtprognos från Yahoo (2025 och 2026)
            growth = info.get("earningsQuarterlyGrowth", 0.10)  # fallback
            tillvaxt_2025 = growth * 100
            tillvaxt_2026 = growth * 100

            # Hämta kvartalsdata för att räkna ut genomsnittligt P/S
            q = yf.Ticker(ticker).quarterly_financials
            hist = yf.Ticker(ticker).history(period="1y")
            if q.empty or hist.empty:
                raise ValueError("Kunde inte hämta kvartalsdata")

            # Skapa lista på TTM-omsättningar för 4 kvartal
            rev = yf.Ticker(ticker).quarterly_financials.loc["Total Revenue"]
            rev = rev.sort_index(ascending=True)
            ps_values = []
            for i in range(len(rev) - 3):
                ttm_sales = rev[i] + rev[i + 1] + rev[i + 2] + rev[i + 3]
                date = rev.index[i + 3]
                price = hist.loc[date:date].iloc[0]["Close"] if date in hist.index else None
                shares = info.get("sharesOutstanding", 1)
                market_cap = price * shares if price else None
                ps = market_cap / ttm_sales if market_cap and ttm_sales else None
                if ps:
                    ps_values.append(ps)

            average_ps = round(sum(ps_values) / len(ps_values), 2) if ps_values else None

            # Hämta aktuell kurs och nuvarande omsättning
            current_price = yf.Ticker(ticker).history(period="1d")["Close"].iloc[-1]
            sales_2024 = rev[-4:].sum()

            # Räkna ut framtida omsättning
            sales_2025 = sales_2024 * (1 + tillvaxt_2025 / 100)
            sales_2026 = sales_2025 * (1 + tillvaxt_2026 / 100)
            sales_2027 = sales_2026 * (1 + tillvaxt_2027 / 100)

            shares_outstanding = info.get("sharesOutstanding", 1)
            target_price = (sales_2027 / shares_outstanding) * average_ps
            undervaluation = round((target_price - current_price) / current_price * 100, 2)

            new_row = {
                "Ticker": ticker,
                "Bolagsnamn": name,
                "Tillväxt_2025": round(tillvaxt_2025, 2),
                "Tillväxt_2026": round(tillvaxt_2026, 2),
                "Tillväxt_2027": tillvaxt_2027,
                "Aktuell kurs": round(current_price, 2),
                "Genomsnittligt P/S": average_ps,
                "Omsättning 2024": round(sales_2024),
                "Omsättning 2025": round(sales_2025),
                "Omsättning 2026": round(sales_2026),
                "Omsättning 2027": round(sales_2027),
                "Målkurs 2027": round(target_price, 2),
                "Undervärdering (%)": undervaluation
            }

            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            worksheet.update([df.columns.values.tolist()] + df.values.tolist())
            st.success("Bolaget har lagts till!")
        except Exception as e:
            st.error(f"Kunde inte hämta data: {e}")

# Bläddringsfunktion – ett bolag i taget, mest undervärderad först
if not df.empty:
    df = df.sort_values(by="Undervärdering (%)", ascending=False).reset_index(drop=True)
    if "index" not in st.session_state:
        st.session_state.index = 0

    current = st.session_state.index
    bolag = df.iloc[current]

    st.subheader(f"📊 {bolag['Bolagsnamn']} ({bolag['Ticker']})")
    st.metric("Aktuell kurs", f"{bolag['Aktuell kurs']}")
    st.metric("Målkurs 2027", f"{bolag['Målkurs 2027']}")
    st.metric("Undervärdering (%)", f"{bolag['Undervärdering (%)']} %")
    st.write("Tillväxt 2025–2027 (%):", bolag["Tillväxt_2025"], bolag["Tillväxt_2026"], bolag["Tillväxt_2027"])
    st.write("Omsättning (M):", {
        "2024": bolag["Omsättning 2024"],
        "2025": bolag["Omsättning 2025"],
        "2026": bolag["Omsättning 2026"],
        "2027": bolag["Omsättning 2027"],
    })
    st.write("Genomsnittligt P/S:", bolag["Genomsnittligt P/S"])

    col1, col2 = st.columns(2)
    if col1.button("⬅️ Föregående", disabled=current == 0):
        st.session_state.index -= 1
    if col2.button("➡️ Nästa", disabled=current >= len(df) - 1):
        st.session_state.index += 1
