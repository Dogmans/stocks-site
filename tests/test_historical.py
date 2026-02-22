import os
import pytest
from pages.historical_utils import get_historical

API_KEY = os.getenv("FINANCIAL_MODELING_PREP_API_KEY")

@pytest.mark.parametrize("symbol,metric,period", [
    ("AAPL", "close", "Day"),
    ("AAPL", "open", "Week"),
    ("AAPL", "high", "Month"),
    ("AAPL", "low", "Year"),
    ("AAPL", "close", "5 Year"),
])
def test_get_historical(symbol, metric, period):
    values, dates = get_historical(symbol, metric, period)
    assert isinstance(values, list)
    assert isinstance(dates, list)
    # Should return at least one value if API and symbol/metric are valid
    assert len(values) == len(dates)
    # If API key is valid and data exists, should have data
    if API_KEY:
        assert len(values) > 0, f"No data returned for {symbol} {metric} {period}"
