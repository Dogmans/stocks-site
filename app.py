import logging
# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

import streamlit as st
from pages.calendar import render_calendar
from pages.gainers_losers import render_gainers_losers
from pages.home import render_home
from pages.markets import render_markets
from pages.detail import render_detail
from pages.screener import render_screener
from queries import handle_query_params

st.set_page_config(page_title="Stock & ETF Visualizer", layout="wide")

# 1. Inject CSS to make sidebar buttons look like a clean list
st.markdown("""
    <style>
    [data-testid="stSidebarNav"] {display: none;} /* Hide default nav if using multi-page files */
    div.stButton > button {
        width: 100%;
        border: none;
        text-align: left;
        background-color: transparent;
        padding: 0.5rem 0px;
    }
    div.stButton > button:hover {
        background-color: rgba(151, 166, 195, 0.1);
        border: none;
    }
    div.stButton > button:focus {
        box-shadow: none;
        border: none;
    }
    </style>
    """, unsafe_allow_html=True)

PAGES = {
    "Home": render_home,
    "Gainers & Losers": render_gainers_losers,
    "Screener": render_screener,
    "Calendar": render_calendar,
    "Markets Overview": render_markets,
    "Stock/ETF Detail": render_detail
}

# Initialize session state
if "page" not in st.session_state:
    st.session_state["page"] = "Home"
if "watchlist" not in st.session_state:
    st.session_state["watchlist"] = []

# 2. Custom Sidebar Navigation
with st.sidebar:
    st.title("Navigation")
    for page_name in PAGES.keys():
        # Bold the label if it is the current page
        label = f"**{page_name}**" if st.session_state["page"] == page_name else page_name
        
        if st.button(label, key=f"nav_{page_name}"):
            st.session_state["page"] = page_name
            st.rerun()

handle_query_params()  # Sync query params to session state on page load

# 3. Render the selected page
PAGES[st.session_state["page"]]()