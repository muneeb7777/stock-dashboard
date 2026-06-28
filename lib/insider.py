"""SEC EDGAR Form 4 (insider transaction) feed helpers.

Pulls the system-wide "latest filings" feed for Form 4, then opens each
filing's index page to locate and parse the underlying ownership XML for
open-market purchase (P) / sale (S) transactions.
"""

from __future__ import annotations

import concurrent.futures
import datetime as dt
import re
import xml.etree.ElementTree as ET

import pandas as pd
import requests
import streamlit as st

HEADERS = {"User-Agent": "Stock Market Analyst research@example.com"}

CURRENT_FEED_URL = (
    "https://www.sec.gov/cgi-bin/browse-edgar"
    "?action=getcurrent&type=4&company=&dateb=&owner=include&count={count}&output=atom"
)

TICKER_SEARCH_URL = (
    "https://efts.sec.gov/LATEST/search-index"
    "?q=%22{ticker}%22&forms=4&dateRange=custom&startdt={startdt}&enddt={enddt}"
)

ATOM_NS = {"a": "http://www.w3.org/2005/Atom"}

TRANSACTION_LABELS = {"P": "Buy", "S": "Sell"}

MIN_SIZE_OPTIONS = {
    "Any size": 0,
    "$100K+": 100_000,
    "$500K+": 500_000,
    "$1M+": 1_000_000,
}


@st.cache_data(ttl=300, show_spinner=False)
def _recent_form4_filings(count: int = 60) -> list[dict]:
    """Return recent Form 4 accessions with issuer + reporting-owner names."""
    url = CURRENT_FEED_URL.format(count=count)
    root = None
    for attempt in range(2):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            resp.raise_for_status()
            root = ET.fromstring(resp.content)
            break
        except Exception:
            continue
    if root is None:
        return []

    by_accession: dict[str, dict] = {}

    for entry in root.findall("a:entry", ATOM_NS):
        title = entry.findtext("a:title", default="", namespaces=ATOM_NS) or ""
        summary = entry.findtext("a:summary", default="", namespaces=ATOM_NS) or ""
        link_el = entry.find("a:link", ATOM_NS)
        href = link_el.get("href") if link_el is not None else None
        if not href:
            continue

        match = re.match(r"4\s*-\s*(.+?)\s*\(\d+\)\s*\((Reporting|Issuer)\)", title)
        if not match:
            continue
        name, role = match.groups()

        acc_match = re.search(r"/(\d{10}-\d{2}-\d{6})-index\.htm", href)
        accession = acc_match.group(1) if acc_match else href

        index_url = href if href.startswith("http") else "https://www.sec.gov" + href
        entry_data = by_accession.setdefault(
            accession, {"accession": accession, "index_url": index_url, "filed": None}
        )

        if role == "Issuer":
            entry_data["issuer_name"] = name
        else:
            entry_data["owner_name"] = name

        if entry_data["filed"] is None:
            filed_match = re.search(r"<b>Filed:</b>\s*(\d{4}-\d{2}-\d{2})", summary)
            if filed_match:
                entry_data["filed"] = filed_match.group(1)

    return list(by_accession.values())


@st.cache_data(ttl=600, show_spinner=False)
def _filing_xml_url(index_url: str) -> str | None:
    """Find the raw ownership XML document linked from a filing's index page."""
    try:
        resp = requests.get(index_url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
    except Exception:
        return None

    candidates = re.findall(r'href="([^"]+\.xml)"', resp.text)
    candidates = [c for c in candidates if "xslF345" not in c]
    if not candidates:
        return None

    href = candidates[0]
    return href if href.startswith("http") else "https://www.sec.gov" + href


@st.cache_data(ttl=600, show_spinner=False)
def _parse_form4_transactions(xml_url: str) -> list[dict]:
    """Parse open-market buy/sell transactions out of a Form 4 ownership XML."""
    try:
        resp = requests.get(xml_url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
    except Exception:
        return []

    issuer = root.find("issuer")
    if issuer is None:
        return []
    issuer_name = (issuer.findtext("issuerName") or "").strip()
    ticker = (issuer.findtext("issuerTradingSymbol") or "").strip().upper()

    owner = root.find("reportingOwner")
    owner_name = ""
    title_parts: list[str] = []
    if owner is not None:
        owner_name = (owner.findtext("reportingOwnerId/rptOwnerName") or "").strip()
        rel = owner.find("reportingOwnerRelationship")
        if rel is not None:
            if (rel.findtext("isDirector") or "").strip().lower() == "true":
                title_parts.append("Director")
            officer_title = (rel.findtext("officerTitle") or "").strip()
            if officer_title:
                title_parts.append(officer_title)
            if (rel.findtext("isTenPercentOwner") or "").strip().lower() == "true":
                title_parts.append("10% Owner")
            other_text = (rel.findtext("otherText") or "").strip()
            if other_text and other_text not in title_parts:
                title_parts.append(other_text)
    title = ", ".join(title_parts) or "—"

    rows = []
    for tx in root.findall(".//nonDerivativeTransaction"):
        code = (tx.findtext("transactionCoding/transactionCode") or "").strip()
        if code not in TRANSACTION_LABELS:
            continue

        shares_raw = tx.findtext("transactionAmounts/transactionShares/value")
        price_raw = tx.findtext("transactionAmounts/transactionPricePerShare/value")
        date_raw = tx.findtext("transactionDate/value")
        try:
            shares = float(shares_raw)
            price = float(price_raw)
        except (TypeError, ValueError):
            continue

        rows.append(
            {
                "Date": date_raw,
                "Company": issuer_name,
                "Ticker": ticker,
                "Insider": owner_name,
                "Title": title,
                "Type": TRANSACTION_LABELS[code],
                "Shares": shares,
                "Price": price,
                "Total Value": shares * price,
            }
        )

    return rows


def _fetch_filing_rows(filing: dict) -> list[dict]:
    """Resolve a filing's ownership XML and parse its buy/sell transactions."""
    xml_url = _filing_xml_url(filing["index_url"])
    if not xml_url:
        return []
    rows = _parse_form4_transactions(xml_url)
    for row in rows:
        row["Filed"] = filing.get("filed")
    return rows


def _search_hit_to_xml_url(hit: dict) -> str | None:
    """Build a Form 4 ownership XML URL from an EDGAR full-text-search hit."""
    hit_id = hit.get("_id", "")
    if ":" not in hit_id:
        return None
    accession, filename = hit_id.split(":", 1)
    ciks = hit.get("_source", {}).get("ciks") or []
    if not ciks:
        return None
    issuer_cik = ciks[-1].lstrip("0") or "0"
    accession_no_dashes = accession.replace("-", "")
    return f"https://www.sec.gov/Archives/edgar/data/{issuer_cik}/{accession_no_dashes}/{filename}"


@st.cache_data(ttl=600, show_spinner=False)
def search_insider_transactions(ticker: str, days: int = 30) -> pd.DataFrame:
    """Search SEC EDGAR full-text search for Form 4 filings mentioning `ticker`
    over the last `days` days, and return parsed buy/sell transactions."""
    columns = ["Date", "Company", "Ticker", "Insider", "Title", "Type", "Shares", "Price", "Total Value", "Filed"]

    today = dt.date.today()
    start = today - dt.timedelta(days=days)
    url = TICKER_SEARCH_URL.format(ticker=ticker, startdt=start.isoformat(), enddt=today.isoformat())

    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        hits = resp.json().get("hits", {}).get("hits", [])
    except Exception:
        return pd.DataFrame(columns=columns)

    xml_urls = [u for u in (_search_hit_to_xml_url(h) for h in hits) if u]
    if not xml_urls:
        return pd.DataFrame(columns=columns)

    rows: list[dict] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        for filing_rows in executor.map(_parse_form4_transactions, xml_urls):
            rows.extend(filing_rows)

    rows = [r for r in rows if r["Ticker"] == ticker]
    if not rows:
        return pd.DataFrame(columns=columns)

    df = pd.DataFrame(rows)
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df["Filed"] = df["Date"].dt.strftime("%Y-%m-%d")
    df = df.sort_values("Date", ascending=False, na_position="last").reset_index(drop=True)
    return df


@st.cache_data(ttl=300, show_spinner=False)
def fetch_insider_feed(filing_count: int = 60) -> pd.DataFrame:
    """Build a feed DataFrame of recent open-market insider buy/sell transactions."""
    filings = _recent_form4_filings(filing_count)

    rows: list[dict] = []
    if filings:
        # Each filing needs 2 sequential SEC requests (index page + XML doc);
        # fetch filings concurrently to keep the page responsive.
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            for filing_rows in executor.map(_fetch_filing_rows, filings):
                rows.extend(filing_rows)

    if not rows:
        return pd.DataFrame(
            columns=["Date", "Company", "Ticker", "Insider", "Title", "Type", "Shares", "Price", "Total Value", "Filed"]
        )

    df = pd.DataFrame(rows)
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.sort_values("Date", ascending=False, na_position="last").reset_index(drop=True)
    return df


def detect_cluster_buying(df: pd.DataFrame, min_insiders: int = 3) -> set[str]:
    """Tickers with `min_insiders` or more distinct insiders buying (within the feed window)."""
    if df.empty:
        return set()
    buys = df[df["Type"] == "Buy"]
    counts = buys.groupby("Ticker")["Insider"].nunique()
    return set(counts[counts >= min_insiders].index)


def hot_stocks(df: pd.DataFrame, top_n: int = 8) -> pd.DataFrame:
    """Tickers with the most insider *buy* transactions in the feed."""
    if df.empty:
        return pd.DataFrame(columns=["Ticker", "Buys", "Total Value"])
    buys = df[df["Type"] == "Buy"]
    if buys.empty:
        return pd.DataFrame(columns=["Ticker", "Buys", "Total Value"])
    grouped = (
        buys.groupby("Ticker")
        .agg(Buys=("Insider", "count"), **{"Total Value": ("Total Value", "sum")})
        .reset_index()
        .sort_values(["Buys", "Total Value"], ascending=False)
        .head(top_n)
    )
    return grouped
