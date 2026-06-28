"""yfinance wrappers shared across the app.

All network calls are cached with @st.cache_data so pages stay snappy and
avoid hammering Yahoo Finance.
"""

from __future__ import annotations

import datetime as dt

import pandas as pd
import streamlit as st
import yfinance as yf

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Real indices / futures / FX, not ETF proxies - used on Market Pulse + charts.
INDEX_TICKERS = {
    "^GSPC": "S&P 500",
    "^NDX": "Nasdaq 100",
    "^DJI": "Dow Jones",
    "^RUT": "Russell 2000",
    "^VIX": "VIX",
    "^TNX": "10Y Yield",
    "GC=F": "Gold",
    "CL=F": "Crude Oil (WTI)",
    "BTC-USD": "Bitcoin",
    "DX-Y.NYB": "US Dollar Index",
}

# The 11 SPDR sector ETFs.
SECTOR_ETFS = {
    "XLK": "Technology",
    "XLF": "Financials",
    "XLV": "Health Care",
    "XLE": "Energy",
    "XLI": "Industrials",
    "XLY": "Consumer Discretionary",
    "XLP": "Consumer Staples",
    "XLU": "Utilities",
    "XLRE": "Real Estate",
    "XLB": "Materials",
    "XLC": "Communication Services",
}

# Universe of widely-held large/mega-cap tickers used to compute "movers"
# (gainers / losers / most active) on the Market Pulse page.
MOVERS_UNIVERSE = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA", "AVGO", "ORCL", "ADBE",
    "CRM", "AMD", "INTC", "CSCO", "NFLX", "DIS", "UBER", "PYPL", "SHOP", "PLTR",
    "JPM", "BAC", "WFC", "GS", "MS", "V", "MA", "AXP", "BRK-B", "BLK",
    "UNH", "JNJ", "LLY", "PFE", "MRK", "ABBV", "TMO", "ABT",
    "WMT", "COST", "PG", "KO", "PEP", "MCD", "HD", "NKE", "TGT", "SBUX",
    "XOM", "CVX", "COP", "BA", "CAT", "GE", "HON", "LMT",
    "T", "VZ", "TMUS", "F", "GM", "COIN", "RBLX", "RIVN",
]

# Display names for tickers used across the app (indices, sector ETFs, and
# the movers universe) - avoids a slow per-ticker .info call just for a name.
NAME_MAP = {
    **INDEX_TICKERS,
    **SECTOR_ETFS,
    "AAPL": "Apple", "MSFT": "Microsoft", "GOOGL": "Alphabet", "AMZN": "Amazon",
    "META": "Meta Platforms", "NVDA": "NVIDIA", "TSLA": "Tesla", "AVGO": "Broadcom",
    "ORCL": "Oracle", "ADBE": "Adobe", "CRM": "Salesforce", "AMD": "AMD",
    "INTC": "Intel", "CSCO": "Cisco", "NFLX": "Netflix", "DIS": "Disney",
    "UBER": "Uber", "PYPL": "PayPal", "SHOP": "Shopify", "PLTR": "Palantir",
    "JPM": "JPMorgan Chase", "BAC": "Bank of America", "WFC": "Wells Fargo",
    "GS": "Goldman Sachs", "MS": "Morgan Stanley", "V": "Visa", "MA": "Mastercard",
    "AXP": "American Express", "BRK-B": "Berkshire Hathaway", "BLK": "BlackRock",
    "UNH": "UnitedHealth", "JNJ": "Johnson & Johnson", "LLY": "Eli Lilly",
    "PFE": "Pfizer", "MRK": "Merck", "ABBV": "AbbVie", "TMO": "Thermo Fisher",
    "ABT": "Abbott Labs",
    "WMT": "Walmart", "COST": "Costco", "PG": "Procter & Gamble", "KO": "Coca-Cola",
    "PEP": "PepsiCo", "MCD": "McDonald's", "HD": "Home Depot", "NKE": "Nike",
    "TGT": "Target", "SBUX": "Starbucks",
    "XOM": "Exxon Mobil", "CVX": "Chevron", "COP": "ConocoPhillips", "BA": "Boeing",
    "CAT": "Caterpillar", "GE": "GE Aerospace", "HON": "Honeywell", "LMT": "Lockheed Martin",
    "T": "AT&T", "VZ": "Verizon", "TMUS": "T-Mobile US", "F": "Ford", "GM": "General Motors",
    "COIN": "Coinbase", "RBLX": "Roblox", "RIVN": "Rivian",
}

# Period label -> yfinance period/interval configuration.
# When "yf_period" is set we use yfinance's built-in period string (cheapest).
# Otherwise we compute a start date "days" ago and request "interval" data.
PERIOD_MAP = {
    "1D": {"yf_period": "1d", "interval": "5m", "days": 1},
    "5D": {"yf_period": "5d", "interval": "15m", "days": 5},
    "1M": {"yf_period": "1mo", "interval": "1d", "days": 30},
    "3M": {"yf_period": "3mo", "interval": "1d", "days": 91},
    "6M": {"yf_period": "6mo", "interval": "1d", "days": 182},
    "YTD": {"yf_period": "ytd", "interval": "1d", "days": None},
    "1Y": {"yf_period": "1y", "interval": "1d", "days": 365},
    "3Y": {"yf_period": None, "interval": "1d", "days": 365 * 3},
    "5Y": {"yf_period": "5y", "interval": "1d", "days": 365 * 5},
    "10Y": {"yf_period": "10y", "interval": "1wk", "days": 365 * 10},
    "20Y": {"yf_period": None, "interval": "1wk", "days": 365 * 20},
    "30Y": {"yf_period": None, "interval": "1wk", "days": 365 * 30},
    "Max": {"yf_period": "max", "interval": "1mo", "days": None},
}

# TradingView-style timeframe selector for the Stock Analyzer chart.
# "resample" (when set) is applied to the raw yfinance bars to build
# intervals yfinance doesn't offer natively.
TIMEFRAMES = {
    "1m": {"yf_period": "7d", "interval": "1m", "resample": None},
    "2m": {"yf_period": "60d", "interval": "2m", "resample": None},
    "5m": {"yf_period": "60d", "interval": "5m", "resample": None},
    "15m": {"yf_period": "60d", "interval": "15m", "resample": None},
    "30m": {"yf_period": "60d", "interval": "30m", "resample": None},
    "60m": {"yf_period": "60d", "interval": "60m", "resample": None},
    "90m": {"yf_period": "60d", "interval": "90m", "resample": None},
    "1d": {"yf_period": "2y", "interval": "1d", "resample": None},
    "1wk": {"yf_period": "10y", "interval": "1wk", "resample": None},
    "1mo": {"yf_period": "max", "interval": "1mo", "resample": None},
}


# ---------------------------------------------------------------------------
# Quotes
# ---------------------------------------------------------------------------

def _empty_quote(ticker: str) -> dict:
    return {
        "ticker": ticker,
        "price": None,
        "prev_close": None,
        "change": None,
        "pct_change": None,
        "name": NAME_MAP.get(ticker, ticker),
        "currency": "USD",
        "volume": None,
    }


def _quote_from_intraday(ticker: str, df: pd.DataFrame | None) -> dict:
    """Derive a quote dict from a slice of intraday OHLCV bars covering the
    last few sessions (as returned by a batched yf.download call).
    """
    if df is None or df.empty:
        return _empty_quote(ticker)

    df = df.dropna(subset=["Close"])
    if df.empty:
        return _empty_quote(ticker)

    sessions = sorted(set(df.index.date))
    last_session = sessions[-1]
    last_df = df[df.index.date == last_session]

    price = float(last_df["Close"].iloc[-1])
    volume = float(last_df["Volume"].sum()) if "Volume" in last_df.columns else None

    prev_close = None
    if len(sessions) >= 2:
        prev_df = df[df.index.date == sessions[-2]]
        if not prev_df.empty:
            prev_close = float(prev_df["Close"].iloc[-1])
    if prev_close is None:
        prev_close = float(last_df["Open"].iloc[0])

    change = price - prev_close
    pct_change = (change / prev_close) * 100 if prev_close else None

    return {
        "ticker": ticker,
        "price": price,
        "prev_close": prev_close,
        "change": change,
        "pct_change": pct_change,
        "name": NAME_MAP.get(ticker, ticker),
        "currency": "USD",
        "volume": volume,
    }


@st.cache_data(ttl=60, show_spinner=False)
def get_quotes_bulk(tickers: tuple) -> dict:
    """Return {ticker: quote_dict} for many tickers via a single batched
    download (fast, even for dozens of tickers).
    """
    tickers = list(dict.fromkeys(tickers))  # de-dupe, preserve order
    if not tickers:
        return {}

    try:
        data = yf.download(
            tickers, period="5d", interval="15m", group_by="ticker",
            threads=True, progress=False, auto_adjust=False,
        )
    except Exception:
        data = None

    result = {}
    for t in tickers:
        df = None
        if data is not None and not data.empty:
            try:
                df = data[t]
            except (KeyError, TypeError):
                df = None
        result[t] = _quote_from_intraday(t, df)

    return result


@st.cache_data(ttl=60, show_spinner=False)
def get_quote(ticker: str) -> dict:
    """Return a snapshot quote for a single ticker."""
    return get_quotes_bulk((ticker,))[ticker]


@st.cache_data(ttl=60, show_spinner=False)
def get_movers(universe: tuple, top_n: int = 5) -> dict:
    """Return {gainers, losers, most_active} lists of quote dicts for the
    given ticker universe, each sorted appropriately and trimmed to top_n.
    """
    quotes = get_quotes_bulk(universe)
    valid = [q for q in quotes.values() if q.get("price") is not None and q.get("pct_change") is not None]

    gainers = sorted(valid, key=lambda q: q["pct_change"], reverse=True)[:top_n]
    losers = sorted(valid, key=lambda q: q["pct_change"])[:top_n]

    with_volume = [q for q in valid if q.get("volume")]
    most_active = sorted(with_volume, key=lambda q: q["volume"], reverse=True)[:top_n]

    return {"gainers": gainers, "losers": losers, "most_active": most_active}


# ---------------------------------------------------------------------------
# History
# ---------------------------------------------------------------------------

@st.cache_data(ttl=300, show_spinner=False)
def get_history(ticker: str, period_label: str) -> pd.DataFrame:
    """Return OHLCV history for a ticker over the given PERIOD_MAP label."""
    cfg = PERIOD_MAP.get(period_label, PERIOD_MAP["1Y"])
    tk = yf.Ticker(ticker)
    try:
        if cfg["yf_period"]:
            df = tk.history(period=cfg["yf_period"], interval=cfg["interval"])
        else:
            start = dt.datetime.now() - dt.timedelta(days=cfg["days"])
            df = tk.history(start=start, interval=cfg["interval"])
    except Exception:
        df = pd.DataFrame()

    if df is None:
        df = pd.DataFrame()
    return df


@st.cache_data(ttl=300, show_spinner=False)
def get_history_tf(ticker: str, timeframe: str) -> pd.DataFrame:
    """Return OHLCV history for a ticker over the given TIMEFRAMES label."""
    cfg = TIMEFRAMES.get(timeframe, TIMEFRAMES["1d"])
    tk = yf.Ticker(ticker)
    try:
        df = tk.history(period=cfg["yf_period"], interval=cfg["interval"])
    except Exception:
        df = pd.DataFrame()

    if df is None:
        df = pd.DataFrame()

    if not df.empty and cfg["resample"]:
        df = df.resample(cfg["resample"]).agg({
            "Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum",
        }).dropna(subset=["Close"])

    return df


@st.cache_data(ttl=300, show_spinner=False)
def get_prev_close(ticker: str) -> float | None:
    """Return the previous trading day's close - used as 1D chart baseline."""
    try:
        tk = yf.Ticker(ticker)
        fast = tk.fast_info
        pc = fast.get("previousClose") or fast.get("previous_close")
        if pc:
            return float(pc)
        hist = tk.history(period="5d", interval="1d")
        if len(hist) >= 2:
            return float(hist["Close"].iloc[-2])
        if len(hist) == 1:
            return float(hist["Close"].iloc[-1])
    except Exception:
        pass
    return None


@st.cache_data(ttl=300, show_spinner=False)
def get_history_bulk(tickers: tuple, period_label: str) -> dict:
    """Return {ticker: DataFrame} of history for many tickers."""
    return {t: get_history(t, period_label) for t in tickers}


# ---------------------------------------------------------------------------
# Fundamentals / ETF details
# ---------------------------------------------------------------------------

@st.cache_data(ttl=300, show_spinner=False)
def is_etf(ticker: str) -> bool:
    try:
        info = yf.Ticker(ticker).info
        return (info.get("quoteType") or "").upper() == "ETF"
    except Exception:
        return False


@st.cache_data(ttl=300, show_spinner=False)
def get_stock_fundamentals(ticker: str) -> dict:
    """Return a curated dict of fundamentals/metadata for a stock."""
    tk = yf.Ticker(ticker)
    try:
        info = tk.info
    except Exception:
        info = {}

    return {
        "ticker": ticker,
        "name": info.get("shortName") or info.get("longName") or ticker,
        "sector": info.get("sector"),
        "industry": info.get("industry"),
        "website": info.get("website"),
        "summary": info.get("longBusinessSummary"),
        "price": info.get("currentPrice") or info.get("regularMarketPrice"),
        "market_cap": info.get("marketCap"),
        "trailing_pe": info.get("trailingPE"),
        "forward_pe": info.get("forwardPE"),
        "peg_ratio": info.get("trailingPegRatio"),
        "price_to_book": info.get("priceToBook"),
        "price_to_sales": info.get("priceToSalesTrailing12Months"),
        "beta": info.get("beta"),
        "dividend_yield": info.get("dividendYield"),
        "profit_margin": info.get("profitMargins"),
        "operating_margin": info.get("operatingMargins"),
        "gross_margin": info.get("grossMargins"),
        "return_on_equity": info.get("returnOnEquity"),
        "return_on_assets": info.get("returnOnAssets"),
        "debt_to_equity": info.get("debtToEquity"),
        "current_ratio": info.get("currentRatio"),
        "quick_ratio": info.get("quickRatio"),
        "revenue": info.get("totalRevenue"),
        "revenue_growth": info.get("revenueGrowth"),
        "earnings_growth": info.get("earningsGrowth"),
        "eps_ttm": info.get("trailingEps"),
        "eps_forward": info.get("forwardEps"),
        "fifty_two_week_low": info.get("fiftyTwoWeekLow"),
        "fifty_two_week_high": info.get("fiftyTwoWeekHigh"),
        "fifty_day_avg": info.get("fiftyDayAverage"),
        "two_hundred_day_avg": info.get("twoHundredDayAverage"),
        "avg_volume": info.get("averageVolume"),
        "volume": info.get("volume") or info.get("regularMarketVolume"),
        "shares_outstanding": info.get("sharesOutstanding"),
        "float_shares": info.get("floatShares"),
        "held_by_insiders": info.get("heldPercentInsiders"),
        "held_by_institutions": info.get("heldPercentInstitutions"),
        "target_mean_price": info.get("targetMeanPrice"),
        "recommendation_mean": info.get("recommendationMean"),
        "number_of_analysts": info.get("numberOfAnalystOpinions"),
        "exchange": info.get("exchange"),
        "currency": info.get("currency", "USD"),
    }


@st.cache_data(ttl=300, show_spinner=False)
def get_etf_details(ticker: str) -> dict:
    """Return ETF metadata: expense ratio, sector weights, top holdings, returns."""
    tk = yf.Ticker(ticker)
    try:
        info = tk.info
    except Exception:
        info = {}

    sector_weights = {}
    top_holdings = []
    try:
        funds = tk.funds_data
        sw = funds.sector_weightings
        if sw:
            sector_weights = sw
        th = funds.top_holdings
        if th is not None and not th.empty:
            for sym, row in th.iterrows():
                top_holdings.append({
                    "symbol": sym,
                    "name": row.get("Name", sym),
                    "weight": row.get("Holding Percent", 0.0),
                })
    except Exception:
        pass

    return {
        "ticker": ticker,
        "name": info.get("shortName") or info.get("longName") or ticker,
        "category": info.get("category"),
        "expense_ratio": info.get("netExpenseRatio") or info.get("annualReportExpenseRatio"),
        "ytd_return": info.get("ytdReturn"),
        "three_year_avg_return": info.get("threeYearAverageReturn"),
        "five_year_avg_return": info.get("fiveYearAverageReturn"),
        "beta_3y": info.get("beta3Year"),
        "total_assets": info.get("totalAssets"),
        "sector_weights": sector_weights,
        "top_holdings": top_holdings,
        "price": info.get("navPrice") or info.get("regularMarketPrice"),
    }


# ---------------------------------------------------------------------------
# Options chain
# ---------------------------------------------------------------------------

@st.cache_data(ttl=300, show_spinner=False)
def get_option_expirations(ticker: str) -> tuple:
    """Return available option expiration date strings (YYYY-MM-DD)."""
    try:
        return tuple(yf.Ticker(ticker).options)
    except Exception:
        return ()


@st.cache_data(ttl=300, show_spinner=False)
def get_option_chain(ticker: str, expiration: str) -> dict:
    """Return {"calls": DataFrame, "puts": DataFrame} for the given expiration."""
    try:
        chain = yf.Ticker(ticker).option_chain(expiration)
        return {"calls": chain.calls, "puts": chain.puts}
    except Exception:
        return {"calls": pd.DataFrame(), "puts": pd.DataFrame()}


# ---------------------------------------------------------------------------
# Valuation data
# ---------------------------------------------------------------------------

@st.cache_data(ttl=300, show_spinner=False)
def get_valuation_data(ticker: str) -> dict:
    """Fetch raw data needed for the Valuation section.

    Returns a dict with keys:
        info              – yfinance .info dict
        quarterly_income  – quarterly income statement DataFrame
        quarterly_cashflow – quarterly cash flow DataFrame
        quarterly_balance – quarterly balance sheet DataFrame
        annual_income     – annual income statement DataFrame
        price_history     – 2-year daily OHLCV DataFrame
    """
    tk = yf.Ticker(ticker)
    try:
        info = tk.info
    except Exception:
        info = {}

    def _safe(fn):
        try:
            result = fn()
            return result if result is not None else pd.DataFrame()
        except Exception:
            return pd.DataFrame()

    return {
        "info": info,
        "quarterly_income": _safe(lambda: tk.quarterly_income_stmt),
        "quarterly_cashflow": _safe(lambda: tk.quarterly_cashflow),
        "quarterly_balance": _safe(lambda: tk.quarterly_balance_sheet),
        "annual_income": _safe(lambda: tk.income_stmt),
        "price_history": _safe(lambda: tk.history(period="2y", interval="1d")),
    }
