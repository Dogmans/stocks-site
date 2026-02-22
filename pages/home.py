from store import PersistentDict

DB_PATH = 'stocks_site_db'
db = PersistentDict(DB_PATH)
import streamlit as st
import requests
from dotenv import load_dotenv
import os
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()
API_KEY = os.getenv("FINANCIAL_MODELING_PREP_API_KEY")
API_BASE = "https://financialmodelingprep.com/api/v3"

# Helper functions

def search_symbol(query, types=("stock", "etf", "index")):
    logger.debug(f"search_symbol called with query={query}, types={types}")
    url = f"{API_BASE}/search"
    params = {"query": query, "apikey": API_KEY, "limit": 10}
    logger.debug(f"API_KEY: {API_KEY}")
    logger.debug(f"API request URL: {url}, params: {params}")
    try:
        if not API_KEY:
            logger.error("API key is missing. Please set FINANCIAL_MODELING_PREP_API_KEY in your .env file.")
            st.error("API key is missing. Please set FINANCIAL_MODELING_PREP_API_KEY in your .env file.")
            return []
        resp = requests.get(url, params=params)
        logger.debug(f"API response status: {resp.status_code}, reason: {resp.reason}")
        logger.debug(f"API response text: {resp.text}")
        if resp.ok:
            results = resp.json()
            logger.debug(f"API results: {results}")
            return results
        else:
            logger.error(f"API request failed: {resp.status_code} {resp.reason}")
            st.error(f"API request failed: {resp.status_code} {resp.reason}")
    except Exception as e:
        logger.exception(f"Error fetching results: {e}")
        st.error(f"Error fetching results: {e}")
    return []

# Home page

def render_home():
    logger.debug("render_home called")
    st.title("Stock & ETF Visualizer")
    st.write("Quickly view stocks, ETFs, and indices with live data from Financial Modeling Prep.")

    query = st.text_input("Search for a stock, ETF, or index:")
    logger.debug(f"User query: {query}")
    results = []
    options = []
    selected = None
    if query:
        results = search_symbol(query)
        logger.debug(f"Search results: {results}")
        options = [f"{item['symbol']} - {item.get('name', '')}" for item in results]
        logger.debug(f"Autocomplete options: {options}")
    if options:
        selected = st.selectbox("Autocomplete results:", options, key="autocomplete")
        logger.debug(f"User selected: {selected}")
        idx = options.index(selected)
        item = results[idx]
        logger.debug(f"Selected item: {item}")
        st.write(f"**{item['symbol']}**: {item.get('name', '')}")
        # Add to watchlist button, greyed out if already in watchlist
        watchlist = db.get('watchlist', {})
        in_watchlist = item['symbol'] in watchlist
        if in_watchlist:
            st.button(f"Add {item['symbol']} to Watchlist", key=f"add_{item['symbol']}", disabled=True, help="Already in watchlist")
        else:
            if st.button(f"Add {item['symbol']} to Watchlist", key=f"add_{item['symbol']}"):
                watchlist[item['symbol']] = item
                db['watchlist'] = watchlist
                st.success(f"Added {item['symbol']} to watchlist.")
        if st.button(f"View {item['symbol']}", key=f"view_{item['symbol']}"):
            logger.debug(f"View button clicked for: {item['symbol']}")
            st.session_state["detail_symbol"] = item['symbol']
            st.session_state["page"] = "Stock/ETF Detail"
            st.rerun()
    elif query:
        logger.debug("No results found for query")
        st.error("No results found.")

    st.markdown("---")
    st.subheader("Featured Stocks/ETFs")
    featured = ["AAPL", "MSFT", "SPY", "QQQ"]
    logger.debug(f"Featured symbols: {featured}")
    for symbol in featured:
        st.write(f"- {symbol}")

    st.markdown("---")
    st.subheader("Market Summary")
    st.write("(Indices, top gainers/losers, sector performance coming soon)")
    logger.debug("Market summary section rendered")
