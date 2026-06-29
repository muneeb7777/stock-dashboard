"""Shared configuration, constants, and the compliance disclosure string."""

import os

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

APP_NAME = "Stock Market Analyst"

DISCLOSURE = (
    "This dashboard is for educational and informational purposes only. "
    "It is not financial advice, not a recommendation to buy or sell any security, "
    "and is not personalized to your situation. Consult a licensed advisor before "
    "making investment decisions."
)


def get_secret(key):
    try:
        return st.secrets[key]
    except Exception:
        return os.getenv(key)


def get_anthropic_key():
    return (get_secret("ANTHROPIC_API_KEY") or "").strip() or None


def get_fred_key():
    return (get_secret("FRED_API_KEY") or "").strip() or None


def get_gemini_key():
    return (get_secret("GEMINI_API_KEY") or "").strip() or None


def get_groq_key():
    return (get_secret("GROQ_API_KEY") or "").strip() or None


def fmt_large_number(value, currency="$"):
    """Format a large number with B/M/T suffixes, e.g. 1234567890 -> '$1.23B'."""
    if value is None:
        return "—"
    abs_value = abs(value)
    sign = "-" if value < 0 else ""
    if abs_value >= 1e12:
        return f"{sign}{currency}{abs_value / 1e12:.2f}T"
    if abs_value >= 1e9:
        return f"{sign}{currency}{abs_value / 1e9:.2f}B"
    if abs_value >= 1e6:
        return f"{sign}{currency}{abs_value / 1e6:.2f}M"
    if abs_value >= 1e3:
        return f"{sign}{currency}{abs_value / 1e3:.2f}K"
    return f"{sign}{currency}{abs_value:,.2f}"


def fmt_pct(value, decimals=2):
    """Format a fraction (0.123) as a percentage string ('12.30%')."""
    if value is None:
        return "—"
    return f"{value * 100:.{decimals}f}%"


def fmt_num(value, decimals=2):
    if value is None:
        return "—"
    return f"{value:,.{decimals}f}"


def render_footer():
    """Render the standard disclosure footer. Import and call at the bottom of every page."""
    import streamlit as st

    st.divider()
    st.caption(DISCLOSURE)


_STRUCTURAL_CSS = """
    .main .block-container {
        font-size: 16px;
        padding-top: 1.5rem;
        padding-bottom: 3rem;
        max-width: 1500px;
    }
    h1, h2, h3, h4 { font-weight: 600; letter-spacing: -0.01em; }
    h1 { font-size: 1.9rem !important; }
    h2, .stApp h2 { font-size: 1.35rem !important; }
    h3 { font-size: 1.1rem !important; }
    hr { margin: 0.9rem 0; }
    div[data-testid="stVerticalBlock"] > div { gap: 0.6rem; }
    [data-testid="stMetric"] {
        border-radius: 10px;
        padding: 0.7rem 1rem 0.6rem 1rem;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.72rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        font-weight: 600;
    }
    [data-testid="stMetricValue"] {
        font-family: 'SFMono-Regular', 'Consolas', 'Menlo', monospace;
        font-size: 1.45rem;
        font-weight: 600;
    }
    [data-testid="stMetricDelta"] {
        font-family: 'SFMono-Regular', 'Consolas', 'Menlo', monospace;
        font-size: 0.85rem;
    }
    [data-testid="stVerticalBlockBorderWrapper"]:has(> div > div[data-testid="stVerticalBlock"]) {
        border-radius: 12px;
    }
    div[data-testid="stVerticalBlockBorderWrapper"] { border-radius: 12px; }
    [data-testid="stTabs"] [data-baseweb="tab-list"] { gap: 4px; }
    [data-testid="stTabs"] [data-baseweb="tab"] { font-weight: 500; font-size: 0.9rem; }
    [data-testid="stTextInput"] input,
    [data-baseweb="select"] > div { border-radius: 8px; }
    [data-testid="stSegmentedControl"] { border-radius: 8px; padding: 2px; }
    [data-testid="stPlotlyChart"] { border-radius: 10px; overflow: hidden; }
    [data-testid="stDataFrame"] { border-radius: 10px; overflow: hidden; }
    .stButton > button { border-radius: 8px; font-weight: 500; }
    [data-testid="stAlert"] { border-radius: 10px; }
"""

_DARK_CSS = """
    .stApp { background-color: #0a0e14; }
    [data-testid="stSidebar"] { background-color: #0d1117; border-right: 1px solid #21262d; }
    [data-testid="stCaptionContainer"] { color: #8b949e; }
    hr { border-color: #21262d; }
    [data-testid="stMetric"] {
        background: linear-gradient(180deg, #161b22 0%, #11151c 100%);
        border: 1px solid #262c36;
        box-shadow: 0 1px 2px rgba(0,0,0,0.45);
    }
    [data-testid="stMetricLabel"] { color: #8b949e !important; }
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: linear-gradient(180deg, #12161d 0%, #0e1218 100%);
        border: 1px solid #21262d !important;
        box-shadow: 0 2px 6px rgba(0,0,0,0.35);
    }
    [data-testid="stTabs"] [data-baseweb="tab-list"] { border-bottom: 1px solid #21262d; }
    [data-testid="stTextInput"] input,
    [data-baseweb="select"] > div { background-color: #161b22 !important; border-color: #30363d !important; }
    [data-testid="stSegmentedControl"] { background-color: #11151c; }
    [data-testid="stPlotlyChart"] { background-color: #0e1218; border: 1px solid #1c2128; }
    [data-testid="stDataFrame"] { border: 1px solid #21262d; }
    .stButton > button { border: 1px solid #30363d; }
    [data-testid="stAlert"] { border: 1px solid #21262d; }
"""

_LIGHT_CSS = """
    .stApp { background-color: #f0f2f6 !important; }
    [data-testid="stSidebar"] {
        background-color: #ffffff !important;
        border-right: 1px solid #e0e4ea !important;
    }
    [data-testid="stCaptionContainer"] { color: #6b7280 !important; }
    hr { border-color: #e0e4ea !important; }
    [data-testid="stMetric"] {
        background: linear-gradient(180deg, #ffffff 0%, #f5f6f8 100%) !important;
        border: 1px solid #dde1e7 !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.08) !important;
    }
    [data-testid="stMetricLabel"] { color: #6b7280 !important; }
    [data-testid="stMetricValue"] { color: #111827 !important; }
    [data-testid="stMetricDelta"] { color: #374151 !important; }
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: linear-gradient(180deg, #ffffff 0%, #f9fafb 100%) !important;
        border: 1px solid #dde1e7 !important;
        box-shadow: 0 2px 6px rgba(0,0,0,0.06) !important;
    }
    [data-testid="stTabs"] [data-baseweb="tab-list"] { border-bottom: 1px solid #dde1e7 !important; }
    [data-testid="stTextInput"] input,
    [data-baseweb="select"] > div { background-color: #ffffff !important; border-color: #d0d5dd !important; }
    [data-testid="stSegmentedControl"] { background-color: #edf0f4 !important; }
    [data-testid="stPlotlyChart"] { background-color: #ffffff !important; border: 1px solid #e0e4ea !important; }
    [data-testid="stDataFrame"] { border: 1px solid #dde1e7 !important; }
    .stButton > button { border: 1px solid #d0d5dd !important; }
    [data-testid="stAlert"] { border: 1px solid #dde1e7 !important; }
"""


def inject_base_style():
    """Inject structural CSS + the active color theme. Called at the top of
    every page so the theme toggle and styles are always present regardless of
    which page the user navigates to.
    """
    # Sidebar: title + theme toggle (persists across navigation via session_state)
    with st.sidebar:
        st.markdown("### 📈 Market Analyst")
        st.caption("Theme")
        st.radio(
            "Theme",
            options=["Dark", "Light", "System"],
            key="theme",
            horizontal=True,
            label_visibility="collapsed",
        )

    theme = st.session_state.get("theme", "Dark")
    color_css = _DARK_CSS if theme == "Dark" else (_LIGHT_CSS if theme == "Light" else "")
    st.markdown(f"<style>{_STRUCTURAL_CSS}{color_css}</style>", unsafe_allow_html=True)
