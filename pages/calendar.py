from datetime import date, timedelta
import streamlit as st
from fmp_api import Event, get_events_for_symbols
from store import PersistentDict

from config import DB_PATH


def render_calendar():
    st.title("Stock Events Calendar")

    # 1. Access Data Sources
    db = PersistentDict(DB_PATH)
    watchlist = db.get('watchlist', {})

    if not watchlist:
        st.info("Add stocks to your watchlist to see their events here.")
        return

    # 2. Handle Week Navigation in Session State
    if "cal_start_date" not in st.session_state:
        # Default to the Monday of the current week
        today = date.today()
        st.session_state.cal_start_date = today - timedelta(days=today.weekday())

    # 3. Navigation UI
    col1, col2, col3 = st.columns([1, 2, 1])
    if col1.button("⬅️ Previous Week"):
        st.session_state.cal_start_date -= timedelta(days=7)
        st.rerun()
    if col3.button("Next Week ➡️"):
        st.session_state.cal_start_date += timedelta(days=7)
        st.rerun()

    # Define the week range for display and fetching
    week_start = st.session_state.cal_start_date
    week_end = week_start + timedelta(days=6)
    
    with col2:
        st.markdown(f"<h3 style='text-align: center;'>{week_start.strftime('%b %d')} - {week_end.strftime('%b %d')}</h3>", unsafe_allow_html=True)

    # 4. Fetch Data (Cached by symbol list and date range)
    # We fetch specifically for the visible week to keep it snappy
    events: list[Event] = get_events_for_symbols(
        watchlist, 
        from_date=week_start.isoformat(), 
        to_date=week_end.isoformat()
    )

    st.divider()

    # 5. Render the Vertical Grid
    # Loop through all 7 days of the current week
    for i in range(7):
        current_day = week_start + timedelta(days=i)
        day_str = current_day.isoformat()
        
        # Filter the events list for this specific day
        # Note: adjust e.date access if e.date is a string vs date object
        day_events = [e for e in events if str(e.date) == day_str]

        day_col, event_col = st.columns([1, 4])

        with day_col:
            st.markdown(f"### {current_day.strftime('%a')}")
            st.caption(current_day.strftime("%b %d"))
            if current_day == date.today():
                st.info("Today")

        with event_col:
            if day_events:
                for event in day_events:
                    with st.container(border=True):
                        c1, c2 = st.columns([3, 1])
                        c1.markdown(f"**{event.name}**")
                        c1.caption(f"Symbol: {event.symbol}")
                        
                        # Direct native link - no iframe issues
                        if event.url:
                            c2.link_button("View Event", event.url, use_container_width=True)
                        else:
                            c2.button("No Link", disabled=True, use_container_width=True)
            else:
                st.write("")
                st.caption("No events scheduled")
        
        st.write("---")