from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from lib.config import APP_NAME, inject_base_style

st.set_page_config(
    page_title=f"Live Chart - {APP_NAME}",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_base_style()

st.markdown(
    """
    <style>
    header[data-testid="stHeader"] { display: none; }
    footer { display: none; }
    .main .block-container,
    section.main > div {
        padding: 0 !important;
        margin: 0 !important;
        max-width: 100% !important;
    }
    div[data-testid="stVerticalBlock"] {
        gap: 0 !important;
    }
    div[data-testid="element-container"] {
        margin: 0 !important;
    }
    iframe {
        border: none;
        display: block;
        width: 100%;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

STATIC_DIR = Path(__file__).resolve().parent.parent / "static" / "live-chart"


@st.cache_data
def load_live_chart_html():
    index_html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")

    js_file = next((STATIC_DIR / "assets").glob("index-*.js"))
    css_file = next((STATIC_DIR / "assets").glob("index-*.css"))

    js_content = js_file.read_text(encoding="utf-8")
    css_content = css_file.read_text(encoding="utf-8")

    html = index_html.replace(
        f'<script type="module" crossorigin src="/assets/{js_file.name}"></script>',
        f"<script type=\"module\">{js_content}</script>",
    )
    html = html.replace(
        f'<link rel="stylesheet" crossorigin href="/assets/{css_file.name}">',
        f"<style>{css_content}</style>",
    )
    return html


if not (STATIC_DIR / "index.html").exists():
    st.error(
        "Live chart build not found. Run `npm run build` in `live-chart/` and "
        "copy `live-chart/dist/*` into `static/live-chart/`."
    )
else:
    components.html(load_live_chart_html(), height=1200, scrolling=True)
