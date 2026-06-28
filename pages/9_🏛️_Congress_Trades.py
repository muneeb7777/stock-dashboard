import datetime as dt

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from lib.config import APP_NAME, inject_base_style, render_footer
from lib.congress import fetch_congress_trades, most_active_traders, most_traded_stocks, politician_returns

st.set_page_config(page_title=f"Congress Trades - {APP_NAME}", page_icon="🏛️", layout="wide")
inject_base_style()

st.title("🏛️ Congress Trades")
st.caption(
    "Stock trading disclosures from members of the House and Senate, sourced from the "
    "House Stock Watcher and Senate Stock Watcher public datasets."
)

with st.spinner("Loading congressional trading disclosures..."):
    trades = fetch_congress_trades()

if trades.empty:
    st.warning(
        "Congressional trading data is currently unavailable from the data provider "
        "(House/Senate Stock Watcher feeds did not return data)."
    )
    render_footer()
    st.stop()

# ---------------------------------------------------------------------------
# Filters
# ---------------------------------------------------------------------------

st.subheader("Filters")
f1, f2, f3, f4, f5 = st.columns([1.2, 1.2, 1.2, 1.6, 1.4])

with f1:
    parties = sorted(p for p in trades["Party"].dropna().unique())
    party_filter = st.multiselect("Party", parties, default=[])
with f2:
    chamber_filter = st.multiselect("Chamber", ["House", "Senate"], default=[])
with f3:
    txn_filter = st.multiselect("Buy/Sell", ["Buy", "Sell", "Exchange", "Other"], default=[])
with f4:
    min_date = trades["Date Traded"].min()
    max_date = trades["Date Traded"].max()
    if pd.isna(min_date) or pd.isna(max_date):
        date_range = None
    else:
        date_range = st.date_input(
            "Date traded range",
            value=(max(min_date.date(), max_date.date() - dt.timedelta(days=180)), max_date.date()),
            min_value=min_date.date(),
            max_value=max_date.date(),
        )
with f5:
    ticker_query = st.text_input("Ticker search", value="", placeholder="e.g. NVDA").strip().upper()

filtered = trades.copy()
if party_filter:
    filtered = filtered[filtered["Party"].isin(party_filter)]
if chamber_filter:
    filtered = filtered[filtered["Chamber"].isin(chamber_filter)]
if txn_filter:
    filtered = filtered[filtered["Transaction"].isin(txn_filter)]
if date_range and isinstance(date_range, tuple) and len(date_range) == 2:
    start, end = date_range
    filtered = filtered[
        filtered["Date Traded"].isna()
        | ((filtered["Date Traded"].dt.date >= start) & (filtered["Date Traded"].dt.date <= end))
    ]
if ticker_query:
    filtered = filtered[filtered["Ticker"] == ticker_query]

st.divider()

# ---------------------------------------------------------------------------
# Feed
# ---------------------------------------------------------------------------

if ticker_query:
    st.subheader(f"Disclosures for {ticker_query}")
else:
    st.subheader("Recent disclosures")

st.caption(f"{len(filtered):,} transactions match the current filters.")

if filtered.empty:
    st.info("No transactions match the current filters.")
else:
    display = filtered.copy()
    display["Date Filed"] = display["Date Filed"].dt.strftime("%Y-%m-%d")
    display["Date Traded"] = display["Date Traded"].dt.strftime("%Y-%m-%d")
    display = display[
        ["Politician", "Party", "Chamber", "Ticker", "Company", "Transaction", "Amount", "Date Filed", "Date Traded"]
    ].head(500)

    def highlight_party(row):
        if row["Party"] == "D":
            color = "rgba(52, 152, 219, 0.18)"
        elif row["Party"] == "R":
            color = "rgba(231, 76, 60, 0.18)"
        else:
            color = ""
        styles = [f"background-color: {color};" if color else ""] * len(row)
        if row["Transaction"] == "Buy":
            styles[row.index.get_loc("Transaction")] += " color: #2ecc71; font-weight: 600;"
        elif row["Transaction"] == "Sell":
            styles[row.index.get_loc("Transaction")] += " color: #e74c3c; font-weight: 600;"
        return styles

    styled = display.style.apply(highlight_party, axis=1)
    st.dataframe(styled, use_container_width=True, hide_index=True, height=520)
    if len(filtered) > 500:
        st.caption("Showing the most recent 500 of " + f"{len(filtered):,} matching transactions.")

# ---------------------------------------------------------------------------
# Most traded stocks
# ---------------------------------------------------------------------------

st.divider()
col1, col2 = st.columns(2)

with col1:
    st.subheader("Most traded stocks by Congress")
    top_stocks = most_traded_stocks(filtered, top_n=15)
    if top_stocks.empty:
        st.info("No data available.")
    else:
        fig = go.Figure(
            go.Bar(
                x=top_stocks["Trades"],
                y=top_stocks["Ticker"],
                orientation="h",
                marker_color="#3498db",
            )
        )
        fig.update_layout(
            template="plotly_dark",
            height=420,
            margin=dict(l=10, r=20, t=10, b=10),
            yaxis=dict(autorange="reversed"),
            xaxis_title="Transactions",
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

with col2:
    st.subheader("Most active traders")
    leaders = most_active_traders(filtered, top_n=15)
    if leaders.empty:
        st.info("No data available.")
    else:
        for _, row in leaders.iterrows():
            party_color = {"D": "blue", "R": "red"}.get(row["Party"], "gray")
            st.markdown(
                f"**{row['Politician']}** ({row['Chamber']}) "
                f":{party_color}[{row['Party']}]  \n{int(row['Trades'])} transactions"
            )

# ---------------------------------------------------------------------------
# Average return if you followed each politician's trades
# ---------------------------------------------------------------------------

st.divider()
st.subheader("Average return if you followed each politician's purchases")
st.caption(
    "For each politician's most recent disclosed *purchases*, this compares the price "
    "shortly after the trade date to the current price. Based on a limited sample per "
    "politician to keep load times reasonable."
)

if st.button("Calculate returns", help="Fetches historical prices via yfinance — may take a minute."):
    with st.spinner("Scoring politician trades against historical prices..."):
        returns_df = politician_returns(filtered, max_trades_per_politician=5)

    if returns_df.empty:
        st.info("Not enough priced purchase data to compute returns.")
    else:
        display_returns = returns_df.copy()
        display_returns["Avg Return"] = display_returns["Avg Return"].map(lambda v: f"{v * 100:+.1f}%")

        def highlight_return(row):
            raw = returns_df.loc[row.name, "Avg Return"]
            color = "#2ecc71" if raw >= 0 else "#e74c3c"
            styles = [""] * len(row)
            styles[row.index.get_loc("Avg Return")] = f"color: {color}; font-weight: 600;"
            return styles

        styled_returns = display_returns.style.apply(highlight_return, axis=1)
        st.dataframe(styled_returns, use_container_width=True, hide_index=True, height=420)

render_footer()
