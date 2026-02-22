import os
import requests
import pytest
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("FINANCIAL_MODELING_PREP_API_KEY")
BASE_URL = "https://financialmodelingprep.com/api/v3/search"

def test_search_symbol():
    query = "GOOGL"
    params = {"query": query, "apikey": API_KEY, "limit": 10}
    resp = requests.get(BASE_URL, params=params)
    assert resp.ok, f"API request failed: {resp.status_code}"
    results = resp.json()
    found = any(item.get("symbol") == "GOOGL" for item in results)
    assert found, f"GOOGL not found in search results: {results}"
