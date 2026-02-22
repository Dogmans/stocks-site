import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from pages.home import search_symbol

def test_search_symbol_goog():
    results = search_symbol("GOOG")
    print("Results:", results)
    if not results:
        print("No results returned for GOOG. Check API key and endpoint.")

if __name__ == "__main__":
    test_search_symbol_goog()
