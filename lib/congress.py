"""Congressional stock trading disclosure helpers (House + Senate stock watchers)."""

from __future__ import annotations

import datetime as dt

import pandas as pd
import requests
import streamlit as st
import yfinance as yf

HEADERS = {"User-Agent": "Stock Market Analyst research@example.com"}

# Each list is tried in order; the first endpoint that returns valid JSON wins.
# The stock-watcher datasets are mirrored across a couple of S3 regions/endpoints,
# and any one of them can be temporarily unavailable.
HOUSE_URLS = [
    "https://house-stock-watcher-data.s3-us-west-2.amazonaws.com/data/all_transactions.json",
    "https://house-stock-watcher-data.s3-us-east-2.amazonaws.com/data/all_transactions.json",
    "https://house-stock-watcher-data.s3.amazonaws.com/data/all_transactions.json",
]
SENATE_URLS = [
    "https://senate-stock-watcher-data.s3-us-west-2.amazonaws.com/data/all_transactions.json",
    "https://senate-stock-watcher-data.s3-us-east-2.amazonaws.com/data/all_transactions.json",
    "https://senate-stock-watcher-data.s3.amazonaws.com/data/all_transactions.json",
]

# Best-effort party lookup for members frequently seen in trading trackers.
# Falls back to "—" (Unknown) for anyone not listed here, since neither
# source dataset reliably includes a party field.
PARTY_MAP = {
    "Nancy Pelosi": "D", "Dan Crenshaw": "R", "Marjorie Taylor Greene": "R",
    "Tommy Tuberville": "R", "Ro Khanna": "D", "Josh Gottheimer": "D",
    "Pat Fallon": "R", "Michael McCaul": "R", "Mark Green": "R",
    "Earl Blumenauer": "D", "Suzan DelBene": "D", "Kevin Hern": "R",
    "Marjorie Greene": "R", "Virginia Foxx": "R", "French Hill": "R",
    "Ro Khanna ": "D", "Markwayne Mullin": "R", "Susie Lee": "D",
    "Debbie Wasserman Schultz": "D", "Don Beyer": "D", " Husted Steve": "R",
    "John Curtis": "R", "Sheldon Whitehouse": "D", "Tom Carper": "D",
    "Robert Garcia": "D", "David Rouzer": "R", "Brian Higgins": "D",
    "Ronny Jackson": "R", "Garret Graves": "R", "Nicole Malliotakis": "R",
    "Mitt Romney": "R", "Markwayne  Mullin": "R", "Thomas Carper": "D",
    "John Boozman": "R", "Roger Marshall": "R", "Daniel Goldman": "D",
    "Bill Hagerty": "R", "Pete Sessions": "R", "Michael Burgess": "R",
}

AMOUNT_MIDPOINT = {
    "$1,001 - $15,000": 8_000,
    "$1,001 -$15,000": 8_000,
    "$15,001 - $50,000": 32_500,
    "$50,001 - $100,000": 75_000,
    "$100,001 - $250,000": 175_000,
    "$250,001 - $500,000": 375_000,
    "$500,001 - $1,000,000": 750_000,
    "$1,000,001 - $5,000,000": 3_000_000,
    "$5,000,001 - $25,000,000": 15_000_000,
    "$25,000,001 - $50,000,000": 37_500_000,
    "$50,000,001 - $100,000,000": 75_000_000,
    "Over $50,000,000": 50_000_000,
}


def _normalize_type(raw: str) -> str:
    raw = (raw or "").lower()
    if "purchase" in raw or raw == "buy":
        return "Buy"
    if "sale" in raw or raw == "sell":
        return "Sell"
    if "exchange" in raw:
        return "Exchange"
    return "Other"


@st.cache_data(ttl=3600, show_spinner=False)
def _fetch_json(urls: tuple[str, ...]) -> list[dict]:
    """Try each candidate URL in turn, returning the first valid JSON payload."""
    for url in urls:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=45)
            resp.raise_for_status()
            data = resp.json()
            if data:
                return data
        except Exception:
            continue
    return []


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_congress_trades() -> pd.DataFrame:
    """Combined, normalized House + Senate trading disclosures."""
    rows = []

    for raw in _fetch_json(tuple(HOUSE_URLS)):
        politician = raw.get("representative") or raw.get("senator") or "Unknown"
        rows.append(
            {
                "Politician": politician,
                "Chamber": "House",
                "Party": PARTY_MAP.get(politician, "—"),
                "Ticker": (raw.get("ticker") or "").strip().upper(),
                "Company": raw.get("asset_description") or "",
                "Transaction": _normalize_type(raw.get("type")),
                "Amount": raw.get("amount") or "",
                "Date Filed": raw.get("disclosure_date"),
                "Date Traded": raw.get("transaction_date"),
            }
        )

    for raw in _fetch_json(tuple(SENATE_URLS)):
        politician = raw.get("senator") or raw.get("representative") or "Unknown"
        rows.append(
            {
                "Politician": politician,
                "Chamber": "Senate",
                "Party": raw.get("party") or PARTY_MAP.get(politician, "—"),
                "Ticker": (raw.get("ticker") or "").strip().upper(),
                "Company": raw.get("asset_description") or "",
                "Transaction": _normalize_type(raw.get("type")),
                "Amount": raw.get("amount") or "",
                "Date Filed": raw.get("disclosure_date"),
                "Date Traded": raw.get("transaction_date"),
            }
        )

    if not rows:
        return pd.DataFrame(
            columns=["Politician", "Chamber", "Party", "Ticker", "Company", "Transaction", "Amount", "Date Filed", "Date Traded", "Amount Mid"]
        )

    df = pd.DataFrame(rows)
    df = df[df["Ticker"] != ""]
    df["Date Filed"] = pd.to_datetime(df["Date Filed"], errors="coerce")
    df["Date Traded"] = pd.to_datetime(df["Date Traded"], errors="coerce")
    df["Amount Mid"] = df["Amount"].map(lambda a: AMOUNT_MIDPOINT.get(a, 0))
    df = df.sort_values("Date Filed", ascending=False, na_position="last").reset_index(drop=True)
    return df


def most_traded_stocks(df: pd.DataFrame, top_n: int = 15) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["Ticker", "Trades"])
    counts = df.groupby("Ticker").size().reset_index(name="Trades")
    return counts.sort_values("Trades", ascending=False).head(top_n)


def most_active_traders(df: pd.DataFrame, top_n: int = 15) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["Politician", "Chamber", "Party", "Trades"])
    grouped = (
        df.groupby(["Politician", "Chamber", "Party"])
        .size()
        .reset_index(name="Trades")
        .sort_values("Trades", ascending=False)
        .head(top_n)
    )
    return grouped


@st.cache_data(ttl=3600, show_spinner=False)
def _price_on_or_after(ticker: str, date: str) -> float | None:
    """Closing price on the first trading day on/after `date`."""
    try:
        start = pd.Timestamp(date)
        end = start + pd.Timedelta(days=7)
        hist = yf.Ticker(ticker).history(start=start, end=end)
        if hist.empty:
            return None
        return float(hist["Close"].iloc[0])
    except Exception:
        return None


@st.cache_data(ttl=3600, show_spinner=False)
def _latest_price(ticker: str) -> float | None:
    try:
        hist = yf.Ticker(ticker).history(period="5d")
        if hist.empty:
            return None
        return float(hist["Close"].iloc[-1])
    except Exception:
        return None


def politician_returns(df: pd.DataFrame, max_trades_per_politician: int = 8) -> pd.DataFrame:
    """Average return since purchase for each politician's "Buy" trades.

    Limited to the most recent `max_trades_per_politician` purchases per
    politician to keep the number of price lookups manageable.
    """
    if df.empty:
        return pd.DataFrame(columns=["Politician", "Chamber", "Party", "Trades Scored", "Avg Return"])

    buys = df[(df["Transaction"] == "Buy") & df["Date Traded"].notna()].copy()
    buys = buys.sort_values("Date Traded", ascending=False)

    results = []
    for (politician, chamber, party), group in buys.groupby(["Politician", "Chamber", "Party"]):
        sample = group.head(max_trades_per_politician)
        returns = []
        for _, row in sample.iterrows():
            ticker = row["Ticker"]
            entry = _price_on_or_after(ticker, row["Date Traded"].strftime("%Y-%m-%d"))
            current = _latest_price(ticker)
            if entry and current and entry > 0:
                returns.append((current - entry) / entry)
        if returns:
            results.append(
                {
                    "Politician": politician,
                    "Chamber": chamber,
                    "Party": party,
                    "Trades Scored": len(returns),
                    "Avg Return": sum(returns) / len(returns),
                }
            )

    if not results:
        return pd.DataFrame(columns=["Politician", "Chamber", "Party", "Trades Scored", "Avg Return"])

    return pd.DataFrame(results).sort_values("Avg Return", ascending=False).reset_index(drop=True)
