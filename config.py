"""
config.py — Shared configuration for API keys, endpoints, and paths
"""
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("FINANCIAL_MODELING_PREP_API_KEY")
API_BASE = "https://financialmodelingprep.com/stable"
DB_PATH = os.getenv("STOCKS_SITE_DB_PATH", "stocks_site_db")
