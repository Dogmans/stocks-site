import streamlit as st
from datetime import datetime
from fmp_api import get_news

def news_feed(symbols, max_articles=10, today_only=False, show_header=True):
    """
    Display a news feed for one or more symbols.
    Args:
        symbols (str or list): Symbol or list of symbols to fetch news for.
        max_articles (int): Maximum number of articles to display.
        today_only (bool): If True, only show articles from today.
        show_header (bool): If True, show a header above the news feed.
    """
    if isinstance(symbols, str):
        symbols = [symbols]
    if not symbols:
        st.info("No symbols provided for news feed.")
        return

    if today_only:
        news = get_news(symbols, max_articles=max_articles)
    else:
        news = get_news(symbols, from_date=datetime.date.today() - datetime.timedelta(days=7), max_articles=max_articles)
    if not news:
        st.info("No news articles found for the selected symbols.")
        return
    
    # Sort and limit total articles for display
    news_sorted = sorted(news, key=lambda x: x.get("publishedDate", ""), reverse=True)
    if len(symbols) > 1:
        # For multi-symbol, show up to max_articles * len(symbols) (or just all)
        news_sorted = news_sorted[:max_articles * len(symbols)]
    else:
        news_sorted = news_sorted[:max_articles]

    if show_header:
        st.subheader("Latest News")
    if news_sorted:
        expanded = True
        for i, article in enumerate(news_sorted):
            with st.expander(f"{article.get('title', 'News')} — {article.get('publishedDate', '')}", expanded=expanded):
                st.write(f"**Source:** {article.get('site', '')}")
                st.write(f"**Date:** {article.get('publishedDate', '')}")
                st.write(f"**Link:** [{article.get('url', 'Read')}]({article.get('url', '')})")
                st.write(f"**Summary:** {article.get('text', '')}")
            expanded = False
    else:
        st.info("No news articles found for the selected symbols.")
