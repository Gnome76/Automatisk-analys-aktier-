import os
import streamlit as st
import pandas as pd
import yfinance as yf
from google.oauth2.service_account import Credentials
import gspread

# Steg 1: Kontrollera och lista /mnt/data/
data_folder = "/mnt/data"
if not os.path.exists(data_folder):
    try:
        os.makedirs(data_folder)
    except PermissionError:
        st.error("🚫 Kunde inte skapa /mnt/data – saknar behörighet.")
    except Exception as e:
        st.error(f"⚠️ Okänt fel vid skapande av /mnt/data: {e}")

try:
    st.write("📁 Innehåll i /mnt/data/:", os.listdir(data_folder))
except FileNotFoundError:
    st.error("❌ Mappen /mnt/data finns inte.")
except PermissionError:
    st.error("🚫 Saknar behörighet att läsa /mnt/data.")

# Steg 2: Autentisera mot Google Sheets
scope = ["https://www.googleapis.com/auth/spreadsheets"]
credentials_path = os.path.join(data_folder, "credentials.json")

if not os.path.isfile(credentials_path):
    st.error("❌ credentials.json saknas i /mnt/data/. Ladda upp den via 'Files' i Streamlit Cloud.")
    st.stop()

try:
    credentials = Credentials.from_service_account_file(
        credentials_path, scopes=scope
    )
    gc = gspread.authorize(credentials)
except Exception as e:
    st.error(f"❌ Fel vid inläsning av credentials.json: {e}")
    st.stop()

# Steg 3: Öppna kalkylarket
SHEET_ID = "1-IGWQacBAGo2nIDhTrCWZ9c3tJgm_oY0vRsWIzjG5Yo"  # Ditt Google Sheet-ID
try:
    sh = gc.open_by_key(SHEET_ID)
    worksheet = sh.sheet1
    data = worksheet.get_all_records()
    df = pd.DataFrame(data)
except Exception as e:
    st.error(f"❌ Kunde inte läsa Google Sheet: {e}")
    df = pd.DataFrame()

# Steg 4: Lägg till nytt bolag
st.header("📈 Lägg till bolag för analys")

ticker = st.text_input("Ange ticker (t.ex. AAPL)")
growth_2025 = st.number_input("Förväntad tillväxt 2025 (%)", value=10.0)
growth_2026 = st.number_input("Förväntad tillväxt 2026 (%)", value=10.0)
growth_2027 = st.number_input("Förväntad tillväxt 2027 (%)", value=10.0)

if st.button("Analysera och spara"):
    if not ticker:
        st.warning("❗ Ange en ticker.")
    else:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            hist = stock.history(period="1y", interval="1d")
            price_now = hist["Close"].iloc[-1]
            shares = info.get("sharesOutstanding")
            currency = info.get("currency", "USD")
            quarterly = stock.quarterly_financials
            revenues = quarterly.loc["Total Revenue"].dropna()

            if len(revenues) >= 4 and shares:
                ttm_revenue = revenues.iloc[:4].sum()
                market_cap = price_now * shares
                ps_ttm = market_cap / ttm_revenue
                growth_factor = (1 + growth_2025 / 100) * (1 + growth_2026 / 100) * (1 + growth_2027 / 100)
                est_2027_revenue = ttm_revenue * growth_factor
                price_target = (est_2027_revenue / shares) * ps_ttm

                st.success(f"{ticker} ({currency}) – Målkurs 2027: {price_target:.2f}")
                st.write(f"📌 Nuvarande kurs: {price_now:.2f}")
                st.write(f"📊 P/S (TTM): {ps_ttm:.2f}")
                st.write(f"📈 TTM-omsättning: {ttm_revenue:,.0f}")

                # Lägg till i DataFrame
                new_row = {
                    "Ticker": ticker,
                    "Price now": price_now,
                    "Shares": shares,
                    "Currency": currency,
                    "TTM Revenue": ttm_revenue,
                    "P/S TTM": ps_ttm,
                    "Growth 2025": growth_2025,
                    "Growth 2026": growth_2026,
                    "Growth 2027": growth_2027,
                    "Est. Revenue 2027": est_2027_revenue,
                    "Target price 2027": price_target
                }

                df = df.append(new_row, ignore_index=True)
                # Spara till Google Sheet
                try:
                    worksheet.clear()
                    worksheet.update([df.columns.values.tolist()] + df.values.tolist())
                    st.success("✅ Data sparad till Google Sheets.")
                except Exception as e:
                    st.error(f"❌ Kunde inte spara till Google Sheet: {e}")
            else:
                st.warning("⚠️ Kunde inte hämta tillräckligt med data för analys.")
        except Exception as e:
            st.error(f"❌ Fel vid analys: {e}")

# Steg 5: Visa befintlig data
if not df.empty:
    st.subheader("📋 Analysdata")
    st.dataframe(df)
else:
    st.info("Ingen data att visa ännu.")
