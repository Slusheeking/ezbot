-- QuestDB Schema for Agentic AI Trading System
-- Live Feed Module - Polygon Data Feed Tables

-- Stock data with technical indicators
CREATE TABLE IF NOT EXISTS polygon_stocks (
    timestamp TIMESTAMP,
    symbol SYMBOL CAPACITY 10000 CACHE,
    price DOUBLE,
    volume LONG,
    open DOUBLE,
    high DOUBLE,
    low DOUBLE,
    close DOUBLE,
    vwap DOUBLE,
    change DOUBLE,
    change_percent DOUBLE,

    -- Technical Indicators
    rsi_14 DOUBLE,
    rsi_30 DOUBLE,
    macd DOUBLE,
    macd_signal DOUBLE,
    macd_histogram DOUBLE,
    bb_upper DOUBLE,
    bb_middle DOUBLE,
    bb_lower DOUBLE,
    sma_20 DOUBLE,
    sma_50 DOUBLE,
    sma_200 DOUBLE,
    ema_12 DOUBLE,
    ema_26 DOUBLE,
    ema_50 DOUBLE,
    stoch_k DOUBLE,
    stoch_d DOUBLE,
    williams_r DOUBLE,
    cci DOUBLE,
    atr DOUBLE,
    adx DOUBLE,
    obv LONG,
    mfi DOUBLE,

    -- Volatility Metrics
    volatility DOUBLE,
    beta DOUBLE,

    -- Market Context
    market_cap DOUBLE,
    pe_ratio DOUBLE,

    feed_source SYMBOL
) TIMESTAMP(timestamp) PARTITION BY DAY WAL;

-- Options flow data
CREATE TABLE IF NOT EXISTS polygon_options (
    timestamp TIMESTAMP,
    underlying_symbol SYMBOL CAPACITY 10000 CACHE,
    option_symbol SYMBOL CAPACITY 50000 CACHE,
    strike_price DOUBLE,
    expiration_date DATE,
    option_type SYMBOL, -- 'call' or 'put'
    price DOUBLE,
    bid DOUBLE,
    ask DOUBLE,
    spread DOUBLE,
    volume LONG,
    open_interest LONG,

    -- Greeks
    delta DOUBLE,
    gamma DOUBLE,
    theta DOUBLE,
    vega DOUBLE,
    rho DOUBLE,

    -- Implied Volatility
    implied_volatility DOUBLE,

    -- Time Value
    intrinsic_value DOUBLE,
    time_value DOUBLE,

    -- Flow Analysis
    volume_oi_ratio DOUBLE,
    unusual_activity BOOLEAN,
    flow_type SYMBOL, -- 'sweep', 'split', 'block', 'normal'

    feed_source SYMBOL
) TIMESTAMP(timestamp) PARTITION BY DAY WAL;

-- Cryptocurrency data
CREATE TABLE IF NOT EXISTS polygon_crypto (
    timestamp TIMESTAMP,
    symbol SYMBOL CAPACITY 1000 CACHE,
    base_currency SYMBOL,
    quote_currency SYMBOL,
    price DOUBLE,
    volume DOUBLE,
    market_cap DOUBLE,
    change_24h DOUBLE,
    change_percent_24h DOUBLE,

    -- Technical Indicators (same as stocks)
    rsi_14 DOUBLE,
    macd DOUBLE,
    macd_signal DOUBLE,
    bb_upper DOUBLE,
    bb_middle DOUBLE,
    bb_lower DOUBLE,
    sma_20 DOUBLE,
    ema_12 DOUBLE,

    -- Crypto-specific metrics
    dominance DOUBLE,
    fear_greed_index INT,

    feed_source SYMBOL
) TIMESTAMP(timestamp) PARTITION BY DAY WAL;

-- Market status and trading halts
CREATE TABLE IF NOT EXISTS polygon_market_status (
    timestamp TIMESTAMP,
    market SYMBOL, -- 'stocks', 'options', 'crypto'
    status SYMBOL, -- 'open', 'closed', 'early_close', 'late_open'
    reason SYMBOL,
    next_open TIMESTAMP,
    next_close TIMESTAMP,

    feed_source SYMBOL
) TIMESTAMP(timestamp) PARTITION BY DAY WAL;

-- Trading halts and LULD events
CREATE TABLE IF NOT EXISTS polygon_trading_halts (
    timestamp TIMESTAMP,
    symbol SYMBOL CAPACITY 10000 CACHE,
    halt_type SYMBOL, -- 'halt', 'resume', 'luld_breach'
    reason_code SYMBOL,
    price_at_halt DOUBLE,
    luld_upper DOUBLE,
    luld_lower DOUBLE,
    expected_resume TIMESTAMP,

    feed_source SYMBOL
) TIMESTAMP(timestamp) PARTITION BY DAY WAL;

-- Snapshots for latest values
CREATE TABLE IF NOT EXISTS polygon_snapshots (
    timestamp TIMESTAMP,
    symbol SYMBOL CAPACITY 10000 CACHE,
    asset_type SYMBOL, -- 'stock', 'option', 'crypto'
    last_price DOUBLE,
    last_volume LONG,
    bid DOUBLE,
    ask DOUBLE,
    spread DOUBLE,
    day_open DOUBLE,
    day_high DOUBLE,
    day_low DOUBLE,
    day_volume LONG,
    day_vwap DOUBLE,
    previous_close DOUBLE,
    change DOUBLE,
    change_percent DOUBLE,

    feed_source SYMBOL
) TIMESTAMP(timestamp) PARTITION BY DAY WAL;

-- Agent analysis results
CREATE TABLE IF NOT EXISTS agent_analysis (
    timestamp TIMESTAMP,
    agent_type SYMBOL, -- 'fundamental', 'technical', 'sentiment', etc.
    symbol SYMBOL CAPACITY 10000 CACHE,
    analysis_type SYMBOL,
    score DOUBLE,
    confidence DOUBLE,
    signal SYMBOL, -- 'buy', 'sell', 'hold'
    reasoning STRING,
    metadata STRING, -- JSON formatted additional data

    feed_source SYMBOL
) TIMESTAMP(timestamp) PARTITION BY DAY WAL;

-- Multi-agent coordination events
CREATE TABLE IF NOT EXISTS agent_coordination (
    timestamp TIMESTAMP,
    session_id SYMBOL,
    event_type SYMBOL, -- 'consensus', 'conflict', 'decision', 'execution'
    participating_agents STRING, -- comma-separated agent types
    symbol SYMBOL CAPACITY 10000 CACHE,
    decision SYMBOL,
    confidence_score DOUBLE,
    risk_assessment DOUBLE,
    execution_plan STRING,

    feed_source SYMBOL
) TIMESTAMP(timestamp) PARTITION BY DAY WAL;

-- Create indexes for optimal query performance
ALTER TABLE polygon_stocks ALTER COLUMN symbol ADD INDEX;
ALTER TABLE polygon_options ALTER COLUMN underlying_symbol ADD INDEX;
ALTER TABLE polygon_options ALTER COLUMN option_symbol ADD INDEX;
ALTER TABLE polygon_crypto ALTER COLUMN symbol ADD INDEX;
ALTER TABLE polygon_snapshots ALTER COLUMN symbol ADD INDEX;
ALTER TABLE agent_analysis ALTER COLUMN symbol ADD INDEX;
ALTER TABLE agent_coordination ALTER COLUMN symbol ADD INDEX;