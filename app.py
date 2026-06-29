import streamlit as st

from lib.config import APP_NAME, inject_base_style, render_footer
from lib.market_data import INDEX_TICKERS, get_quotes_bulk
from utils.theme import apply_theme, theme_sidebar

st.set_page_config(page_title=APP_NAME, page_icon="📈", layout="wide")
apply_theme()
inject_base_style()
theme_sidebar()

st.title("📈 Stock Market Analyst")
st.caption("A personal, educational market research dashboard.")

st.markdown(
    """
Welcome! This dashboard pulls live market data, fundamentals, macro
indicators, and news for **personal research and learning**. Use the pages
in the sidebar to explore:

- **💹 Market Pulse** - indices, sectors, movers, and headlines
- **🔍 Stock Analyzer** - fundamentals, technicals, and AI-assisted reading
- **🧺 ETF Analyzer** - holdings, sector exposure, and cost comparisons
- **🌍 Macro** - growth, inflation, employment, and rates
- **💼 Portfolio** - track your own holdings
- **📰 News** - aggregated and per-ticker headlines
- **📈 Live Chart** - real-time TradingView-style candlestick chart
- **🕴️ Insider Flow** - live SEC Form 4 insider buy/sell feed
- **🔬 Backtester** - test trading strategies against historical data
- **🔭 Stock Screener** - scan and filter a universe of liquid stocks
- **⚖️ Portfolio Optimizer** - mean-variance optimization and Monte Carlo simulation
"""
)

st.divider()
st.subheader("Quick market snapshot")

quotes = get_quotes_bulk(tuple(INDEX_TICKERS.keys()))

cols = st.columns(5)
for i, (ticker, name) in enumerate(INDEX_TICKERS.items()):
    q = quotes.get(ticker, {})
    price = q.get("price")
    pct = q.get("pct_change")

    with cols[i % 5]:
        if price is None:
            st.metric(name, "—")
        else:
            st.metric(
                name,
                f"{price:,.2f}",
                f"{pct:+.2f}%" if pct is not None else None,
            )

render_footer()
