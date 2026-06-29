"""Options flow helpers: unusual activity detection via yfinance option chains."""

from __future__ import annotations

import pandas as pd
import streamlit as st
import yfinance as yf

from lib.market_data import _YF_SESSION

WHALE_PREMIUM = 500_000


@st.cache_data(ttl=300, show_spinner=False)
def get_expirations(ticker: str) -> list[str]:
    try:
        return list(yf.Ticker(ticker, session=_YF_SESSION).options)
    except Exception:
        return []


@st.cache_data(ttl=300, show_spinner=False)
def get_option_chain(ticker: str, expiry: str) -> pd.DataFrame:
    try:
        chain = yf.Ticker(ticker, session=_YF_SESSION).option_chain(expiry)
    except Exception:
        return pd.DataFrame()

    calls = chain.calls.copy()
    puts = chain.puts.copy()
    calls["Type"] = "Call"
    puts["Type"] = "Put"
    combined = pd.concat([calls, puts], ignore_index=True)
    combined["Ticker"] = ticker
    combined["Expiry"] = expiry
    return combined


def _classify_sentiment(row) -> str:
    bid = row.get("bid") or 0
    ask = row.get("ask") or 0
    last = row.get("lastPrice") or 0
    is_call = row["Type"] == "Call"

    bought_near_ask = ask > 0 and last >= ask * 0.98
    sold_near_bid = bid > 0 and last <= bid * 1.02

    if bought_near_ask:
        return "Bullish" if is_call else "Bearish"
    if sold_near_bid:
        return "Bearish" if is_call else "Bullish"
    return "Bullish" if is_call else "Bearish"


def add_flow_metrics(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    df = df.copy()
    df["volume"] = df["volume"].fillna(0)
    df["openInterest"] = df["openInterest"].fillna(0)
    df["impliedVolatility"] = df["impliedVolatility"].fillna(0)

    df["Vol/OI"] = df.apply(
        lambda r: (r["volume"] / r["openInterest"]) if r["openInterest"] > 0 else (float("inf") if r["volume"] > 0 else 0.0),
        axis=1,
    )
    df["Premium"] = df["volume"] * df["lastPrice"] * 100
    df["Sentiment"] = df.apply(_classify_sentiment, axis=1)
    df["IV%"] = df["impliedVolatility"] * 100
    return df


@st.cache_data(ttl=300, show_spinner=False)
def unusual_activity(ticker: str, max_expiries: int = 6, min_ratio: float = 2.0, min_volume: int = 50) -> pd.DataFrame:
    """Options with volume >= min_ratio x open interest across the next few expiries."""
    expiries = get_expirations(ticker)[:max_expiries]
    frames = [get_option_chain(ticker, exp) for exp in expiries]
    frames = [f for f in frames if not f.empty]
    if not frames:
        return pd.DataFrame()

    all_opts = add_flow_metrics(pd.concat(frames, ignore_index=True))
    unusual = all_opts[(all_opts["Vol/OI"] >= min_ratio) & (all_opts["volume"] >= min_volume)]
    return unusual.sort_values("Premium", ascending=False).reset_index(drop=True)


@st.cache_data(ttl=300, show_spinner=False)
def put_call_ratio_by_expiry(ticker: str, max_expiries: int = 6) -> pd.DataFrame:
    expiries = get_expirations(ticker)[:max_expiries]
    rows = []
    for exp in expiries:
        chain = get_option_chain(ticker, exp)
        if chain.empty:
            continue
        call_vol = chain.loc[chain["Type"] == "Call", "volume"].fillna(0).sum()
        put_vol = chain.loc[chain["Type"] == "Put", "volume"].fillna(0).sum()
        ratio = (put_vol / call_vol) if call_vol > 0 else None
        rows.append({"Expiry": exp, "Call Volume": call_vol, "Put Volume": put_vol, "Put/Call Ratio": ratio})
    return pd.DataFrame(rows)


@st.cache_data(ttl=600, show_spinner=False)
def scan_market(tickers: tuple[str, ...], max_expiries: int = 2, min_ratio: float = 2.0, min_volume: int = 50) -> pd.DataFrame:
    """Scan a universe of tickers for unusual options activity (nearest expiries only)."""
    frames = []
    for ticker in tickers:
        try:
            df = unusual_activity(ticker, max_expiries=max_expiries, min_ratio=min_ratio, min_volume=min_volume)
        except Exception:
            df = pd.DataFrame()
        if not df.empty:
            frames.append(df)

    if not frames:
        return pd.DataFrame()

    return pd.concat(frames, ignore_index=True).sort_values("Premium", ascending=False).reset_index(drop=True)


def follow_the_money(df: pd.DataFrame, top_n: int = 5) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Net bullish/bearish premium by ticker -> top bullish and top bearish tables."""
    if df.empty:
        empty = pd.DataFrame(columns=["Ticker", "Bullish Premium", "Bearish Premium", "Net Premium"])
        return empty, empty

    pivot = (
        df.groupby(["Ticker", "Sentiment"])["Premium"]
        .sum()
        .unstack(fill_value=0)
        .reset_index()
    )
    for col in ("Bullish", "Bearish"):
        if col not in pivot.columns:
            pivot[col] = 0.0

    pivot = pivot.rename(columns={"Bullish": "Bullish Premium", "Bearish": "Bearish Premium"})
    pivot["Net Premium"] = pivot["Bullish Premium"] - pivot["Bearish Premium"]

    top_bullish = pivot.sort_values("Net Premium", ascending=False).head(top_n)
    top_bearish = pivot.sort_values("Net Premium", ascending=True).head(top_n)
    return top_bullish[["Ticker", "Bullish Premium", "Bearish Premium", "Net Premium"]], top_bearish[
        ["Ticker", "Bullish Premium", "Bearish Premium", "Net Premium"]
    ]
