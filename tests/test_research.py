import numpy as np
import pandas as pd
import pytest
from src.generate_data import generate
from src.validation import validate,build_returns
from src.backtest import compute_weights,run_backtest,metrics

@pytest.fixture(scope='module')
def market():
    p,_=generate()
    return p,build_returns(p)

def test_all_data_checks_pass(market):
    assert all(validate(market[0]).values())

def test_duplicate_rows_rejected(market):
    d=pd.concat([market[0], market[0].iloc[:1]],ignore_index=True)
    assert not validate(d)['no_duplicates']

def test_negative_price_rejected(market):
    d=market[0].copy()
    d.loc[0,'close']=-1
    assert not validate(d)['positive_prices']

def test_split_adjusted_returns_not_artificial_crash(market):
    p=market[1]
    for ticker, day in [('ALFA','2022-06-15'),('DURA','2024-09-16')]:
        r=p.loc[(p.ticker==ticker)&(p.date==pd.Timestamp(day)),'total_return'].iloc[0]
        assert abs(r) < .20

def test_weights_no_leverage_and_cap(market):
    r,w,_=run_backtest(market[1])
    assert (w.sum(axis=1) <= 1+1e-8).all()
    assert (w.min().min() >= -1e-8)
    # Caps apply when the strategy rebalances; positions may drift above the cap later.
    rebalance_days = w.index.to_series().dt.to_period("M").ne(w.index.to_series().dt.to_period("M").shift())
    assert (w.loc[rebalance_days].max().max() <= 0.5000001)

def test_no_lookahead_weights_when_future_changes(market):
    d=market[1]
    r=d.pivot(index='date',columns='ticker',values='total_return').sort_index()
    dv=d.pivot(index='date',columns='ticker',values='dollar_volume').reindex_like(r)
    # A shocking move ON decision date must not change that day's allocation.
    cut=pd.Timestamp('2024-06-03')
    a=compute_weights(r,dv).loc[cut]
    mutated=r.copy()
    mutated.loc[cut,'ALFA']=25
    b=compute_weights(mutated,dv).loc[cut]
    pd.testing.assert_series_equal(a,b)

def test_costs_reduce_strategy_returns(market):
    zero,_,_=run_backtest(market[1],0)
    fee,_,_=run_backtest(market[1],25)
    assert fee.strategy_net.sum() <= zero.strategy_net.sum()
    assert (fee.strategy_net <= zero.strategy_net+1e-12).all()

def test_holdout_is_later_than_development(market):
    report,_,_=run_backtest(market[1])
    assert report.loc[report.period=='development'].index.max() < report.loc[report.period=='out_of_sample'].index.min()

def test_metrics_defined(market):
    out,_,_=run_backtest(market[1])
    m=metrics(out.loc['2023':,'strategy_net'])
    assert m['observations'] > 700
    assert m['max_drawdown_pct'] <= 0

def test_api_payload_parsing_offline():
    from src.api_adapter import parse_adjusted_daily
    sample={"Time Series (Daily)":{"2025-01-02":{"4. close":"101.5","6. volume":"90000","7. dividend amount":"0.02","8. split coefficient":"1.0"}}}
    parsed=parse_adjusted_daily(sample,"DEMO")
    assert len(parsed)==1 and parsed.loc[0,"dividend"] == .02
    assert parsed.loc[0,"source"] == "ALPHA_VANTAGE"

def test_bad_api_payload_rejected():
    from src.api_adapter import parse_adjusted_daily
    with pytest.raises(ValueError):
        parse_adjusted_daily({"Note":"rate limit"},"DEMO")

def test_sql_ingestion_and_reconciliation(tmp_path,market):
    from pathlib import Path
    from src.sql_store import build_sqlite
    import sqlite3
    import shutil
    (tmp_path/'sql').mkdir()
    (tmp_path/'data/processed').mkdir(parents=True)
    shutil.copy(Path(__file__).resolve().parents[1]/'sql/schema.sql',tmp_path/'sql/schema.sql')
    _,actions=generate()
    audit=build_sqlite(tmp_path,market[1],actions)
    assert audit['sql_unmatched_actions']==0
    assert audit['cache_rows']==len(market[1])
    with sqlite3.connect(tmp_path/'data/processed/research_cache.sqlite') as con:
        assert con.execute('SELECT COUNT(*) FROM corporate_actions').fetchone()[0]==len(actions)
