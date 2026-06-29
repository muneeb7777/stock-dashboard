import streamlit as st

def apply_theme():
    theme = st.query_params.get("theme", "Dark")
    if theme == "Light":
        st.markdown("""<style>
        html, body, .stApp, [data-testid="stAppViewContainer"],
        [data-testid="stHeader"], section[data-testid="stSidebar"],
        .main, .block-container { background-color: #ffffff !important; }
        [data-testid="stSidebar"] { background-color: #f8f9fa !important; }
        p, h1, h2, h3, h4, h5, span, div, label,
        [data-testid="stMarkdownContainer"] { color: #131722 !important; }
        .stButton button { background-color: #f0f3fa !important; color: #131722 !important; border: 1px solid #cccccc !important; }
        </style>""", unsafe_allow_html=True)

def theme_sidebar():
    current = st.query_params.get("theme", "Dark")
    choice = st.sidebar.radio("🎨 Theme", ["Dark", "Light"],
        index=0 if current=="Dark" else 1, horizontal=True)
    if choice != current:
        st.query_params["theme"] = choice
        st.rerun()
