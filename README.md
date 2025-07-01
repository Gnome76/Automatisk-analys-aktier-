# Målkurs 2027 – Enkelversion

Denna app analyserar bolag utifrån P/S och tillväxt, och beräknar ett rimligt aktiepris för 2027. Allt sker utan databas – i minnet under din session.

## Funktioner
- Automatisk hämtning av tillväxt i % (2025 och 2026)
- Manuell tillväxtinmatning för 2027
- Uträkning av målkurs baserat på omsättning och P/S
- Undervärdering i %

## Starta appen lokalt
```bash
pip install -r requirements.txt
streamlit run app.py
