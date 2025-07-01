import yfinance as yf

def fetch_data(ticker, growth_2027):
    stock = yf.Ticker(ticker)
    info = stock.info
    name = info.get("longName", ticker)
    currency = info.get("currency", "USD")
    shares = info.get("sharesOutstanding", 1)
    revenue_ttm = info.get("totalRevenue", 0)

    # Tillväxtprognoser från analyst estimates (2025 & 2026)
    growth_2025 = None
    growth_2026 = None

    try:
        analysis = stock.analysis
        if "Revenue Estimate" in analysis.index:
            if "2025" in analysis.columns:
                rev_2025 = analysis.loc["Revenue Estimate", "2025"]
                growth_2025 = ((rev_2025 - revenue_ttm) / revenue_ttm) * 100
            if "2026" in analysis.columns:
                rev_2026 = analysis.loc["Revenue Estimate", "2026"]
                growth_2026 = ((rev_2026 - rev_2025) / rev_2025) * 100 if rev_2025 else None
    except:
        pass

    # Fallback om ingen tillväxtdata finns
    growth_2025 = growth_2025 or 20.0
    growth_2026 = growth_2026 or 20.0

    # Omsättning 2027
    revenue_2025 = revenue_ttm * (1 + growth_2025 / 100)
    revenue_2026 = revenue_2025 * (1 + growth_2026 / 100)
    revenue_2027 = revenue_2026 * (1 + growth_2027 / 100)

    # Snitt P/S på senaste 4 kvartal (fallback = 5)
    ps_avg = info.get("trailingPegRatio", 5)

    target_price = (revenue_2027 / shares) * ps_avg

    return {
        "ticker": ticker,
        "name": name,
        "currency": currency,
        "revenue_ttm": revenue_ttm,
        "growth_2025": growth_2025,
        "growth_2026": growth_2026,
        "growth_2027": growth_2027,
        "revenue_2027": revenue_2027,
        "ps_avg": ps_avg,
        "target_price_base": target_price
    }
