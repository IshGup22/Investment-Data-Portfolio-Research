# Data dictionary

| Field | Type | Meaning |
|---|---|---|
| `date` | YYYY-MM-DD | Simulated business date |
| `ticker` | string | Fictional security code |
| `sector` | string | Simulated sector label |
| `close` | float | Raw price per share, not backward split-adjusted |
| `volume` | integer | Shares traded in the synthetic session |
| `split_factor` | float | Number of new shares for one prior share on event date, otherwise 1 |
| `dividend` | float | Cash dividend per share after split convention, otherwise 0 |
| `source` | string | `SYNTHETIC_SIMULATION`, explicit provenance |
| `total_return` | float | Daily split/dividend-aware close-to-close return |
| `dollar_volume` | float | Raw close × simulated traded shares |
| `strategy_gross` | float | Strategy daily return before trade costs |
| `strategy_net` | float | Strategy daily return after turnover costs |
| `benchmark` | float | Gross daily equal-weight reference return |
| `turnover` | float | Sum absolute target minus pretrade weights |
| `invested` | float | Risky invested fraction; cash is remainder |
| `period` | string | `development` or `out_of_sample` |

Synthetic corporate actions are also exported in `data/raw/corporate_actions.csv`. Holdout positions are exported in `outputs/portfolio_weights.csv` for audit.

Research tables are defined in `sql/schema.sql`; the SQLite output is `data/processed/research_cache.sqlite`. Corporate actions and raw prices are simulated.
