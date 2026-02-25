from datetime import date
import requests

from pydantic import BaseModel
from config import API_KEY, API_BASE


def get_quote(symbol):
    url = f"{API_BASE}/quote/{symbol}"
    params = {"apikey": API_KEY}
    resp = requests.get(url, params=params)
    if resp.ok and resp.json():
        return resp.json()[0]
    return None


def get_profile(symbol):
    url = f"{API_BASE}/profile/{symbol}"
    params = {"apikey": API_KEY}
    resp = requests.get(url, params=params)
    if resp.ok and resp.json():
        return resp.json()[0]
    return None


def get_filings(symbol):
    """
    Fetch SEC filings for a given symbol from FMP API.
    Args:
        symbol (str): Stock ticker symbol.
    Returns:
        list: List of filings dictionaries.
    """
    url = f"{API_BASE}/sec-filings-search/symbol"
    params = {"symbol": symbol, "apikey": API_KEY}
    resp = requests.get(url, params=params)
    if resp.ok and resp.json():
        return resp.json()
    return []


def get_historical(symbol, metric, period):
    # Map period to API params
    if period == "Day":
        timeseries = 13  # 6.5 hours * 2 intervals per hour (30min)
        interval = "30min"
    elif period == "Week":
        timeseries = 65  # 5 trading days * 13 hours * 1 interval per 30min
        interval = "30min"
    elif period == "Month":
        timeseries = 22  # 22 trading days
        interval = "1day"
    elif period == "Year":
        timeseries = 252
        interval = "1day"
    elif period == "5 Year":
        timeseries = 1260
        interval = "1day"
    else:
        timeseries = 1
        interval = "5min"
    url = f"{API_BASE}/historical-chart/{interval}/{symbol}"
    params = {"apikey": API_KEY}
    resp = requests.get(url, params=params)
    if resp.ok and resp.json():
        data = resp.json()[:timeseries]
        return [d[metric] for d in data if metric in d], [d["date"] for d in data if metric in d]
    return [], []


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
        url = f"{API_BASE}/news/stock"
        params = {"symbols": tickers, "limit": max_articles, "apikey": API_KEY}
        resp = requests.get(url, params=params)
        news = resp.json() if resp.ok and resp.json() else []
    else:
        all_articles = []
        seen_urls = set()
        for symbol in symbols:
            url = f"{API_BASE}/news/stock"
            params = {"symbols": symbol, "limit": max_articles, "apikey": API_KEY}
            resp = requests.get(url, params=params)
            articles = resp.json() if resp.ok and resp.json() else []
            for article in articles:
                url_key = article.get("url")
                if url_key and url_key not in seen_urls:
                    all_articles.append(article)
                    seen_urls.add(url_key)
        news = all_articles
    return news


class Event(BaseModel):
    date: str
    name: str
    type: str
    symbol: str


def get_events_for_symbols(symbols=[], from_date: date=None, to_date: date=None) -> list[Event]:
    """
    Fetch upcoming events (earnings, dividends, splits) for a given stock symbol from FMP API.
    Args:
        symbol (str): Stock ticker symbol.
        from_date (str): Start date for events in YYYY-MM-DD format.
        to_date (str): End date for events in YYYY-MM-DD format.
    Returns:
        list: List of event dictionaries with keys: date, name, type, and symbol.
    """
    events = []
    event_sources = [
        {
            "url": f"{API_BASE}/earnings-calendar",
            "type": "earnings",
            "name": "Earnings Report"
        },
        {
            "url": f"{API_BASE}/dividends-calendar",
            "type": "dividend",
            "name": "Dividend"
        },
        {
            "url": f"{API_BASE}/splits-calendar",
            "type": "split",
            "name": "Stock Split"
        },
    ]
    params={"apikey": API_KEY}
    if from_date:
        params["from"] = from_date.isoformat() if isinstance(from_date, date) else from_date
    if to_date:
        params["to"] = to_date.isoformat() if isinstance(to_date, date) else to_date
    for src in event_sources:
        resp = requests.get(src["url"], params=params)
        if resp.ok and resp.json():
            for item in resp.json():
                events.append(Event(
                    date=item.get("date", item.get("paymentDate")),
                    name=src["name"],
                    type=src["type"],
                    symbol=item["symbol"]
                ))
    
    if len(symbols):
        events = [e for e in events if e.symbol in symbols]

    return events


def get_bulk_quotes(symbols):
    """
    Fetch quotes for multiple symbols in a single API call.
    Returns a dict mapping symbol to quote dict.
    """
    if not symbols:
        return {}
    url = f"{API_BASE}/batch-quote"
    params = {"symbols": ','.join(symbols), "apikey": API_KEY}
    resp = requests.get(url, params=params)
    if resp.ok:
        quotes = resp.json()
        return {q['symbol']: q for q in quotes}
    return {}


def search_symbol(query):
    url = f"{API_BASE}/search-symbol"
    params = {"query": query, "apikey": API_KEY, "limit": 10}
    resp = requests.get(url, params=params)
    if resp.ok:
        return resp.json()
    return []
