"""
Test for get_events_for_symbol using META, verifying that at least one event is returned from the FMP earnings calendar endpoint.
"""
from datetime import date, timedelta

from fmp_api import get_events_for_symbol

def test_get_events_for_symbol_meta():
    start = date.today() - timedelta(days=date.today().weekday())
    end = start + timedelta(days=30)  # Show events for the next 30 days
    events = get_events_for_symbol("META", from_date=start, to_date=end)
    # Should return a list, possibly empty, but for META there should be at least one event
    assert isinstance(events, list)
    # Check for at least one event with a date and symbol
    has_valid_event = any(
        ev.get("date") and ev.get("symbol") == "META" for ev in events
    )
    assert has_valid_event, "No valid events found for META"
