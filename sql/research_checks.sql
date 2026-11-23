-- Query 1: Daily cross-sectional coverage; investigate if the universe unexpectedly shrinks.
SELECT date, COUNT(DISTINCT ticker) AS asset_count
FROM daily_market_data
GROUP BY date
HAVING asset_count <> (SELECT COUNT(DISTINCT ticker) FROM daily_market_data)
ORDER BY date;

-- Query 2: Impossible raw observations missed by the ingestion rules.
SELECT date, ticker, close, volume, split_factor, dividend
FROM daily_market_data
WHERE close <= 0 OR volume < 0 OR split_factor < 1 OR dividend < 0;

-- Query 3: Corporate action event completeness; each event must agree with market data.
SELECT a.date, a.ticker, a.action_type, a.value
FROM corporate_actions AS a
LEFT JOIN daily_market_data AS m ON m.date = a.date AND m.ticker = a.ticker
WHERE m.ticker IS NULL
   OR (a.action_type = 'SPLIT' AND ABS(m.split_factor - a.value) > 0.000001)
   OR (a.action_type = 'DIVIDEND' AND ABS(m.dividend - a.value) > 0.000001);

-- Query 4: Typical dollar-volume by fictional sector, for descriptive research only.
SELECT sector, COUNT(*) AS observations, ROUND(AVG(dollar_volume),2) AS mean_dollar_volume
FROM daily_market_data
GROUP BY sector
ORDER BY mean_dollar_volume DESC;
