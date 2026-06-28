"""FRED-backed macro indicators.

Requires FRED_API_KEY in .env. If missing, all functions return None /empty
so pages can show a friendly message instead of crashing.
"""

import streamlit as st

from lib.config import get_fred_key

# label -> (FRED series id, units, "level" or "yoy_pct")
MACRO_SERIES = {
    "Real GDP": ("GDPC1", "Billions of chained $", "level"),
    "Unemployment Rate": ("UNRATE", "%", "level"),
    "CPI (YoY)": ("CPIAUCSL", "%", "yoy_pct"),
    "Core CPI (YoY)": ("CPILFESL", "%", "yoy_pct"),
    "Fed Funds Rate": ("FEDFUNDS", "%", "level"),
    "10Y-2Y Treasury Spread": ("T10Y2Y", "pp", "level"),
    "Retail Sales (YoY)": ("RSAFS", "%", "yoy_pct"),
    "Industrial Production": ("INDPRO", "Index 2017=100", "level"),
}


@st.cache_resource(show_spinner=False)
def _get_fred_client():
    key = get_fred_key()
    if not key:
        return None
    try:
        from fredapi import Fred
        return Fred(api_key=key)
    except Exception:
        return None


def fred_available() -> bool:
    return _get_fred_client() is not None


@st.cache_data(ttl=3600, show_spinner=False)
def get_series(series_id: str):
    fred = _get_fred_client()
    if fred is None:
        return None
    try:
        return fred.get_series(series_id)
    except Exception:
        return None


@st.cache_data(ttl=3600, show_spinner=False)
def get_macro_snapshot() -> dict:
    """Return {label: {value, prior_value, date, units}} for MACRO_SERIES.

    For "yoy_pct" series, `value` is the year-over-year % change computed
    from the raw level series.
    """
    if not fred_available():
        return {}

    snapshot = {}
    for label, (series_id, units, kind) in MACRO_SERIES.items():
        series = get_series(series_id)
        if series is None or series.empty:
            continue
        series = series.dropna()
        if series.empty:
            continue

        if kind == "yoy_pct":
            if len(series) < 13:
                continue
            latest_date = series.index[-1]
            latest = series.iloc[-1]
            prior = series.iloc[-2] if len(series) > 1 else None
            yoy_latest = series.iloc[-13]
            value = (latest / yoy_latest - 1) * 100
            prior_value = None
            if prior is not None and len(series) > 13:
                yoy_prior = series.iloc[-14]
                prior_value = (prior / yoy_prior - 1) * 100
        else:
            latest_date = series.index[-1]
            value = float(series.iloc[-1])
            prior_value = float(series.iloc[-2]) if len(series) > 1 else None

        snapshot[label] = {
            "value": float(value),
            "prior_value": float(prior_value) if prior_value is not None else None,
            "date": latest_date,
            "units": units,
        }

    return snapshot
