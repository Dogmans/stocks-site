from store import PersistentDict
from components.buttons import hyperlink_button
from config import DB_PATH
from fmp_api import get_daily_performance, search_symbol
from queries import handle_query_params

db = PersistentDict(DB_PATH)
import streamlit as st
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

# Home page
def render_home():
    logger.debug("render_home called")
    handle_query_params()  # Sync query params to session state on page load
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
        # Symbol as a hyperlink (true link)
        cols = st.columns([2, 6])
        with cols[0]:
            symbol_clicked = hyperlink_button(item['symbol'], item['symbol'])
        with cols[1]:
            st.markdown(f"{item.get('name', '')}")
        if symbol_clicked:
            st.session_state["detail_symbol"] = item['symbol']
            st.session_state["page"] = "Stock/ETF Detail"
            st.rerun()
        # Add to watchlist button below (standard button, not hyperlink style)
        watchlist = db.get('watchlist', {})
        in_watchlist = item['symbol'] in watchlist
        if in_watchlist:
            st.button("Add to Watchlist", key=f"add_{item['symbol']}", disabled=True, help="Already in watchlist")
        else:
            if st.button("Add to Watchlist", key=f"add_{item['symbol']}"):
                watchlist[item['symbol']] = item
                db['watchlist'] = watchlist
                st.success(f"Added {item['symbol']} to watchlist.")
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
        page = "Stock/ETF Detail"
        symbols = list(watchlist.keys())
        # Header row for alignment
        cols = st.columns([2, 4, 2, 2], gap="small")
        with cols[0]:
            st.markdown("**Symbol**")
        with cols[1]:
            st.markdown("**Name**")
        with cols[2]:
            st.markdown("**Price**")
        with cols[3]:
            st.markdown("**Remove**")
        for symbol, item in sorted(watchlist.items()):
            cols = st.columns([2, 4, 2, 2], gap="small")
            with cols[0]:
                symbol_clicked = hyperlink_button(symbol, symbol)
                # if symbol_clicked:
                #     st.session_state["detail_symbol"] = symbol
                #     st.session_state["page"] = page
                #     st.rerun()
            with cols[1]:
                st.markdown(f"{item.get('name', '')}")
            with cols[2]:
                from components.price_widget import price_widget
                performance = get_daily_performance(symbol)
                if performance:
                    price_widget(performance["current"], performance["percent"], size='small')
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
        news_feed(symbols=symbols, max_articles=10, today_only=True, show_header=True)

    st.markdown("---")
    st.subheader("Market Summary")
    st.write("(Indices, top gainers/losers, sector performance coming soon)")
    logger.debug("Market summary section rendered")
