"""ETF / portfolio risk scoring (0-100), based on volatility, drawdown, and
concentration. Purely descriptive - higher means more variable historically,
not "riskier" in a predictive sense.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

RISK_BANDS = [
    (0, 20, "Conservative"),
    (20, 40, "Moderately conservative"),
    (40, 60, "Moderate"),
    (60, 80, "Aggressive"),
    (80, 101, "Very aggressive"),
]


def risk_label(score: float) -> str:
    for lo, hi, label in RISK_BANDS:
        if lo <= score < hi:
            return label
    return "Very aggressive"


def _annualized_vol(close: pd.Series) -> float | None:
    returns = close.pct_change().dropna()
    if len(returns) < 5:
        return None
    return float(returns.std() * np.sqrt(252))


def _max_drawdown(close: pd.Series) -> float | None:
    if close.empty:
        return None
    running_max = close.cummax()
    drawdown = (close - running_max) / running_max
    return float(abs(drawdown.min()))


def etf_risk_score(history: pd.DataFrame, top_holdings: list[dict] | None = None) -> tuple[float | None, list[str]]:
    """Return (score 0-100, driver strings) for an ETF.

    Weights: volatility 45%, max drawdown 35%, concentration (top-10 holdings
    weight) 20%.
    """
    if history is None or history.empty:
        return None, []

    close = history["Close"].dropna()
    components = []
    drivers = []

    vol = _annualized_vol(close)
    if vol is not None:
        comp = min(vol / 0.40, 1.0) * 100  # 40% annualized vol -> max score
        components.append((comp, 45))
        drivers.append(f"Annualized volatility of {vol * 100:.1f}%")

    dd = _max_drawdown(close)
    if dd is not None:
        comp = min(dd / 0.50, 1.0) * 100  # 50% drawdown -> max score
        components.append((comp, 35))
        drivers.append(f"Maximum drawdown over the period of {dd * 100:.1f}%")

    if top_holdings:
        top10_weight = sum(h.get("weight", 0) for h in top_holdings[:10])
        if top10_weight <= 1.0:
            top10_weight *= 100
        comp = min(top10_weight / 60.0, 1.0) * 100  # 60% in top10 -> max score
        components.append((comp, 20))
        drivers.append(f"Top 10 holdings represent {top10_weight:.1f}% of assets")

    if not components:
        return None, drivers

    total_weight = sum(w for _, w in components)
    score = sum(c * w for c, w in components) / total_weight
    return round(score, 1), drivers


def portfolio_risk_score(per_holding_scores: list[tuple[float, float]]) -> float | None:
    """Weighted-average risk score for a portfolio.

    per_holding_scores: list of (risk_score, position_value) tuples.
    """
    valid = [(s, v) for s, v in per_holding_scores if s is not None and v]
    if not valid:
        return None
    total_value = sum(v for _, v in valid)
    if total_value == 0:
        return None
    return round(sum(s * v for s, v in valid) / total_value, 1)
