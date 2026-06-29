import pandas as pd
import streamlit as st

from lib.config import APP_NAME, fmt_large_number, inject_base_style, render_footer
from lib.screener import PRESETS, SCREENER_UNIVERSE, apply_filters, scan_universe
from utils.theme import apply_theme, theme_sidebar

st.set_page_config(page_title=f"Stock Screener - {APP_NAME}", page_icon="🔭", layout="wide")
apply_theme()
inject_base_style()
theme_sidebar()

st.title("🔭 Stock Screener")
st.caption(
    f"Scans a fixed universe of {len(SCREENER_UNIVERSE)} liquid large/mega-cap US stocks. "
    "Fundamentals and technicals refresh every 30 minutes."
)

with st.spinner("Scanning universe..."):
    universe_df = scan_universe(tuple(SCREENER_UNIVERSE))

if universe_df.empty:
    st.warning("No data available right now - try again shortly.")
    render_footer()
    st.stop()

# ---------------------------------------------------------------------------
# Preset screens
# ---------------------------------------------------------------------------

st.subheader("Preset screens")
preset_cols = st.columns(len(PRESETS) + 1)
for i, name in enumerate(PRESETS):
    if preset_cols[i].button(name, use_container_width=True):
        st.session_state["screener_preset"] = name
if preset_cols[-1].button("Clear filters", use_container_width=True):
    st.session_state["screener_preset"] = None

active_preset = st.session_state.get("screener_preset")
preset_filters = PRESETS.get(active_preset, {}) if active_preset else {}
if active_preset:
    st.caption(f"Active preset: **{active_preset}**")

# ---------------------------------------------------------------------------
# Filters
# ---------------------------------------------------------------------------

with st.expander("Filters", expanded=not active_preset):
    f1, f2, f3, f4 = st.columns(4)

    with f1:
        pe_vals = universe_df["P/E"].dropna()
        pe_max_data = float(pe_vals.max()) if not pe_vals.empty else 100.0
        pe_range = st.slider(
            "P/E ratio", 0.0, max(pe_max_data, 1.0),
            (0.0, float(preset_filters.get("pe_max", pe_max_data))),
        )
        rsi_range = st.slider(
            "RSI range", 0, 100,
            (int(preset_filters.get("rsi_min", 0)), int(preset_filters.get("rsi_max", 100))),
        )

    with f2:
        mcap_vals = universe_df["Market Cap"].dropna()
        mcap_max_data = float(mcap_vals.max()) if not mcap_vals.empty else 1e12
        mcap_range = st.slider(
            "Market cap ($B)", 0.0, mcap_max_data / 1e9,
            (0.0, mcap_max_data / 1e9),
            format="%.0f",
        )
        range_pos = st.slider(
            "52-week range position (%)", 0.0, 100.0,
            (float(preset_filters.get("range_pos_min", 0.0)), float(preset_filters.get("range_pos_max", 100.0))),
        )

    with f3:
        rev_growth_min = st.slider(
            "Min revenue growth (%)", -50.0, 100.0, float(preset_filters.get("revenue_growth_min", -0.5) * 100), step=1.0,
        )
        profit_margin_min = st.slider(
            "Min profit margin (%)", -50.0, 60.0, float(preset_filters.get("profit_margin_min", -0.5) * 100), step=1.0,
        )

    with f4:
        beta_vals = universe_df["Beta"].dropna()
        beta_max_data = float(beta_vals.max()) if not beta_vals.empty else 3.0
        beta_range = st.slider("Beta", 0.0, max(beta_max_data, 1.0), (0.0, max(beta_max_data, 1.0)))
        avg_vol_vals = universe_df["Avg Volume"].dropna()
        avg_vol_max = float(avg_vol_vals.max()) if not avg_vol_vals.empty else 1e8
        avg_vol_min = st.slider("Min average volume (M)", 0.0, avg_vol_max / 1e6, 0.0)

    st.markdown("##### Technical filters")
    t1, t2, t3, t4 = st.columns(4)
    with t1:
        dma50 = st.selectbox("vs 50DMA", ["Any", "Above", "Below"], index=["Any", "Above", "Below"].index(preset_filters.get("dma50", "Any")))
    with t2:
        dma200 = st.selectbox("vs 200DMA", ["Any", "Above", "Below"], index=["Any", "Above", "Below"].index(preset_filters.get("dma200", "Any")))
    with t3:
        rsi_signal = st.selectbox("RSI signal", ["Any", "Overbought (RSI > 70)", "Oversold (RSI < 30)"])
    with t4:
        macd_signal = st.selectbox("MACD", ["Any", "Bullish", "Bearish"], index=["Any", "Bullish", "Bearish"].index(preset_filters.get("macd", "Any")))

filters = {
    "pe_min": pe_range[0], "pe_max": pe_range[1],
    "rsi_min": rsi_range[0], "rsi_max": rsi_range[1],
    "mcap_min": mcap_range[0] * 1e9, "mcap_max": mcap_range[1] * 1e9,
    "range_pos_min": range_pos[0], "range_pos_max": range_pos[1],
    "revenue_growth_min": rev_growth_min / 100,
    "profit_margin_min": profit_margin_min / 100,
    "beta_min": beta_range[0], "beta_max": beta_range[1],
    "avg_volume_min": avg_vol_min * 1e6,
    "dma50": dma50, "dma200": dma200,
    "rsi_signal": rsi_signal, "macd": macd_signal,
}

filtered = apply_filters(universe_df, filters)

st.divider()
st.caption(f"{len(filtered)} of {len(universe_df)} stocks match the current filters.")

# ---------------------------------------------------------------------------
# Top 5 highlighted cards
# ---------------------------------------------------------------------------

if not filtered.empty:
    st.subheader("Top 5")
    top5 = filtered.sort_values("RSI", ascending=False).head(5)
    cards = st.columns(len(top5))
    for col, (_, row) in zip(cards, top5.iterrows()):
        with col:
            st.markdown(f"#### {row['Ticker']}")
            st.caption(row["Name"])
            st.metric("Price", f"${row['Price']:,.2f}", f"{row['Change%']:+.2f}%")
            st.caption(f"RSI {row['RSI']:.0f} · vs200DMA {row['vs200DMA%']:+.1f}%" if pd.notna(row["vs200DMA%"]) else f"RSI {row['RSI']:.0f}")
            if st.button("Open in Analyzer", key=f"open_{row['Ticker']}"):
                st.query_params["ticker"] = row["Ticker"]
                st.switch_page("pages/2_🔍_Stock_Analyzer.py")

st.divider()

# ---------------------------------------------------------------------------
# Results table
# ---------------------------------------------------------------------------

st.subheader("Results")

if filtered.empty:
    st.info("No stocks match the current filters.")
else:
    display = filtered.copy()
    display["Market Cap"] = display["Market Cap"].map(fmt_large_number)
    display["Price"] = display["Price"].map(lambda v: f"${v:,.2f}")
    display["Change%"] = display["Change%"].map(lambda v: f"{v:+.2f}%")
    display["P/E"] = display["P/E"].map(lambda v: f"{v:.1f}" if pd.notna(v) else "—")
    display["RSI"] = display["RSI"].map(lambda v: f"{v:.0f}" if pd.notna(v) else "—")
    display["vs200DMA%"] = display["vs200DMA%"].map(lambda v: f"{v:+.1f}%" if pd.notna(v) else "—")
    display["Volume"] = display["Volume"].map(lambda v: fmt_large_number(v, currency=""))

    display = display[["Ticker", "Name", "Price", "Change%", "Market Cap", "P/E", "RSI", "vs200DMA%", "Volume"]]

    st.dataframe(display, use_container_width=True, hide_index=True, height=480)

    pick = st.selectbox("Jump to Stock Analyzer", [""] + filtered["Ticker"].tolist())
    if pick:
        st.query_params["ticker"] = pick
        st.switch_page("pages/2_🔍_Stock_Analyzer.py")

render_footer()
