-- Research cache. Input records are synthetic, not licensed actual market data.
CREATE TABLE IF NOT EXISTS daily_market_data (
    date TEXT NOT NULL,
    ticker TEXT NOT NULL,
    sector TEXT NOT NULL,
    close REAL NOT NULL CHECK (close > 0),
    volume INTEGER NOT NULL CHECK (volume >= 0),
    split_factor REAL NOT NULL CHECK (split_factor >= 1),
    dividend REAL NOT NULL CHECK (dividend >= 0),
    total_return REAL,
    dollar_volume REAL NOT NULL,
    source TEXT NOT NULL,
    PRIMARY KEY (date, ticker)
);
CREATE INDEX IF NOT EXISTS idx_market_ticker_date ON daily_market_data(ticker, date);
CREATE TABLE IF NOT EXISTS corporate_actions (
    date TEXT NOT NULL,
    ticker TEXT NOT NULL,
    action_type TEXT NOT NULL CHECK (action_type IN ('SPLIT','DIVIDEND')),
    value REAL NOT NULL CHECK (value > 0)
);
