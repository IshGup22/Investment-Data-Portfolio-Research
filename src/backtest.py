"""Lagged-signal monthly long-only backtest; no data from date t determines weights at t."""
import numpy as np
import pandas as pd

START = "2021-01-01"
TRAIN_END = "2022-12-30"
TEST_START = "2023-01-02"
TEST_END = "2025-12-31"


def compute_weights(returns, dollar_volume, top_n=3):
    """Monthly targets from signals through t-2, allowing execution at t-1 close."""
    momentum = (1 + returns.fillna(0)).rolling(63, min_periods=63).apply(np.prod, raw=True) - 1
    volatility = returns.rolling(21, min_periods=21).std()
    liquidity = dollar_volume.rolling(20, min_periods=20).median()
    # Conservative execution convention: use indicators ending at t-2,
    # assume rebalance at close t-1, earn close-to-close return for t.
    momentum, volatility, liquidity = momentum.shift(2), volatility.shift(2), liquidity.shift(2)
    dates = returns.index
    rebalance = pd.Series(dates.to_period("M"), index=dates).ne(pd.Series(dates.to_period("M"), index=dates).shift(1))
    weights = pd.DataFrame(0.0, index=dates, columns=returns.columns)
    last = pd.Series(0.0, index=returns.columns)
    for date in dates:
        if rebalance.loc[date]:
            allowed = (liquidity.loc[date] > 1_000_000) & (volatility.loc[date] > 0) & momentum.loc[date].notna()
            scores = momentum.loc[date].where(allowed).dropna().sort_values(ascending=False)
            if len(scores) >= top_n:
                selected = scores.head(top_n).index
                # Inverse-volatility tilt, 50% hard cap, no leverage or shorting.
                inv_vol = 1 / volatility.loc[date, selected]
                candidate = inv_vol / inv_vol.sum()
                # Cap and redistribute for the small three-name basket.
                w = candidate.clip(upper=0.50)
                for _ in range(10):
                    rem = max(0, 1 - w.sum())
                    room = 0.50 - w
                    if rem < 1e-10 or room.sum() <= 0:
                        break
                    w += rem * room / room.sum()
                last = pd.Series(0.0, index=returns.columns)
                last.loc[selected] = w / w.sum()
            else:
                # Never backfill the score with future prices: sit in cash.
                last = pd.Series(0.0, index=returns.columns)
        weights.loc[date] = last
    return weights


def run_backtest(d, cost_bps=10):
    r = d.pivot(index="date", columns="ticker", values="total_return").sort_index()
    dv = d.pivot(index="date", columns="ticker", values="dollar_volume").reindex_like(r)
    w = compute_weights(r, dv)
    # Self-financing portfolio: positions drift with returns between monthly rebalances.
    # Trade on a new month only, starting with the previous close's drifted weights.
    dates = r.index
    month = dates.to_period("M")
    held = pd.Series(0.0, index=r.columns)
    realized_weights, gross_list, net_list, turnover_list, invested_list = [], [], [], [], []
    for j, date in enumerate(dates):
        is_rebalance = j == 0 or month[j] != month[j-1]
        target = w.loc[date] if is_rebalance else held
        change = float((target - held).abs().sum()) if is_rebalance else 0.0
        daily = r.loc[date].fillna(0)
        gross = float((target * daily).sum())
        net = gross - change * cost_bps / 10000
        # Post-return risky weights; the remainder represents cash with 0% yield.
        held = target * (1 + daily) / (1 + gross)
        realized_weights.append(target.to_numpy())
        gross_list.append(gross)
        net_list.append(net)
        turnover_list.append(change)
        invested_list.append(float(target.sum()))
    w = pd.DataFrame(realized_weights, index=dates, columns=r.columns)
    benchmark = r.fillna(0).mean(axis=1)  # equal-weight daily rebalanced reference, gross of fees
    output = pd.DataFrame({"strategy_gross": gross_list, "strategy_net": net_list, "benchmark": benchmark,
                           "turnover": turnover_list, "invested": invested_list}, index=dates)
    output = output.loc[START:TEST_END]
    output["period"] = np.where(output.index < TEST_START, "development", "out_of_sample")
    return output, w.loc[START:TEST_END], r


def metrics(returns):
    r = pd.Series(returns).dropna().astype(float)
    if r.empty:
        return {}
    equity = (1 + r).cumprod()
    annualized = float(equity.iloc[-1] ** (252 / len(r)) - 1)
    vol = float(r.std(ddof=1) * np.sqrt(252))
    drawdown = equity / equity.cummax() - 1
    return {"total_return_pct": round((equity.iloc[-1]-1)*100,2), "cagr_pct": round(annualized*100,2), "volatility_pct": round(vol*100,2), "sharpe_0rf": round(float(r.mean()/r.std(ddof=1)*np.sqrt(252)),2) if r.std(ddof=1)>0 else None, "max_drawdown_pct": round(float(drawdown.min())*100,2), "win_day_pct": round(float((r>0).mean())*100,2), "observations": len(r)}


def block_bootstrap_cagr_diff(strategy, benchmark, draws=500, block=20, seed=42):
    """Exploratory uncertainty only; overlapping blocks preserve some serial dependence."""
    a = np.asarray(strategy)
    b = np.asarray(benchmark)
    n = len(a)
    rng = np.random.default_rng(seed)
    diffs = []
    for _ in range(draws):
        ix = np.concatenate([np.arange(s, s+block) % n for s in rng.integers(0, n, size=int(np.ceil(n/block)))])[:n]
        ca = np.prod(1+a[ix]) ** (252/n)-1
        cb = np.prod(1+b[ix]) ** (252/n)-1
        diffs.append((ca-cb)*100)
    return {"median_cagr_spread_pp": round(float(np.median(diffs)),2), "ci_95_pp": [round(float(x),2) for x in np.quantile(diffs,[0.025,0.975])], "prob_outperform_bootstrap_pct": round(float(100*np.mean(np.array(diffs)>0)),1)}
