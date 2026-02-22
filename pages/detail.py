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
        # Show historical chart for close price
        st.markdown("---")
        st.subheader("Price History")
        period = st.selectbox("Time period", ["Day", "Week", "Month", "Year", "5 Year"], index=0)
        from pages.historical_utils import get_historical
        values, dates = get_historical(symbol, "close", period)
        if values and dates:
            import pandas as pd
            from datetime import datetime
            import altair as alt
            # Preserve time for day/week, use date for month/year/5year
            if period in ["Day", "Week"]:
                formatted_dates = dates  # Keep full datetime
            else:
                formatted_dates = [datetime.strptime(d, "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d") if len(d) > 10 else d for d in dates]
            df = pd.DataFrame({"date": formatted_dates, "close": values})
            df = df.set_index("date")
            # Only label start and end
            start_label = df.index[0]
            end_label = df.index[-1]
            # Altair chart for custom y-axis scaling, hide x-axis labels
            chart = alt.Chart(df.reset_index()).mark_line().encode(
                x=alt.X('date', axis=alt.Axis(labels=False, ticks=False)),
                y=alt.Y('close', scale=alt.Scale(domain=[df['close'].min(), df['close'].max()]))
            ).properties(width='container', height=300)
            st.altair_chart(chart, use_container_width=True)
            st.caption(f"{start_label} ... {end_label}")
        else:
            st.info("No historical data available for close price.")

        st.subheader("All Metrics")
        # Show all metrics except price at the top
        for k, v in quote.items():
            if k != "price":
                st.write(f"{k}: {v}")
    st.markdown("---")
    from components.watchlist_button import watchlist_button
    watchlist_button(symbol, quote)
