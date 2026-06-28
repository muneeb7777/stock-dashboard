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


def inject_base_style():
    """Inject shared Bloomberg/TradingView-style dark theme: tighter spacing,
    bordered metric/card tiles, monospace numerics, and bigger charts."""
    import streamlit as st

    st.markdown(
        """
        <style>
        /* ---- Base layout ----------------------------------------------- */
        .main .block-container {
            font-size: 16px;
            padding-top: 1.5rem;
            padding-bottom: 3rem;
            max-width: 1500px;
        }
        .stApp {
            background-color: #0a0e14;
        }
        [data-testid="stSidebar"] {
            background-color: #0d1117;
            border-right: 1px solid #21262d;
        }

        /* ---- Typography -------------------------------------------------- */
        h1, h2, h3, h4 {
            font-weight: 600;
            letter-spacing: -0.01em;
        }
        h1 { font-size: 1.9rem !important; }
        h2, .stApp h2 { font-size: 1.35rem !important; }
        h3 { font-size: 1.1rem !important; }
        [data-testid="stCaptionContainer"] {
            color: #8b949e;
        }
        hr {
            border-color: #21262d;
            margin: 0.9rem 0;
        }

        /* ---- Tighter vertical rhythm ------------------------------------- */
        div[data-testid="stVerticalBlock"] > div {
            gap: 0.6rem;
        }

        /* ---- Metric tiles -> terminal-style cards ------------------------ */
        [data-testid="stMetric"] {
            background: linear-gradient(180deg, #161b22 0%, #11151c 100%);
            border: 1px solid #262c36;
            border-radius: 10px;
            padding: 0.7rem 1rem 0.6rem 1rem;
            box-shadow: 0 1px 2px rgba(0,0,0,0.45);
        }
        [data-testid="stMetricLabel"] {
            font-size: 0.72rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: #8b949e !important;
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

        /* ---- Bordered containers -> cards --------------------------------- */
        [data-testid="stVerticalBlockBorderWrapper"]:has(> div > div[data-testid="stVerticalBlock"]) {
            border-radius: 12px;
        }
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background: linear-gradient(180deg, #12161d 0%, #0e1218 100%);
            border: 1px solid #21262d !important;
            border-radius: 12px;
            box-shadow: 0 2px 6px rgba(0,0,0,0.35);
        }

        /* ---- Tabs ---------------------------------------------------------- */
        [data-testid="stTabs"] [data-baseweb="tab-list"] {
            gap: 4px;
            border-bottom: 1px solid #21262d;
        }
        [data-testid="stTabs"] [data-baseweb="tab"] {
            font-weight: 500;
            font-size: 0.9rem;
        }

        /* ---- Inputs / segmented controls ----------------------------------- */
        [data-testid="stTextInput"] input,
        [data-baseweb="select"] > div {
            background-color: #161b22 !important;
            border-color: #30363d !important;
            border-radius: 8px;
        }
        [data-testid="stSegmentedControl"] {
            background-color: #11151c;
            border-radius: 8px;
            padding: 2px;
        }

        /* ---- Charts ---------------------------------------------------------- */
        [data-testid="stPlotlyChart"] {
            border-radius: 10px;
            overflow: hidden;
            background-color: #0e1218;
            border: 1px solid #1c2128;
        }

        /* ---- Dataframes / tables ---------------------------------------------- */
        [data-testid="stDataFrame"] {
            border-radius: 10px;
            overflow: hidden;
            border: 1px solid #21262d;
        }

        /* ---- Buttons ------------------------------------------------------------ */
        .stButton > button {
            border-radius: 8px;
            border: 1px solid #30363d;
            font-weight: 500;
        }

        /* ---- Alerts / info boxes -------------------------------------------------- */
        [data-testid="stAlert"] {
            border-radius: 10px;
            border: 1px solid #21262d;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.markdown("### 📈 Market Analyst")
