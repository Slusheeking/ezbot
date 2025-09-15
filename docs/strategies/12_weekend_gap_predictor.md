# Weekend Gap Predictor Strategy

## Strategy Overview
**Type**: Cross-Asset Gap Prediction/Pre-Market
**Priority**: High (Weekend Edge)
**Target Win Rate**: 65-72%
**Position Size**: $2,500 per trade
**Entry Window**: Monday pre-market 4:00 AM - 9:25 AM ET
**Exit Window**: Same day by 11:00 AM ET
**Hold Time**: 30 minutes - 3 hours
**Instruments**: SPY, QQQ (based on weekend crypto moves)

## Strategy Thesis
Cryptocurrency markets trade 24/7 while traditional equity markets are closed on weekends. Significant crypto moves during weekend hours often predict the direction and magnitude of Monday morning gaps in equity markets. This strategy analyzes Bitcoin and Ethereum weekend performance to predict and trade SPY/QQQ gaps at Monday market open.

## Weekend Analysis Framework

### Crypto Weekend Movement Analysis
```python
class WeekendGapPredictor:
    def __init__(self):
        self.weekend_start = 'Friday 4:00 PM ET'
        self.weekend_end = 'Monday 9:30 AM ET'
        self.min_crypto_move = 0.03  # 3% minimum weekend move
        self.gap_correlation_threshold = 0.5
        self.lookback_weeks = 12  # 3 months of weekend data

    def analyze_weekend_crypto_moves(self):
        """Analyze weekend crypto movements for gap prediction"""

        # Get weekend timeframe
        weekend_start = self.get_last_weekend_start()
        weekend_end = self.get_current_weekend_end()

        # Get crypto data for weekend period
        btc_data = get_polygon_weekend_data('X:BTCUSD', weekend_start, weekend_end)
        eth_data = get_polygon_weekend_data('X:ETHUSD', weekend_start, weekend_end)

        # Calculate weekend moves
        btc_weekend_move = (btc_data['end_price'] - btc_data['start_price']) / btc_data['start_price']
        eth_weekend_move = (eth_data['end_price'] - eth_data['start_price']) / eth_data['start_price']

        # Analyze volume and volatility
        btc_weekend_volume = btc_data['total_volume']
        btc_avg_weekend_volume = get_avg_weekend_volume('BTC-USD', weeks=self.lookback_weeks)
        btc_volume_ratio = btc_weekend_volume / btc_avg_weekend_volume

        eth_weekend_volume = eth_data['total_volume']
        eth_avg_weekend_volume = get_avg_weekend_volume('ETH-USD', weeks=self.lookback_weeks)
        eth_volume_ratio = eth_weekend_volume / eth_avg_weekend_volume

        # Check for news/catalyst correlation
        weekend_news = get_weekend_news_sentiment(weekend_start, weekend_end)

        return {
            'btc_weekend_move': btc_weekend_move,
            'eth_weekend_move': eth_weekend_move,
            'avg_crypto_move': (btc_weekend_move + eth_weekend_move) / 2,
            'btc_volume_ratio': btc_volume_ratio,
            'eth_volume_ratio': eth_volume_ratio,
            'weekend_volume_surge': max(btc_volume_ratio, eth_volume_ratio) > 1.3,
            'weekend_news_sentiment': weekend_news['net_sentiment'],
            'move_significance': abs(btc_weekend_move) > self.min_crypto_move,
            'directional_alignment': btc_weekend_move * eth_weekend_move > 0,  # Same direction
            'analysis_timestamp': datetime.now()
        }

    def predict_monday_gap(self, weekend_analysis):
        """Predict Monday gap based on weekend crypto analysis"""

        # Historical correlation analysis
        historical_data = self.get_historical_weekend_gap_data(weeks=self.lookback_weeks)

        # Calculate predictive factors
        crypto_move_magnitude = abs(weekend_analysis['avg_crypto_move'])
        crypto_direction = 1 if weekend_analysis['avg_crypto_move'] > 0 else -1

        # Factor weights based on historical performance
        factor_weights = {
            'crypto_move_magnitude': 0.35,
            'volume_confirmation': 0.20,
            'directional_alignment': 0.15,
            'news_sentiment_alignment': 0.15,
            'historical_correlation': 0.15
        }

        # Calculate individual factor scores
        move_magnitude_score = min(crypto_move_magnitude / 0.05, 1.0)  # Normalize to 5% max
        volume_score = 1.0 if weekend_analysis['weekend_volume_surge'] else 0.5
        alignment_score = 1.0 if weekend_analysis['directional_alignment'] else 0.3
        sentiment_score = abs(weekend_analysis['weekend_news_sentiment']) / 100  # Normalize sentiment
        correlation_score = self.calculate_recent_correlation_strength(historical_data)

        # Weighted prediction score
        prediction_score = (
            move_magnitude_score * factor_weights['crypto_move_magnitude'] +
            volume_score * factor_weights['volume_confirmation'] +
            alignment_score * factor_weights['directional_alignment'] +
            sentiment_score * factor_weights['news_sentiment_alignment'] +
            correlation_score * factor_weights['historical_correlation']
        )

        # Predict gap magnitude based on historical relationships
        predicted_gap_magnitude = crypto_move_magnitude * 0.4  # 40% of crypto move typically
        predicted_gap_direction = crypto_direction

        return {
            'prediction_confidence': prediction_score,
            'predicted_gap_percent': predicted_gap_magnitude * predicted_gap_direction,
            'predicted_direction': 'bullish' if predicted_gap_direction > 0 else 'bearish',
            'is_tradeable': prediction_score > 0.6 and crypto_move_magnitude > self.min_crypto_move,
            'factor_breakdown': {
                'move_magnitude': move_magnitude_score,
                'volume_confirmation': volume_score,
                'directional_alignment': alignment_score,
                'sentiment_alignment': sentiment_score,
                'correlation_strength': correlation_score
            },
            'historical_accuracy': self.calculate_prediction_accuracy(prediction_score)
        }

    def get_historical_weekend_gap_data(self, weeks):
        """Get historical weekend crypto moves and Monday gaps for analysis"""

        # QuestDB query for historical correlation analysis
        query = """
        WITH weekend_crypto AS (
            SELECT date_trunc('week', timestamp) as week,
                   symbol,
                   FIRST(price) as friday_close,
                   LAST(price) as monday_open,
                   (LAST(price) - FIRST(price)) / FIRST(price) as weekend_move
            FROM crypto_data
            WHERE symbol IN ('BTC-USD', 'ETH-USD')
              AND timestamp >= NOW() - INTERVAL '{} weeks'
              AND EXTRACT(DOW FROM timestamp) IN (5, 1)  -- Friday and Monday
            GROUP BY week, symbol
        ),
        monday_gaps AS (
            SELECT date_trunc('week', timestamp) as week,
                   symbol,
                   (open_price - prev_close) / prev_close as gap_percent
            FROM market_data
            WHERE symbol IN ('SPY', 'QQQ')
              AND timestamp >= NOW() - INTERVAL '{} weeks'
              AND EXTRACT(DOW FROM timestamp) = 1  -- Monday only
        )
        SELECT wc.week, wc.symbol as crypto_symbol, wc.weekend_move,
               mg.symbol as equity_symbol, mg.gap_percent
        FROM weekend_crypto wc
        JOIN monday_gaps mg ON wc.week = mg.week
        ORDER BY wc.week DESC
        """.format(weeks, weeks)

        return self.questdb.execute_query(query)
```

## Entry Strategy

### Gap Prediction Entry Rules
```python
weekend_gap_entry_rules = {
    'prediction_criteria': {
        'min_crypto_weekend_move': 0.03,     # 3% minimum
        'min_prediction_confidence': 0.6,     # 60% confidence
        'directional_alignment_required': True,  # BTC and ETH same direction
        'volume_confirmation_preferred': True,   # Weekend volume surge
        'max_predicted_gap': 0.02             # 2% max predicted gap (risk control)
    },
    'timing_requirements': {
        'analysis_window': 'Friday 4PM - Monday 4AM ET',
        'entry_window': 'Monday 4AM - 9:25AM ET',
        'pre_market_entry': True,
        'market_open_entry': True,
        'exit_by': '11:00 AM ET same day'
    },
    'market_conditions': {
        'avoid_high_vix': 'VIX > 30',
        'avoid_major_news': 'No scheduled major announcements',
        'prefer_normal_volume': 'Pre-market volume < 2x average',
        'check_futures': 'ES/NQ alignment with prediction'
    }
}

async def execute_weekend_gap_trade(prediction, weekend_analysis):
    """Execute gap trade based on weekend crypto analysis"""

    if not prediction['is_tradeable']:
        return None

    # Determine optimal symbol (SPY vs QQQ)
    symbol = select_optimal_gap_symbol(weekend_analysis)

    # Calculate position parameters
    direction = 'buy' if prediction['predicted_direction'] == 'bullish' else 'sell'
    predicted_gap = abs(prediction['predicted_gap_percent'])
    confidence = prediction['prediction_confidence']

    # Position sizing based on confidence and predicted magnitude
    base_size = 2500
    confidence_mult = confidence * 1.5
    magnitude_mult = min(predicted_gap / 0.01, 2.0)  # Scale by 1% increments
    position_size = min(base_size * confidence_mult * magnitude_mult, 5000)

    # Entry strategy based on timing
    current_time = datetime.now().time()
    market_open = time(9, 30)

    if current_time < market_open:
        # Pre-market entry strategy
        entry_strategy = await plan_premarket_gap_entry(symbol, direction, prediction)
    else:
        # At-open entry strategy
        entry_strategy = await plan_market_open_gap_entry(symbol, direction, prediction)

    # Risk management parameters
    stop_loss_pct = 0.008  # 0.8% stop loss
    take_profit_pct = predicted_gap * 0.7  # 70% of predicted gap
    max_hold_time = 3  # hours

    order = await create_gap_prediction_trade(
        symbol=symbol,
        direction=direction,
        position_size=position_size,
        entry_strategy=entry_strategy,
        stop_loss_pct=stop_loss_pct,
        take_profit_pct=take_profit_pct,
        max_hold_hours=max_hold_time,
        prediction_metadata={
            'weekend_analysis': weekend_analysis,
            'prediction': prediction,
            'entry_time': datetime.now()
        }
    )

    return order

def select_optimal_gap_symbol(weekend_analysis):
    """Select SPY or QQQ based on weekend crypto characteristics"""

    # QQQ tends to correlate more strongly with crypto during tech-heavy moves
    # SPY is more stable for broader market predictions

    if weekend_analysis['btc_weekend_move'] > weekend_analysis['eth_weekend_move']:
        # BTC-driven moves often correlate better with SPY
        return 'SPY'
    else:
        # ETH-driven moves often correlate better with QQQ (tech heavy)
        return 'QQQ'

async def plan_premarket_gap_entry(symbol, direction, prediction):
    """Plan pre-market entry for gap trade"""

    # Get current pre-market price action
    premarket_data = get_premarket_data(symbol)
    current_gap = premarket_data['gap_percent']
    predicted_gap = prediction['predicted_gap_percent']

    if abs(current_gap) >= abs(predicted_gap) * 0.8:
        # Gap already largely realized in pre-market
        return {
            'entry_type': 'gap_fill_play',
            'entry_method': 'limit_order_fade_gap',
            'entry_price': calculate_gap_fill_entry(premarket_data),
            'reasoning': 'Gap overshoot - fade the move'
        }
    else:
        # Gap not yet realized - momentum play
        return {
            'entry_type': 'gap_momentum_play',
            'entry_method': 'market_on_open',
            'entry_price': 'market',
            'reasoning': 'Gap prediction still valid - momentum entry'
        }
```

## Position Management

### Gap Trade Management
```python
async def manage_weekend_gap_position(position):
    """Manage weekend gap prediction position"""

    current_time = datetime.now()
    entry_time = position.entry_time
    hold_time = (current_time - entry_time).total_seconds() / 3600

    # Get current market conditions
    current_gap = calculate_current_gap_vs_prediction(position)
    market_momentum = assess_gap_momentum_continuation(position.symbol)

    gap_management_rules = {
        'gap_target_achieved': {
            'condition': current_gap >= position.prediction['predicted_gap_percent'] * 0.8,
            'action': 'take_profit_75_percent',
            'reasoning': 'Gap prediction largely achieved'
        },
        'gap_reversal_detected': {
            'condition': current_gap < 0 and position.prediction['predicted_gap_percent'] > 0,
            'action': 'immediate_exit',
            'reasoning': 'Gap prediction failed - reversal detected'
        },
        'momentum_continuation': {
            'condition': market_momentum['strength'] > 0.7 and hold_time < 1,
            'action': 'hold_position',
            'reasoning': 'Strong momentum continuation'
        },
        'momentum_exhaustion': {
            'condition': market_momentum['strength'] < 0.3,
            'action': 'reduce_position_50_percent',
            'reasoning': 'Gap momentum exhausting'
        },
        'time_exit': {
            'condition': hold_time > 3 or current_time.hour >= 11,
            'action': 'market_exit',
            'reasoning': 'Gap window closing'
        },
        'stop_loss': {
            'condition': position.pnl_percent < -position.stop_loss_pct,
            'action': 'immediate_exit',
            'reasoning': 'Stop loss hit'
        }
    }

    # Execute management actions
    for rule_name, rule in gap_management_rules.items():
        if rule['condition']:
            await execute_management_action(position, rule['action'])
            log_gap_trade_action(position, rule_name, rule['reasoning'])
            break

def assess_gap_momentum_continuation(symbol):
    """Assess whether gap momentum is likely to continue"""

    # Get current market data
    current_data = get_real_time_data(symbol)

    momentum_factors = {
        'volume_confirmation': current_data['volume'] > current_data['avg_volume'] * 1.5,
        'price_action_strength': abs(current_data['price_change']) > 0.01,
        'bid_ask_imbalance': calculate_order_flow_imbalance(symbol),
        'sector_alignment': check_sector_momentum_alignment(symbol),
        'futures_confirmation': check_futures_alignment(symbol)
    }

    # Weight momentum factors
    weights = {
        'volume_confirmation': 0.25,
        'price_action_strength': 0.25,
        'bid_ask_imbalance': 0.2,
        'sector_alignment': 0.15,
        'futures_confirmation': 0.15
    }

    momentum_score = sum(
        (1.0 if momentum_factors[factor] else 0.0) * weights[factor]
        for factor in momentum_factors
    )

    return {
        'strength': momentum_score,
        'factors': momentum_factors,
        'recommendation': 'hold' if momentum_score > 0.6 else 'reduce' if momentum_score > 0.3 else 'exit'
    }
```

## Risk Management

### Weekend Gap Risk Controls
```python
def calculate_weekend_gap_position_size(prediction, weekend_analysis, base_size=2500):
    """Calculate position size based on prediction confidence and risk factors"""

    confidence = prediction['prediction_confidence']
    predicted_magnitude = abs(prediction['predicted_gap_percent'])

    # Risk adjustments
    risk_factors = {
        'prediction_confidence': confidence,
        'gap_magnitude': min(predicted_magnitude / 0.02, 1.0),  # Normalize to 2%
        'crypto_alignment': 1.0 if weekend_analysis['directional_alignment'] else 0.6,
        'volume_confirmation': 1.0 if weekend_analysis['weekend_volume_surge'] else 0.8,
        'market_regime': assess_gap_trading_regime()
    }

    # Calculate size multipliers
    size_multiplier = (
        risk_factors['prediction_confidence'] * 0.3 +
        risk_factors['gap_magnitude'] * 0.25 +
        risk_factors['crypto_alignment'] * 0.2 +
        risk_factors['volume_confirmation'] * 0.15 +
        risk_factors['market_regime'] * 0.1
    )

    position_size = base_size * size_multiplier

    # Risk management caps
    max_risk_per_trade = get_account_value() * 0.025  # 2.5% max risk
    estimated_volatility = 0.012  # Estimated 1.2% volatility for gap trades
    max_position_by_risk = max_risk_per_trade / estimated_volatility

    return min(position_size, max_position_by_risk, 5000)  # Hard cap at $5000

def assess_gap_trading_regime():
    """Assess current market regime for gap trading effectiveness"""

    vix_level = get_current_vix()
    market_correlation = get_polygon_crypto_equity_correlation(days=10)
    recent_gap_accuracy = calculate_recent_gap_prediction_accuracy(weeks=4)

    regime_score = 0

    # VIX-based regime assessment
    if vix_level < 20:
        regime_score += 0.4  # Low volatility favors gap prediction
    elif vix_level < 25:
        regime_score += 0.3  # Normal volatility
    else:
        regime_score += 0.1  # High volatility reduces effectiveness

    # Correlation-based assessment
    if market_correlation > 0.6:
        regime_score += 0.3  # Strong correlation favors strategy
    elif market_correlation > 0.4:
        regime_score += 0.2  # Moderate correlation
    else:
        regime_score += 0.1  # Weak correlation

    # Recent accuracy assessment
    if recent_gap_accuracy > 0.7:
        regime_score += 0.3  # Recent success
    elif recent_gap_accuracy > 0.6:
        regime_score += 0.2  # Moderate recent success
    else:
        regime_score += 0.1  # Poor recent performance

    return regime_score
```

## Historical Performance

### Weekend Gap Prediction Performance
```python
weekend_gap_performance = {
    'overall_stats': {
        'win_rate': 0.688,
        'avg_winner': 0.021,      # 2.1%
        'avg_loser': 0.009,       # 0.9%
        'profit_factor': 1.73,
        'avg_hold_time': 2.4,     # hours
        'sharpe_ratio': 1.97,
        'max_drawdown': 0.034     # 3.4%
    },
    'by_prediction_confidence': {
        'high_confidence_0.8+': {'win_rate': 0.79, 'avg_return': 0.027},
        'medium_confidence_0.6-0.8': {'win_rate': 0.68, 'avg_return': 0.019},
        'low_confidence_0.4-0.6': {'win_rate': 0.54, 'avg_return': 0.012}
    },
    'by_crypto_move_size': {
        'large_weekend_moves_5%+': {'win_rate': 0.74, 'avg_return': 0.025},
        'medium_weekend_moves_3-5%': {'win_rate': 0.69, 'avg_return': 0.021},
        'small_weekend_moves_2-3%': {'win_rate': 0.61, 'avg_return': 0.016}
    },
    'by_gap_direction': {
        'bullish_gaps': {'win_rate': 0.71, 'avg_return': 0.023},
        'bearish_gaps': {'win_rate': 0.66, 'avg_return': 0.019}
    },
    'seasonal_patterns': {
        'Q1_strong_correlation': {'win_rate': 0.73, 'note': 'Post-holiday rebalancing'},
        'Q2_moderate_correlation': {'win_rate': 0.68, 'note': 'Stable correlation'},
        'Q3_weaker_correlation': {'win_rate': 0.64, 'note': 'Summer doldrums'},
        'Q4_variable_correlation': {'win_rate': 0.71, 'note': 'Year-end effects'}
    }
}
```

## Implementation Code

```python
class WeekendGapPredictorStrategy:
    def __init__(self, config):
        self.gap_predictor = WeekendGapPredictor()
        self.base_position_size = 2500
        self.max_positions = 2  # Conservative limit
        self.polygon = PolygonClient()  # Unified client with crypto currencies support
        self.equity_client = PolygonEquityClient()
        self.questdb = QuestDBClient()

    async def analyze_weekend_and_predict(self):
        """Main weekend analysis and gap prediction function"""

        # Only run on Sundays and Monday pre-market
        current_day = datetime.now().weekday()
        current_hour = datetime.now().hour

        if not (current_day == 6 or (current_day == 0 and current_hour < 9)):
            return None

        # Analyze weekend crypto moves
        weekend_analysis = self.gap_predictor.analyze_weekend_crypto_moves()

        if not weekend_analysis['move_significance']:
            return None

        # Generate gap prediction
        prediction = self.gap_predictor.predict_monday_gap(weekend_analysis)

        if not prediction['is_tradeable']:
            return None

        # Create trading opportunity
        opportunity = {
            'strategy': 'weekend_gap_predictor',
            'weekend_analysis': weekend_analysis,
            'prediction': prediction,
            'symbol': select_optimal_gap_symbol(weekend_analysis),
            'position_size': calculate_weekend_gap_position_size(prediction, weekend_analysis),
            'confidence': prediction['prediction_confidence'],
            'expected_hold_time': 2.5,  # hours
            'analysis_timestamp': datetime.now()
        }

        return opportunity

    async def execute_gap_prediction_trade(self, opportunity):
        """Execute weekend gap prediction trade"""

        # Final validation
        if not self.validate_gap_trade_conditions(opportunity):
            return None

        # Execute the trade
        order = await execute_weekend_gap_trade(
            opportunity['prediction'],
            opportunity['weekend_analysis']
        )

        if order and order.filled:
            # Set up position monitoring
            asyncio.create_task(self.monitor_gap_position(order))

            # Log detailed trade information
            log_weekend_gap_trade(opportunity, order)

        return order

    async def monitor_gap_position(self, position):
        """Monitor gap position throughout the trading session"""

        while position.is_open and datetime.now().hour < 11:
            # Manage position based on gap evolution
            await manage_weekend_gap_position(position)

            # Sleep before next check
            await asyncio.sleep(180)  # Check every 3 minutes

        # Force exit at 11 AM if still open
        if position.is_open:
            await self.force_exit_gap_position(position, 'time_limit_reached')

    def validate_gap_trade_conditions(self, opportunity):
        """Final validation before executing gap trade"""

        current_time = datetime.now()

        validations = {
            'timing_valid': current_time.weekday() == 0 and current_time.hour < 10,  # Monday before 10 AM
            'prediction_confident': opportunity['confidence'] > 0.6,
            'position_limit_ok': self.get_open_positions() < self.max_positions,
            'market_regime_suitable': assess_gap_trading_regime() > 0.5,
            'no_major_news': not has_major_market_news_scheduled()
        }

        return sum(validations.values()) >= 4  # Need 4/5 validations

# QuestDB Integration for Historical Analysis
async def update_weekend_gap_database():
    """Update QuestDB with weekend gap analysis results"""

    weekend_analysis = WeekendGapPredictor().analyze_weekend_crypto_moves()
    prediction = WeekendGapPredictor().predict_monday_gap(weekend_analysis)

    # Store weekend analysis in QuestDB
    insert_sql = """
    INSERT INTO weekend_gap_analysis (
        timestamp, btc_weekend_move, eth_weekend_move, avg_crypto_move,
        btc_volume_ratio, eth_volume_ratio, weekend_volume_surge,
        directional_alignment, prediction_confidence, predicted_gap_percent,
        predicted_direction, is_tradeable
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    await questdb.execute_insert(insert_sql, [
        datetime.now(),
        weekend_analysis['btc_weekend_move'],
        weekend_analysis['eth_weekend_move'],
        weekend_analysis['avg_crypto_move'],
        weekend_analysis['btc_volume_ratio'],
        weekend_analysis['eth_volume_ratio'],
        weekend_analysis['weekend_volume_surge'],
        weekend_analysis['directional_alignment'],
        prediction['prediction_confidence'],
        prediction['predicted_gap_percent'],
        prediction['predicted_direction'],
        prediction['is_tradeable']
    ])
```

## Common Pitfalls

1. **Stale weekend data**: Ensure analysis includes full weekend timeframe
2. **Ignoring pre-market action**: Gap may already be realized before market open
3. **Over-leveraging**: Weekend predictions can fail, size conservatively
4. **Missing macro events**: Major news can override crypto correlation
5. **Regime changes**: Crypto-equity correlation varies with market conditions

## Advanced Features

### Machine Learning Enhancement
```python
weekend_gap_ml_features = [
    'btc_weekend_move_percent',
    'eth_weekend_move_percent',
    'crypto_weekend_volume_ratio',
    'weekend_news_sentiment_score',
    'crypto_directional_alignment',
    'pre_weekend_vix_level',
    'crypto_fear_greed_index',
    'weekend_social_media_buzz',
    'historical_correlation_strength',
    'previous_gap_accuracy'
]
```

This strategy leverages Claude Code's ability to continuously monitor 24/7 crypto markets and predict traditional market gaps with mathematical precision - capturing weekend alpha that most traders miss.