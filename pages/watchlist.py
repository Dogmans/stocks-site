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
            # Layout: Symbol | Name | Price widget | View | Remove (all in one row)
            cols = st.columns([2, 4, 2, 1, 1.2], gap="small")
            with cols[0]:
                st.markdown(f"**{symbol}**")
            with cols[1]:
                st.markdown(f"{item.get('name', '')}")
            with cols[2]:
                from components.price_widget import price_widget
                if quote:
                    price_widget(quote.get('price'), quote.get('changesPercentage'), size='small')
                else:
                    st.markdown(":-")
            with cols[3]:
                view_clicked = st.button("View", key=f"view_{symbol}")
            with cols[4]:
                remove_clicked = st.button("Remove", key=f"remove_{symbol}")
            if 'view_clicked' in locals() and view_clicked:
                st.session_state["detail_symbol"] = symbol
                st.session_state["page"] = "Stock/ETF Detail"
                st.rerun()
            if 'remove_clicked' in locals() and remove_clicked:
                del watchlist[symbol]
                db['watchlist'] = watchlist
                st.rerun()
