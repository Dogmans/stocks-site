import os
import requests
import pytest
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("FINANCIAL_MODELING_PREP_API_KEY")
BASE_URL = "https://financialmodelingprep.com/api/v3/sec_filings"

@pytest.mark.parametrize("symbol", ["GOOG"])
def test_filings_for_symbol(symbol):
    params = {"apikey": API_KEY}
    url = f"{BASE_URL}/{symbol}"
    resp = requests.get(url, params=params)
    assert resp.ok, f"API request failed: {resp.status_code}"
    filings = resp.json()
    # Filings should be a list
    assert isinstance(filings, list), f"Filings response is not a list: {filings}"
    # If API key is valid, should return filings or empty list
    # Check for at least one valid filing (with formType, date, url, title)
    valid_filings = [f for f in filings if f.get('formType') and f.get('date') and f.get('url') and f.get('title')]
    # Allow empty if none exist, but print for debug
    print(f"Valid filings for {symbol}:", valid_filings)
    # If API returns filings, at least one should be valid
    if filings:
        assert valid_filings, f"No valid filings found for {symbol}: {filings}"
