"""Stock screener: scans a fixed universe of liquid large/mega-cap names
and computes fundamental + technical metrics for filtering."""

from __future__ import annotations

import concurrent.futures

import pandas as pd
import streamlit as st

from lib.market_data import NAME_MAP, MOVERS_UNIVERSE, get_history, get_stock_fundamentals
from lib.signals import compute_rsi, macd_series

# 100 of the most liquid large/mega-cap US stocks (MOVERS_UNIVERSE plus
# additional liquid names across sectors not already covered there).
_EXTRA = [
    "QCOM", "TXN", "IBM", "NOW", "INTU", "AMAT", "MU", "LRCX", "ADI", "PANW",
    "SNOW", "SQ", "ABNB", "BKNG", "LOW", "CMCSA", "CHTR", "UPS", "NEE", "DUK",
    "SO", "LIN", "APD", "MDT", "BMY", "AMGN", "GILD", "CVS", "ELV", "SPGI",
    "ICE", "CME", "SCHW", "C", "PM", "MDLZ",
]

SCREENER_UNIVERSE = list(dict.fromkeys(MOVERS_UNIVERSE + _EXTRA))[:100]

PRESETS = {
    "Momentum Leaders": {
        "rsi_min": 55, "rsi_max": 80,
        "vs200_min": 0.0,
        "macd": "Bullish",
    },
    "Oversold Quality": {
        "rsi_max": 35,
        "profit_margin_min": 0.0,
        "revenue_growth_min": 0.0,
    },
    "Breakout Candidates": {
        "range_pos_min": 85.0,
        "dma50": "Above",
        "dma200": "Above",
    },
    "Value Stocks": {
        "pe_max": 18.0,
        "profit_margin_min": 0.08,
    },
}


def _scan_one(ticker: str) -> dict | None:
    fund = get_stock_fundamentals(ticker)
    hist = get_history(ticker, "1Y")
    if hist.empty or len(hist) < 30:
        return None

    close = hist["Close"]
    last = float(close.iloc[-1])
    prev = float(close.iloc[-2]) if len(close) >= 2 else last
    change_pct = (last / prev - 1) * 100 if prev else 0.0

    sma50 = close.rolling(50).mean().iloc[-1] if len(close) >= 50 else None
    sma200 = close.rolling(200).mean().iloc[-1] if len(close) >= 200 else None
    vs50 = (last / sma50 - 1) * 100 if sma50 and sma50 > 0 else None
    vs200 = (last / sma200 - 1) * 100 if sma200 and sma200 > 0 else None

    rsi = compute_rsi(close)

    macd_line, signal_line, _ = macd_series(close)
    macd_bullish = bool(macd_line.iloc[-1] > signal_line.iloc[-1]) if len(macd_line) else None

    window = close.tail(252) if len(close) >= 252 else close
    lo, hi = float(window.min()), float(window.max())
    range_pos = (last - lo) / (hi - lo) * 100 if hi > lo else None

    return {
        "Ticker": ticker,
        "Name": NAME_MAP.get(ticker, fund.get("name") or ticker),
        "Price": last,
        "Change%": change_pct,
        "Market Cap": fund.get("market_cap"),
        "P/E": fund.get("trailing_pe"),
        "RSI": rsi,
        "vs50DMA%": vs50,
        "vs200DMA%": vs200,
        "Range Position%": range_pos,
        "Revenue Growth": fund.get("revenue_growth"),
        "Profit Margin": fund.get("profit_margin"),
        "Beta": fund.get("beta"),
        "Volume": fund.get("volume"),
        "Avg Volume": fund.get("avg_volume"),
        "MACD Bullish": macd_bullish,
    }


@st.cache_data(ttl=1800, show_spinner=False)
def scan_universe(tickers: tuple[str, ...]) -> pd.DataFrame:
    """Scan `tickers` and return a DataFrame of fundamental + technical metrics."""
    rows = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        for row in executor.map(_scan_one, tickers):
            if row:
                rows.append(row)
    return pd.DataFrame(rows)


def apply_filters(df: pd.DataFrame, filters: dict) -> pd.DataFrame:
    """Apply a dict of filter values (see screener page for keys) to `df`."""
    out = df.copy()

    if "pe_min" in filters:
        out = out[(out["P/E"].isna()) | (out["P/E"] >= filters["pe_min"])]
    if "pe_max" in filters:
        out = out[(out["P/E"].isna()) | (out["P/E"] <= filters["pe_max"])]

    if "mcap_min" in filters:
        out = out[(out["Market Cap"].isna()) | (out["Market Cap"] >= filters["mcap_min"])]
    if "mcap_max" in filters:
        out = out[(out["Market Cap"].isna()) | (out["Market Cap"] <= filters["mcap_max"])]

    if "rsi_min" in filters:
        out = out[(out["RSI"].isna()) | (out["RSI"] >= filters["rsi_min"])]
    if "rsi_max" in filters:
        out = out[(out["RSI"].isna()) | (out["RSI"] <= filters["rsi_max"])]

    if "range_pos_min" in filters:
        out = out[(out["Range Position%"].isna()) | (out["Range Position%"] >= filters["range_pos_min"])]
    if "range_pos_max" in filters:
        out = out[(out["Range Position%"].isna()) | (out["Range Position%"] <= filters["range_pos_max"])]

    if "revenue_growth_min" in filters:
        out = out[(out["Revenue Growth"].isna()) | (out["Revenue Growth"] >= filters["revenue_growth_min"])]

    if "profit_margin_min" in filters:
        out = out[(out["Profit Margin"].isna()) | (out["Profit Margin"] >= filters["profit_margin_min"])]

    if "beta_min" in filters:
        out = out[(out["Beta"].isna()) | (out["Beta"] >= filters["beta_min"])]
    if "beta_max" in filters:
        out = out[(out["Beta"].isna()) | (out["Beta"] <= filters["beta_max"])]

    if "avg_volume_min" in filters:
        out = out[(out["Avg Volume"].isna()) | (out["Avg Volume"] >= filters["avg_volume_min"])]

    if filters.get("dma50") == "Above":
        out = out[out["vs50DMA%"] > 0]
    elif filters.get("dma50") == "Below":
        out = out[out["vs50DMA%"] < 0]

    if filters.get("dma200") == "Above":
        out = out[out["vs200DMA%"] > 0]
    elif filters.get("dma200") == "Below":
        out = out[out["vs200DMA%"] < 0]

    if filters.get("rsi_signal") == "Overbought (RSI > 70)":
        out = out[out["RSI"] > 70]
    elif filters.get("rsi_signal") == "Oversold (RSI < 30)":
        out = out[out["RSI"] < 30]

    if filters.get("macd") == "Bullish":
        out = out[out["MACD Bullish"] == True]  # noqa: E712
    elif filters.get("macd") == "Bearish":
        out = out[out["MACD Bullish"] == False]  # noqa: E712

    return out
