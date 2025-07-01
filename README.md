# 📊 Aktieanalys – Målkurs 2027

Den här appen hämtar bolagsdata via `yfinance` och gör en automatisk beräkning av förväntad omsättning och målkurs till 2027, baserat på förväntad tillväxt i %.

## Funktioner
- Automatisk hämtning av tillväxt i % för 2025 och 2026
- Manuell inmatning av tillväxt 2027 (%)
- Uträkning av omsättning 2027
- Beräkning av målkurs 2027 baserat på snitt-P/S
- Undervärdering visas i procent
- Data sparas i lokal SQLite-databas (`/mnt/data/database.db`)
- Kan köras i Streamlit Cloud

## Installation
```bash
pip install -r requirements.txt
streamlit run app.py
