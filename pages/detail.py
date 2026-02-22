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

def get_profile(symbol):
    url = f"{API_BASE}/profile/{symbol}"
    params = {"apikey": API_KEY}
    resp = requests.get(url, params=params)
    if resp.ok and resp.json():
        return resp.json()[0]
    return None

def render_detail():
    symbol = st.session_state.get("detail_symbol")
    if not symbol:
        st.info("Search for a symbol on the Home page.")
        return
    quote = get_quote(symbol)
    profile = get_profile(symbol)
    st.header(f"{symbol}")
    if profile:
        st.subheader(profile.get("companyName", ""))
        st.write(profile.get("description", ""))
        st.write(f"Sector: {profile.get('sector', 'N/A')}")
        st.write(f"Industry: {profile.get('industry', 'N/A')}")
        st.write(f"Website: {profile.get('website', 'N/A')}")
    if quote:
        st.metric("Price", quote.get("price"), quote.get("changesPercentage"))
        st.write(f"Market Cap: {quote.get('marketCap')}")
        st.write(f"Volume: {quote.get('volume')}")
        st.write(f"52 Week High: {quote.get('yearHigh')}")
        st.write(f"52 Week Low: {quote.get('yearLow')}")
    st.markdown("---")
    if st.button("Add to Watchlist"):
        if symbol not in st.session_state["watchlist"]:
            st.session_state["watchlist"].append(symbol)
            st.success(f"Added {symbol} to watchlist.")
