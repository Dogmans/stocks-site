# Stocks Site Project Documentation

## Overview
This project is a Streamlit-based web application for visualizing stocks, ETFs, and indices using live data from the Financial Modeling Prep API. It features search, detail views, a persistent watchlist, and dynamic charting of historical metrics.

## Main Components

### 1. `app.py`
- Entry point for the Streamlit app.
- Handles page routing using `st.session_state["page"]`.
- Loads and displays the appropriate page module (home, detail, markets, watchlist).

### 2. `pages/home.py`
- Implements the search interface for stocks, ETFs, and indices.
- Allows users to add symbols to their watchlist (using a generic persistent store).
- Disables the add button if the symbol is already in the watchlist.

### 3. `pages/detail.py`
- Displays detailed information for a selected symbol.
- Dynamically lists all available metrics from the API response.
- Shows a chart for the selected metric over a selectable time period (day, week, month, year, 5 year).
- Uses `pages/historical_utils.py` to fetch and display historical data.

### 4. `pages/watchlist.py`
- Loads the user's watchlist from the persistent store.
- Displays each symbol with info, a View button (navigates to details), and a Remove button (removes from watchlist).
- Ensures buttons are aligned in columns for a consistent UI.

### 5. `pages/historical_utils.py`
- Provides the `get_historical(symbol, metric, period)` function.
- Fetches historical data for a symbol and metric from the Financial Modeling Prep API.
- Maps UI period selections to API intervals and timeseries.
- Note: For price history, use the `close` metric as the API does not provide a `price` field in historical endpoints.

### 6. `store.py`
- Implements a generic `PersistentDict` class using Python's `shelve` module.
- All persistent data (e.g., watchlist) is stored as subkeys in a single database file.
- Each method opens and closes the shelve file to ensure thread safety with Streamlit.

### 7. `tests/`
- Contains all test files for the project.
- All tests use the `pytest` framework for consistency.
- Example: `tests/test_historical.py` tests the historical data fetching logic.

## Testing
- All tests are written using the `pytest` framework.
- To run all tests: `python -m pytest`
- To add new tests, create a file in the `tests/` directory and use the `pytest` style (functions prefixed with `test_`).
- See `tests/test_historical.py` for an example.

## API Keys
- The app requires a valid Financial Modeling Prep API key in a `.env` file as `FINANCIAL_MODELING_PREP_API_KEY`.

## Notes
- For historical price charts, select the `close` metric.
- The persistent store is generic and can be used for other user preferences.
- UI is built with Streamlit and is designed for clarity and ease of use.

---
This documentation is intended to help both developers and LLMs understand the structure and implementation of the project for future development and maintenance.
