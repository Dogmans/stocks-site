import diskcache
import datetime
import logging
import requests

from dateutil import parser
from pydantic import BaseModel
from gliner import GLiNER
from config import API_KEY, API_BASE, DISK_CACHE_PATH

logger = logging.getLogger(__name__)

cache = diskcache.Cache(DISK_CACHE_PATH)

model = GLiNER.from_pretrained("urchade/gliner_small-v2.1")


class GainerLoser(BaseModel):
    symbol: str
    name: str
    price: float
    changesPercentage: float
    exchange: str


def get_gainers():
    """
    Fetch biggest stock gainers from FMP API.
    Returns a list of GainerLoser models.
    """
    url = "https://financialmodelingprep.com/stable/biggest-gainers"
    if resp := make_authorised_request(url):
        return [GainerLoser(**item) for item in resp]
    return []


def get_losers():
    """
    Fetch biggest stock losers from FMP API.
    Returns a list of GainerLoser models.
    """
    url = "https://financialmodelingprep.com/stable/biggest-losers"
    if resp := make_authorised_request(url):
        return [GainerLoser(**item) for item in resp]
    return []


def make_authorised_request(url, params=None):
    """
    Helper to make a GET request with API key injected into params.
    Returns the response object.
    """
    if params is None:
        params = {}
    params = dict(params)  # copy to avoid mutating caller
    params["apikey"] = API_KEY
    # Create a cache key from url and sorted params
    key = f"{url}|{sorted(params.items())}"
    if cached := cache.get(key):
        return cached
    resp = requests.get(url, params=params)
    if resp.ok:
        try:
            data = resp.json()
            cache.set(key, data, expire=900)  # 15 minutes
            return data
        except Exception as e:
            logger.error(f"Error caching response for {url}: {e}")
    else:
        logger.error(f"Request to {url} failed with status {resp.status_code}: {resp.text}")
    return None

def get_profile(symbol):
    url = f"{API_BASE}/profile"
    params = {"symbol": symbol}
    if resp := make_authorised_request(url, params):
        return resp[0]
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
    if resp := make_authorised_request(url, params):
        return resp
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
        timeseries = 132  # 22 trading days
        interval = "4hour"
    elif period == "Year":
        timeseries = 1584
        interval = "4hour"
    elif period == "5 Year":
        timeseries = 7920
        interval = "4hour"
    else:
        timeseries = 1
        interval = "5min"
    url = f"{API_BASE}/historical-chart/{interval}"
    if resp := make_authorised_request(url, params={"symbol": symbol, "limit": timeseries}):
        return [HistoricalQuote(**quote) for quote in resp[:timeseries]]
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
        url = f"{API_BASE}/news/stock"
        params = {"symbols": symbols[0], "limit": max_articles}
        if resp:= make_authorised_request(url, params):
            news = resp
    else:
        all_articles = []
        seen_urls = set()
        url = f"{API_BASE}/news/stock"
        params = {"symbols": symbols, "limit": max_articles}
        if resp:= make_authorised_request(url, params):
            articles = resp
        else:
            articles = []
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


def get_events_for_symbols(symbols, from_date: datetime.date=None, to_date: datetime.date=None) -> list[Event]:
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
        params["from"] = from_date.isoformat() if isinstance(from_date, datetime.date) else from_date
    if to_date:
        params["to"] = to_date.isoformat() if isinstance(to_date, datetime.date) else to_date
    for src in event_sources:
        resp = make_authorised_request(src["url"], params)
        if resp:
            for item in resp:
                events.append(Event(
                    date=item.get("date", item.get("paymentDate")),
                    name=src["name"],
                    type=src["type"],
                    symbol=item["symbol"]
                ))

    # Treat news differently since we have to filter text to determine if it's a relevant event
    resp = get_news(symbols.keys(), max_articles=100)  # Get more news to increase chances of finding events
    if resp:
        labels = ["Financial Conference", "Tech Expo", "Date", "Company"]
        for item in resp:
            title = item.get("title", "")
            text = item.get("text", "")
            combined_text = f"{title} {text}"
            entities = model.predict_entities(combined_text, labels, threshold=0.5)
            clean_date = None
            event_found = False
            org_found = False
            event_name = "Press Release"
            for ent in entities:
                if ent['label'] == "Financial Conference" or ent['label'] == "Tech Expo":
                    event_name = ent['text']
                    event_found = True
                elif ent['label'] == "Company":
                    org_found = True
                elif ent['label'] == "Date":
                    try:
                        clean_date = parser.parse(ent['text']).date().isoformat()
                    except Exception:
                        pass
                if clean_date and event_found and org_found:
                    events.append(Event(
                    date=clean_date,
                    name=event_name,
                    type="event",
                    symbol=item["symbol"]
                ))
                    break

    # Filter to only include events for our symbols
    events = [e for e in events if e.symbol in symbols]

    return events


def get_daily_performance(symbol: str):
    # Fetching 'Day' gives us the 15min or 30min intervals for today
    quotes = get_historical(symbol, "Day") 
    return get_performance(quotes)
    

def get_performance(quotes):
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
    if resp := make_authorised_request(url, params):
        return resp
    return []
