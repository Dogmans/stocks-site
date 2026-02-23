from dotenv import load_dotenv
import requests
import os

load_dotenv()
API_KEY = os.getenv("FINANCIAL_MODELING_PREP_API_KEY")
API_BASE = "https://financialmodelingprep.com/api/v3"

def get_news(symbols, max_articles=10):
    """
    Fetch news for one or more symbols. Returns a list of news articles.
    If multiple symbols, deduplicates by URL.
    """
    if isinstance(symbols, str):
        symbols = [symbols]
    if not symbols:
        return []
    news = []
    if len(symbols) == 1:
        tickers = symbols[0]
        url = f"{API_BASE}/stock_news"
        params = {"tickers": tickers, "limit": max_articles, "apikey": API_KEY}
        resp = requests.get(url, params=params)
        news = resp.json() if resp.ok and resp.json() else []
    else:
        all_articles = []
        seen_urls = set()
        for symbol in symbols:
            url = f"{API_BASE}/stock_news"
            params = {"tickers": symbol, "limit": max_articles, "apikey": API_KEY}
            resp = requests.get(url, params=params)
            articles = resp.json() if resp.ok and resp.json() else []
            for article in articles:
                url_key = article.get("url")
                if url_key and url_key not in seen_urls:
                    all_articles.append(article)
                    seen_urls.add(url_key)
        news = all_articles
    return news

import requests
import os
from dotenv import load_dotenv

def get_bulk_quotes(symbols):
    """
    Fetch quotes for multiple symbols in a single API call.
    Returns a dict mapping symbol to quote dict.
    """
    if not symbols:
        return {}
    url = f"{API_BASE}/quote/{','.join(symbols)}"
    params = {"apikey": API_KEY}
    resp = requests.get(url, params=params)
    if resp.ok:
        quotes = resp.json()
        return {q['symbol']: q for q in quotes}
    return {}

def search_symbol(query):
    url = f"{API_BASE}/search"
    params = {"query": query, "apikey": API_KEY, "limit": 10}
    resp = requests.get(url, params=params)
    if resp.ok:
        return resp.json()
    return []
