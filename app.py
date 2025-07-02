import streamlit as st
import pandas as pd
import yfinance as yf
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# ---- Google Sheets setup ----
SHEET_ID = "1-IGWQacBAGo2nIDhTrCWZ9c3tJgm_oY0vRsWIzjG5Yo"
CREDENTIALS_PATH = "/mnt/data/credentials.json"

# Koppla till Google Sheet
gc = gspread.service_account(filename=CREDENTIALS_PATH)
sh = gc.open_by_key(SHEET_ID)
worksheet = sh.sheet1

# Läs in data
try:
    data = worksheet.get_all_records()
    df = pd.DataFrame(data)
except Exception as e:
    st.error("Kunde inte läsa data från Google Sheet.")
    st.stop()

# Hämta inmatning
st.title("Automatisk aktieanalys – P/S-modell")
ticker = st.text_input("Ange ticker (t.ex. AAPL eller MSFT)")
growth_2027 = st.number_input("Förväntad tillväxt 2027 (%)", step=1.0, format="%.2f")

if st.button("Analysera bolag"):
    if not ticker:
        st.warning("Du måste ange en ticker.")
    else:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            # Hämta TTM-omsättning och antal aktier
            ttm_revenue = info.get("totalRevenue")
            shares_outstanding = info.get("sharesOutstanding")
            currency = info.get("financialCurrency", "USD")

            if ttm_revenue and shares_outstanding:
                # Tillväxtberäkningar
                growth_factor = 1 + growth_2027 / 100
                est_revenue_2027 = ttm_revenue * growth_factor

                # Kursdata från senaste 4 kvartal
                hist = stock.history(period="1y", interval="3mo")
                ps_values = []
                for i in range(len(hist)):
                    price = hist["Close"].iloc[i]
                    if i >= 3:
                        revs = []
                        for j in range(i - 3, i + 1):
                            q = stock.quarterly_financials
                            rev = q.iloc[:, j].sum() if not q.empty else None
                            if rev:
                                revs.append(rev)
                        ttm_q_revenue = sum(revs)
                        if ttm_q_revenue and shares_outstanding:
                            ps = (price * shares_outstanding) / ttm_q_revenue
                            ps_values.append(ps)

                avg_ps = sum(ps_values) / len(ps_values) if ps_values else 5
                target_price = (est_revenue_2027 / shares_outstanding) * avg_ps

                # Visa resultat
                st.success(f"Beräknad målkurs för {ticker.upper()} år 2027: {target_price:.2f} {currency}")

                # Lägg till i Google Sheet
                new_row = {
                    "Ticker": ticker.upper(),
                    "Tillväxt 2027 (%)": growth_2027,
                    "Valuta": currency,
                    "Omsättning (TTM)": ttm_revenue,
                    "Antal aktier": shares_outstanding,
                    "Snitt P/S (TTM)": round(avg_ps, 2),
                    "Beräknad målkurs 2027": round(target_price, 2),
                }
                worksheet.append_row(list(new_row.values()))
                st.info("Resultat sparat i Google Sheets.")

            else:
                st.error("Kunde inte hämta finansiell data för bolaget.")
        except Exception as e:
            st.error(f"Ett fel uppstod: {e}")
