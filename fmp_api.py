
import datetime
import requests

from pydantic import BaseModel
from config import API_KEY, API_BASE


def make_authorised_request(url, params=None):
    """
    Helper to make a GET request with API key injected into params.
    Returns the response object.
    """
    if params is None:
        params = {}
    params = dict(params)  # copy to avoid mutating caller
    params["apikey"] = API_KEY
    return requests.get(url, params=params)


def get_quote(symbol):
    url = f"{API_BASE}/quote/{symbol}"
    resp = make_authorised_request(url)
    if resp.ok and resp.json():
        return resp.json()[0]
    return None


def get_profile(symbol):
    url = f"{API_BASE}/profile/{symbol}"
    resp = make_authorised_request(url)
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
    params = {"symbol": symbol}
    resp = make_authorised_request(url, params)
    if resp.ok and resp.json():
        return resp.json()
    return []


# 1. Define the Pydantic Model for a Historical Data Point
class HistoricalQuote(BaseModel):
    date: str
    open: float
    low: float
    high: float
    close: float
    volume: int

    @property
    def change(self) -> float:
        return self.close - self.open

    @property
    def percent_change(self) -> float:
        return (self.change / self.open) * 100
    
    # Optional: If you want to automatically convert the string date to a datetime object
    @property
    def datetime_obj(self) -> datetime:
        return datetime.strptime(self.date, "%Y-%m-%d %H:%M:%S" if ":" in self.date else "%Y-%m-%d")


def get_historical(symbol, period):
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
    url = f"{API_BASE}/historical-chart/{interval}"
    resp = make_authorised_request(url, params={"symbol": symbol, "limit": timeseries})
    if resp.ok and resp.json():
        return [HistoricalQuote(**quote) for quote in resp.json()[:timeseries]]
    return []


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
        params = {"symbols": tickers, "limit": max_articles}
        resp = make_authorised_request(url, params)
        news = resp.json() if resp.ok and resp.json() else []
    else:
        all_articles = []
        seen_urls = set()
        for symbol in symbols:
            url = f"{API_BASE}/news/stock"
            params = {"symbols": symbol, "limit": max_articles}
            resp = make_authorised_request(url, params)
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


def get_events_for_symbols(symbols=[], from_date: datetime.date=None, to_date: datetime.date=None) -> list[Event]:
    """
    Fetch upcoming events (earnings, dividends, splits) for a given stock symbol from FMP API.
    Args:
        symbols (list): List of stock ticker symbols.
        from_date (datetime.date, optional): Start date for events.
        to_date (datetime.date, optional): End date for events.
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
    params = {}
    if from_date:
        params["from"] = from_date.isoformat() if isinstance(from_date, date) else from_date
    if to_date:
        params["to"] = to_date.isoformat() if isinstance(to_date, date) else to_date
    for src in event_sources:
        resp = make_authorised_request(src["url"], params)
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


def get_daily_performance(symbol: str):
    # Fetching 'Day' gives us the 15min or 30min intervals for today
    quotes = get_historical(symbol, "Day") 
    
    if len(quotes) < 2:
        return None

    latest_quote = quotes[0]    # Most recent 15 mins
    opening_quote = quotes[-1]  # The first candle of the session
    
    day_change = latest_quote.close - opening_quote.open
    day_percent = (day_change / opening_quote.open) * 100
    
    return {
        "current": latest_quote.close,
        "change": day_change,
        "percent": day_percent
    }


def search_symbol(query):
    url = f"{API_BASE}/search-symbol"
    params = {"query": query, "limit": 10}
    resp = make_authorised_request(url, params)
    if resp.ok:
        return resp.json()
    return []
