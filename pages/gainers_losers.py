"""
gainers_losers.py — Streamlit page for biggest stock gainers and losers

Displays the top gainers and losers using the FMP API.
"""

from typing import List

import streamlit as st
from fmp_api import get_gainers, get_losers, GainerLoser
from components.buttons import hyperlink_button


def render_line(cols, gainerLoser: GainerLoser):
    with cols[0]:
        hyperlink_button(gainerLoser.symbol, gainerLoser.symbol)
    with cols[1]:
        st.markdown(gainerLoser.name)
    with cols[2]:
        st.markdown(f"${gainerLoser.price}")
    with cols[3]:
        st.markdown(f"{gainerLoser.changesPercentage}%")
    with cols[4]:
         st.markdown(gainerLoser.exchange)


def render_table(items: List[GainerLoser]):
    cols = st.columns([2, 4, 2, 2, 2], gap="small")
    with cols[0]:
        st.markdown("**Symbol**")
    with cols[1]:
        st.markdown("**Name**")
    with cols[2]:
        st.markdown("**Price**")
    with cols[3]:
        st.markdown("**Change**")
    with cols[4]:
        st.markdown("**Exchange**")
    for item in items:
        render_line(cols, item)


def render_gainers_losers():
    st.title("Biggest Gainers & Losers")

    st.subheader("Top Gainers")
    gainers: List[GainerLoser] = get_gainers()
    if gainers:
        render_table(gainers)
    else:
        st.info("No gainers data available.")

    st.subheader("Top Losers")
    losers: List[GainerLoser] = get_losers()
    if losers:
        render_table(losers)
    else:
        st.info("No losers data available.")
