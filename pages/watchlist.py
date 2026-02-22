from store import PersistentDict

DB_PATH = 'stocks_site_db'
db = PersistentDict(DB_PATH)
import streamlit as st
import requests
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("FINANCIAL_MODELING_PREP_API_KEY")
API_BASE = "https://financialmodelingprep.com/api/v3"

# Helper functions

def get_quote(symbol):
    url = f"{API_BASE}/quote/{symbol}"
    params = {"apikey": API_KEY}
    resp = requests.get(url, params=params)
    if resp.ok and resp.json():
        return resp.json()[0]
    return None

def render_watchlist():
    st.title("Watchlist")
    watchlist = db.get('watchlist', {})
    if not watchlist:
        st.info("No symbols in watchlist.")
    else:
        for symbol, item in watchlist.items():
            quote = get_quote(symbol)
            cols = st.columns([6, 2])
            # Stock info
            with cols[0]:
                if quote:
                    st.markdown(f"**{symbol}**: {quote.get('price')} ({quote.get('changesPercentage')})")
                else:
                    st.markdown(f"**{symbol}**: {item.get('name', '')}")
            # Right-justified buttons, minimal gap
            with cols[1]:
                btn_cols = st.columns([1, 1.2], gap="small")
                view_clicked = btn_cols[0].button("View", key=f"view_{symbol}")
                remove_clicked = btn_cols[1].button("Remove", key=f"remove_{symbol}")
                if view_clicked:
                    st.session_state["detail_symbol"] = symbol
                    st.session_state["page"] = "Stock/ETF Detail"
                    st.rerun()
                if remove_clicked:
                    del watchlist[symbol]
                    db['watchlist'] = watchlist
                    st.rerun()
