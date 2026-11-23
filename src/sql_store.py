"""SQLite data ingestion and SQL quality checks for the local research cache."""
import sqlite3
from pathlib import Path


def build_sqlite(root, processed, actions):
    root=Path(root)
    path=root/'data/processed/research_cache.sqlite'
    if path.exists():
        path.unlink()
    with sqlite3.connect(path) as con:
        con.executescript((root/'sql/schema.sql').read_text())
        cols=['date','ticker','sector','close','volume','split_factor','dividend','total_return','dollar_volume','source']
        rows=processed[cols].copy()
        rows['date']=rows['date'].dt.strftime('%Y-%m-%d')
        rows=rows.astype(object).where(rows.notna(), None)
        con.executemany(f"INSERT INTO daily_market_data ({','.join(cols)}) VALUES ({','.join(['?']*len(cols))})", rows.itertuples(index=False,name=None))
        a=actions[['date','ticker','action_type','value']].copy()
        a['date']=a['date'].dt.strftime('%Y-%m-%d')
        con.executemany('INSERT INTO corporate_actions (date,ticker,action_type,value) VALUES (?,?,?,?)',a.itertuples(index=False,name=None))
        bad_coverage=con.execute('SELECT COUNT(*) FROM (SELECT date FROM daily_market_data GROUP BY date HAVING COUNT(DISTINCT ticker) <> (SELECT COUNT(DISTINCT ticker) FROM daily_market_data))').fetchone()[0]
        bad_actions=con.execute('''SELECT COUNT(*) FROM corporate_actions a LEFT JOIN daily_market_data m ON m.date=a.date AND m.ticker=a.ticker WHERE m.ticker IS NULL OR (a.action_type='SPLIT' AND ABS(m.split_factor-a.value)>0.000001) OR (a.action_type='DIVIDEND' AND ABS(m.dividend-a.value)>0.000001)''').fetchone()[0]
        count=con.execute('SELECT COUNT(*) FROM daily_market_data').fetchone()[0]
    if bad_coverage or bad_actions or count != len(processed):
        raise ValueError(f'SQL data quality failed: coverage={bad_coverage}, actions={bad_actions}, rows={count}')
    return {'cache_rows':count,'sql_missing_asset_days':bad_coverage,'sql_unmatched_actions':bad_actions,'cache_file':'data/processed/research_cache.sqlite'}
