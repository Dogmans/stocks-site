# Investing App

## Purpose
This project is a Streamlit-based web application for visualizing stocks, ETFs, and indices with live data from Financial Modeling Prep. It provides search, autocomplete, watchlist, and detailed views for financial instruments.

## Features
- Search and autocomplete for stocks, ETFs, and indices
- Live market data and featured tickers
- Watchlist management
- Detailed company profiles and quotes
- Custom navigation and error handling

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

## Contributing
Pull requests and issues are welcome.
