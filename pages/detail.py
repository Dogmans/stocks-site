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
        st.subheader("All Metrics")
        # Show all metrics except price at the top
        for k, v in quote.items():
            if k != "price":
                st.write(f"{k}: {v}")

        st.markdown("---")
        st.subheader("Metric History Chart")
        metric_options = [k for k in quote.keys() if isinstance(quote[k], (int, float))]
        selected_metric = st.selectbox("Select metric to chart", metric_options, index=0)
        period = st.selectbox("Time period", ["Day", "Week", "Month", "Year", "5 Year"], index=0)
        from pages.historical_utils import get_historical
        values, dates = get_historical(symbol, selected_metric, period)
        if values and dates:
            st.line_chart({selected_metric: values}, x=dates)
        else:
            st.info("No historical data available for this metric.")
    st.markdown("---")
    if st.button("Add to Watchlist"):
        if symbol not in st.session_state["watchlist"]:
            st.session_state["watchlist"].append(symbol)
            st.success(f"Added {symbol} to watchlist.")
