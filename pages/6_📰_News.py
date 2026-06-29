import streamlit as st

from lib.config import APP_NAME, inject_base_style, render_footer
from lib.news import market_news, ticker_news, time_ago
from utils.theme import apply_theme, theme_sidebar

st.set_page_config(page_title=f"News - {APP_NAME}", page_icon="📰", layout="wide")
apply_theme()
inject_base_style()
theme_sidebar()

st.title("📰 News")

tab1, tab2 = st.tabs(["Market headlines", "By ticker"])


def render_news_list(items):
    if not items:
        st.info("No news available right now.")
        return
    for item in items:
        with st.container(border=True):
            st.markdown(f"**{item['title']}**")
            meta = item["publisher"]
            ago = time_ago(item["time"])
            if ago:
                meta += f" · {ago}"
            st.caption(meta)
            summary = (item.get("summary") or "").strip()
            if summary:
                st.write(summary[:320] + ("..." if len(summary) > 320 else ""))
            if item.get("link"):
                st.markdown(f"[Read more]({item['link']})")


with tab1:
    st.subheader("Aggregated market headlines")
    render_news_list(market_news(limit=20))

with tab2:
    st.subheader("Search by ticker")
    ticker = st.text_input("Ticker", value="AAPL", key="news_ticker").strip().upper()
    if ticker:
        render_news_list(ticker_news(ticker, limit=15))

render_footer()
