# Methodology and decision log

## Business question
Can a simple, liquidity-filtered momentum strategy create a robust improvement over an equal-weight benchmark **after realistic research safeguards and trading-cost assumptions**? This is a falsifiable research hypothesis, not an attempt to find positive returns.

## Data provenance
The primary dataset is **synthetic**. `generate_data.py` creates 8 fictional securities and daily observations for 2019–2025, using deterministic random seed 2026, varying risk profiles and simulated market regimes. Corporate actions include two synthetic splits plus periodic synthetic dividends. The original simulated values are not exchange data and cannot establish any real-world alpha.

`src/api_adapter.py` additionally illustrates ingestion from Alpha Vantage's `TIME_SERIES_DAILY_ADJUSTED` endpoint. It is optional, requires an API key, and was **not executed** to create the packaged report. No assertion is made that live data were used or validated.

## Validation and corporate actions
11 fail-fast checks cover required schema, duplicate keys, missing keys, strictly positive prices, nonnegative volume, valid split factors and dividends, time ordering, provenance, aligned trading calendars, dividend plausibility, and sufficient history. Errors must fail the run instead of silently contaminating performance statistics.

For a split factor `S_t`, dividend `D_t` paid per post-split share, and raw close `P_t`, the daily total return is:

`r_t = S_t * (P_t + D_t) / P_(t-1) - 1`

This prevents a 2-for-1 split from creating a false 50% daily loss. It is a simplification and assumes corporate actions align with the close data convention.

## Research design / controls
- **Warm-up:** 2019–2020; indicators need prior observations
- **Development window:** 2021–2022; methodology established before the holdout review
- **Out-of-sample window:** 2023–2025; no rule tuning on this interval
- **Signal:** 63-business-day compounded total-return momentum
- **Risk adjustment:** 21-day realized daily volatility; selected positions weighted inversely to volatility
- **Liquidity proxy:** trailing 20-day median `raw close × shares traded`, minimum $1,000,000 per day, strictly from historical data
- **Selection:** top three momentum names that pass eligibility; initial allocation capped at 50% per name
- **Execution timing:** indicators at date *t* use observations through *t-2*; monthly rebalance is assumed to execute at the close of *t-1*, so weights at *t* cannot use *t-1* closes discovered only at execution
- **Between rebalance dates:** held weights are allowed to drift with market returns; their instantaneous value may exceed the 50% **target** cap between rebalance dates
- **Transaction costs:** 10 basis points per absolute unit of trade turnover; cost sensitivity 0/10/25/50 bps
- **Comparator:** eight-asset daily equal-weight basket with no execution fees, so this is a conservative comparator for the strategy, not a fully investable benchmark
- **Cash assumption:** 0% yield if eligibility leaves insufficient holdings
- **Uncertainty:** paired 20-day circular block bootstrap of holdout return vectors, 500 resamples; descriptive sensitivity rather than an inferential claim about future markets

### No-lookahead validation
A unit test overwrites a future-day asset return with an extreme value and asserts that the current-day signal weights remain unchanged. Other tests verify split adjustment, nonpositive-price rejection, duplicate detection, capped initial weights, transaction-cost effects, and chronological holdout separation.

## Results and decision
The packaged results are measured in the executed synthetic experiment. **The hypothesis does not pass this holdout test.** The strategy's out-of-sample CAGR is close to the reference and its drawdown is deeper; uncertainty around relative performance is wide. There is no compelling evidence to deploy. See `outputs/results.json`, `outputs/dashboard.html`, and `docs/RESULTS.md` for precise values.

### Why a negative result matters
Research discipline means rejecting an attractive narrative when results don't support it. A production portfolio should not trade on this study; the more valuable outcome is a reproducible set of checks that expose instability, dependence on assumed liquidity, and sensitivity to costs.

## Limitations / tradeoffs
This sample is not an executable brokerage model: fictional tickers; only eight assets; simplified split/dividend convention; survivorship not modeled; no delistings, holidays beyond business-day calendar, or market closures; no spreads, partial fills, bid/ask impact, borrow constraints, commissions beyond simple turnover; simplified liquidity proxy; same-day equal-weight reference rebalanced without fees; no institutional data licensing checks; no stress test for missing market history; no third-party price reconciliation; no risk-free rate; no tax accounting. Corporate action adjustment for actual exchange data requires careful handling of vendor conventions. No financial return claim applies outside the simulation.

## Next steps (not implemented)
1. Acquire and license historical prices and corporate-action events from a verifiable vendor, and document vendor adjustment conventions
2. Add point-in-time universe membership, delisted assets, exchange calendars, and slippage estimates
3. Build factor-neutral, sector-neutral and exposure stress tests and compare multiple pre-registered hypotheses
4. Use nested rolling walk-forward model selection and a genuinely untouched additional holdout
