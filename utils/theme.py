import streamlit as st

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
    /* ---- Semantic card classes (dark) ---------------------------------- */
    .tv-card-bull    { background-color: #0d2b0d; }
    .tv-card-bear    { background-color: #2b0d0d; }
    .tv-card-amber   { background-color: #2b2300; }
    .tv-card-blue    { background-color: #0d1a2b; }
    .tv-card-neutral { background-color: #1e1e1e; }
    .tv-card-warm    { background-color: #1e1a0d; }
    .tv-banner-bull  { background-color: #0d2b0d; }
    .tv-banner-bear  { background-color: #2b0d0d; }
    .tv-vcard-container { border: 1px solid #2d2d2d; border-radius: 8px; padding: 10px 12px; margin-bottom: 8px; }
    .tv-corr-track   { background-color: #2a2a2a; border-radius: 4px; height: 8px; }
"""

_LIGHT_CSS = """
    /* ---- Backgrounds --------------------------------------------------- */
    .stApp, .main, .block-container { background-color: #ffffff !important; }
    section[data-testid="stSidebar"],
    [data-testid="stSidebar"] {
        background-color: #f8f9fa !important;
        border-right: 1px solid #e0e3eb !important;
    }
    /* ---- Force text dark everywhere ------------------------------------ */
    p, h1, h2, h3, h4, h5, h6, span, label, div {
        color: #131722 !important;
    }
    .stApp, .stApp p, .stApp span, .stApp label,
    .stMarkdown, .stMarkdown p, .stMarkdown span,
    section[data-testid="stSidebar"], section[data-testid="stSidebar"] * {
        color: #131722 !important;
    }
    [data-testid="stCaptionContainer"] { color: #555f73 !important; }
    hr { border-color: #e0e3eb !important; }
    /* ---- Fix ALL stMetric / metric-container variants ------------------ */
    div[data-testid="stMetric"],
    div[data-testid="metric-container"],
    div[class*="stMetric"] {
        background-color: #f0f3fa !important;
        color: #131722 !important;
    }
    [data-testid="stMetric"] {
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
    .stMultiSelect span, .stSelectbox * { color: #131722 !important; }
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
    /* ---- Alerts / info boxes ------------------------------------------- */
    .stAlert, [data-baseweb="notification"] {
        filter: brightness(3) saturate(0.3) !important;
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
    /* ---- Segmented control / timeframe buttons ------------------------- */
    [data-testid="stSegmentedControl"] {
        background-color: #e0e3eb !important;
        border-radius: 8px !important;
        padding: 2px !important;
    }
    [data-testid="stSegmentedControl"] label,
    [data-testid="stSegmentedControl"] label > div,
    [data-testid="stSegmentedControl"] button,
    [data-testid="stSegmentedControl"] button > div,
    [data-testid="stSegmentedControl"] [data-baseweb="button"],
    [data-testid="stSegmentedControl"] [data-baseweb="button"] > div {
        background-color: transparent !important;
        color: #131722 !important;
        box-shadow: none !important;
    }
    [data-testid="stSegmentedControl"] p,
    [data-testid="stSegmentedControl"] span {
        color: #131722 !important;
    }
    /* Active / selected segment */
    [data-testid="stSegmentedControl"] [data-active="true"],
    [data-testid="stSegmentedControl"] [aria-checked="true"],
    [data-testid="stSegmentedControl"] [aria-pressed="true"],
    [data-testid="stSegmentedControl"] input[type="radio"]:checked + div {
        background-color: #ffffff !important;
        color: #131722 !important;
        border-radius: 6px !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.15) !important;
    }
    /* ---- Semantic card classes (light) --------------------------------- */
    .tv-card-bull    { background-color: #e8f5e9 !important; }
    .tv-card-bear    { background-color: #fdecea !important; }
    .tv-card-amber   { background-color: #fff8e1 !important; }
    .tv-card-blue    { background-color: #e3f0fd !important; }
    .tv-card-neutral { background-color: #f5f6f8 !important; }
    .tv-card-warm    { background-color: #fef3e2 !important; }
    .tv-banner-bull  { background-color: #e8f5e9 !important; }
    .tv-banner-bear  { background-color: #fdecea !important; }
    .tv-vcard-container { background-color: #f5f6f8 !important; border-color: #dde1e7 !important; }
    .tv-corr-track   { background-color: #e0e3eb !important; }
"""


def apply_theme() -> None:
    """Inject theme CSS based on st.query_params["theme"]. Call after st.set_page_config()."""
    theme = st.query_params.get("theme", "Dark")
    if theme == "Light":
        st.markdown(f"<style>{_LIGHT_CSS}</style>", unsafe_allow_html=True)
    elif theme == "Dark":
        st.markdown(f"<style>{_DARK_CSS}</style>", unsafe_allow_html=True)
    # System: no override — Streamlit default


def render_theme_toggle() -> None:
    """Render the Dark/Light/System radio inside the active sidebar context."""
    theme = st.query_params.get("theme", "Dark")
    valid = ("Dark", "Light", "System")
    idx = valid.index(theme) if theme in valid else 0
    st.caption("Theme")
    selected = st.radio(
        "Theme",
        options=list(valid),
        index=idx,
        key="theme_radio",
        horizontal=True,
        label_visibility="collapsed",
    )
    if selected != theme:
        st.query_params["theme"] = selected
        st.rerun()
