import streamlit as st
import config
from store import PersistentDict


def hyperlink_button(label, symbol, page="Stock/ETF Detail"):
    """
    Renders a true hyperlink that, when clicked, sets session state for navigation.
    Returns True if this link was just clicked (i.e., query param matches), else False.
    """
    import urllib.parse
    # Encode the symbol and page for the URL
    url = f"?detail_symbol={urllib.parse.quote(symbol)}&page={urllib.parse.quote(page)}"
    st.markdown(f'<a href="{url}" style="color:#1a73e8;text-decoration:underline;">{label}</a>', unsafe_allow_html=True)
    return False


def watchlist_button(symbol, item=None):
    db = PersistentDict(config.DB_PATH)
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
