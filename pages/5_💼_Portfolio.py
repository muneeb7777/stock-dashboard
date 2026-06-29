import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from lib import claude_analyst
from lib.charts import render_gauge
from lib.config import APP_NAME, fmt_large_number, inject_base_style, render_footer
from lib.market_data import get_history, get_quotes_bulk, get_stock_fundamentals
from lib.portfolio import load_portfolio, save_portfolio
from lib.risk import etf_risk_score, portfolio_risk_score, risk_label
from utils.theme import apply_theme, render_theme_toggle

st.set_page_config(page_title=f"Portfolio - {APP_NAME}", page_icon="💼", layout="wide")
apply_theme()
inject_base_style()

st.title("💼 Portfolio")
st.caption("Your holdings are stored locally in `data/portfolio.json` and are never sent anywhere except to Claude if you click the AI analysis button below.")

# ---------------------------------------------------------------------------
# Holdings editor
# ---------------------------------------------------------------------------

holdings = load_portfolio()
if not holdings:
    holdings = [{"ticker": "AAPL", "shares": 10.0, "cost_basis": 150.0}]

df = pd.DataFrame(holdings)
for col, default in (("ticker", ""), ("shares", 0.0), ("cost_basis", 0.0)):
    if col not in df.columns:
        df[col] = default

st.subheader("Holdings")
edited = st.data_editor(
    df[["ticker", "shares", "cost_basis"]],
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "ticker": st.column_config.TextColumn("Ticker"),
        "shares": st.column_config.NumberColumn("Shares", min_value=0.0, step=1.0),
        "cost_basis": st.column_config.NumberColumn("Cost basis / share ($)", min_value=0.0, step=0.01),
    },
    key="portfolio_editor",
)

if st.button("Save portfolio"):
    cleaned = edited.dropna(subset=["ticker"])
    cleaned = cleaned[cleaned["ticker"].str.strip() != ""]
    records = []
    for _, row in cleaned.iterrows():
        records.append({
            "ticker": row["ticker"].strip().upper(),
            "shares": float(row["shares"]) if pd.notna(row["shares"]) else 0.0,
            "cost_basis": float(row["cost_basis"]) if pd.notna(row["cost_basis"]) else 0.0,
        })
    save_portfolio(records)
    st.success("Portfolio saved.")
    st.rerun()

holdings = load_portfolio()
holdings = [h for h in holdings if h.get("ticker") and h.get("shares", 0) > 0]

if not holdings:
    st.info("Add at least one holding above and click **Save portfolio** to see analysis.")
    render_footer()
    st.stop()

# ---------------------------------------------------------------------------
# Valuation
# ---------------------------------------------------------------------------

st.divider()

tickers = tuple(h["ticker"] for h in holdings)
quotes = get_quotes_bulk(tickers)

rows = []
total_value = 0.0
total_cost = 0.0
for h in holdings:
    q = quotes.get(h["ticker"], {})
    price = q.get("price")
    shares = h["shares"]
    cost_basis = h.get("cost_basis", 0.0)
    value = price * shares if price is not None else None
    cost = cost_basis * shares
    gain = (value - cost) if value is not None else None
    gain_pct = (gain / cost * 100) if (gain is not None and cost > 0) else None

    rows.append({
        "ticker": h["ticker"], "shares": shares, "price": price, "value": value,
        "cost": cost, "gain": gain, "gain_pct": gain_pct,
    })
    if value is not None:
        total_value += value
    total_cost += cost

total_gain = total_value - total_cost
total_gain_pct = (total_gain / total_cost * 100) if total_cost > 0 else None

m1, m2, m3 = st.columns(3)
m1.metric("Current value", fmt_large_number(total_value))
m2.metric("Total cost basis", fmt_large_number(total_cost))
m3.metric("Total return", fmt_large_number(total_gain), f"{total_gain_pct:+.2f}%" if total_gain_pct is not None else None)

display_df = pd.DataFrame(rows)
display_df["price"] = display_df["price"].map(lambda v: f"${v:,.2f}" if v is not None else "—")
display_df["value"] = display_df["value"].map(lambda v: f"${v:,.2f}" if v is not None else "—")
display_df["cost"] = display_df["cost"].map(lambda v: f"${v:,.2f}")
display_df["gain"] = display_df["gain"].map(lambda v: f"${v:,.2f}" if v is not None else "—")
display_df["gain_pct"] = display_df["gain_pct"].map(lambda v: f"{v:+.2f}%" if v is not None else "—")
display_df.columns = ["Ticker", "Shares", "Price", "Value", "Cost basis", "Gain/Loss", "Gain/Loss %"]
st.dataframe(display_df, hide_index=True, use_container_width=True)

# ---------------------------------------------------------------------------
# Allocation pie + sector breakdown
# ---------------------------------------------------------------------------

st.divider()
cols = st.columns(2)

with cols[0]:
    st.markdown("##### Allocation")
    valued = [r for r in rows if r["value"]]
    if valued:
        fig = go.Figure(go.Pie(
            labels=[r["ticker"] for r in valued], values=[r["value"] for r in valued],
            hole=0.4,
        ))
        fig.update_layout(template="plotly_dark", height=380, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("No valued holdings to chart.")

with cols[1]:
    st.markdown("##### Sector breakdown")
    sector_values = {}
    for r in rows:
        if not r["value"]:
            continue
        fund = get_stock_fundamentals(r["ticker"])
        sector = fund.get("sector") or "Other"
        sector_values[sector] = sector_values.get(sector, 0.0) + r["value"]

    if sector_values:
        fig = go.Figure(go.Pie(
            labels=list(sector_values.keys()), values=list(sector_values.values()), hole=0.4,
        ))
        fig.update_layout(template="plotly_dark", height=380, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("Sector data unavailable.")

sector_breakdown_pct = {
    sector: (value / total_value * 100) for sector, value in sector_values.items()
} if total_value else {}

# ---------------------------------------------------------------------------
# Portfolio risk score
# ---------------------------------------------------------------------------

st.divider()
st.subheader("Portfolio risk score")

per_holding_scores = []
for r in rows:
    if not r["value"]:
        continue
    hist = get_history(r["ticker"], "1Y")
    score, _ = etf_risk_score(hist, None)
    per_holding_scores.append((score, r["value"]))

p_score = portfolio_risk_score(per_holding_scores)

g_col, _ = st.columns([1, 2])
with g_col:
    st.plotly_chart(render_gauge(p_score, "green_red", height=200), use_container_width=True, config={"displayModeBar": False})
    if p_score is not None:
        st.markdown(f"<h4 style='text-align:center'>{p_score:.0f} / 100 - {risk_label(p_score)}</h4>", unsafe_allow_html=True)
    else:
        st.markdown("<h4 style='text-align:center'>—</h4>", unsafe_allow_html=True)
st.caption("A value-weighted blend of each holding's historical volatility and drawdown. Higher = historically more variable, not riskier in a predictive sense.")

# ---------------------------------------------------------------------------
# Claude deep analysis
# ---------------------------------------------------------------------------

st.divider()
st.subheader("AI analysis")

if not claude_analyst.is_configured():
    st.info("AI analysis is unavailable. Set `GROQ_API_KEY` in Streamlit secrets to enable it.")
else:
    if st.button("Generate portfolio analysis"):
        holdings_summary = "\n".join(
            f"- {r['ticker']}: {r['shares']} shares, value {fmt_large_number(r['value'])}, "
            f"gain/loss {r['gain_pct']:+.2f}%" if r['gain_pct'] is not None else f"- {r['ticker']}: {r['shares']} shares"
            for r in rows
        )
        try:
            st.write_stream(claude_analyst.portfolio_analysis(holdings_summary, p_score, sector_breakdown_pct))
        except Exception as e:
            st.error(f"AI analysis failed: {e}")

render_footer()
