# src/services/financial.py
"""Financial analysis service using yfinance."""

from typing import Any

import yfinance as yf

# --- Scoring Functions ---


def score_pe(value: float | None) -> int:
    """Score P/E ratio."""
    if value is None:
        return 0
    if value < 15:
        return 10
    if value < 30:
        return 7
    if value < 45:
        return 5
    return 2


def score_roe(value: float | None) -> int:
    """Score ROE percentage."""
    if value is None:
        return 0
    if value > 20:
        return 10
    if value >= 10:
        return 7
    return 3


def score_debt_equity(value: float | None) -> int:
    """Score Debt/Equity ratio."""
    if value is None:
        return 0
    if value < 1:
        return 10
    if value <= 2:
        return 6
    return 2


def score_beta(value: float | None) -> int:
    """Score Beta."""
    if value is None:
        return 0
    if 0.8 <= value <= 1.2:
        return 10
    if 1.2 < value <= 1.5:
        return 7
    if 1.5 < value <= 2:
        return 5
    return 2


def score_dividend_yield(value: float | None) -> int:
    """Score Dividend Yield."""
    if value is None:
        return 0
    if value > 0.03:
        return 10
    if value >= 0.01:
        return 7
    return 3


def score_revenue_growth(value: float | None) -> int:
    """Score Revenue Growth."""
    if value is None:
        return 0
    if value > 0.10:
        return 10
    if value >= 0:
        return 6
    return 2


def score_ev_ebitda(value: float | None) -> int:
    """Score EV/EBITDA."""
    if value is None:
        return 0
    if value < 8:
        return 10
    if value <= 14:
        return 6
    return 2


# --- Indicator Weights ---

WEIGHTS: dict[str, float] = {
    "pe": 0.15,
    "roe": 0.20,
    "de": 0.15,
    "beta": 0.10,
    "dividend": 0.10,
    "growth": 0.15,
    "evebitda": 0.15,
}


# --- Analysis Function ---


def analyze_stock_sync(ticker: str) -> dict[str, Any]:
    """
    Perform simplified fundamental analysis using yfinance.
    Returns weighted score with BUY/HOLD/SELL decision.
    """
    stock = yf.Ticker(ticker)
    info = stock.info or {}

    pe = info.get("trailingPE")
    roe = info.get("returnOnEquity")
    de = info.get("debtToEquity")
    beta = info.get("beta")
    dividend = info.get("dividendYield")
    revenue_growth = info.get("revenueGrowth")
    evebitda = info.get("enterpriseToEbitda")

    scores: dict[str, float] = {
        "pe": score_pe(pe),
        "roe": score_roe((roe * 100) if roe is not None else None),
        "de": score_debt_equity(de),
        "beta": score_beta(beta),
        "dividend": score_dividend_yield(dividend),
        "growth": score_revenue_growth(revenue_growth),
        "evebitda": score_ev_ebitda(evebitda),
    }

    total_score = sum(scores[k] * WEIGHTS[k] for k in scores)

    if total_score >= 7.5:
        decision = "BUY"
    elif total_score >= 6:
        decision = "HOLD"
    else:
        decision = "SELL"

    return {
        "ticker": ticker.upper(),
        "raw_metrics": {
            "trailingPE": pe,
            "returnOnEquity": roe,
            "debtToEquity": de,
            "beta": beta,
            "dividendYield": dividend,
            "revenueGrowth": revenue_growth,
            "enterpriseToEbitda": evebitda,
        },
        "scores": scores,
        "weights": WEIGHTS,
        "total_score": round(float(total_score), 2),
        "decision": decision,
    }


# --- Analysis Functions ---


def get_stock_price_sync(ticker: str, period: str = "1mo") -> dict[str, Any]:
    """
    Get current price and historical data for a stock.
    """
    stock = yf.Ticker(ticker)
    info = stock.info or {}
    hist = stock.history(period=period)

    if hist.empty:
        return {"ticker": ticker.upper(), "error": "No data available"}

    current_price = info.get("currentPrice") or info.get("regularMarketPrice")
    prev_close = info.get("previousClose")

    # Calculate change
    change_pct = None
    if current_price and prev_close:
        change_pct = round(((current_price - prev_close) / prev_close) * 100, 2)

    # Period stats
    period_high = round(float(hist["High"].max()), 2)
    period_low = round(float(hist["Low"].min()), 2)
    period_open = round(float(hist["Open"].iloc[0]), 2)
    period_close = round(float(hist["Close"].iloc[-1]), 2)
    period_change = round(((period_close - period_open) / period_open) * 100, 2)

    # Trend
    if period_change > 5:
        trend = "BULLISH"
    elif period_change < -5:
        trend = "BEARISH"
    else:
        trend = "NEUTRAL"

    return {
        "ticker": ticker.upper(),
        "current_price": current_price,
        "previous_close": prev_close,
        "change_pct": change_pct,
        "period": period,
        "period_stats": {
            "open": period_open,
            "close": period_close,
            "high": period_high,
            "low": period_low,
            "change_pct": period_change,
        },
        "trend": trend,
        "currency": info.get("currency", "USD"),
    }


def compare_stocks_sync(tickers: list[str]) -> dict[str, Any]:
    """
    Compare multiple stocks side by side.
    """
    if len(tickers) < 2:
        return {"error": "At least 2 tickers required"}
    if len(tickers) > 5:
        tickers = tickers[:5]  # Limit to 5

    comparison = []
    for ticker in tickers:
        stock = yf.Ticker(ticker)
        info = stock.info or {}

        comparison.append(
            {
                "ticker": ticker.upper(),
                "name": info.get("shortName", "N/A"),
                "price": info.get("currentPrice") or info.get("regularMarketPrice"),
                "market_cap": info.get("marketCap"),
                "pe_ratio": info.get("trailingPE"),
                "forward_pe": info.get("forwardPE"),
                "roe": info.get("returnOnEquity"),
                "dividend_yield": info.get("dividendYield"),
                "beta": info.get("beta"),
                "52w_high": info.get("fiftyTwoWeekHigh"),
                "52w_low": info.get("fiftyTwoWeekLow"),
            }
        )

    # Rank by metrics
    rankings = {
        "by_pe": sorted([c for c in comparison if c["pe_ratio"]], key=lambda x: x["pe_ratio"] or 999),
        "by_roe": sorted([c for c in comparison if c["roe"]], key=lambda x: x["roe"] or 0, reverse=True),
        "by_market_cap": sorted(
            [c for c in comparison if c["market_cap"]], key=lambda x: x["market_cap"] or 0, reverse=True
        ),
    }

    return {
        "tickers": [t.upper() for t in tickers],
        "comparison": comparison,
        "rankings": {
            "lowest_pe": rankings["by_pe"][0]["ticker"] if rankings["by_pe"] else None,
            "highest_roe": rankings["by_roe"][0]["ticker"] if rankings["by_roe"] else None,
            "largest_market_cap": rankings["by_market_cap"][0]["ticker"] if rankings["by_market_cap"] else None,
        },
    }


def dividend_analysis_sync(ticker: str) -> dict[str, Any]:
    """
    Analyze dividend history and metrics.
    """
    stock = yf.Ticker(ticker)
    info = stock.info or {}
    dividends = stock.dividends

    dividend_yield = info.get("dividendYield")
    payout_ratio = info.get("payoutRatio")
    dividend_rate = info.get("dividendRate")
    ex_dividend_date = info.get("exDividendDate")

    # Analyze dividend history
    dividend_history = []
    if not dividends.empty:
        # Last 20 dividends
        recent = dividends.tail(20)
        for date, amount in recent.items():
            dividend_history.append(
                {
                    "date": date.strftime("%Y-%m-%d"),
                    "amount": round(float(amount), 4),
                }
            )

        # Calculate growth
        if len(dividends) >= 8:
            old_div = dividends.iloc[-8:-4].sum()
            new_div = dividends.iloc[-4:].sum()
            if old_div > 0:
                growth = ((new_div - old_div) / old_div) * 100
            else:
                growth = None
        else:
            growth = None
    else:
        growth = None

    return {
        "ticker": ticker.upper(),
        "dividend_yield": round(dividend_yield * 100, 2) if dividend_yield else None,
        "dividend_rate": dividend_rate,
        "payout_ratio": round(payout_ratio * 100, 2) if payout_ratio else None,
        "ex_dividend_date": ex_dividend_date,
        "dividend_growth_yoy": round(growth, 2) if growth else None,
        "history": dividend_history[-8:],  # Last 8 dividends
        "pays_dividend": len(dividend_history) > 0,
    }


def company_profile_sync(ticker: str) -> dict[str, Any]:
    """
    Get company profile information.
    """
    stock = yf.Ticker(ticker)
    info = stock.info or {}

    return {
        "ticker": ticker.upper(),
        "name": info.get("shortName") or info.get("longName"),
        "sector": info.get("sector"),
        "industry": info.get("industry"),
        "country": info.get("country"),
        "city": info.get("city"),
        "employees": info.get("fullTimeEmployees"),
        "website": info.get("website"),
        "description": info.get("longBusinessSummary", "")[:500],  # Truncate
        "market_cap": info.get("marketCap"),
        "currency": info.get("currency"),
        "exchange": info.get("exchange"),
    }


def stock_news_sync(ticker: str) -> dict[str, Any]:
    """
    Get recent news for a stock.
    """
    stock = yf.Ticker(ticker)
    news = stock.news or []

    news_list = []
    for item in news[:5]:  # Last 5 news
        news_list.append(
            {
                "title": item.get("title"),
                "publisher": item.get("publisher"),
                "link": item.get("link"),
                "published": item.get("providerPublishTime"),
                "type": item.get("type"),
            }
        )

    return {
        "ticker": ticker.upper(),
        "news_count": len(news_list),
        "news": news_list,
    }


def technical_indicators_sync(ticker: str, period: str = "3mo") -> dict[str, Any]:
    """
    Calculate technical indicators for a stock.
    """
    stock = yf.Ticker(ticker)
    hist = stock.history(period=period)

    if hist.empty:
        return {"ticker": ticker.upper(), "error": "No data available"}

    close = hist["Close"]
    volume = hist["Volume"]

    # Simple Moving Averages
    sma_20 = close.rolling(window=20).mean().iloc[-1] if len(close) >= 20 else None
    sma_50 = close.rolling(window=50).mean().iloc[-1] if len(close) >= 50 else None
    sma_200 = close.rolling(window=200).mean().iloc[-1] if len(close) >= 200 else None

    # RSI (14 days)
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    rsi_value = rsi.iloc[-1] if len(rsi) >= 14 else None

    # Volume average
    avg_volume = volume.mean()
    current_volume = volume.iloc[-1]

    # Current price
    current_price = close.iloc[-1]

    # Support and Resistance estimates
    support = round(float(close.tail(20).min()), 2)
    resistance = round(float(close.tail(20).max()), 2)

    # Signal
    if rsi_value:
        if rsi_value < 30:
            rsi_signal = "OVERSOLD"
        elif rsi_value > 70:
            rsi_signal = "OVERBOUGHT"
        else:
            rsi_signal = "NEUTRAL"
    else:
        rsi_signal = None

    return {
        "ticker": ticker.upper(),
        "period": period,
        "current_price": round(float(current_price), 2),
        "sma_20": round(float(sma_20), 2) if sma_20 else None,
        "sma_50": round(float(sma_50), 2) if sma_50 else None,
        "sma_200": round(float(sma_200), 2) if sma_200 else None,
        "rsi_14": round(float(rsi_value), 2) if rsi_value else None,
        "rsi_signal": rsi_signal,
        "avg_volume": int(avg_volume),
        "current_volume": int(current_volume),
        "volume_ratio": round(current_volume / avg_volume, 2) if avg_volume > 0 else None,
        "support_20d": support,
        "resistance_20d": resistance,
    }


def earnings_calendar_sync(ticker: str) -> dict[str, Any]:
    """
    Get earnings calendar and history.
    """
    stock = yf.Ticker(ticker)
    info = stock.info or {}
    calendar = stock.calendar or {}
    earnings = stock.earnings_history

    # Next earnings date
    earnings_dates = calendar.get("Earnings Date") if isinstance(calendar, dict) else None

    # Earnings history
    earnings_list = []
    if earnings is not None and not earnings.empty:
        for idx, row in earnings.tail(8).iterrows():
            earnings_list.append(
                {
                    "date": idx.strftime("%Y-%m-%d") if hasattr(idx, "strftime") else str(idx),
                    "eps_estimate": row.get("epsEstimate"),
                    "eps_actual": row.get("epsActual"),
                    "surprise_pct": row.get("surprisePercent"),
                }
            )

    return {
        "ticker": ticker.upper(),
        "next_earnings_date": str(earnings_dates[0]) if earnings_dates else None,
        "earnings_history": earnings_list,
        "eps_trailing": info.get("trailingEps"),
        "eps_forward": info.get("forwardEps"),
    }
