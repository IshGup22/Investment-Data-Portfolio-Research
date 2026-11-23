# Empirical run results — synthetic research experiment

This document summarizes the executed results from `python -m src.run_pipeline` using fixed random seed **2026**. All prices and hypothetical returns are **simulated**.

## Model and timeline
- Eight synthetic assets; **14,608 asset-day rows** from 2019-01-02 to 2025-12-31
- 11 of 11 data checks passed
- 12 of 12 unit tests passed
- Warm-up: 2019–2020; development: 2021–2022 (521 business days); holdout: 2023–2025 (783 business days)
- Model: 63-session momentum, 21-session volatility, 20-session dollar-volume filter; one-session execution cushion with indicators shifted two trading days; monthly rebalancing
- Fees: 10 basis points per unit traded; equal-weight reference excludes costs

## Holdout findings (2023–2025)

| Statistic | Strategy, after 10 bps fee | Reference, before trading fee |
|---|---:|---:|
| Total compounded return | -31.33% | -31.22% |
| Annualized compounded growth (CAGR) | -11.39% | -11.35% |
| Annualized daily volatility | 14.73% | 13.09% |
| Sharpe, zero risk-free assumption | -0.75 | -0.85 |
| Maximum peak-to-trough drawdown | -40.21% | -35.10% |
| Positive-return trading days | 47.64% | 47.51% |
| Trading sessions | 783 | 783 |

Gross strategy CAGR: **-10.57%**. Recorded holdout gross absolute portfolio turnover: **28.805 portfolio-weight units** across rebalances.

### Cost sensitivity

| Transaction cost | Strategy CAGR | Max drawdown |
|---|---:|---:|
| 0 bps | -10.57% | -39.08% |
| 10 bps | -11.39% | -40.21% |
| 25 bps | -12.62% | -41.86% |
| 50 bps | -14.63% | -44.51% |

### Uncertainty

Paired 20-day circular block bootstrap across the same holdout observations (500 draws) returned **median annualized-growth spread +0.07 percentage points**, with **95% exploratory interval [-10.90, +9.71] percentage points**. The interval spans zero widely; it does not establish reliable alpha.

## Decision and business implication

**Reject the proposed strategy in this simulated test.** It does not outperform the reference on either growth or maximum drawdown after costs. The strategy has a somewhat less negative Sharpe but this does not compensate for poor absolute performance or wide uncertainty. The operational contribution is a tested process that surfaces weakness before an investment decision, rather than a favorable trading result.

## Further validation needed

Real licensed market data, point-in-time asset universe, liquidity/impact assumptions, a fully costed comparator, and untouched future data are needed before evaluating a live application.
