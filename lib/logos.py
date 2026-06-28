"""Ticker -> company domain map and a base64 data-URL loader for local logo files.

Logos are downloaded ahead of time by scripts/fetch_logos.py into
assets/logos/<TICKER>.<ext> so the running app never makes a live request to
a third-party icon service.
"""

from __future__ import annotations

import base64
import os

ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "logos")

# Ticker -> primary company domain, used by scripts/fetch_logos.py to fetch
# favicons/apple-touch-icons, and as a hint for simple-icons slugs.
TICKER_DOMAINS = {
    # Mega-cap tech
    "AAPL": "apple.com",
    "MSFT": "microsoft.com",
    "GOOGL": "google.com",
    "GOOG": "google.com",
    "AMZN": "amazon.com",
    "META": "meta.com",
    "NVDA": "nvidia.com",
    "TSLA": "tesla.com",
    "AVGO": "broadcom.com",
    "ORCL": "oracle.com",
    "ADBE": "adobe.com",
    "CRM": "salesforce.com",
    "AMD": "amd.com",
    "INTC": "intel.com",
    "CSCO": "cisco.com",
    "IBM": "ibm.com",
    "QCOM": "qualcomm.com",
    "TXN": "ti.com",
    "NOW": "servicenow.com",
    "INTU": "intuit.com",
    "AMAT": "appliedmaterials.com",
    "MU": "micron.com",
    "ADI": "analog.com",
    "LRCX": "lamresearch.com",
    "PANW": "paloaltonetworks.com",
    "SNPS": "synopsys.com",
    "CDNS": "cadence.com",
    "PYPL": "paypal.com",
    "UBER": "uber.com",
    "ABNB": "airbnb.com",
    "SHOP": "shopify.com",
    "SQ": "block.xyz",
    "NFLX": "netflix.com",
    "DIS": "disney.com",
    "ROKU": "roku.com",
    "SPOT": "spotify.com",
    "SNAP": "snap.com",
    "PINS": "pinterest.com",
    "ZM": "zoom.us",
    "DOCU": "docusign.com",
    "CRWD": "crowdstrike.com",
    "ZS": "zscaler.com",
    "DDOG": "datadoghq.com",
    "NET": "cloudflare.com",
    "MDB": "mongodb.com",
    "TEAM": "atlassian.com",
    "WDAY": "workday.com",
    "OKTA": "okta.com",
    "TTD": "thetradedesk.com",
    "ASML": "asml.com",
    "ARM": "arm.com",
    "DELL": "dell.com",
    "HPQ": "hp.com",
    "HPE": "hpe.com",
    "STX": "seagate.com",
    "WDC": "westerndigital.com",
    "NXPI": "nxp.com",
    "MRVL": "marvell.com",
    "ON": "onsemi.com",
    "SWKS": "skyworksinc.com",
    "MCHP": "microchip.com",
    "FTNT": "fortinet.com",

    # Financials
    "JPM": "jpmorganchase.com",
    "BAC": "bankofamerica.com",
    "WFC": "wellsfargo.com",
    "GS": "goldmansachs.com",
    "MS": "morganstanley.com",
    "C": "citigroup.com",
    "BLK": "blackrock.com",
    "SCHW": "schwab.com",
    "AXP": "americanexpress.com",
    "V": "visa.com",
    "MA": "mastercard.com",
    "COF": "capitalone.com",
    "USB": "usbank.com",
    "PNC": "pnc.com",
    "TFC": "truist.com",
    "BK": "bnymellon.com",
    "SPGI": "spglobal.com",
    "ICE": "ice.com",
    "CME": "cmegroup.com",
    "MMC": "marshmclennan.com",
    "AIG": "aig.com",
    "MET": "metlife.com",
    "PRU": "prudential.com",
    "TRV": "travelers.com",
    "ALL": "allstate.com",
    "PGR": "progressive.com",
    "BRK-B": "berkshirehathaway.com",

    # Healthcare
    "UNH": "unitedhealthgroup.com",
    "JNJ": "jnj.com",
    "LLY": "lilly.com",
    "PFE": "pfizer.com",
    "MRK": "merck.com",
    "ABBV": "abbvie.com",
    "TMO": "thermofisher.com",
    "ABT": "abbott.com",
    "DHR": "danaher.com",
    "BMY": "bms.com",
    "AMGN": "amgen.com",
    "GILD": "gilead.com",
    "MDT": "medtronic.com",
    "CVS": "cvshealth.com",
    "CI": "cigna.com",
    "ELV": "elevancehealth.com",
    "ISRG": "intuitive.com",
    "VRTX": "vrtx.com",
    "REGN": "regeneron.com",
    "ZTS": "zoetis.com",
    "BSX": "bostonscientific.com",
    "SYK": "stryker.com",
    "HCA": "hcahealthcare.com",

    # Consumer / Retail
    "WMT": "walmart.com",
    "COST": "costco.com",
    "PG": "pg.com",
    "KO": "coca-cola.com",
    "PEP": "pepsico.com",
    "MCD": "mcdonalds.com",
    "SBUX": "starbucks.com",
    "NKE": "nike.com",
    "HD": "homedepot.com",
    "LOW": "lowes.com",
    "TGT": "target.com",
    "TJX": "tjx.com",
    "BKNG": "booking.com",
    "MAR": "marriott.com",
    "CMG": "chipotle.com",
    "YUM": "yum.com",
    "EL": "elcompanies.com",
    "CL": "colgatepalmolive.com",
    "KMB": "kimberly-clark.com",
    "MDLZ": "mondelezinternational.com",
    "MNST": "monsterbevcorp.com",
    "KHC": "kraftheinzcompany.com",
    "GIS": "generalmills.com",
    "PM": "pmi.com",
    "MO": "altria.com",

    # Industrials / Energy
    "XOM": "exxonmobil.com",
    "CVX": "chevron.com",
    "COP": "conocophillips.com",
    "SLB": "slb.com",
    "OXY": "oxy.com",
    "BA": "boeing.com",
    "CAT": "caterpillar.com",
    "GE": "ge.com",
    "HON": "honeywell.com",
    "UPS": "ups.com",
    "FDX": "fedex.com",
    "LMT": "lockheedmartin.com",
    "RTX": "rtx.com",
    "DE": "deere.com",
    "MMM": "3m.com",
    "UNP": "unionpacific.com",
    "NOC": "northropgrumman.com",
    "GD": "gd.com",

    # Telecom / Media
    "T": "att.com",
    "VZ": "verizon.com",
    "TMUS": "t-mobile.com",
    "CMCSA": "comcastcorporation.com",
    "CHTR": "charter.com",

    # Utilities / Real Estate / Materials
    "NEE": "nexteraenergy.com",
    "DUK": "duke-energy.com",
    "SO": "southerncompany.com",
    "LIN": "linde.com",
    "AMT": "americantower.com",
    "PLD": "prologis.com",

    # Other notable
    "BABA": "alibaba.com",
    "PLTR": "palantir.com",
    "COIN": "coinbase.com",
    "RBLX": "roblox.com",
    "RIVN": "rivian.com",
    "LCID": "lucidmotors.com",
    "F": "ford.com",
    "GM": "gm.com",
}

# ETFs and indices typically don't have a useful favicon - map to issuer site.
ETF_DOMAINS = {
    "SPY": "ssga.com",
    "VOO": "vanguard.com",
    "VTI": "vanguard.com",
    "QQQ": "invesco.com",
    "IVV": "ishares.com",
    "DIA": "ssga.com",
    "IWM": "ishares.com",
    "XLK": "ssga.com",
    "XLF": "ssga.com",
    "XLV": "ssga.com",
    "XLE": "ssga.com",
    "XLI": "ssga.com",
    "XLY": "ssga.com",
    "XLP": "ssga.com",
    "XLU": "ssga.com",
    "XLRE": "ssga.com",
    "XLB": "ssga.com",
    "XLC": "ssga.com",
    "GLD": "ssga.com",
    "SLV": "ishares.com",
    "ARKK": "ark-funds.com",
    "VEA": "vanguard.com",
    "VWO": "vanguard.com",
    "AGG": "ishares.com",
    "BND": "vanguard.com",
    "TLT": "ishares.com",
}

ALL_DOMAINS = {**TICKER_DOMAINS, **ETF_DOMAINS}

_EXT_MIME = {
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".ico": "image/x-icon",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
}

_cache: dict[str, str | None] = {}


def get_logo_data_url(ticker: str) -> str | None:
    """Return a base64 data: URL for a locally cached logo, or None if missing."""
    ticker = ticker.upper()
    if ticker in _cache:
        return _cache[ticker]

    result = None
    if os.path.isdir(ASSETS_DIR):
        for ext, mime in _EXT_MIME.items():
            path = os.path.join(ASSETS_DIR, f"{ticker}{ext}")
            if os.path.isfile(path):
                with open(path, "rb") as f:
                    encoded = base64.b64encode(f.read()).decode("ascii")
                result = f"data:{mime};base64,{encoded}"
                break

    _cache[ticker] = result
    return result


def get_logo_or_placeholder(ticker: str) -> str:
    """Return a data URL, or a simple SVG placeholder with the ticker initial."""
    url = get_logo_data_url(ticker)
    if url:
        return url

    initial = (ticker[:1] or "?").upper()
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64">'
        f'<rect width="64" height="64" rx="12" fill="#30363d"/>'
        f'<text x="32" y="40" font-size="28" fill="#c9d1d9" '
        f'font-family="Arial" text-anchor="middle">{initial}</text></svg>'
    )
    encoded = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded}"
