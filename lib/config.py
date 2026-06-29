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
    /* ---- Backgrounds --------------------------------------------------- */
    .stApp, .main { background-color: #131722 !important; }
    .block-container { background-color: #131722 !important; }
    section[data-testid="stSidebar"],
    [data-testid="stSidebar"] {
        background-color: #1e222d !important;
        border-right: 1px solid #2a2e39 !important;
    }
    /* ---- Text ---------------------------------------------------------- */
    [data-testid="stCaptionContainer"] { color: #787b86 !important; }
    hr { border-color: #2a2e39 !important; }
    /* ---- Metric tiles -------------------------------------------------- */
    [data-testid="stMetric"] {
        background-color: #1e222d !important;
        border: 1px solid #2a2e39 !important;
        box-shadow: none !important;
    }
    [data-testid="stMetricLabel"] { color: #787b86 !important; }
    [data-testid="stMetricValue"] { color: #d1d4dc !important; }
    /* ---- Cards / bordered containers ----------------------------------- */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #1e222d !important;
        border: 1px solid #2a2e39 !important;
        box-shadow: none !important;
    }
    /* ---- Tabs ---------------------------------------------------------- */
    [data-testid="stTabs"] [data-baseweb="tab-list"] { border-bottom: 1px solid #2a2e39; }
    [data-testid="stTabs"] [data-baseweb="tab"] { color: #787b86 !important; }
    [data-testid="stTabs"] [aria-selected="true"] { color: #2962ff !important; }
    /* ---- Inputs -------------------------------------------------------- */
    [data-testid="stTextInput"] input,
    [data-baseweb="select"] > div {
        background-color: #1e222d !important;
        border-color: #2a2e39 !important;
        color: #d1d4dc !important;
    }
    [data-testid="stSegmentedControl"] { background-color: #1e222d !important; }
    /* ---- Charts -------------------------------------------------------- */
    [data-testid="stPlotlyChart"] {
        background-color: #131722 !important;
        border: 1px solid #2a2e39 !important;
    }
    /* ---- Data tables --------------------------------------------------- */
    [data-testid="stDataFrame"] { border: 1px solid #2a2e39 !important; }
    /* ---- Buttons ------------------------------------------------------- */
    .stButton > button {
        background-color: #2962ff !important;
        color: #ffffff !important;
        border: none !important;
    }
    .stButton > button:hover { background-color: #1e53e5 !important; }
    /* ---- Alerts -------------------------------------------------------- */
    [data-testid="stAlert"] { border: 1px solid #2a2e39 !important; }
"""

_LIGHT_CSS = """
    /* ---- Backgrounds --------------------------------------------------- */
    .stApp, .main { background-color: #ffffff !important; }
    .block-container { background-color: #ffffff !important; }
    section[data-testid="stSidebar"],
    [data-testid="stSidebar"] {
        background-color: #f8f9fa !important;
        border-right: 1px solid #e0e3eb !important;
    }
    /* ---- Text — blanket override so no dark remnants show through ------- */
    .stApp, .stApp p, .stApp span, .stApp div, .stApp label,
    .stMarkdown, .stMarkdown p, .stMarkdown span,
    section[data-testid="stSidebar"], section[data-testid="stSidebar"] * {
        color: #131722 !important;
    }
    h1, h2, h3, h4, h5, h6 { color: #131722 !important; }
    [data-testid="stCaptionContainer"] { color: #555f73 !important; }
    hr { border-color: #e0e3eb !important; }
    /* ---- Metric tiles -------------------------------------------------- */
    [data-testid="stMetric"] {
        background-color: #f0f3fa !important;
        border: 1px solid #e0e3eb !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06) !important;
    }
    [data-testid="stMetricLabel"] { color: #555f73 !important; }
    [data-testid="stMetricValue"] { color: #131722 !important; }
    [data-testid="stMetricDelta"] { color: #131722 !important; }
    /* ---- Cards / bordered containers ----------------------------------- */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #f0f3fa !important;
        border: 1px solid #e0e3eb !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06) !important;
    }
    /* ---- Tabs ---------------------------------------------------------- */
    [data-testid="stTabs"] [data-baseweb="tab-list"] {
        background-color: #ffffff !important;
        border-bottom: 1px solid #e0e3eb !important;
    }
    [data-testid="stTabs"] [data-baseweb="tab"] { color: #555f73 !important; }
    [data-testid="stTabs"] [aria-selected="true"] { color: #2962ff !important; }
    /* ---- Inputs -------------------------------------------------------- */
    [data-testid="stTextInput"] input,
    [data-baseweb="select"] > div {
        background-color: #ffffff !important;
        border-color: #cccccc !important;
        color: #131722 !important;
    }
    [data-testid="stSelectbox"] label { color: #131722 !important; }
    [data-testid="stSegmentedControl"] { background-color: #f0f3fa !important; }
    [data-testid="stRadio"] label,
    [data-testid="stCheckbox"] label { color: #131722 !important; }
    /* ---- Charts -------------------------------------------------------- */
    [data-testid="stPlotlyChart"] {
        background-color: #ffffff !important;
        border: 1px solid #e0e3eb !important;
    }
    /* ---- Data tables --------------------------------------------------- */
    [data-testid="stDataFrame"] { border: 1px solid #e0e3eb !important; }
    [data-testid="stDataFrame"] * { color: #131722 !important; }
    /* ---- Buttons ------------------------------------------------------- */
    .stButton > button {
        background-color: #2962ff !important;
        color: #ffffff !important;
        border: none !important;
    }
    .stButton > button:hover { background-color: #1e53e5 !important; }
    /* ---- Alerts -------------------------------------------------------- */
    [data-testid="stAlert"] {
        background-color: #f0f3fa !important;
        border: 1px solid #e0e3eb !important;
    }
    [data-testid="stAlert"] * { color: #131722 !important; }
    /* ---- BasewUI dropdowns --------------------------------------------- */
    [data-baseweb="popover"],
    [data-baseweb="menu"] { background-color: #ffffff !important; }
    [data-baseweb="option"] {
        background-color: #ffffff !important;
        color: #131722 !important;
    }
    [data-baseweb="option"]:hover { background-color: #f0f3fa !important; }
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
