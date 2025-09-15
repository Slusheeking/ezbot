# Enhanced Multi-Source Screener Configurations

## Overview
Comprehensive screening framework integrating Polygon, Unusual Whales, Stock Titan, Reddit, and QuestDB for real-time opportunity detection across all 13 trading strategies.

## Universal Screener Architecture

### Core Screener Framework
```python
class EnhancedUniversalScreener:
    def __init__(self):
        self.data_sources = {
            'polygon': PolygonClient(),
            'unusual_whales': UnusualWhalesClient(),
            'stock_titan': StockTitanRSSClient(),
            'reddit': RedditFeedClient(),
            'questdb': QuestDBClient()
        }

        self.strategy_screeners = {
            'news_catalyst': NewssCatalystScreener(),
            '0dte_iron_condor': ZeroDTEScreener(),
            'earnings_iv_crush': EarningsIVScreener(),
            'rsi_mean_reversion': RSIMeanReversionScreener(),
            'gap_fill': GapFillScreener(),
            'premarket_momentum': PremarketMomentumScreener(),
            'vwap_mean_reversion': VWAPMeanReversionScreener(),
            'opening_range_breakout': OpeningRangeScreener(),
            'support_resistance': SupportResistanceScreener(),
            'momentum_continuation': MomentumContinuationScreener(),
            'btc_spy_correlation': BTCSPYCorrelationScreener(),
            'weekend_gap_predictor': WeekendGapScreener(),
            'crypto_mean_reversion': CryptoMeanReversionScreener()
        }

    async def run_all_screeners(self):
        """Execute all strategy screeners in parallel"""

        screener_tasks = []

        for strategy_name, screener in self.strategy_screeners.items():
            task = asyncio.create_task(
                screener.scan_opportunities(),
                name=f"screener_{strategy_name}"
            )
            screener_tasks.append(task)

        # Execute all screeners concurrently
        results = await asyncio.gather(*screener_tasks, return_exceptions=True)

        # Compile results
        all_opportunities = {}
        for i, result in enumerate(results):
            strategy_name = list(self.strategy_screeners.keys())[i]
            if not isinstance(result, Exception):
                all_opportunities[strategy_name] = result
            else:
                logger.error(f"Screener {strategy_name} failed: {result}")
                all_opportunities[strategy_name] = []

        return all_opportunities
```

## Strategy-Specific Screeners

### 1. News Catalyst Momentum Screener
```sql
-- QuestDB SQL for News Catalyst Screening
WITH recent_news AS (
    SELECT DISTINCT
        stn.symbol,
        stn.title,
        stn.sentiment,
        stn.category,
        r.sentiment_score as reddit_sentiment,
        p.price_change_pct,
        p.volume_ratio,
        uw.flow_score,
        uw.institutional_flow,
        ROW_NUMBER() OVER (PARTITION BY stn.symbol ORDER BY stn.timestamp DESC) as rn
    FROM stock_titan_news stn
    LEFT JOIN reddit_posts r ON stn.symbol = r.ticker
        AND r.timestamp > NOW() - INTERVAL '2 hours'
    JOIN polygon_live_data p ON stn.symbol = p.symbol
    LEFT JOIN uw_flow_alerts uw ON stn.symbol = uw.symbol
        AND uw.timestamp > NOW() - INTERVAL '10 minutes'
    WHERE stn.timestamp > NOW() - INTERVAL '5 minutes'
      AND ABS(p.price_change_pct) > 0.015
      AND p.volume_ratio > 1.8
      AND stn.category IN ('earnings', 'upgrade', 'acquisition', 'fda', 'guidance')
)
SELECT symbol, title, sentiment, reddit_sentiment, price_change_pct,
       volume_ratio, flow_score, institutional_flow,
       (volume_ratio * ABS(price_change_pct) * COALESCE(flow_score, 1)) as composite_score
FROM recent_news
WHERE rn = 1
ORDER BY composite_score DESC
LIMIT 10;
```

### 2. 0DTE Iron Condor Screener
```sql
-- 0DTE Iron Condor Opportunity Screening
WITH gamma_analysis AS (
    SELECT
        uw.symbol,
        uw.gamma_exposure,
        uw.dealer_gamma_flip,
        oc.iv_rank,
        oc.expected_move,
        p.vix_level,
        ec.has_earnings_today
    FROM uw_gamma_exposure uw
    JOIN options_chains oc ON uw.symbol = oc.underlying
    JOIN polygon_vix p ON p.timestamp = (SELECT MAX(timestamp) FROM polygon_vix)
    LEFT JOIN earnings_calendar ec ON uw.symbol = ec.symbol
        AND ec.report_date = CURRENT_DATE
    WHERE oc.expiry = CURRENT_DATE
      AND oc.iv_rank > 30
      AND p.vix_level < 25
      AND (ec.has_earnings_today IS NULL OR ec.has_earnings_today = false)
)
SELECT symbol, gamma_exposure, iv_rank, expected_move, vix_level,
       (iv_rank * 0.4 + (25 - vix_level) * 0.3 + gamma_exposure * 0.3) as condor_score
FROM gamma_analysis
WHERE condor_score > 60
ORDER BY condor_score DESC
LIMIT 5;
```

### 3. Earnings IV Crush Screener
```sql
-- Earnings IV Crush Opportunity Detection
WITH earnings_analysis AS (
    SELECT
        e.symbol,
        e.report_time,
        e.expected_move_perc,
        oc.implied_volatility,
        he.avg_historical_move,
        oc.iv_rank,
        uw.options_volume_ratio,
        (oc.implied_volatility - he.avg_historical_iv) as iv_overpricing
    FROM earnings e
    JOIN options_chains oc ON e.symbol = oc.underlying
    JOIN historical_earnings he ON e.symbol = he.symbol
    LEFT JOIN uw_options_volume uw ON e.symbol = uw.symbol
    WHERE e.report_date = CURRENT_DATE
      AND e.has_options = true
      AND oc.iv_rank > 70
      AND oc.implied_volatility > he.avg_historical_iv * 1.2
)
SELECT symbol, report_time, expected_move_perc, implied_volatility,
       iv_rank, iv_overpricing, options_volume_ratio,
       (iv_rank * 0.3 + iv_overpricing * 100 * 0.4 + options_volume_ratio * 0.3) as crush_score
FROM earnings_analysis
WHERE crush_score > 70
ORDER BY crush_score DESC
LIMIT 8;
```

### 4. RSI Mean Reversion Screener
```sql
-- RSI Extreme Mean Reversion Screening
WITH rsi_analysis AS (
    SELECT
        p.symbol,
        p.price,
        p.rsi_15min,
        p.rsi_5min,
        p.volume_ratio,
        p.price_change_pct,
        sr.nearest_support,
        sr.nearest_resistance,
        ABS(p.rsi_15min - 50) as rsi_extreme_score
    FROM polygon_live_data p
    LEFT JOIN support_resistance_levels sr ON p.symbol = sr.symbol
    WHERE (p.rsi_15min < 25 OR p.rsi_15min > 75)
      AND p.volume_ratio > 1.5
      AND p.symbol IN ('SPY', 'QQQ', 'IWM', 'AAPL', 'MSFT', 'TSLA', 'NVDA')
      AND p.bid_ask_spread < 0.02
)
SELECT symbol, price, rsi_15min, rsi_5min, volume_ratio,
       price_change_pct, nearest_support, nearest_resistance,
       (rsi_extreme_score * 0.4 + volume_ratio * 0.3 + ABS(price_change_pct) * 100 * 0.3) as reversion_score
FROM rsi_analysis
ORDER BY reversion_score DESC
LIMIT 10;
```

### 5. Gap Fill Strategy Screener
```sql
-- Gap Fill Opportunity Detection
WITH gap_analysis AS (
    SELECT
        pm.symbol,
        pm.gap_percent,
        pm.premarket_volume_ratio,
        pm.previous_close,
        pm.premarket_price,
        stn.catalyst_strength,
        ls.avg_volume,
        CASE WHEN stn.symbol IS NOT NULL THEN 1 ELSE 0 END as has_catalyst
    FROM premarket_data pm
    LEFT JOIN stock_titan_news stn ON pm.symbol = stn.symbol
        AND stn.timestamp > pm.market_date - INTERVAL '12 hours'
    JOIN liquid_stocks ls ON pm.symbol = ls.symbol
    WHERE ABS(pm.gap_percent) BETWEEN 0.02 AND 0.04
      AND pm.premarket_volume_ratio < 2.0
      AND ls.avg_volume > 1000000
)
SELECT symbol, gap_percent, premarket_volume_ratio, has_catalyst,
       catalyst_strength, avg_volume,
       (ABS(gap_percent) * 100 * 0.5 + (1.0 - has_catalyst) * 0.3 +
        (2.0 - premarket_volume_ratio) * 0.2) as gap_fill_score
FROM gap_analysis
WHERE gap_fill_score > 60
ORDER BY gap_fill_score DESC
LIMIT 8;
```

### 6. BTC-SPY Correlation Screener
```sql
-- BTC-SPY Correlation Signal Detection
WITH crypto_analysis AS (
    SELECT
        cd.symbol,
        cd.price as current_price,
        LAG(cd.price, 48) OVER (ORDER BY cd.timestamp) as price_4h_ago,  -- 48 5-min bars = 4 hours
        ((cd.price - LAG(cd.price, 48) OVER (ORDER BY cd.timestamp)) /
         LAG(cd.price, 48) OVER (ORDER BY cd.timestamp)) as btc_move_4h,
        corr.correlation_strength,
        corr.optimal_lag_hours,
        vix.level as vix_level
    FROM crypto_data cd
    JOIN btc_spy_correlation corr ON corr.timestamp = (SELECT MAX(timestamp) FROM btc_spy_correlation)
    JOIN vix_data vix ON vix.timestamp = (SELECT MAX(timestamp) FROM vix_data)
    WHERE cd.symbol = 'X:BTCUSD'  -- Polygon crypto currency symbol
      AND cd.timestamp = (SELECT MAX(timestamp) FROM crypto_data WHERE symbol = 'X:BTCUSD')
)
SELECT symbol, current_price, btc_move_4h, correlation_strength,
       optimal_lag_hours, vix_level,
       (ABS(btc_move_4h) * correlation_strength * 100) as correlation_signal_score
FROM crypto_analysis
WHERE ABS(btc_move_4h) > 0.02
  AND correlation_strength > 0.6
  AND vix_level < 30
  AND correlation_signal_score > 120
ORDER BY correlation_signal_score DESC;
```

### 7. Weekend Gap Predictor Screener
```sql
-- Weekend Gap Prediction Analysis (Sunday/Monday Only)
WITH weekend_crypto_analysis AS (
    SELECT
        'X:BTCUSD' as crypto_symbol,  -- Polygon crypto currency symbol
        FIRST(price) OVER (ORDER BY timestamp) as friday_close,
        LAST(price) OVER (ORDER BY timestamp) as sunday_current,
        ((LAST(price) OVER (ORDER BY timestamp) - FIRST(price) OVER (ORDER BY timestamp)) /
         FIRST(price) OVER (ORDER BY timestamp)) as weekend_move,
        AVG(volume) as weekend_avg_volume,
        COUNT(*) as data_points
    FROM crypto_data
    WHERE symbol = 'X:BTCUSD'
      AND timestamp >= date_trunc('week', NOW()) + INTERVAL '4 days 16 hours'  -- Friday 4 PM
      AND timestamp <= NOW()
      AND EXTRACT(DOW FROM timestamp) IN (5, 6, 0)  -- Friday, Saturday, Sunday
),
eth_weekend_analysis AS (
    SELECT
        'X:ETHUSD' as crypto_symbol,
        ((LAST(price) OVER (ORDER BY timestamp) - FIRST(price) OVER (ORDER BY timestamp)) /
         FIRST(price) OVER (ORDER BY timestamp)) as eth_weekend_move
    FROM crypto_data
    WHERE symbol = 'X:ETHUSD'
      AND timestamp >= date_trunc('week', NOW()) + INTERVAL '4 days 16 hours'
      AND timestamp <= NOW()
      AND EXTRACT(DOW FROM timestamp) IN (5, 6, 0)
)
SELECT
    btc.weekend_move,
    eth.eth_weekend_move,
    (btc.weekend_move + eth.eth_weekend_move) / 2 as avg_crypto_move,
    CASE WHEN btc.weekend_move * eth.eth_weekend_move > 0 THEN 1 ELSE 0 END as directional_alignment,
    ABS(btc.weekend_move + eth.eth_weekend_move) / 2 * 100 as prediction_strength
FROM weekend_crypto_analysis btc
CROSS JOIN eth_weekend_analysis eth
WHERE ABS(btc.weekend_move) > 0.03
  AND EXTRACT(DOW FROM NOW()) IN (0, 1)  -- Sunday or Monday only
  AND EXTRACT(HOUR FROM NOW()) < 10      -- Before 10 AM
ORDER BY prediction_strength DESC;
```

### 8. Crypto Mean Reversion Screener
```sql
-- 24/7 Crypto Mean Reversion Opportunities
WITH crypto_rsi_analysis AS (
    SELECT
        cd.symbol,
        cd.price,
        cd.rsi_5min,
        cd.rsi_15min,
        cd.volume_24h / cd.avg_volume_24h as volume_ratio,
        cd.volatility_24h,
        fg.fear_greed_index,
        CASE
            WHEN cd.rsi_5min <= 20 THEN 'oversold'
            WHEN cd.rsi_5min >= 80 THEN 'overbought'
            ELSE 'neutral'
        END as rsi_signal,
        ABS(cd.rsi_5min - 50) as rsi_extreme_level
    FROM crypto_data cd
    JOIN fear_greed_index fg ON fg.timestamp = (SELECT MAX(timestamp) FROM fear_greed_index)
    WHERE cd.symbol IN ('X:BTCUSD', 'X:ETHUSD')
      AND cd.timestamp = (SELECT MAX(timestamp) FROM crypto_data WHERE symbol = cd.symbol)
      AND (cd.rsi_5min <= 20 OR cd.rsi_5min >= 80)
      AND cd.volatility_24h < 0.06  -- Less than 6% daily volatility
)
SELECT symbol, price, rsi_5min, rsi_15min, volume_ratio,
       volatility_24h, fear_greed_index, rsi_signal,
       (rsi_extreme_level * 0.4 + volume_ratio * 0.3 +
        (0.06 - volatility_24h) * 100 * 0.3) as crypto_reversion_score
FROM crypto_rsi_analysis
WHERE crypto_reversion_score > 50
ORDER BY crypto_reversion_score DESC;
```

## Integrated Screening Workflow

### Real-Time Screening Pipeline
```python
class RealTimeScreeningPipeline:
    def __init__(self):
        self.screener = EnhancedUniversalScreener()
        self.running = False

    async def start_continuous_screening(self):
        """Start continuous multi-strategy screening"""

        self.running = True

        while self.running:
            try:
                # Run all screeners
                opportunities = await self.screener.run_all_screeners()

                # Prioritize opportunities
                prioritized = self.prioritize_opportunities(opportunities)

                # Execute top opportunities
                if prioritized:
                    await self.execute_top_opportunities(prioritized)

                # Determine next scan interval based on market conditions
                scan_interval = self.calculate_scan_interval()
                await asyncio.sleep(scan_interval)

            except Exception as e:
                logger.error(f"Screening pipeline error: {e}")
                await asyncio.sleep(300)  # 5 minute error recovery

    def prioritize_opportunities(self, opportunities):
        """Prioritize opportunities across all strategies"""

        all_opps = []

        # Tier S strategies (highest priority)
        tier_s_strategies = ['news_catalyst', '0dte_iron_condor', 'earnings_iv_crush']
        for strategy in tier_s_strategies:
            for opp in opportunities.get(strategy, []):
                opp['tier'] = 'S'
                opp['priority_score'] = opp.get('confidence', 0) * 1.5
                all_opps.append(opp)

        # Tier A strategies
        tier_a_strategies = ['rsi_mean_reversion', 'gap_fill', 'premarket_momentum']
        for strategy in tier_a_strategies:
            for opp in opportunities.get(strategy, []):
                opp['tier'] = 'A'
                opp['priority_score'] = opp.get('confidence', 0) * 1.2
                all_opps.append(opp)

        # Tier B strategies
        tier_b_strategies = ['vwap_mean_reversion', 'opening_range_breakout',
                           'support_resistance', 'momentum_continuation']
        for strategy in tier_b_strategies:
            for opp in opportunities.get(strategy, []):
                opp['tier'] = 'B'
                opp['priority_score'] = opp.get('confidence', 0) * 1.0
                all_opps.append(opp)

        # Tier C crypto strategies
        tier_c_strategies = ['btc_spy_correlation', 'weekend_gap_predictor', 'crypto_mean_reversion']
        for strategy in tier_c_strategies:
            for opp in opportunities.get(strategy, []):
                opp['tier'] = 'C'
                opp['priority_score'] = opp.get('confidence', 0) * 0.8
                all_opps.append(opp)

        # Sort by priority score
        return sorted(all_opps, key=lambda x: x['priority_score'], reverse=True)

    def calculate_scan_interval(self):
        """Calculate optimal scanning interval based on market conditions"""

        current_time = datetime.now()
        market_status = get_market_status()

        if market_status == 'open':
            if 9.5 <= current_time.hour <= 10.5:  # Market open hour
                return 30  # 30 seconds during high activity
            else:
                return 60  # 1 minute during regular hours
        elif market_status == 'premarket':
            return 120  # 2 minutes during pre-market
        elif market_status == 'afterhours':
            return 300  # 5 minutes during after hours
        else:
            return 600  # 10 minutes when market closed (crypto only)
```

### Performance Monitoring
```python
class ScreenerPerformanceMonitor:
    def __init__(self):
        self.questdb = QuestDBClient()

    async def track_screener_performance(self):
        """Track and analyze screener effectiveness"""

        performance_sql = """
        WITH screener_signals AS (
            SELECT
                strategy_name,
                symbol,
                signal_timestamp,
                confidence_score,
                actual_return,
                CASE WHEN actual_return > 0 THEN 1 ELSE 0 END as win
            FROM strategy_signals ss
            JOIN trade_results tr ON ss.signal_id = tr.signal_id
            WHERE signal_timestamp >= NOW() - INTERVAL '30 days'
        )
        SELECT
            strategy_name,
            COUNT(*) as total_signals,
            AVG(win) as win_rate,
            AVG(actual_return) as avg_return,
            AVG(confidence_score) as avg_confidence,
            CORR(confidence_score, actual_return) as confidence_accuracy
        FROM screener_signals
        GROUP BY strategy_name
        ORDER BY win_rate DESC;
        """

        return await self.questdb.execute_query(performance_sql)
```

This enhanced screening framework provides comprehensive, real-time opportunity detection across all 13 strategies with intelligent prioritization and execution.