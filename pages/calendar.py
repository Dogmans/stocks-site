"""
calendar.py — Calendar page for stock-related events

Displays a calendar view of upcoming events for stocks in the user's watchlist. Each event includes a link or indication of the related stock.
"""

from datetime import date, timedelta

import streamlit as st
from fmp_api import Event, get_events_for_symbols
from store import PersistentDict

DB_PATH = 'stocks_site_db'

def render_calendar():
    st.title("Stock Events Calendar")

    # Helper to get watchlist
    db = PersistentDict(DB_PATH)
    watchlist = db.get('watchlist', {})

    if not watchlist:
        st.info("Add stocks to your watchlist to see their events here.")
    else:
        # Collect events for all watchlist stocks
        events = []
        start = date.today() - timedelta(days=date.today().weekday())
        end = start + timedelta(days=30)  # Show events for the next 30 days
        events: list[Event] = get_events_for_symbols(watchlist, from_date=start.isoformat(), to_date=end.isoformat())

        if not events:
            st.info("No upcoming events found for your watchlist.")
        else:
            # Sort events by date
            events.sort(key=lambda e: e.date)
            st.write("### Upcoming Events")
            for event in events:
                link = f"/detail?symbol={event.symbol}"
                st.markdown(f"**{event.date}** — [{event.name} ({event.symbol})]({link})")
