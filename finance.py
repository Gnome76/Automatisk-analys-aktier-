import yfinance as yf
from datetime import datetime

def fetch_data(ticker):
    stock = yf.Ticker(ticker)
    info = stock.info

    name = info.get("shortName", ticker)
    currency = info.get("currency", "USD")
    market_cap = info.get("marketCap", 0)
    revenue_ttm = info.get("totalRevenue", 0)
    shares_outstanding = info.get("sharesOutstanding", 0)

    if revenue_ttm and market_cap:
        ps_avg = market_cap / revenue_ttm
    else:
        ps_avg = 0

    revenue_2027 = revenue_ttm * 4  # 4 års antagen tillväxt (≈ +42 %/år)
    target_price_base = (revenue_2027 / shares_outstanding) * ps_avg
    target_price_low = target_price_base * 0.7
    target_price_high = target_price_base * 1.3

    return {
        "ticker": ticker.upper(),
        "name": name,
        "currency": currency,
        "market_cap": market_cap,
        "revenue_ttm": revenue_ttm,
        "shares_outstanding": shares_outstanding,
        "ps_avg": ps_avg,
        "revenue_2027": revenue_2027,
        "target_price_low": target_price_low,
        "target_price_base": target_price_base,
        "target_price_high": target_price_high,
        "last_updated": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    }
