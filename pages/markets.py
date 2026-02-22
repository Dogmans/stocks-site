import streamlit as st
import requests
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("FINANCIAL_MODELING_PREP_API_KEY")
API_BASE = "https://financialmodelingprep.com/api/v3"

# Helper functions

def get_indices():
    url = f"{API_BASE}/quotes/index"
    params = {"apikey": API_KEY}
    resp = requests.get(url, params=params)
    if resp.ok:
        return resp.json()
    return []

def get_gainers():
    url = f"{API_BASE}/stock_market/gainers"
    params = {"apikey": API_KEY}
    resp = requests.get(url, params=params)
    if resp.ok:
        return resp.json()
    return []

def get_losers():
    url = f"{API_BASE}/stock_market/losers"
    params = {"apikey": API_KEY}
    resp = requests.get(url, params=params)
    if resp.ok:
        return resp.json()
    return []

# Markets Overview page

def render_markets():
    st.title("Markets Overview")
    st.subheader("Major Indices")
    indices = get_indices()
    for idx in indices[:5]:
        st.metric(label=idx["name"], value=idx["price"], delta=idx["changesPercentage"])

    st.markdown("---")
    st.subheader("Top Gainers")
    gainers = get_gainers()
    for g in gainers[:5]:
        st.write(f"{g['symbol']} - {g['name']} : {g['price']} ({g['changesPercentage']})")

    st.markdown("---")
    st.subheader("Top Losers")
    losers = get_losers()
    for l in losers[:5]:
        st.write(f"{l['symbol']} - {l['name']} : {l['price']} ({l['changesPercentage']})")
