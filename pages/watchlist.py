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
            if quote:
                st.write(f"**{symbol}**: {quote.get('price')} ({quote.get('changesPercentage')})")
            else:
                st.write(f"**{symbol}**: {item.get('name', '')}")
            if st.button(f"Remove {symbol}", key=f"remove_{symbol}"):
                del watchlist[symbol]
                db['watchlist'] = watchlist
                st.experimental_rerun()
