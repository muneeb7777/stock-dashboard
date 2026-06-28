"""News helpers: per-ticker news and aggregated market headlines.

Primary source is yfinance's Ticker.news. If that comes back empty (it's
occasionally unreliable), we fall back to Yahoo Finance's public RSS feed.
"""

from __future__ import annotations

import datetime as dt
import xml.etree.ElementTree as ET

import requests
import streamlit as st
import yfinance as yf

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; StockMarketAnalyst/1.0)"}


def _extract_item(raw: dict) -> dict | None:
    """Normalize a yfinance news item (old or new schema) into a common dict."""
    # New schema (yfinance >= 0.2.4x) nests fields under "content".
    content = raw.get("content") if isinstance(raw.get("content"), dict) else raw

    title = content.get("title")
    if not title:
        return None

    link = None
    canonical = content.get("canonicalUrl") or content.get("clickThroughUrl")
    if isinstance(canonical, dict):
        link = canonical.get("url")
    link = link or raw.get("link")

    publisher = None
    provider = content.get("provider")
    if isinstance(provider, dict):
        publisher = provider.get("displayName")
    publisher = publisher or raw.get("publisher") or "Unknown"

    summary = content.get("summary") or content.get("description") or ""

    ts = None
    pub_date = content.get("pubDate") or content.get("displayTime")
    if pub_date:
        try:
            ts = dt.datetime.strptime(pub_date, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=dt.timezone.utc)
        except (ValueError, TypeError):
            ts = None
    if ts is None and raw.get("providerPublishTime"):
        try:
            ts = dt.datetime.fromtimestamp(raw["providerPublishTime"], tz=dt.timezone.utc)
        except (ValueError, OSError, TypeError):
            ts = None

    thumbnail = None
    thumb = content.get("thumbnail") or raw.get("thumbnail")
    if isinstance(thumb, dict):
        resolutions = thumb.get("resolutions") or []
        if resolutions:
            thumbnail = resolutions[0].get("url")
        else:
            thumbnail = thumb.get("originalUrl")

    return {
        "title": title,
        "link": link,
        "publisher": publisher,
        "summary": summary,
        "time": ts,
        "thumbnail": thumbnail,
    }


@st.cache_data(ttl=300, show_spinner=False)
def _yf_news(ticker: str, limit: int) -> list[dict]:
    try:
        raw_items = yf.Ticker(ticker).news or []
    except Exception:
        raw_items = []

    items = []
    for raw in raw_items:
        item = _extract_item(raw)
        if item:
            items.append(item)
    return items[:limit]


@st.cache_data(ttl=300, show_spinner=False)
def _rss_news(ticker: str | None, limit: int) -> list[dict]:
    if ticker:
        url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}&region=US&lang=en-US"
    else:
        url = "https://feeds.finance.yahoo.com/rss/2.0/headline?s=%5EGSPC&region=US&lang=en-US"

    try:
        resp = requests.get(url, headers=HEADERS, timeout=8)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
    except Exception:
        return []

    items = []
    for item in root.findall(".//item")[:limit]:
        title = item.findtext("title") or ""
        link = item.findtext("link") or ""
        pub_date = item.findtext("pubDate")
        publisher = item.findtext("source") or "Yahoo Finance"
        summary = item.findtext("description") or ""

        ts = None
        if pub_date:
            for fmt in ("%a, %d %b %Y %H:%M:%S %z", "%a, %d %b %Y %H:%M:%S %Z"):
                try:
                    ts = dt.datetime.strptime(pub_date, fmt)
                    if ts.tzinfo is None:
                        ts = ts.replace(tzinfo=dt.timezone.utc)
                    break
                except ValueError:
                    continue

        items.append({
            "title": title,
            "link": link,
            "publisher": publisher,
            "summary": summary,
            "time": ts,
            "thumbnail": None,
        })

    return items


def ticker_news(ticker: str, limit: int = 10) -> list[dict]:
    """Return recent news items for a single ticker."""
    items = _yf_news(ticker, limit)
    if not items:
        items = _rss_news(ticker, limit)
    return items[:limit]


def market_news(limit: int = 10) -> list[dict]:
    """Return aggregated, de-duplicated, time-sorted market headlines."""
    seen_titles = set()
    combined = []

    for ticker in ("^GSPC", "^DJI", "^NDX", "SPY"):
        for item in ticker_news(ticker, limit=8):
            key = item["title"].strip().lower()
            if key in seen_titles:
                continue
            seen_titles.add(key)
            combined.append(item)

    if not combined:
        combined = _rss_news(None, limit)

    combined.sort(key=lambda i: i["time"] or dt.datetime(1970, 1, 1, tzinfo=dt.timezone.utc), reverse=True)
    return combined[:limit]


def headlines_last_24h(items: list[dict], limit: int = 3) -> list[dict]:
    """Filter to items published within the last 24 hours (falls back to most recent)."""
    now = dt.datetime.now(dt.timezone.utc)
    recent = [i for i in items if i["time"] and (now - i["time"]) <= dt.timedelta(hours=24)]
    return (recent or items)[:limit]


def time_ago(timestamp: dt.datetime | None) -> str:
    if timestamp is None:
        return ""
    now = dt.datetime.now(dt.timezone.utc)
    delta = now - timestamp
    seconds = delta.total_seconds()
    if seconds < 3600:
        return f"{int(seconds // 60)}m ago"
    if seconds < 86400:
        return f"{int(seconds // 3600)}h ago"
    return f"{int(seconds // 86400)}d ago"
