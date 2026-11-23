"""Create labelled SYNTHETIC daily OHLCV and corporate actions for an offline demonstration."""
from pathlib import Path
import numpy as np
import pandas as pd

TICKERS = ["ALFA", "BRVO", "CRST", "DURA", "ECHO", "FLUX", "GLDN", "HARB"]
SECTORS = ["Technology", "Finance", "Industrials", "Health", "Technology", "Consumer", "Materials", "Utilities"]


def generate(seed=2026):
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range("2019-01-02", "2025-12-31")
    n = len(dates)
    factors = rng.normal(0, 0.007, n)
    # Distinct regimes to make the test nontrivial; these are simulated, NOT market estimates.
    factors[(dates >= "2020-03-01") & (dates <= "2020-05-31")] -= 0.0025
    factors[(dates >= "2022-01-01") & (dates <= "2022-10-31")] -= 0.0006
    factors[(dates >= "2023-01-01") & (dates <= "2024-12-31")] += 0.0003
    frames, actions = [], []
    for i, (ticker, sector) in enumerate(zip(TICKERS, SECTORS)):
        noise = rng.normal(0, 0.009 + i * 0.0008, n)
        # Gradual trend persistence in some assets; no investment signal guarantees.
        returns = np.zeros(n)
        for t in range(n):
            returns[t] = 0.00020 + (0.85 + i * 0.04) * factors[t] + noise[t] + (0.08 if i % 3 == 0 else -0.02) * (returns[t-1] if t else 0)
        economic_close = (40 + 12*i) * np.cumprod(1 + np.clip(returns, -0.20, 0.20))
        split = np.ones(n)
        if ticker == "ALFA":
            split[np.where(dates == pd.Timestamp("2022-06-15"))[0][0]] = 2.0
        if ticker == "DURA":
            split[np.where(dates == pd.Timestamp("2024-09-16"))[0][0]] = 3.0
        cumulative_split = np.cumprod(split)
        close = economic_close / cumulative_split
        dividend = np.zeros(n)
        for j in range(55 + i, n, 63):
            dividend[j] = round(0.055 + 0.012 * (i % 4), 3)
        volume = (rng.lognormal(13.1 - i * 0.15, 0.42, n)).astype(int)
        df = pd.DataFrame({"date": dates, "ticker": ticker, "sector": sector, "close": close.round(6), "volume": volume, "split_factor": split, "dividend": dividend, "source": "SYNTHETIC_SIMULATION"})
        frames.append(df)
        for j in np.where(split != 1)[0]:
            actions.append({"date": dates[j], "ticker": ticker, "action_type": "SPLIT", "value": split[j]})
        for j in np.where(dividend > 0)[0]:
            actions.append({"date": dates[j], "ticker": ticker, "action_type": "DIVIDEND", "value": dividend[j]})
    return pd.concat(frames, ignore_index=True).sort_values(["date", "ticker"]).reset_index(drop=True), pd.DataFrame(actions).sort_values(["date", "ticker"]).reset_index(drop=True)


def write_raw(root):
    root = Path(root)
    (root / "data/raw").mkdir(parents=True, exist_ok=True)
    prices, actions = generate()
    prices.to_csv(root / "data/raw/synthetic_prices.csv", index=False, date_format="%Y-%m-%d")
    actions.to_csv(root / "data/raw/corporate_actions.csv", index=False, date_format="%Y-%m-%d")
    return prices, actions
