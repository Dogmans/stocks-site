import requests
import streamlit as st
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("FINANCIAL_MODELING_PREP_API_KEY")
API_BASE = "https://financialmodelingprep.com/api/v3"

def get_historical(symbol, metric, period):
    # Map period to API params
    if period == "Day":
        timeseries = 13  # 6.5 hours * 2 intervals per hour (30min)
        interval = "30min"
    elif period == "Week":
        timeseries = 65  # 5 trading days * 13 hours * 1 interval per 30min
        interval = "30min"
    elif period == "Month":
        timeseries = 22  # 22 trading days
        interval = "1day"
    elif period == "Year":
        timeseries = 252
        interval = "1day"
    elif period == "5 Year":
        timeseries = 1260
        interval = "1day"
    else:
        timeseries = 1
        interval = "5min"
    url = f"{API_BASE}/historical-chart/{interval}/{symbol}"
    params = {"apikey": API_KEY}
    resp = requests.get(url, params=params)
    if resp.ok and resp.json():
        data = resp.json()[:timeseries]
        return [d[metric] for d in data if metric in d], [d["date"] for d in data if metric in d]
    return [], []
