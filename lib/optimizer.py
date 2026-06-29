"""Portfolio optimization helpers built on PyPortfolioOpt.

Educational mean-variance optimization over historical returns - not a
forecast or recommendation. Past returns/covariances are not predictive of
future performance.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf
from pypfopt import EfficientFrontier, expected_returns, risk_models

from lib.market_data import _YF_SESSION

TRADING_DAYS_PER_YEAR = 252


@st.cache_data(ttl=1800, show_spinner=False)
def fetch_price_history(tickers: tuple[str, ...], period: str = "2y") -> pd.DataFrame:
    """Adjusted close price history for `tickers`, aligned on common dates."""
    if not tickers:
        return pd.DataFrame()
    try:
        data = yf.download(list(tickers), period=period, auto_adjust=True, progress=False, session=_YF_SESSION)
    except Exception:
        return pd.DataFrame()

    if data.empty:
        return pd.DataFrame()

    if isinstance(data.columns, pd.MultiIndex):
        prices = data["Close"]
    else:
        prices = data[["Close"]]
        prices.columns = list(tickers)[:1]

    prices = prices.dropna(axis=1, how="all").dropna(axis=0, how="any")
    return prices


def optimize_portfolio(prices: pd.DataFrame) -> dict | None:
    """Return Max Sharpe / Min Volatility / Max Return portfolios for `prices`."""
    if prices.empty or prices.shape[1] < 2 or len(prices) < 30:
        return None

    mu = expected_returns.mean_historical_return(prices)
    cov = risk_models.sample_cov(prices)

    portfolios = {}

    ef = EfficientFrontier(mu, cov)
    ef.max_sharpe()
    portfolios["Max Sharpe"] = _summarize(ef)

    ef = EfficientFrontier(mu, cov)
    ef.min_volatility()
    portfolios["Min Volatility"] = _summarize(ef)

    ef = EfficientFrontier(mu, cov)
    try:
        ef.efficient_return(target_return=float(mu.max()) * 0.999)
        portfolios["Max Return"] = _summarize(ef)
    except Exception:
        portfolios["Max Return"] = None

    return {"mu": mu, "cov": cov, "portfolios": portfolios}


def _summarize(ef: EfficientFrontier) -> dict:
    weights = ef.clean_weights()
    ret, vol, sharpe = ef.portfolio_performance()
    return {
        "weights": {t: w for t, w in weights.items() if w > 0.0001},
        "expected_return": ret,
        "volatility": vol,
        "sharpe": sharpe,
    }


def efficient_frontier_points(mu: pd.Series, cov: pd.DataFrame, n_points: int = 30) -> pd.DataFrame:
    """Sample the efficient frontier as (Volatility, Return) points."""
    points = []
    lo, hi = float(mu.min()), float(mu.max())
    if hi <= lo:
        return pd.DataFrame(points)

    for target in np.linspace(lo, hi * 0.999, n_points):
        try:
            ef = EfficientFrontier(mu, cov)
            ef.efficient_return(target_return=target)
            ret, vol, _ = ef.portfolio_performance()
            points.append({"Return": ret, "Volatility": vol})
        except Exception:
            continue

    return pd.DataFrame(points)


def current_weights(holdings: list[dict], latest_prices: dict[str, float]) -> tuple[dict[str, float], float]:
    """Return (ticker -> weight, total market value) for current holdings."""
    values = {}
    for h in holdings:
        price = latest_prices.get(h["ticker"])
        if price is None:
            continue
        values[h["ticker"]] = h["shares"] * price

    total = sum(values.values())
    if total <= 0:
        return {}, 0.0
    return {t: v / total for t, v in values.items()}, total


def rebalance_suggestions(
    holdings: list[dict], latest_prices: dict[str, float], target_weights: dict[str, float], total_value: float
) -> list[dict]:
    """Suggested share changes to move from current holdings to `target_weights`."""
    suggestions = []
    held_tickers = {h["ticker"] for h in holdings}

    for h in holdings:
        ticker = h["ticker"]
        price = latest_prices.get(ticker)
        if not price:
            continue
        target_value = target_weights.get(ticker, 0.0) * total_value
        target_shares = target_value / price
        diff_shares = target_shares - h["shares"]
        diff_value = diff_shares * price
        if abs(diff_value) < 1.0:
            continue
        suggestions.append({
            "Ticker": ticker,
            "Action": "Add" if diff_shares > 0 else "Reduce",
            "Shares": abs(diff_shares),
            "Value": abs(diff_value),
        })

    for ticker, weight in target_weights.items():
        if ticker in held_tickers or weight < 0.001:
            continue
        price = latest_prices.get(ticker)
        if not price:
            continue
        target_shares = weight * total_value / price
        suggestions.append({
            "Ticker": ticker,
            "Action": "Add",
            "Shares": target_shares,
            "Value": target_shares * price,
        })

    return suggestions


def correlation_matrix(prices: pd.DataFrame) -> pd.DataFrame:
    return prices.pct_change().dropna().corr()


def monte_carlo_simulation(
    prices: pd.DataFrame, weights: dict[str, float], n_sims: int = 1000, n_days: int = 252, initial_value: float = 10_000.0
) -> np.ndarray:
    """Return an (n_days, n_sims) array of simulated portfolio values via
    geometric random walk using historical daily mean/volatility."""
    returns = prices.pct_change().dropna()
    cols = [c for c in prices.columns if c in weights]
    weight_vec = np.array([weights.get(c, 0.0) for c in cols])
    if weight_vec.sum() <= 0:
        weight_vec = np.ones(len(cols)) / len(cols) if cols else weight_vec

    portfolio_returns = returns[cols].dot(weight_vec)
    mu = portfolio_returns.mean()
    sigma = portfolio_returns.std()

    rng = np.random.default_rng()
    daily = rng.normal(mu, sigma, size=(n_days, n_sims))
    growth = np.cumprod(1 + daily, axis=0)
    return initial_value * growth
