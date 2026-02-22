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

    tabs = st.tabs(["Overview", "Filings", "News"])

    with tabs[0]:
        if quote:
            st.metric("Price", quote.get("price"), quote.get("changesPercentage"))
            st.markdown("---")
            st.subheader("Price History")
            period = st.selectbox("Time period", ["Day", "Week", "Month", "Year", "5 Year"], index=0)
            from pages.historical_utils import get_historical
            values, dates = get_historical(symbol, "close", period)
            if values and dates:
                import pandas as pd
                from datetime import datetime
                import altair as alt
                if period in ["Day", "Week"]:
                    formatted_dates = dates
                else:
                    formatted_dates = [datetime.strptime(d, "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d") if len(d) > 10 else d for d in dates]
                df = pd.DataFrame({"date": formatted_dates, "close": values})
                df = df.set_index("date")
                start_label = df.index[0]
                end_label = df.index[-1]
                chart = alt.Chart(df.reset_index()).mark_line().encode(
                    x=alt.X('date', axis=alt.Axis(labels=False, ticks=False)),
                    y=alt.Y('close', scale=alt.Scale(domain=[df['close'].min(), df['close'].max()]))
                ).properties(width='container', height=300)
                st.altair_chart(chart, use_container_width=True)
                st.caption(f"{start_label} ... {end_label}")
            else:
                st.info("No historical data available for close price.")

            st.subheader("All Metrics")
            def format_metric(val):
                try:
                    num = float(val)
                    abs_num = abs(num)
                    if abs_num >= 1e9:
                        return f"{num/1e9:.5g} bn"
                    elif abs_num >= 1e6:
                        return f"{num/1e6:.5g} m"
                    elif abs_num >= 1e3:
                        return f"{num/1e3:.5g} k"
                    else:
                        return f"{num:.5g}"
                except (ValueError, TypeError):
                    return val

            metrics = [(k, format_metric(v)) for k, v in quote.items() if k != "price"]
            import pandas as pd
            df_metrics = pd.DataFrame(metrics, columns=["Metric", "Value"])
            st.table(df_metrics.style.hide(axis="index"))
        st.markdown("---")
        from components.watchlist_button import watchlist_button
        watchlist_button(symbol, quote)

    # Filings Tab
    with tabs[1]:
        st.subheader("Filings & Documents")
        filings_url = f"{API_BASE}/sec_filings/{symbol}"
        params = {"apikey": API_KEY}
        resp = requests.get(filings_url, params=params)
        filings = resp.json() if resp.ok and resp.json() else []
        # Filter filings based on actual API fields
        valid_filings = [f for f in filings if f.get('fillingDate') and f.get('type') and f.get('link') and f.get('finalLink')]
        if valid_filings:
            filings_sorted = sorted(valid_filings, key=lambda x: x.get("fillingDate", ""), reverse=True)
            expanded = True
            for i, filing in enumerate(filings_sorted):
                # Format date as yyyy-mm-dd
                date_str = filing.get('fillingDate', '')[:10]
                # Use type and name (if available) in the expander title
                filing_type = filing.get('type', 'Document')
                filing_name = filing.get('name', filing_type)
                expander_title = f"{filing_type} ({filing_name}) — {date_str}"
                with st.expander(expander_title, expanded=expanded):
                    st.write(f"CIK: {filing.get('cik', 'N/A')}")
                    st.write(f"Accepted: {filing.get('acceptedDate', 'N/A')}")
                    st.write(f"[View Filing]({filing.get('link', '#')})")
                    st.write(f"[Document Link]({filing.get('finalLink')})")
                expanded = False
        else:
            st.info("No valid filings found for this symbol.")

    # News Tab
    with tabs[2]:
        st.subheader("Latest News")
        news_url = f"{API_BASE}/stock_news"
        params = {"tickers": symbol, "limit": 10, "apikey": API_KEY}
        resp = requests.get(news_url, params=params)
        news = resp.json() if resp.ok and resp.json() else []
        if news:
            news_sorted = sorted(news, key=lambda x: x.get("publishedDate", ""), reverse=True)
            expanded = True
            for i, article in enumerate(news_sorted):
                with st.expander(f"{article.get('title', 'News')} — {article.get('publishedDate', '')}", expanded=expanded):
                    st.write(f"**Source:** {article.get('site', '')}")
                    st.write(f"**Date:** {article.get('publishedDate', '')}")
                    st.write(f"**Link:** [{article.get('url', 'Read')}]({article.get('url', '')})")
                    st.write(f"**Summary:** {article.get('text', '')}")
                expanded = False
        else:
            st.info("No news articles found for this symbol.")
