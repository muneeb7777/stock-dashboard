import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from lib.config import APP_NAME, fmt_large_number, inject_base_style, render_footer
from lib.optimizer import (
    correlation_matrix,
    current_weights,
    efficient_frontier_points,
    fetch_price_history,
    monte_carlo_simulation,
    optimize_portfolio,
    rebalance_suggestions,
)
from lib.portfolio import load_portfolio

st.set_page_config(page_title=f"Portfolio Optimizer - {APP_NAME}", page_icon="⚖️", layout="wide")
inject_base_style()

st.title("⚖️ Portfolio Optimizer")
st.caption(
    "Mean-variance optimization over historical returns (PyPortfolioOpt). This describes "
    "what historical-return/risk tradeoffs would have looked like - it is not a forecast "
    "or a recommendation."
)

# ---------------------------------------------------------------------------
# Holdings input
# ---------------------------------------------------------------------------

if "optimizer_holdings" not in st.session_state:
    saved = load_portfolio()
    if saved:
        st.session_state["optimizer_holdings"] = pd.DataFrame(saved)[["ticker", "shares", "cost_basis"]]
    else:
        st.session_state["optimizer_holdings"] = pd.DataFrame(
            [{"ticker": "AAPL", "shares": 10.0, "cost_basis": 150.0}, {"ticker": "MSFT", "shares": 5.0, "cost_basis": 300.0}]
        )

c1, c2 = st.columns([3, 1])
with c1:
    st.subheader("Your holdings")
with c2:
    if st.button("Import from Portfolio page"):
        saved = load_portfolio()
        if saved:
            st.session_state["optimizer_holdings"] = pd.DataFrame(saved)[["ticker", "shares", "cost_basis"]]
            st.rerun()
        else:
            st.warning("No holdings saved on the Portfolio page yet.")

edited = st.data_editor(
    st.session_state["optimizer_holdings"],
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "ticker": st.column_config.TextColumn("Ticker"),
        "shares": st.column_config.NumberColumn("Shares", min_value=0.0, step=1.0),
        "cost_basis": st.column_config.NumberColumn("Cost basis / share ($)", min_value=0.0, step=0.01),
    },
    key="optimizer_editor",
)
st.session_state["optimizer_holdings"] = edited

holdings = []
for _, row in edited.iterrows():
    ticker = str(row.get("ticker") or "").strip().upper()
    shares = float(row.get("shares") or 0)
    cost_basis = float(row.get("cost_basis") or 0)
    if ticker and shares > 0:
        holdings.append({"ticker": ticker, "shares": shares, "cost_basis": cost_basis})

if len(holdings) < 2:
    st.info("Add at least 2 holdings with shares > 0 to run the optimizer.")
    render_footer()
    st.stop()

run = st.button("Run optimization", type="primary")

if run:
    st.session_state["opt_run"] = True

if not st.session_state.get("opt_run"):
    render_footer()
    st.stop()

tickers = tuple(h["ticker"] for h in holdings)

with st.spinner("Loading price history..."):
    prices = fetch_price_history(tickers, period="2y")

missing = [t for t in tickers if t not in prices.columns]
if missing:
    st.warning(f"No price history available for: {', '.join(missing)}. These were excluded from optimization.")

if prices.shape[1] < 2 or len(prices) < 30:
    st.warning("Not enough overlapping price history across these holdings to optimize.")
    render_footer()
    st.stop()

result = optimize_portfolio(prices)
if result is None:
    st.warning("Could not compute an optimization for this set of holdings.")
    render_footer()
    st.stop()

latest_prices = {t: float(prices[t].iloc[-1]) for t in prices.columns}
cur_weights, total_value = current_weights(holdings, latest_prices)

# ---------------------------------------------------------------------------
# Optimized portfolios
# ---------------------------------------------------------------------------

st.divider()
st.subheader("Optimized portfolios")

portfolios = result["portfolios"]
cols = st.columns(3)
labels = {
    "Max Sharpe": "Max Sharpe Ratio (best risk-adjusted)",
    "Min Volatility": "Min Volatility (safest)",
    "Max Return": "Max Return (aggressive)",
}

for col, (key, label) in zip(cols, labels.items()):
    port = portfolios.get(key)
    with col:
        st.markdown(f"**{label}**")
        if not port:
            st.caption("Not available.")
            continue
        st.metric("Expected annual return", f"{port['expected_return'] * 100:+.1f}%")
        st.metric("Annual volatility", f"{port['volatility'] * 100:.1f}%")
        st.metric("Sharpe ratio", f"{port['sharpe']:.2f}")
        weights_df = pd.DataFrame(sorted(port["weights"].items(), key=lambda x: -x[1]), columns=["Ticker", "Weight"])
        weights_df["Weight"] = weights_df["Weight"].map(lambda w: f"{w * 100:.1f}%")
        st.dataframe(weights_df, use_container_width=True, hide_index=True, height=min(280, 40 + 35 * len(weights_df)))

# ---------------------------------------------------------------------------
# Efficient frontier
# ---------------------------------------------------------------------------

st.divider()
st.subheader("Efficient frontier")

frontier = efficient_frontier_points(result["mu"], result["cov"], n_points=30)

fig = go.Figure()
if not frontier.empty:
    fig.add_trace(go.Scatter(
        x=frontier["Volatility"] * 100, y=frontier["Return"] * 100,
        mode="lines", name="Efficient frontier", line=dict(color="#7f8c8d", width=2),
    ))

# Individual assets
mu, cov = result["mu"], result["cov"]
fig.add_trace(go.Scatter(
    x=[np.sqrt(cov.loc[t, t]) * 100 for t in mu.index], y=[mu[t] * 100 for t in mu.index],
    mode="markers+text", text=list(mu.index), textposition="top center",
    marker=dict(size=9, color="#7f8c8d"), name="Individual holdings",
))

marker_colors = {"Max Sharpe": "#2ecc71", "Min Volatility": "#3498db", "Max Return": "#e74c3c"}
for key, label in labels.items():
    port = portfolios.get(key)
    if not port:
        continue
    fig.add_trace(go.Scatter(
        x=[port["volatility"] * 100], y=[port["expected_return"] * 100],
        mode="markers", name=label, marker=dict(size=14, symbol="star", color=marker_colors[key]),
    ))

if cur_weights:
    cur_ret = sum(cur_weights.get(t, 0) * mu.get(t, 0) for t in mu.index)
    cur_vol = float(np.sqrt(
        sum(cur_weights.get(a, 0) * cur_weights.get(b, 0) * cov.loc[a, b] for a in mu.index for b in mu.index)
    ))
    fig.add_trace(go.Scatter(
        x=[cur_vol * 100], y=[cur_ret * 100], mode="markers", name="Current portfolio",
        marker=dict(size=14, symbol="diamond", color="#f1c40f"),
    ))

fig.update_layout(
    template="plotly_dark",
    height=480,
    margin=dict(l=10, r=10, t=30, b=10),
    xaxis_title="Annual volatility (%)",
    yaxis_title="Expected annual return (%)",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
)
st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# ---------------------------------------------------------------------------
# Current vs optimized allocation
# ---------------------------------------------------------------------------

st.divider()
st.subheader("Current vs optimized allocation")

target_choice = st.radio("Compare current allocation against:", list(labels.values()), horizontal=True)
target_key = next(k for k, v in labels.items() if v == target_choice)
target_port = portfolios.get(target_key)

if target_port and cur_weights:
    all_tickers = sorted(set(cur_weights) | set(target_port["weights"]))
    comp_df = pd.DataFrame({
        "Ticker": all_tickers,
        "Current": [cur_weights.get(t, 0) * 100 for t in all_tickers],
        "Optimized": [target_port["weights"].get(t, 0) * 100 for t in all_tickers],
    })

    fig2 = go.Figure()
    fig2.add_trace(go.Bar(x=comp_df["Ticker"], y=comp_df["Current"], name="Current", marker_color="#f1c40f"))
    fig2.add_trace(go.Bar(x=comp_df["Ticker"], y=comp_df["Optimized"], name="Optimized", marker_color=marker_colors[target_key]))
    fig2.update_layout(
        template="plotly_dark", height=380, barmode="group",
        margin=dict(l=10, r=10, t=30, b=10), yaxis_title="Weight (%)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

    st.markdown("##### Suggested rebalancing")
    suggestions = rebalance_suggestions(holdings, latest_prices, target_port["weights"], total_value)
    if not suggestions:
        st.info("Current allocation is already close to this target - no material rebalancing suggested.")
    else:
        for s in sorted(suggestions, key=lambda x: -x["Value"]):
            verb = "Add" if s["Action"] == "Add" else "Reduce"
            st.markdown(f"- **{verb} {s['Ticker']}** by **{s['Shares']:,.2f} shares** (~${s['Value']:,.0f})")
else:
    st.info("Could not compute current portfolio weights (missing price data).")

# ---------------------------------------------------------------------------
# Correlation heatmap
# ---------------------------------------------------------------------------

st.divider()
st.subheader("Correlation between holdings")

corr = correlation_matrix(prices)
fig3 = go.Figure(go.Heatmap(
    z=corr.values, x=corr.columns, y=corr.columns,
    colorscale="RdBu", zmid=0, zmin=-1, zmax=1,
    text=corr.round(2).values, texttemplate="%{text}",
))
fig3.update_layout(template="plotly_dark", height=420, margin=dict(l=10, r=10, t=30, b=10))
st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})

# ---------------------------------------------------------------------------
# Monte Carlo simulation
# ---------------------------------------------------------------------------

st.divider()
st.subheader("Monte Carlo simulation - next 12 months")
st.caption("1,000 simulated paths using the current portfolio's historical daily mean return and volatility.")

if cur_weights:
    sims = monte_carlo_simulation(prices, cur_weights, n_sims=1000, n_days=252, initial_value=total_value)

    fig4 = go.Figure()
    sample = sims[:, ::20]  # thin out for rendering
    for i in range(sample.shape[1]):
        fig4.add_trace(go.Scatter(y=sample[:, i], mode="lines", line=dict(width=1, color="rgba(52, 152, 219, 0.15)"), showlegend=False))

    median_path = np.median(sims, axis=1)
    p10 = np.percentile(sims, 10, axis=1)
    p90 = np.percentile(sims, 90, axis=1)
    fig4.add_trace(go.Scatter(y=median_path, mode="lines", name="Median", line=dict(color="#f1c40f", width=2)))
    fig4.add_trace(go.Scatter(y=p10, mode="lines", name="10th percentile", line=dict(color="#e74c3c", width=2, dash="dot")))
    fig4.add_trace(go.Scatter(y=p90, mode="lines", name="90th percentile", line=dict(color="#2ecc71", width=2, dash="dot")))

    fig4.update_layout(
        template="plotly_dark", height=420, margin=dict(l=10, r=10, t=30, b=10),
        xaxis_title="Trading days ahead", yaxis_title="Portfolio value ($)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(fig4, use_container_width=True, config={"displayModeBar": False})

    final_values = sims[-1, :]
    m1, m2, m3 = st.columns(3)
    m1.metric("Median outcome (1Y)", f"${np.median(final_values):,.0f}")
    m2.metric("10th percentile", f"${np.percentile(final_values, 10):,.0f}")
    m3.metric("90th percentile", f"${np.percentile(final_values, 90):,.0f}")
else:
    st.info("Could not compute current weights for the simulation.")

render_footer()
