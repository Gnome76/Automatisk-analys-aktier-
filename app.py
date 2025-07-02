import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# Ange ID för ditt Google Sheet (från länken)
SHEET_ID = "1-IGWQacBAGo2nIDhTrCWZ9c3tJgm_oY0vRsWIzjG5Yo"
SHEET_NAME = "Ark1"

# Autentisering – credentials.json ligger i projektroten
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]
credentials_path = "credentials.json"
credentials = Credentials.from_service_account_file(credentials_path, scopes=scope)
gc = gspread.authorize(credentials)
sh = gc.open_by_key(SHEET_ID)
worksheet = sh.worksheet(SHEET_NAME)

# Ladda data från Google Sheets
def load_data():
    records = worksheet.get_all_records()
    return pd.DataFrame(records)

# Spara data till Google Sheets
def save_data(df):
    worksheet.clear()
    worksheet.update([df.columns.values.tolist()] + df.values.tolist())

# Streamlit UI
st.title("📈 Automatisk aktieanalys")

# Ladda nuvarande data
df = load_data()

# Visa nuvarande bolag
st.subheader("📊 Nuvarande analyser")
if df.empty:
    st.info("Inga bolag har lagts till ännu.")
else:
    st.dataframe(df)

# Formulär för att lägga till nytt bolag
st.subheader("➕ Lägg till nytt bolag")
with st.form("add_company_form"):
    namn = st.text_input("Bolagsnamn")
    kurs = st.number_input("Nuvarande aktiekurs", min_value=0.0)
    oms_ttm = st.number_input("Omsättning TTM", min_value=0.0)
    aktier = st.number_input("Antal aktier", min_value=1.0)
    tillväxt_2025 = st.number_input("Tillväxt 2025 (%)", value=0.0)
    tillväxt_2026 = st.number_input("Tillväxt 2026 (%)", value=0.0)
    tillväxt_2027 = st.number_input("Tillväxt 2027 (%)", value=0.0)
    ps_tal = st.number_input("Genomsnittligt P/S TTM", min_value=0.0)
    submit = st.form_submit_button("Lägg till bolag")

    if submit and namn:
        oms_2025 = oms_ttm * (1 + tillväxt_2025 / 100)
        oms_2026 = oms_2025 * (1 + tillväxt_2026 / 100)
        oms_2027 = oms_2026 * (1 + tillväxt_2027 / 100)
        målkurs = (oms_2027 / aktier) * ps_tal

        ny_rad = pd.DataFrame([{
            "Bolag": namn,
            "Kurs": kurs,
            "Oms_TTM": oms_ttm,
            "Tillväxt 2025 (%)": tillväxt_2025,
            "Tillväxt 2026 (%)": tillväxt_2026,
            "Tillväxt 2027 (%)": tillväxt_2027,
            "Antal aktier": aktier,
            "P/S TTM": ps_tal,
            "Målkurs 2027": round(målkurs, 2)
        }])

        df = pd.concat([df, ny_rad], ignore_index=True)
        save_data(df)
        st.success(f"{namn} har lagts till.")
        st.experimental_rerun()
