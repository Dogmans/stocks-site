# Investing App

## Purpose
This project is a Streamlit-based web application for visualizing stocks, ETFs, and indices with live data from Financial Modeling Prep. It provides search, autocomplete, watchlist, and detailed views for financial instruments.


## Features
- Search and autocomplete for stocks, ETFs, and indices
- Live market data and featured tickers
- Watchlist management
- Detailed company profiles and quotes
- Tabbed stock screener page with multiple integrated strategy views
- Filings/documents tab (SEC filings, 10-K, 10-Q, etc.) with accordion UI
- News tab showing latest articles in accordion UI
- Custom navigation and error handling
- Calendar page showing stock-related events for watchlist symbols

## Project Structure
```
.
├── app.py                # Streamlit entry point
├── components/           # UI widgets (price_widget, news_feed, etc.)
├── pages/                # Streamlit multipage app pages
│   ├── calendar.py       # Calendar page for stock-related events
│   ├── screener.py       # Tabbed screener page
├── screeners/            # Integrated strategy logic
│   ├── strategies.py     # Screener universe + strategy scoring
├── fmp_api.py            # All Financial Modeling Prep API logic (quotes, search, news, filings, etc.)
├── store.py              # PersistentDict for watchlist/session
├── requirements.txt      # Python dependencies
├── README.md             # Human onboarding
├── AGENTS.md             # Agent onboarding (AI/dev instructions)
```

## Architecture Overview
- All Financial Modeling Prep API calls are centralized in `fmp_api.py` (quotes, search, news, filings, etc.)
- UI components (e.g., news_feed, price_widget) import API methods from `fmp_api.py` and do not make direct HTTP requests
- News feed and price widgets are reusable across pages
- Watchlist and session state are managed via `store.py`

## Setup
1. Clone the repository.
2. Create a `.env` file with your Financial Modeling Prep API key:
   ```
   FINANCIAL_MODELING_PREP_API_KEY=your_api_key_here
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Run the app:
   ```
   streamlit run app.py
   ```

## Development Notes
- Python virtual environment recommended (`.venv`)
- Logging and error messages are shown in the frontend
- `.gitignore` excludes cache, environment, and secrets
- All FMP API logic is in `fmp_api.py` (do not call requests.get directly in components/pages)
- Filings and news are retrieved from FMP API and displayed using Streamlit tabs and expanders (accordion style)

## Contributing
Pull requests and issues are welcome.
