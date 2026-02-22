import streamlit as st
from store import PersistentDict

DB_PATH = 'stocks_site_db'

def watchlist_button(symbol, item=None):
    db = PersistentDict(DB_PATH)
    watchlist = db.get('watchlist', {})
    in_watchlist = symbol in watchlist
    btn_label = f"Add {symbol} to Watchlist"
    if in_watchlist:
        st.button(btn_label, key=f"add_{symbol}", disabled=True, help="Already in watchlist")
    else:
        if st.button(btn_label, key=f"add_{symbol}"):
            if item is None:
                item = {"symbol": symbol}
            watchlist[symbol] = item
            db['watchlist'] = watchlist
            st.success(f"Added {symbol} to watchlist.")
