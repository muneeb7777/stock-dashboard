import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from lib.charts import render_gauge, render_price_chart
from lib.config import APP_NAME, fmt_large_number, fmt_pct, inject_base_style, render_footer
from lib.etf_peers import get_peers
from lib.logos import get_logo_or_placeholder
from lib.market_data import PERIOD_MAP, get_etf_details, get_history, get_prev_close
from lib.risk import etf_risk_score, risk_label
from utils.theme import apply_dark_plotly

st.set_page_config(page_title=f"ETF Analyzer - {APP_NAME}", page_icon="🧺", layout="wide")
inject_base_style()

st.title("🧺 ETF Analyzer")

col_input, col_period = st.columns([2, 3])
with col_input:
    ticker = st.text_input("ETF ticker", value="SPY").strip().upper()
with col_period:
    period = st.segmented_control("Period", options=list(PERIOD_MAP.keys()), default="1Y", key="etf_period")
    period = period or "1Y"

if not ticker:
    st.stop()

try:
    details = get_etf_details(ticker)
except Exception as e:
    st.error(f"Error loading {ticker}: {type(e).__name__}: {str(e)}")
    render_footer()
    st.stop()

if not details.get("price"):
    st.error(f"Error loading {ticker}: no price data returned (ticker may be invalid or delisted)")
    render_footer()
    st.stop()

st.markdown(f"### {details['name']} ({ticker})")
st.caption(" · ".join(filter(None, [details.get("category"), f"AUM {fmt_large_number(details.get('total_assets'))}" if details.get("total_assets") else None])))

# ---------------------------------------------------------------------------
# Chart
# ---------------------------------------------------------------------------

st.divider()

view = st.segmented_control(
    "Chart view", options=["Performance", "Price", "Candlestick", "Area"], default="Performance", key="etf_view"
)
view = view or "Performance"

history = get_history(ticker, period)
baseline = get_prev_close(ticker) if period == "1D" else None
fig = render_price_chart(history, view=view, baseline_price=baseline, show_volume=True, height=520)
st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# ---------------------------------------------------------------------------
# Returns table + risk gauge
# ---------------------------------------------------------------------------

st.divider()
cols = st.columns([3, 2])

with cols[0]:
    st.markdown("##### Returns")
    returns_df = pd.DataFrame({
        "Metric": ["YTD return", "3-year average return", "5-year average return", "3-year beta"],
        "Value": [
            fmt_pct(details.get("ytd_return")),
            fmt_pct(details.get("three_year_avg_return")),
            fmt_pct(details.get("five_year_avg_return")),
            f"{details['beta_3y']:.2f}" if details.get("beta_3y") is not None else "—",
        ],
    })
    st.dataframe(returns_df, hide_index=True, use_container_width=True)

with cols[1]:
    st.markdown("##### Risk profile")
    risk_history = get_history(ticker, "1Y")
    score, drivers = etf_risk_score(risk_history, details.get("top_holdings"))
    st.plotly_chart(render_gauge(score, "green_red", height=180), use_container_width=True, config={"displayModeBar": False})
    if score is not None:
        st.markdown(f"<h4 style='text-align:center'>{score:.0f} / 100 - {risk_label(score)}</h4>", unsafe_allow_html=True)
    else:
        st.markdown("<h4 style='text-align:center'>—</h4>", unsafe_allow_html=True)
    for d in drivers:
        st.caption(f"• {d}")

# ---------------------------------------------------------------------------
# Sector breakdown
# ---------------------------------------------------------------------------

st.divider()
st.subheader("Sector breakdown")

sector_weights = details.get("sector_weights") or {}
if sector_weights:
    rows = []
    for sector, weight in sector_weights.items():
        pct = weight * 100 if weight <= 1 else weight
        label = sector.replace("_", " ").title()
        rows.append((label, pct))
    rows = [r for r in rows if r[1] > 0]
    rows.sort(key=lambda r: r[1])

    fig = go.Figure(go.Bar(
        x=[r[1] for r in rows], y=[r[0] for r in rows], orientation="h",
        marker_color="#5dade2", text=[f"{r[1]:.1f}%" for r in rows], textposition="outside",
    ))
    fig.update_layout(
        height=max(300, 30 * len(rows)), margin=dict(l=10, r=40, t=10, b=10), xaxis_title="Weight (%)",
    )
    apply_dark_plotly(fig)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
else:
    st.info("Sector breakdown unavailable for this ETF.")

# ---------------------------------------------------------------------------
# Top holdings
# ---------------------------------------------------------------------------

st.divider()
st.subheader("Top holdings")

holdings = details.get("top_holdings") or []
if holdings:
    half = (len(holdings) + 1) // 2
    col1, col2 = st.columns(2)
    for col, group in zip((col1, col2), (holdings[:half], holdings[half:])):
        with col:
            for h in group:
                weight = h["weight"] * 100 if h["weight"] <= 1 else h["weight"]
                c1, c2, c3 = st.columns([1, 4, 2])
                with c1:
                    st.image(get_logo_or_placeholder(h["symbol"]), width=28)
                with c2:
                    st.markdown(f"**{h['symbol']}**  \n<span style='font-size:0.85em;color:gray'>{h['name']}</span>", unsafe_allow_html=True)
                with c3:
                    st.markdown(f"<div style='text-align:right'>{weight:.2f}%</div>", unsafe_allow_html=True)
else:
    st.info("Top holdings unavailable for this ETF.")

# ---------------------------------------------------------------------------
# Peer comparison / cheaper alternatives
# ---------------------------------------------------------------------------

st.divider()
st.subheader("Peer cost comparison")

peers = get_peers(ticker)
peer_rows = []
for peer in peers:
    pd_details = details if peer == ticker else get_etf_details(peer)
    er = pd_details.get("expense_ratio")
    if er is None:
        continue
    er_pct = er * 100 if er <= 1 else er
    peer_rows.append({
        "Ticker": peer,
        "Name": pd_details.get("name"),
        "Expense ratio": er_pct,
        "AUM": pd_details.get("total_assets"),
    })

if peer_rows:
    peer_df = pd.DataFrame(peer_rows).sort_values("Expense ratio")
    display_df = peer_df.copy()
    display_df["Expense ratio"] = display_df["Expense ratio"].map(lambda v: f"{v:.2f}%")
    display_df["AUM"] = display_df["AUM"].map(fmt_large_number)
    st.dataframe(display_df, hide_index=True, use_container_width=True)

    current_er = next((r["Expense ratio"] for r in peer_rows if r["Ticker"] == ticker), None)
    if current_er is not None:
        cheaper = [r for r in peer_rows if r["Ticker"] != ticker and r["Expense ratio"] < current_er]
        if cheaper:
            cheapest = min(cheaper, key=lambda r: r["Expense ratio"])
            savings_bps = (current_er - cheapest["Expense ratio"]) * 100
            savings_dollars = savings_bps / 10000 * 100_000
            st.success(
                f"💡 **{cheapest['Ticker']}** tracks a similar exposure with an expense ratio "
                f"{savings_bps:.0f} bps lower than {ticker} "
                f"({cheapest['Expense ratio']:.2f}% vs {current_er:.2f}%). "
                f"On a $100,000 position, that's roughly **${savings_dollars:,.0f} per year** "
                f"in fees, all else equal."
            )
        else:
            st.caption(f"{ticker} already has the lowest expense ratio among its identified peers.")
else:
    st.info("No peer comparison data available for this ticker.")

render_footer()
