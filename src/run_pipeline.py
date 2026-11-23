"""Run: python -m src.run_pipeline --root ."""
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
from .generate_data import write_raw
from .sql_store import build_sqlite
from .validation import validate, build_returns
from .backtest import run_backtest, metrics, block_bootstrap_cagr_diff, TEST_START


def run(root):
    root = Path(root)
    for folder in ("outputs", "data/processed"):
        (root / folder).mkdir(parents=True, exist_ok=True)
    raw, actions = write_raw(root)
    checks = validate(raw)
    if not all(checks.values()):
        raise ValueError(f"Data validation failed: {checks}")
    processed = build_returns(raw)
    processed.to_csv(root / "data/processed/market_data.csv", index=False, date_format="%Y-%m-%d")
    sql_audit = build_sqlite(root, processed, actions)
    results, weights, returns = run_backtest(processed, cost_bps=10)
    results.to_csv(root / "outputs/daily_backtest.csv", date_format="%Y-%m-%d", index_label="date")
    weights.to_csv(root / "outputs/portfolio_weights.csv", date_format="%Y-%m-%d", index_label="date")
    holdout = results.loc[TEST_START:]
    report = {"dataset": "SYNTHETIC_SIMULATION: not actual market observations", "data_window": [str(raw.date.min().date()),str(raw.date.max().date())], "tickers": sorted(raw.ticker.unique().tolist()), "price_rows": int(len(raw)), "corporate_actions": int(len(actions)), "validation": checks, "sql_audit": sql_audit, "methodology": {"warmup": "2019-2020", "development": "2021-2022", "holdout": "2023-2025", "signal": "63-session total return momentum, 21-session volatility and 20-session median dollar volume, lagged two sessions for execution timing", "rebalance": "monthly target weights applied to first business-day return with prior close execution; risky holdings drift between rebalances", "portfolio": "top 3 liquid names, inverse-volatility weights capped at 50%; cash when insufficient", "cost": "10 bps per unit of gross absolute turnover", "benchmark": "daily equal-weighted asset basket; informational, not tradeable net of fees", "dividend_splits": "split- and dividend-aware simple returns", "note": "Synthetic research demonstration; not an investment recommendation"}, "development": {}, "holdout": {}, "cost_sensitivity": {}, "uncertainty": {}}
    for label, subset in (("development",results.loc[:"2022-12-30"]),("holdout",holdout)):
        report[label] = {"strategy_net":metrics(subset.strategy_net),"benchmark":metrics(subset.benchmark), "strategy_gross":metrics(subset.strategy_gross)}
    for cost in (0,10,25,50):
        net = holdout.strategy_gross - holdout.turnover * cost / 10000
        report["cost_sensitivity"][f"{cost}_bps"] = metrics(net)
    report["uncertainty"] = block_bootstrap_cagr_diff(holdout.strategy_net,holdout.benchmark)
    report["holdout_total_turnover"] = round(float(holdout.turnover.sum()),3)
    report["holdout_rebalance_count"] = int((holdout.turnover>0).sum())
    (root / "outputs/results.json").write_text(json.dumps(report,indent=2))
    create_static_dashboard(root,results,weights,report)
    return report


def create_static_dashboard(root, results, weights, report):
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    from plotly.offline import plot
    r = results.loc[TEST_START:]
    wealth = (1 + r[["strategy_net","benchmark"]]).cumprod()
    drawdown = (wealth / wealth.cummax() - 1) * 100
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=.09, row_heights=[.47,.28,.25], subplot_titles=("Growth of $10,000 · holdout only", "Underwater chart · drawdown (%)", "Monthly turnover"))
    for col, color, label in (("strategy_net","#6ee7b7","Momentum strategy · after costs"),("benchmark","#9aa9c4","Equal-weight reference")):
        fig.add_trace(go.Scatter(x=wealth.index,y=10000*wealth[col],name=label,mode="lines",line=dict(color=color,width=2.5)),row=1,col=1)
        fig.add_trace(go.Scatter(x=drawdown.index,y=drawdown[col],name=label,mode="lines",line=dict(color=color,width=1.5),showlegend=False),row=2,col=1)
    fig.add_trace(go.Bar(x=r.index,y=r.turnover,name="Turnover",marker_color="#68a4fd",showlegend=False),row=3,col=1)
    fig.update_layout(template="plotly_dark",paper_bgcolor="#111827",plot_bgcolor="#111827",font=dict(family="Arial",color="#e5e7eb"),height=950,margin=dict(l=48,r=20,t=85,b=60),title=dict(text="OUT-OF-SAMPLE PERFORMANCE | Synthetic market-data case study",font=dict(size=18)),legend=dict(orientation="h",y=1.05,x=0),hovermode="x unified")
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="#263345")
    h = report["holdout"]
    cards = [("Strategy CAGR",f'{h["strategy_net"]["cagr_pct"]:.2f}%'),("Reference CAGR",f'{h["benchmark"]["cagr_pct"]:.2f}%'),("Strategy Sharpe (0% rf)",str(h["strategy_net"]["sharpe_0rf"])),("Max drawdown",f'{h["strategy_net"]["max_drawdown_pct"]:.2f}%'),("Validation checks",f'{sum(report["validation"].values())}/{len(report["validation"])}')]
    cardhtml = ''.join(f'<div class="metric"><small>{key}</small><strong>{value}</strong></div>' for key,value in cards)
    page = '''<!doctype html><html lang="en"><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/><title>Market Research Lab | Results</title><style>body{margin:0;background:#0b1220;color:#e5e7eb;font-family:Inter,system-ui,Arial}main{max-width:1180px;margin:auto;padding:38px 22px}.eyebrow{letter-spacing:.16em;text-transform:uppercase;color:#6ee7b7;font-weight:700;font-size:12px}h1{font-size:34px;letter-spacing:-.04em;margin:12px 0}p{line-height:1.65;color:#a5b4cc}.alert{border:1px solid #c68f38;background:#30281b;color:#fbd38d;padding:12px 18px;border-radius:9px;font-size:14px;margin:20px 0}.metrics{display:grid;grid-template-columns:repeat(auto-fit,minmax(165px,1fr));gap:12px;margin:25px 0}.metric{background:#172238;border:1px solid #263345;border-radius:13px;padding:20px}.metric small{color:#9aa9c4;display:block;margin-bottom:12px}.metric strong{font-size:24px}.foot{font-size:12px;color:#9aa9c4;padding:20px 0;border-top:1px solid #263345}a{color:#6ee7b7}</style></head><body><main><div class="eyebrow">Quant Research Engineering · Reproducible study</div><h1>Investment Data & Portfolio Research</h1><p>A documented research workflow: corporate-action-aware data processing, eleven automated data checks, lagged momentum signals, a chronological holdout, cost stress tests and an auditable dashboard.</p><div class="alert"><b>SYNTHETIC DATA.</b> These results are simulated, not real securities performance, and should not be used for investment decisions.</div><div class="metrics">CARDS</div>CHART<div class="foot">Holdout: 2023–2025 · Benchmark: daily equal-weight basket · Costs: 10 basis points per unit turnover · Chart data regenerated by <code>python -m src.run_pipeline</code> · This report is a standalone HTML file that works offline</div></main></body></html>'''
    page = page.replace("CARDS",cardhtml).replace("CHART",plot(fig,output_type="div",include_plotlyjs=True,config={"responsive":True,"displaylogo":False}))
    (root / "outputs/dashboard.html").write_text(page,encoding="utf-8")


if __name__ == "__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--root",default=".")
    args=p.parse_args()
    print(json.dumps(run(args.root),indent=2))
