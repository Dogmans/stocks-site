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
    if "watchlist" not in st.session_state:
        st.session_state["watchlist"] = []
    if not st.session_state["watchlist"]:
        st.info("No symbols in watchlist.")
    else:
        for symbol in st.session_state["watchlist"]:
            quote = get_quote(symbol)
            if quote:
                st.write(f"**{symbol}**: {quote.get('price')} ({quote.get('changesPercentage')})")
            if st.button(f"Remove {symbol}", key=f"remove_{symbol}"):
                st.session_state["watchlist"].remove(symbol)
                st.experimental_rerun()
