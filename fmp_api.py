import requests
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("FINANCIAL_MODELING_PREP_API_KEY")
API_BASE = "https://financialmodelingprep.com/api/v3"

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
