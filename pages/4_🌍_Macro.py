import plotly.graph_objects as go
import streamlit as st

from lib import claude_analyst
from lib.config import APP_NAME, inject_base_style, render_footer
from lib.macro import fred_available, get_macro_snapshot
from lib.rates import get_yield_curve
from utils.theme import apply_theme, render_theme_toggle

st.set_page_config(page_title=f"Macro - {APP_NAME}", page_icon="🌍", layout="wide")
apply_theme()
inject_base_style()

st.title("🌍 Macro")

if not fred_available():
    st.info(
        "Macro indicators require a FRED API key. Set `FRED_API_KEY` in Streamlit secrets "
        "to enable this page. You can get a free key at https://fred.stlouisfed.org/docs/api/api_key.html"
    )
    render_footer()
    st.stop()

# ---------------------------------------------------------------------------
# Indicators
# ---------------------------------------------------------------------------

st.subheader("Indicators")

snapshot = get_macro_snapshot()

if not snapshot:
    st.warning("Macro data is temporarily unavailable.")
else:
    items = list(snapshot.items())
    for row_start in range(0, len(items), 4):
        cols = st.columns(4)
        for col, (label, data) in zip(cols, items[row_start:row_start + 4]):
            with col:
                delta = None
                if data.get("prior_value") is not None:
                    delta = data["value"] - data["prior_value"]
                unit = data["units"]
                suffix = "%" if "%" in unit or unit == "pp" else ""
                value_str = f"{data['value']:.2f}{suffix}"
                delta_str = f"{delta:+.2f}{suffix}" if delta is not None else None
                st.metric(label, value_str, delta_str)
                st.caption(f"As of {data['date'].strftime('%b %Y')}")

# ---------------------------------------------------------------------------
# Yield curve
# ---------------------------------------------------------------------------

st.divider()
st.subheader("Treasury yield curve")

curve = get_yield_curve()
yield_curve_summary = "unavailable"
if not curve.empty:
    fig = go.Figure(go.Scatter(
        x=curve["maturity"], y=curve["yield"], mode="lines+markers",
        line=dict(color="#5dade2", width=2), marker=dict(size=7),
    ))
    fig.update_layout(
        template="plotly_dark", height=400, margin=dict(l=10, r=10, t=10, b=10),
        xaxis_title="Maturity", yaxis_title="Yield (%)",
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    yield_curve_summary = ", ".join(f"{m}: {y:.2f}%" for m, y in zip(curve["maturity"], curve["yield"]))
else:
    st.warning("Yield curve data is temporarily unavailable.")

# ---------------------------------------------------------------------------
# Claude macro pulse-check
# ---------------------------------------------------------------------------

st.divider()
st.subheader("Macro pulse-check")

if not claude_analyst.is_configured():
    st.info("AI macro summaries are unavailable. Set `GROQ_API_KEY` in Streamlit secrets to enable them.")
else:
    if st.button("Generate macro pulse-check"):
        if not snapshot:
            st.warning("No macro data available to summarize.")
        else:
            try:
                st.write_stream(claude_analyst.macro_pulse_check(snapshot, yield_curve_summary))
            except Exception as e:
                st.error(f"AI analysis failed: {e}")

render_footer()
