# AGENTS.md — Investing App

## What This Project Does
A Streamlit web app for searching, visualizing, and tracking stocks, ETFs, and indices with live data from Financial Modeling Prep. Features include search/autocomplete, watchlist, detailed quotes, news, and filings.

## Dev Environment
- Runtime: Python 3.10+
- Package manager: pip
- Setup: `pip install -r requirements.txt`

## Commands
| Action   | Command                        |
|----------|-------------------------------|
| Install  | `pip install -r requirements.txt` |
| Run      | `streamlit run app.py`         |
| Lint     | `isort . && flake8 .`          |
| Test     | (no formal tests yet)          |

## Project Structure
- `app.py` — Streamlit entry point
- `components/` — UI widgets (e.g., price_widget, news_feed)
- `pages/` — Streamlit multipage app pages
- `fmp_api.py` — All Financial Modeling Prep API logic (quotes, search, news, filings, etc.)
- `store.py` — PersistentDict for watchlist/session
- `requirements.txt` — Python dependencies
- `README.md` — Human onboarding
- `AGENTS.md` — Agent onboarding (this file)

## Architecture
| Component      | File/Module         | Role                                    |
|----------------|--------------------|-----------------------------------------|
| API methods    | fmp_api.py         | All FMP API calls (quotes, news, etc.)  |
| News feed      | components/news_feed.py | Renders news, uses fmp_api.get_news    |
| Price widget   | components/price_widget.py | Price display widget                |
| Home page      | pages/home.py      | Main UI, search, watchlist, navigation  |

## Code Style
- Black/isort for formatting and import order
- One class/function per concern
- Use type hints where possible
- Docstrings for all public functions
- Imports: standard, third-party, local (in that order)

## Testing
- No formal test suite yet
- Add tests in `tests/` as needed

## Pitfalls
- FMP API search is US-centric; LSE/FTSE coverage is limited
- News API returns a global limit, not per-symbol
- Always use `fmp_api.py` for FMP requests (do not call requests.get directly in components/pages)
- Update .env with your API key

## PR/commit conventions
- Update README.md and AGENTS.md with any new modules, dependencies, or workflows
- Use descriptive commit messages
- Run lint before PR
