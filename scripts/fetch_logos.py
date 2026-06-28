"""Download logos for the top ~125 US tickers/ETFs into assets/logos/<TICKER>.<ext>.

Tries, in order, for each ticker:
  1. simple-icons SVG via jsdelivr CDN (recolored to white for dark mode)
  2. vectorlogo.zone SVG
  3. apple-touch-icon.png from the company's domain
  4. Google's faviconV2 endpoint (size=256)
  5. DuckDuckGo's icon proxy

The first source that returns a usable image "wins" for that ticker.

Usage:
    python scripts/fetch_logos.py
"""

from __future__ import annotations

import os
import re
import sys

import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.logos import ALL_DOMAINS  # noqa: E402

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "logos")
TIMEOUT = 8
MIN_BYTES = 200  # below this we treat the response as a "not found" placeholder

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; StockMarketAnalyst/1.0)"}

# Manual overrides for simple-icons slugs that don't match the domain's
# second-level name (simple-icons uses lowercase, no spaces/punctuation).
SIMPLE_ICONS_SLUGS = {
    "AAPL": "apple",
    "MSFT": "microsoft",
    "GOOGL": "google",
    "GOOG": "google",
    "AMZN": "amazon",
    "META": "meta",
    "NVDA": "nvidia",
    "TSLA": "tesla",
    "ADBE": "adobe",
    "CRM": "salesforce",
    "AMD": "amd",
    "INTC": "intel",
    "CSCO": "cisco",
    "IBM": "ibm",
    "QCOM": "qualcomm",
    "PYPL": "paypal",
    "UBER": "uber",
    "ABNB": "airbnb",
    "SHOP": "shopify",
    "SQ": "block",
    "NFLX": "netflix",
    "DIS": "disney",
    "SPOT": "spotify",
    "SNAP": "snapchat",
    "PINS": "pinterest",
    "ZM": "zoom",
    "DOCU": "docusign",
    "CRWD": "crowdstrike",
    "ZS": "zscaler",
    "DDOG": "datadog",
    "NET": "cloudflare",
    "MDB": "mongodb",
    "TEAM": "atlassian",
    "WDAY": "workday",
    "OKTA": "okta",
    "ASML": "asml",
    "ARM": "arm",
    "DELL": "dell",
    "HPQ": "hp",
    "NXPI": "nxp",
    "V": "visa",
    "MA": "mastercard",
    "BABA": "alibabadotcom",
    "PLTR": "palantir",
    "COIN": "coinbase",
    "RBLX": "roblox",
    "F": "ford",
    "GM": "generalmotors",
    "GE": "generalelectric",
    "BA": "boeing",
    "T": "att",
    "VZ": "verizon",
    "TMUS": "tmobile",
}


def ensure_out_dir():
    os.makedirs(OUT_DIR, exist_ok=True)


def already_have(ticker: str) -> bool:
    for ext in (".svg", ".png", ".ico", ".jpg", ".jpeg", ".webp"):
        if os.path.isfile(os.path.join(OUT_DIR, f"{ticker}{ext}")):
            return True
    return False


def try_simple_icons(ticker: str) -> bytes | None:
    slug = SIMPLE_ICONS_SLUGS.get(ticker)
    if not slug:
        return None
    url = f"https://cdn.jsdelivr.net/npm/simple-icons@latest/icons/{slug}.svg"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        if resp.status_code == 200 and len(resp.content) > MIN_BYTES:
            svg = resp.text
            # Recolor for dark backgrounds: simple-icons ship with fill="#000" or
            # rely on currentColor - force white.
            svg = re.sub(r'fill="#[0-9A-Fa-f]{3,6}"', 'fill="#ffffff"', svg)
            if "fill=" not in svg:
                svg = svg.replace("<svg", '<svg fill="#ffffff"', 1)
            return svg.encode("utf-8")
    except requests.RequestException:
        pass
    return None


def try_vectorlogo_zone(ticker: str, domain: str) -> bytes | None:
    # vectorlogo.zone organizes by company slug, which we approximate from the
    # domain's second-level name. Best-effort; many will 404 and fall through.
    slug = domain.split(".")[0]
    candidates = [
        f"https://www.vectorlogo.zone/logos/{slug}/{slug}-icon.svg",
        f"https://www.vectorlogo.zone/logos/{slug}/{slug}-ar21.svg",
    ]
    for url in candidates:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
            if resp.status_code == 200 and len(resp.content) > MIN_BYTES and b"<svg" in resp.content[:200]:
                return resp.content
        except requests.RequestException:
            continue
    return None


def try_apple_touch_icon(domain: str) -> bytes | None:
    for url in (f"https://{domain}/apple-touch-icon.png", f"https://www.{domain}/apple-touch-icon.png"):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
            if resp.status_code == 200 and len(resp.content) > MIN_BYTES and resp.headers.get("content-type", "").startswith("image"):
                return resp.content
        except requests.RequestException:
            continue
    return None


def try_favicon_v2(domain: str) -> bytes | None:
    url = (
        "https://t1.gstatic.com/faviconV2"
        f"?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://{domain}&size=256"
    )
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        if resp.status_code == 200 and len(resp.content) > MIN_BYTES:
            return resp.content
    except requests.RequestException:
        pass
    return None


def try_duckduckgo(domain: str) -> bytes | None:
    url = f"https://icons.duckduckgo.com/ip3/{domain}.ico"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        if resp.status_code == 200 and len(resp.content) > MIN_BYTES:
            return resp.content
    except requests.RequestException:
        pass
    return None


def save(ticker: str, content: bytes, ext: str):
    path = os.path.join(OUT_DIR, f"{ticker}{ext}")
    with open(path, "wb") as f:
        f.write(content)
    print(f"  saved {ticker}{ext} ({len(content)} bytes)")


def fetch_one(ticker: str, domain: str):
    if already_have(ticker):
        print(f"{ticker}: already have a logo, skipping")
        return

    print(f"{ticker} ({domain}):")

    content = try_simple_icons(ticker)
    if content:
        save(ticker, content, ".svg")
        return

    content = try_vectorlogo_zone(ticker, domain)
    if content:
        save(ticker, content, ".svg")
        return

    content = try_apple_touch_icon(domain)
    if content:
        save(ticker, content, ".png")
        return

    content = try_favicon_v2(domain)
    if content:
        save(ticker, content, ".png")
        return

    content = try_duckduckgo(domain)
    if content:
        save(ticker, content, ".ico")
        return

    print(f"  no logo found for {ticker}")


def main():
    ensure_out_dir()
    for ticker, domain in ALL_DOMAINS.items():
        fetch_one(ticker, domain)


if __name__ == "__main__":
    main()
