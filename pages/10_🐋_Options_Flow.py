import plotly.graph_objects as go
import streamlit as st

from lib.config import APP_NAME, inject_base_style, render_footer
from lib.market_data import MOVERS_UNIVERSE
from lib.options_flow import (
    WHALE_PREMIUM,
    follow_the_money,
    put_call_ratio_by_expiry,
    scan_market,
    unusual_activity,
)

st.set_page_config(page_title=f"Options Flow - {APP_NAME}", page_icon="🐋", layout="wide")
inject_base_style()

st.title("🐋 Options Flow")
st.caption(
    "Unusual options activity from live option chains (volume > 2x open interest). "
    "Sentiment is a heuristic based on contract type and whether the last trade printed "
    "near the ask (aggressive buying) or the bid (aggressive selling)."
)


def style_flow(df):
    display = df.copy()
    display["Vol/OI"] = display["Vol/OI"].map(lambda v: "∞" if v == float("inf") else f"{v:.1f}x")
    display["Premium"] = display["Premium"].map(lambda v: f"${v:,.0f}")
    display["IV%"] = display["IV%"].map(lambda v: f"{v:.1f}%")
    display["Whale"] = df["Premium"].map(lambda v: "🐋" if v >= WHALE_PREMIUM else "")
    display = display.rename(columns={"strike": "Strike", "volume": "Volume", "openInterest": "OI"})
    display = display[
        ["Ticker", "Strike", "Expiry", "Type", "Volume", "OI", "Vol/OI", "Premium", "IV%", "Sentiment", "Whale"]
    ]

    def highlight(row):
        color = "rgba(46, 204, 113, 0.15)" if row["Sentiment"] == "Bullish" else "rgba(231, 76, 60, 0.15)"
        text_color = "#2ecc71" if row["Sentiment"] == "Bullish" else "#e74c3c"
        styles = [f"background-color: {color};"] * len(row)
        idx = row.index.get_loc("Sentiment")
        styles[idx] += f" color: {text_color}; font-weight: 600;"
        return styles

    return display.style.apply(highlight, axis=1)


tab1, tab2 = st.tabs(["Ticker scanner", "Market-wide scanner"])

# ---------------------------------------------------------------------------
# Tab 1: single-ticker unusual activity
# ---------------------------------------------------------------------------

with tab1:
    col1, col2, col3 = st.columns([1.5, 1, 1])
    with col1:
        ticker = st.text_input("Ticker", value="AAPL", key="of_ticker").strip().upper()
    with col2:
        min_ratio = st.number_input("Min Vol/OI ratio", min_value=1.0, value=2.0, step=0.5, key="of_ratio")
    with col3:
        min_volume = st.number_input("Min volume", min_value=0, value=50, step=10, key="of_min_vol")

    if ticker:
        with st.spinner(f"Loading option chains for {ticker}..."):
            unusual = unusual_activity(ticker, max_expiries=6, min_ratio=min_ratio, min_volume=int(min_volume))
            pc = put_call_ratio_by_expiry(ticker, max_expiries=6)

        st.subheader(f"Unusual options activity — {ticker}")
        if unusual.empty:
            st.info("No unusual activity found (volume below the ratio/volume thresholds across the next expiries).")
        else:
            whales = unusual[unusual["Premium"] >= WHALE_PREMIUM]
            if not whales.empty:
                st.caption(f"🐋 {len(whales)} whale trade(s) with premium ≥ ${WHALE_PREMIUM:,.0f}")
            st.dataframe(style_flow(unusual), use_container_width=True, hide_index=True, height=420)

        st.subheader("Put/Call volume ratio by expiry")
        st.caption("True historical put/call ratio isn't available via yfinance; this shows today's ratio across upcoming expiries.")
        if pc.empty:
            st.info("No option chain data available for this ticker.")
        else:
            fig = go.Figure()
            fig.add_trace(go.Bar(x=pc["Expiry"], y=pc["Call Volume"], name="Call volume", marker_color="#2ecc71"))
            fig.add_trace(go.Bar(x=pc["Expiry"], y=pc["Put Volume"], name="Put volume", marker_color="#e74c3c"))
            fig.add_trace(
                go.Scatter(
                    x=pc["Expiry"], y=pc["Put/Call Ratio"], name="Put/Call ratio",
                    yaxis="y2", mode="lines+markers", line=dict(color="#f1c40f", width=2),
                )
            )
            fig.update_layout(
                template="plotly_dark",
                height=420,
                barmode="group",
                margin=dict(l=10, r=10, t=30, b=10),
                yaxis=dict(title="Volume"),
                yaxis2=dict(title="Put/Call ratio", overlaying="y", side="right", showgrid=False),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# ---------------------------------------------------------------------------
# Tab 2: market-wide scanner
# ---------------------------------------------------------------------------

with tab2:
    st.subheader("Scan the top 50 most active stocks")
    st.caption("Checks the two nearest expiries for each ticker. This can take a minute — results are cached for 10 minutes.")

    universe = tuple(MOVERS_UNIVERSE[:50])

    if st.button("Run scanner", type="primary"):
        with st.spinner(f"Scanning {len(universe)} tickers for unusual options flow..."):
            market_unusual = scan_market(universe, max_expiries=2, min_ratio=2.0, min_volume=50)
        st.session_state["of_market_scan"] = market_unusual

    market_unusual = st.session_state.get("of_market_scan")

    if market_unusual is None:
        st.info("Click **Run scanner** to check options flow across the watchlist.")
    elif market_unusual.empty:
        st.info("No unusual activity found across the scanned universe right now.")
    else:
        whales = market_unusual[market_unusual["Premium"] >= WHALE_PREMIUM]
        if not whales.empty:
            st.caption(f"🐋 {len(whales)} whale trade(s) with premium ≥ ${WHALE_PREMIUM:,.0f} found across the scan.")

        st.markdown("##### Follow the Money")
        bullish, bearish = follow_the_money(market_unusual, top_n=5)

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Strongest bullish flow**")
            if bullish.empty:
                st.caption("No bullish flow detected.")
            else:
                for _, row in bullish.iterrows():
                    st.markdown(f":green[**{row['Ticker']}**] — net premium :green[${row['Net Premium']:,.0f}]")
        with c2:
            st.markdown("**Strongest bearish flow**")
            if bearish.empty:
                st.caption("No bearish flow detected.")
            else:
                for _, row in bearish.iterrows():
                    st.markdown(f":red[**{row['Ticker']}**] — net premium :red[${row['Net Premium']:,.0f}]")

        st.markdown("##### All unusual flow")
        st.dataframe(style_flow(market_unusual.head(200)), use_container_width=True, hide_index=True, height=520)

render_footer()
