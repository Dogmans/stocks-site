"""
gainers_losers.py — Streamlit page for biggest stock gainers and losers

Displays the top gainers and losers using the FMP API.
"""

import streamlit as st
from fmp_api import get_gainers, get_losers


def render_gainers_losers():
    st.title("Biggest Gainers & Losers")

    col1, col2 = st.columns(2)

    st.subheader("Top Gainers")
    gainers = get_gainers()
    if gainers:
        st.dataframe([g.dict() for g in gainers])
    else:
        st.info("No gainers data available.")

    st.subheader("Top Losers")
    losers = get_losers()
    if losers:
        st.dataframe([l.dict() for l in losers])
    else:
        st.info("No losers data available.")
