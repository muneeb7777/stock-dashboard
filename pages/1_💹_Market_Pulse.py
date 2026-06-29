import streamlit as st

from lib.charts import render_price_chart, render_sparkline
from lib.config import APP_NAME, inject_base_style, render_footer
from lib.logos import get_logo_or_placeholder
from lib.market_data import (
    INDEX_TICKERS,
    MOVERS_UNIVERSE,
    PERIOD_MAP,
    SECTOR_ETFS,
    get_history,
    get_history_bulk,
    get_movers,
    get_prev_close,
    get_quotes_bulk,
)
from lib.news import headlines_last_24h, market_news, time_ago
from utils.theme import apply_dark_plotly

st.set_page_config(page_title=f"Market Pulse - {APP_NAME}", page_icon="💹", layout="wide")
inject_base_style()

st.title("💹 Market Pulse")

period = st.segmented_control(
    "Period", options=list(PERIOD_MAP.keys()), default="1D", key="pulse_period"
)
period = period or "1D"

# ---------------------------------------------------------------------------
# Index / asset cards with sparklines
# ---------------------------------------------------------------------------

st.subheader("Markets at a glance")

quotes = get_quotes_bulk(tuple(INDEX_TICKERS.keys()))
histories = get_history_bulk(tuple(INDEX_TICKERS.keys()), period)

tickers = list(INDEX_TICKERS.items())
for row_start in range(0, len(tickers), 5):
    cols = st.columns(5)
    for col, (ticker, name) in zip(cols, tickers[row_start:row_start + 5]):
        with col:
            with st.container(border=True):
                q = quotes.get(ticker, {})
                price = q.get("price")
                pct = q.get("pct_change")

                st.markdown(f"**{name}**")
                if price is not None:
                    st.markdown(f"### {price:,.2f}")
                    color = "green" if (pct or 0) >= 0 else "red"
                    sign = "+" if (pct or 0) >= 0 else ""
                    st.markdown(f":{color}[{sign}{pct:.2f}%]" if pct is not None else "—")
                else:
                    st.markdown("### —")

                hist = histories.get(ticker)
                baseline = None
                if period == "1D":
                    baseline = get_prev_close(ticker)
                fig = render_sparkline(hist, baseline_price=baseline)
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False}, key=f"spark_{ticker}_{period}")

# ---------------------------------------------------------------------------
# Big S&P 500 chart
# ---------------------------------------------------------------------------

st.divider()
st.subheader("S&P 500")

view = st.segmented_control(
    "Chart view", options=["Performance", "Price", "Candlestick", "Area"], default="Performance", key="pulse_spx_view"
)
view = view or "Performance"

spx_hist = get_history("^GSPC", period)
spx_baseline = get_prev_close("^GSPC") if period == "1D" else None
fig = render_price_chart(spx_hist, view=view, baseline_price=spx_baseline, height=520)
st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# ---------------------------------------------------------------------------
# Sector heatmap
# ---------------------------------------------------------------------------

st.divider()
st.subheader("Sector performance")

sector_quotes = get_quotes_bulk(tuple(SECTOR_ETFS.keys()))
sector_rows = []
for ticker, name in SECTOR_ETFS.items():
    q = sector_quotes.get(ticker, {})
    pct = q.get("pct_change")
    if pct is not None:
        sector_rows.append((name, ticker, pct))

sector_rows.sort(key=lambda r: r[2])

if sector_rows:
    import plotly.graph_objects as go

    names = [f"{n} ({t})" for n, t, _ in sector_rows]
    pcts = [p for _, _, p in sector_rows]
    colors = ["#e74c3c" if p < 0 else "#2ecc71" for p in pcts]

    fig = go.Figure(go.Bar(x=pcts, y=names, orientation="h", marker_color=colors,
                            text=[f"{p:+.2f}%" for p in pcts], textposition="outside"))
    fig.update_layout(height=400, margin=dict(l=10, r=40, t=10, b=10), xaxis_title="1-day change (%)")
    apply_dark_plotly(fig)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
else:
    st.info("Sector data unavailable right now.")

# ---------------------------------------------------------------------------
# Gainers / Losers / Most active
# ---------------------------------------------------------------------------

st.divider()
st.subheader("Movers")
st.caption(f"From a curated watchlist of {len(MOVERS_UNIVERSE)} widely-held large-cap stocks.")

movers = get_movers(tuple(MOVERS_UNIVERSE), top_n=5)


def render_mover_row(q):
    ticker = q["ticker"]
    name = q.get("name", ticker)
    price = q.get("price")
    pct = q.get("pct_change")
    color = "green" if (pct or 0) >= 0 else "red"
    sign = "+" if (pct or 0) >= 0 else ""

    logo_url = get_logo_or_placeholder(ticker)
    c1, c2, c3 = st.columns([1, 4, 3])
    with c1:
        st.image(logo_url, width=32)
    with c2:
        st.markdown(f"**{ticker}**  \n<span style='font-size:0.85em;color:gray'>{name}</span>", unsafe_allow_html=True)
    with c3:
        st.markdown(
            f"${price:,.2f}  \n:{color}[{sign}{pct:.2f}%]" if price is not None else "—",
        )


col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("##### 📈 Top gainers")
    for q in movers["gainers"]:
        render_mover_row(q)

with col2:
    st.markdown("##### 📉 Top losers")
    for q in movers["losers"]:
        render_mover_row(q)

with col3:
    st.markdown("##### 🔥 Most active")
    for q in movers["most_active"]:
        render_mover_row(q)

# ---------------------------------------------------------------------------
# Headlines
# ---------------------------------------------------------------------------

st.divider()
st.subheader("Top headlines (last 24h)")

news_items = headlines_last_24h(market_news(limit=15), limit=3)

if not news_items:
    st.info("No recent headlines available.")
else:
    for item in news_items:
        with st.container(border=True):
            st.markdown(f"**{item['title']}**")
            meta = item["publisher"]
            ago = time_ago(item["time"])
            if ago:
                meta += f" · {ago}"
            st.caption(meta)
            summary = (item.get("summary") or "").strip()
            if summary:
                lines = summary.split("\n")
                short = " ".join(lines)[:280]
                st.write(short + ("..." if len(short) == 280 else ""))
            if item.get("link"):
                st.markdown(f"[Read more]({item['link']})")

render_footer()
