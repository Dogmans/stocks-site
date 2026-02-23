import streamlit as st
import requests
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("FINANCIAL_MODELING_PREP_API_KEY")
API_BASE = "https://financialmodelingprep.com/api/v3"

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

    # If only one symbol, use old logic for efficiency
    if len(symbols) == 1:
        tickers = symbols[0]
        url = f"{API_BASE}/stock_news"
        params = {"tickers": tickers, "limit": max_articles, "apikey": API_KEY}
        resp = requests.get(url, params=params)
        news = resp.json() if resp.ok and resp.json() else []
        if today_only:
            today_str = datetime.now().strftime("%Y-%m-%d")
            news = [n for n in news if n.get("publishedDate", "").startswith(today_str)]
    else:
        # For multiple symbols, fetch per-symbol and collate
        all_articles = []
        seen_urls = set()
        today_str = datetime.now().strftime("%Y-%m-%d") if today_only else None
        for symbol in symbols:
            url = f"{API_BASE}/stock_news"
            params = {"tickers": symbol, "limit": max_articles, "apikey": API_KEY}
            resp = requests.get(url, params=params)
            articles = resp.json() if resp.ok and resp.json() else []
            if today_only:
                articles = [n for n in articles if n.get("publishedDate", "").startswith(today_str)]
            for article in articles:
                # Deduplicate by URL
                url_key = article.get("url")
                if url_key and url_key not in seen_urls:
                    all_articles.append(article)
                    seen_urls.add(url_key)
        news = all_articles

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
