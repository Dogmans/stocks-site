import os
import unittest
import requests
from dotenv import load_dotenv

class TestFinancialModelingPrepSearch(unittest.TestCase):
    def setUp(self):
        load_dotenv()
        self.api_key = os.getenv("FINANCIAL_MODELING_PREP_API_KEY")
        self.base_url = "https://financialmodelingprep.com/api/v3/search"

    def test_search_symbol(self):
        query = "GOOGL"
        params = {"query": query, "apikey": self.api_key, "limit": 10}
        resp = requests.get(self.base_url, params=params)
        self.assertTrue(resp.ok, f"API request failed: {resp.status_code}")
        results = resp.json()
        found = any(item.get("symbol") == "GOOGL" for item in results)
        self.assertTrue(found, f"GOOGL not found in search results: {results}")

if __name__ == "__main__":
    unittest.main()
