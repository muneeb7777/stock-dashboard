import pandas as pd
import streamlit as st

from lib.config import APP_NAME, inject_base_style, render_footer
from lib.insider import MIN_SIZE_OPTIONS, detect_cluster_buying, fetch_insider_feed, hot_stocks, search_insider_transactions
from utils.theme import apply_theme, render_theme_toggle

st.set_page_config(page_title=f"Insider Flow - {APP_NAME}", page_icon="🕴️", layout="wide")
apply_theme()
inject_base_style()

st.title("🕴️ Insider Flow")
st.caption(
    "Live feed of open-market Form 4 buy/sell transactions, sourced from SEC EDGAR's "
    "latest-filings feed. Only purchase (code P) and sale (code S) transactions are shown."
)

with st.spinner("Pulling latest Form 4 filings from SEC EDGAR..."):
    feed = fetch_insider_feed(100)

clusters = detect_cluster_buying(feed, min_insiders=3)

# ---------------------------------------------------------------------------
# Sidebar: Hot Stocks
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown("### 🔥 Hot Stocks")
    st.caption("Most insider buying this week")
    hot = hot_stocks(feed, top_n=8)
    if hot.empty:
        st.caption("No buy clusters in the current feed.")
    else:
        for _, row in hot.iterrows():
            badge = " 🚀" if row["Ticker"] in clusters else ""
            st.markdown(f"**{row['Ticker']}**{badge}  \n{int(row['Buys'])} buys · ${row['Total Value']:,.0f}")

# ---------------------------------------------------------------------------
# Filters
# ---------------------------------------------------------------------------

col1, col2, col3 = st.columns([2, 2, 2])
with col1:
    ticker_query = st.text_input("Search by ticker", value="", placeholder="e.g. AAPL").strip().upper()
with col2:
    buys_only = st.toggle("Buys only", value=False)
with col3:
    min_size_label = st.selectbox("Minimum transaction size", list(MIN_SIZE_OPTIONS.keys()))

if ticker_query:
    with st.spinner(f"Searching SEC EDGAR full-text search for {ticker_query} Form 4 filings..."):
        searched = search_insider_transactions(ticker_query, days=30)
    if not searched.empty:
        filtered = searched
    else:
        filtered = feed[feed["Ticker"] == ticker_query].copy() if not feed.empty else feed.copy()
elif not feed.empty:
    filtered = feed.copy()
else:
    filtered = feed.copy()

if feed.empty and filtered.empty:
    st.warning("No insider transaction data available right now — SEC EDGAR may be temporarily unreachable.")
else:
    if buys_only:
        filtered = filtered[filtered["Type"] == "Buy"]
    min_size = MIN_SIZE_OPTIONS[min_size_label]
    if min_size:
        filtered = filtered[filtered["Total Value"] >= min_size]

    st.divider()

    if ticker_query:
        st.subheader(f"Insider activity for {ticker_query}")
        st.caption("Showing Form 4 transactions from the last 30 days (SEC EDGAR full-text search).")
    else:
        st.subheader("Live feed")

    if filtered.empty:
        st.info("No transactions match the current filters.")
    else:
        display = filtered.copy()
        display["Cluster"] = display["Ticker"].apply(lambda t: "🚀 Cluster buy" if t in clusters else "")
        display["Date"] = display["Date"].dt.strftime("%Y-%m-%d")
        display["Shares"] = display["Shares"].map(lambda v: f"{v:,.0f}")
        display["Price"] = display["Price"].map(lambda v: f"${v:,.2f}")
        display["Total Value"] = display["Total Value"].map(lambda v: f"${v:,.0f}")

        display = display[["Date", "Company", "Ticker", "Insider", "Title", "Type", "Shares", "Price", "Total Value", "Cluster"]]

        def highlight_type(row):
            color = "rgba(46, 204, 113, 0.18)" if row["Type"] == "Buy" else "rgba(231, 76, 60, 0.18)"
            text_color = "#2ecc71" if row["Type"] == "Buy" else "#e74c3c"
            styles = [""] * len(row)
            type_idx = row.index.get_loc("Type")
            styles[type_idx] = f"color: {text_color}; font-weight: 600;"
            return [f"background-color: {color};" if i != type_idx else styles[type_idx] for i in range(len(row))]

        styled = display.style.apply(highlight_type, axis=1)
        st.dataframe(styled, use_container_width=True, hide_index=True, height=560)

        if clusters:
            st.caption(f"🚀 Cluster buying detected: {', '.join(sorted(clusters))} (3+ distinct insiders buying)")

render_footer()
