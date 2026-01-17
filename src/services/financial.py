
from typing import Any, Dict, Optional

import yfinance as yf
from pydantic import BaseModel, Field

# ============================
# 1) FUNZIONI DI SCORING
# ============================

def score_pe(value: Optional[float]) -> int:
    if value is None:
        return 0
    if value < 15:
        return 10
    if value < 30:
        return 7
    if value < 45:
        return 5
    return 2


def score_roe(value: Optional[float]) -> int:
    if value is None:
        return 0
    if value > 20:
        return 10
    if value >= 10:
        return 7
    return 3


def score_debt_equity(value: Optional[float]) -> int:
    if value is None:
        return 0
    if value < 1:
        return 10
    if value <= 2:
        return 6
    return 2


def score_beta(value: Optional[float]) -> int:
    if value is None:
        return 0
    if 0.8 <= value <= 1.2:
        return 10
    if 1.2 < value <= 1.5:
        return 7
    if 1.5 < value <= 2:
        return 5
    return 2


def score_dividend_yield(value: Optional[float]) -> int:
    if value is None:
        return 0
    if value > 0.03:
        return 10
    if value >= 0.01:
        return 7
    return 3


def score_revenue_growth(value: Optional[float]) -> int:
    if value is None:
        return 0
    if value > 0.10:
        return 10
    if value >= 0:
        return 6
    return 2


def score_ev_ebitda(value: Optional[float]) -> int:
    if value is None:
        return 0
    if value < 8:
        return 10
    if value <= 14:
        return 6
    return 2


# ============================
# 2) PESI DEGLI INDICATORI
# ============================

_WEIGHTS: Dict[str, float] = {
    "pe": 0.15,
    "roe": 0.20,
    "de": 0.15,
    "beta": 0.10,
    "dividend": 0.10,
    "growth": 0.15,
    "evebitda": 0.15,
}


# ============================
# 3) LOGICA DI ANALISI (SYNC)
# ============================

def _analyze_stock_sync(ticker: str) -> Dict[str, Any]:
    """
    Esegue l'analisi fondamentale semplificata del titolo tramite yfinance
    e calcola uno score pesato con output BUY/HOLD/SELL.
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

    scores: Dict[str, float] = {
        "pe": score_pe(pe),
        "roe": score_roe((roe * 100) if roe is not None else None),
        "de": score_debt_equity(de),
        "beta": score_beta(beta),
        "dividend": score_dividend_yield(dividend),
        "growth": score_revenue_growth(revenue_growth),
        "evebitda": score_ev_ebitda(evebitda),
    }

    total_score = sum(scores[k] * _WEIGHTS[k] for k in scores)

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
        "weights": _WEIGHTS,
        "total_score": round(float(total_score), 2),
        "decision": decision,
    }


# ============================
# 4) TOOL (ASYNC) - LANGCHAIN
# ============================

class StockAnalysisSchema(BaseModel):
    """Schema per il tool di analisi fondamentale/score del titolo."""
    ticker: str = Field(description="Ticker del titolo (es. AAPL, MSFT, NVDA).")
