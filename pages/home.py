from store import PersistentDict
from components.hyperlink_button import hyperlink_button

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
        # Symbol as a button styled as a hyperlink
        symbol_clicked = hyperlink_button(item['symbol'], key=f"search_symbol_{item['symbol']}", help="View details")
        st.write(f": {item.get('name', '')}")
        if symbol_clicked:
            st.session_state["detail_symbol"] = item['symbol']
            st.session_state["page"] = "Stock/ETF Detail"
            st.rerun()
        # Style the button to look like a link
        st.markdown("""
            <style>
            div[data-testid="stButton"] button {
                background: none !important;
                color: #1a73e8;
                border: none;
                padding: 0;
                font-size: 1em;
                text-decoration: underline;
                cursor: pointer;
            }
            </style>
        """, unsafe_allow_html=True)
    elif query:
        logger.debug("No results found for query")
        st.error("No results found.")


    # --- Watchlist Section (replaces featured stocks) ---
    st.markdown("---")
    st.subheader("Your Watchlist")
    watchlist = db.get('watchlist', {})
    if not watchlist:
        st.info("No symbols in watchlist.")
    else:
        for symbol, item in sorted(watchlist.items()):
            # Inline import to avoid circular import
            def get_quote(symbol):
                url = f"{API_BASE}/quote/{symbol}"
                params = {"apikey": API_KEY}
                resp = requests.get(url, params=params)
                if resp.ok and resp.json():
                    return resp.json()[0]
                return None
            quote = get_quote(symbol)
            cols = st.columns([2, 4, 3, 2.2], gap="small")
            with cols[0]:
                # Symbol as a button styled as a hyperlink
                symbol_clicked = hyperlink_button(symbol, key=f"watchlist_symbol_{symbol}", help="View details")
                if symbol_clicked:
                    st.session_state["detail_symbol"] = symbol
                    st.session_state["page"] = "Stock/ETF Detail"
                    st.rerun()
            # Style the button to look like a link (inject only once)
            if symbol == sorted(watchlist.keys())[0]:
                st.markdown("""
                    <style>
                    div[data-testid="stButton"] button {
                        background: none !important;
                        color: #1a73e8;
                        border: none;
                        padding: 0;
                        font-size: 1em;
                        text-decoration: underline;
                        cursor: pointer;
                    }
                    </style>
                """, unsafe_allow_html=True)
            with cols[1]:
                st.markdown(f"{item.get('name', '')}")
            with cols[2]:
                from components.price_widget import price_widget
                if quote:
                    price_widget(quote.get('price'), quote.get('changesPercentage'), size='small')
                else:
                    st.markdown(":-")
            with cols[3]:
                remove_clicked = st.button("Remove", key=f"watchlist_remove_{symbol}")
            if 'remove_clicked' in locals() and remove_clicked:
                del watchlist[symbol]
                db['watchlist'] = watchlist
                st.rerun()

        # News feed for all watchlist stocks (today's news)
        from components.news_feed import news_feed
        st.markdown("---")
        symbols = list(watchlist.keys())
        news_feed(symbols=symbols, max_articles=10, today_only=True, show_header=True)

    st.markdown("---")
    st.subheader("Market Summary")
    st.write("(Indices, top gainers/losers, sector performance coming soon)")
    logger.debug("Market summary section rendered")
