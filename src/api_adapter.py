"""Optional live-market API adapter, deliberately NOT used to produce packaged results.

Usage requires ALPHAVANTAGE_API_KEY in environment and internet access.
Provider terms, request limits, data quality, and market conventions must be reviewed.
"""
import json
import os
from urllib.parse import urlencode
from urllib.request import urlopen
import pandas as pd

BASE = "https://www.alphavantage.co/query"


def parse_adjusted_daily(payload, ticker):
    series = payload.get("Time Series (Daily)")
    if not isinstance(series, dict):
        raise ValueError("API returned no daily adjusted time series; inspect provider status, key and rate limits")
    rows = []
    for day, values in series.items():
        rows.append({"date":pd.Timestamp(day),"ticker":ticker,
                     "close":float(values["4. close"]),
                     "volume":int(float(values["6. volume"])),
                     "split_factor":float(values.get("8. split coefficient",1)),
                     "dividend":float(values.get("7. dividend amount",0)),
                     "source":"ALPHA_VANTAGE"})
    return pd.DataFrame(rows).sort_values("date").reset_index(drop=True)


def fetch_adjusted_daily(ticker, api_key=None):
    api_key = api_key or os.environ.get("ALPHAVANTAGE_API_KEY")
    if not api_key:
        raise RuntimeError("Set ALPHAVANTAGE_API_KEY to use optional live data ingestion")
    params = urlencode({"function":"TIME_SERIES_DAILY_ADJUSTED","symbol":ticker,"outputsize":"full","apikey":api_key})
    with urlopen(BASE + "?" + params, timeout=20) as response:
        payload=json.loads(response.read().decode("utf-8"))
    return parse_adjusted_daily(payload,ticker)
