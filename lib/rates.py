"""Treasury yield curve via FRED."""

import pandas as pd
import streamlit as st

from lib.macro import _get_fred_client, fred_available, get_series

# Maturity label -> FRED constant-maturity Treasury series id.
YIELD_CURVE_SERIES = {
    "1M": "DGS1MO",
    "3M": "DGS3MO",
    "6M": "DGS6MO",
    "1Y": "DGS1",
    "2Y": "DGS2",
    "3Y": "DGS3",
    "5Y": "DGS5",
    "7Y": "DGS7",
    "10Y": "DGS10",
    "20Y": "DGS20",
    "30Y": "DGS30",
}


@st.cache_data(ttl=3600, show_spinner=False)
def get_yield_curve() -> pd.DataFrame:
    """Return a DataFrame with columns [maturity, yield] for the latest
    available observation of each maturity. Empty if FRED isn't configured.
    """
    if not fred_available():
        return pd.DataFrame(columns=["maturity", "yield"])

    rows = []
    for label, series_id in YIELD_CURVE_SERIES.items():
        series = get_series(series_id)
        if series is None:
            continue
        series = series.dropna()
        if series.empty:
            continue
        rows.append({"maturity": label, "yield": float(series.iloc[-1])})

    return pd.DataFrame(rows)
