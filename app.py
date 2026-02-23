import streamlit as st
from pages.home import render_home
from pages.markets import render_markets
from pages.detail import render_detail
st.set_page_config(page_title="Stock & ETF Visualizer", layout="wide")

PAGES = {
    "Home": render_home,
    "Markets Overview": render_markets,
    "Stock/ETF Detail": render_detail
}

# Set default page in session state
if "page" not in st.session_state:
    st.session_state["page"] = "Home"

# Sidebar reflects session state
selected_page = st.sidebar.radio(
    "Navigation",
    list(PAGES.keys()),
    index=list(PAGES.keys()).index(st.session_state["page"])
)

# Update session state if sidebar selection changes
if selected_page != st.session_state["page"]:
    st.session_state["page"] = selected_page
    st.rerun()

if "watchlist" not in st.session_state:
    st.session_state["watchlist"] = []

# Render the selected page
PAGES[st.session_state["page"]]()
