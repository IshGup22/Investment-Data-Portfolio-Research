"""Fail-fast data quality checks and auditable daily return reconstruction."""
import numpy as np
import pandas as pd

REQUIRED = {"date", "ticker", "sector", "close", "volume", "split_factor", "dividend", "source"}


def validate(prices):
    checks = {}
    checks["required_columns"] = REQUIRED.issubset(prices.columns)
    if not checks["required_columns"]:
        raise ValueError(f"Missing columns: {sorted(REQUIRED - set(prices.columns))}")
    d = prices.copy()
    d["date"] = pd.to_datetime(d["date"])
    checks["no_duplicates"] = not d.duplicated(["date", "ticker"]).any()
    checks["non_null_keys"] = d[["date", "ticker"]].notna().all().all()
    checks["positive_prices"] = d["close"].notna().all() and (d["close"] > 0).all()
    checks["nonnegative_volume"] = d["volume"].notna().all() and (d["volume"] >= 0).all()
    checks["valid_actions"] = d[["split_factor", "dividend"]].notna().all().all() and (d["split_factor"] >= 1).all() and (d["dividend"] >= 0).all()
    checks["ordered_per_asset"] = all(g["date"].is_monotonic_increasing for _, g in d.sort_values(["ticker", "date"]).groupby("ticker"))
    checks["synthetic_provenance"] = d["source"].eq("SYNTHETIC_SIMULATION").all()
    counts = d.groupby("ticker")["date"].nunique()
    checks["aligned_calendar"] = counts.nunique() == 1 and d["date"].nunique() == int(counts.iloc[0])
    checks["no_absurd_dividends"] = (d["dividend"] <= d["close"] * 0.25).all()
    checks["sufficient_history"] = d["date"].nunique() > 252 * 5
    return {k: bool(v) for k, v in checks.items()}


def build_returns(prices):
    d = prices.copy()
    d["date"] = pd.to_datetime(d["date"])
    d = d.sort_values(["ticker", "date"])
    # Split at t multiplies shares held from t-1; dividends are per post-split share.
    # Starting from prev raw share price, per-share total return is:
    #   split_factor[t] * (close[t] + dividend[t]) / close[t-1] - 1
    d["previous_close"] = d.groupby("ticker")["close"].shift()
    d["total_return"] = d["split_factor"] * (d["close"] + d["dividend"]) / d["previous_close"] - 1
    d["dollar_volume"] = d["close"] * d["volume"]
    return d
