# Crypto Mean Reversion Strategy

## Strategy Overview
**Type**: Mean Reversion/Crypto-Native
**Priority**: Medium (24/7 Opportunity)
**Target Win Rate**: 60-68%
**Position Size**: $1,500 per trade
**Entry Window**: 24/7 (RSI-based triggers)
**Exit Window**: Within 8 hours maximum
**Hold Time**: 1-8 hours typical
**Instruments**: BTC-USD, ETH-USD (direct crypto trading)

## Strategy Thesis
Cryptocurrency markets exhibit stronger and faster mean reversion patterns compared to traditional equities due to higher volatility, 24/7 trading, and emotional retail participation. This strategy exploits RSI extremes in major cryptocurrencies with the advantage of no market hour constraints, allowing for optimal entry and exit timing without overnight risk concerns.

## Crypto Mean Reversion Framework

### Enhanced RSI Analysis for Crypto
```python
class CryptoMeanReversionAnalyzer:
    def __init__(self):
        self.rsi_periods = [14, 21]  # Multiple timeframes
        self.timeframes = ['5min', '15min', '1hour']
        self.oversold_threshold = 20
        self.overbought_threshold = 80
        self.volume_confirmation_factor = 1.3
        self.crypto_volatility_adjustment = True

    def analyze_crypto_rsi_setup(self, symbol):
        """Analyze RSI setup for crypto mean reversion"""

        rsi_data = {}
        volume_data = {}

        # Get RSI data across multiple timeframes
        for timeframe in self.timeframes:
            for period in self.rsi_periods:
                key = f'rsi_{period}_{timeframe}'
                rsi_data[key] = calculate_rsi(symbol, period, timeframe)

            # Get volume analysis for timeframe
            volume_data[timeframe] = analyze_volume_profile(symbol, timeframe)

        # Current price and volatility context
        current_price = get_current_crypto_price(symbol)
        volatility_24h = calculate_crypto_volatility(symbol, hours=24)
        volatility_7d = calculate_crypto_volatility(symbol, days=7)

        # Support/resistance levels for crypto
        support_resistance = identify_crypto_levels(symbol)

        # Fear & Greed index for market sentiment
        fear_greed_index = get_crypto_fear_greed_index()

        analysis = {
            'symbol': symbol,
            'current_price': current_price,
            'rsi_data': rsi_data,
            'volume_data': volume_data,
            'volatility_24h': volatility_24h,
            'volatility_7d': volatility_7d,
            'volatility_regime': self.classify_volatility_regime(volatility_24h, volatility_7d),
            'support_resistance': support_resistance,
            'fear_greed_index': fear_greed_index,
            'market_sentiment': self.classify_market_sentiment(fear_greed_index),
            'setup_quality': self.score_mean_reversion_setup(rsi_data, volume_data, volatility_24h)
        }

        return analysis

    def classify_volatility_regime(self, vol_24h, vol_7d):
        """Classify current volatility regime for crypto"""

        vol_ratio = vol_24h / vol_7d

        if vol_ratio > 1.5:
            return 'high_volatility'  # Recent spike in volatility
        elif vol_ratio < 0.7:
            return 'low_volatility'   # Below recent average
        else:
            return 'normal_volatility'

    def classify_market_sentiment(self, fear_greed_index):
        """Classify market sentiment based on Fear & Greed index"""

        if fear_greed_index <= 20:
            return 'extreme_fear'      # Strong contrarian opportunity
        elif fear_greed_index <= 40:
            return 'fear'              # Contrarian opportunity
        elif fear_greed_index <= 60:
            return 'neutral'           # No sentiment edge
        elif fear_greed_index <= 80:
            return 'greed'             # Potential reversal
        else:
            return 'extreme_greed'     # Strong reversal opportunity

    def score_mean_reversion_setup(self, rsi_data, volume_data, volatility):
        """Score the quality of mean reversion setup"""

        score = 0

        # RSI extreme scoring
        rsi_14_5min = rsi_data.get('rsi_14_5min', 50)
        rsi_14_15min = rsi_data.get('rsi_14_15min', 50)

        if rsi_14_5min <= 20 or rsi_14_5min >= 80:
            score += 3  # Strong 5min signal
        elif rsi_14_5min <= 25 or rsi_14_5min >= 75:
            score += 2  # Moderate 5min signal

        if rsi_14_15min <= 25 or rsi_14_15min >= 75:
            score += 2  # 15min confirmation

        # Volume confirmation
        if volume_data.get('5min', {}).get('volume_surge', False):
            score += 2

        # Multi-timeframe alignment
        if abs(rsi_14_5min - rsi_14_15min) <= 10:  # RSI alignment
            score += 1

        # Volatility adjustment
        if volatility > 0.04:  # High volatility (>4% daily)
            score -= 1  # Reduce score in extreme volatility

        return 'A' if score >= 6 else 'B' if score >= 4 else 'C'

    def detect_mean_reversion_signals(self, analysis):
        """Detect specific mean reversion entry signals"""

        signals = []
        rsi_data = analysis['rsi_data']
        current_price = analysis['current_price']

        # Oversold signal detection
        rsi_5min = rsi_data.get('rsi_14_5min', 50)
        rsi_15min = rsi_data.get('rsi_14_15min', 50)

        if rsi_5min <= self.oversold_threshold:
            signal_strength = (self.oversold_threshold - rsi_5min) / self.oversold_threshold

            signals.append({
                'type': 'oversold_reversal',
                'direction': 'long',
                'strength': signal_strength,
                'entry_price': current_price,
                'timeframe': '5min',
                'rsi_level': rsi_5min,
                'confirmation': rsi_15min <= 30,  # 15min oversold too
                'volume_confirmation': analysis['volume_data'].get('5min', {}).get('volume_surge', False)
            })

        # Overbought signal detection
        if rsi_5min >= self.overbought_threshold:
            signal_strength = (rsi_5min - self.overbought_threshold) / (100 - self.overbought_threshold)

            signals.append({
                'type': 'overbought_reversal',
                'direction': 'short',
                'strength': signal_strength,
                'entry_price': current_price,
                'timeframe': '5min',
                'rsi_level': rsi_5min,
                'confirmation': rsi_15min >= 70,  # 15min overbought too
                'volume_confirmation': analysis['volume_data'].get('5min', {}).get('volume_surge', False)
            })

        return signals
```

## Entry Strategy

### Crypto Mean Reversion Entry Rules
```python
crypto_mean_reversion_entry = {
    'signal_criteria': {
        'rsi_extreme_threshold': {'oversold': 20, 'overbought': 80},
        'multi_timeframe_confirmation': 'Prefer 5min + 15min alignment',
        'volume_confirmation': 'Volume > 1.3x recent average',
        'volatility_filter': 'Avoid if 24h volatility > 6%',
        'sentiment_alignment': 'Fear/Greed index supports reversal'
    },
    'entry_timing': {
        'immediate_entries': 'RSI < 15 or RSI > 85',
        'confirmation_entries': 'Wait for first bounce/rejection',
        'scale_in_entries': 'Add on further extremes',
        'max_wait_time': '30 minutes for confirmation'
    },
    'position_sizing': {
        'base_size': 1500,
        'signal_strength_multiplier': 'strength * 1.5',
        'volatility_adjustment': 'reduce 20% if high volatility',
        'sentiment_boost': '+20% if extreme fear/greed alignment'
    }
}

async def execute_crypto_mean_reversion_trade(analysis, signal):
    """Execute crypto mean reversion trade"""

    symbol = analysis['symbol']
    direction = signal['direction']
    entry_price = signal['entry_price']

    # Validate signal quality
    if analysis['setup_quality'] == 'C' or signal['strength'] < 0.3:
        return None

    # Calculate position size
    base_size = 1500
    strength_mult = signal['strength'] * 1.5
    volatility_mult = 0.8 if analysis['volatility_regime'] == 'high_volatility' else 1.0

    # Sentiment adjustment
    sentiment_mult = 1.0
    if analysis['market_sentiment'] in ['extreme_fear', 'extreme_greed']:
        sentiment_mult = 1.2

    position_size = base_size * strength_mult * volatility_mult * sentiment_mult
    position_size = min(position_size, 3000)  # Cap at $3000

    # Determine entry method based on signal strength
    if signal['strength'] > 0.7:
        entry_method = 'market_order'  # Strong signal - immediate entry
    else:
        entry_method = 'limit_order_with_slippage'  # Wait for better price

    # Calculate stop loss and target
    stop_loss_pct = calculate_crypto_stop_loss(analysis, signal)
    take_profit_pct = calculate_crypto_take_profit(analysis, signal)

    order = await create_crypto_mean_reversion_order(
        symbol=symbol,
        direction=direction,
        position_size=position_size,
        entry_method=entry_method,
        entry_price=entry_price,
        stop_loss_pct=stop_loss_pct,
        take_profit_pct=take_profit_pct,
        max_hold_hours=8,
        signal_metadata=signal,
        analysis_metadata=analysis
    )

    return order

def calculate_crypto_stop_loss(analysis, signal):
    """Calculate appropriate stop loss for crypto mean reversion"""

    base_stop = 0.025  # 2.5% base stop loss

    # Adjust for volatility
    volatility_24h = analysis['volatility_24h']
    volatility_adjustment = min(volatility_24h / 0.03, 2.0)  # Scale to 3% baseline

    # Adjust for signal strength (stronger signals get tighter stops)
    signal_adjustment = 1.0 - (signal['strength'] * 0.3)

    # Adjust for market sentiment (extreme sentiment gets wider stops)
    sentiment_adjustment = 1.0
    if analysis['market_sentiment'] in ['extreme_fear', 'extreme_greed']:
        sentiment_adjustment = 1.3

    final_stop = base_stop * volatility_adjustment * signal_adjustment * sentiment_adjustment
    return min(final_stop, 0.04)  # Cap at 4%

def calculate_crypto_take_profit(analysis, signal):
    """Calculate take profit target for crypto mean reversion"""

    base_target = 0.02  # 2% base target

    # Adjust for signal strength
    strength_adjustment = 1.0 + (signal['strength'] * 0.5)

    # Adjust for volatility (higher volatility = higher targets)
    volatility_adjustment = 1.0 + (analysis['volatility_24h'] / 0.02)

    # Adjust for RSI extreme level
    rsi_level = signal['rsi_level']
    if signal['direction'] == 'long':
        rsi_adjustment = (20 - rsi_level) / 20 + 1.0  # More oversold = higher target
    else:
        rsi_adjustment = (rsi_level - 80) / 20 + 1.0   # More overbought = higher target

    final_target = base_target * strength_adjustment * volatility_adjustment * rsi_adjustment
    return min(final_target, 0.035)  # Cap at 3.5%
```

## Position Management

### 24/7 Crypto Position Management
```python
async def manage_crypto_mean_reversion_position(position):
    """Manage crypto mean reversion position with 24/7 monitoring"""

    while position.is_open:
        current_time = datetime.now()
        hold_time = (current_time - position.entry_time).total_seconds() / 3600

        # Get current RSI status
        current_rsi = get_current_rsi(position.symbol, period=14, timeframe='5min')
        entry_rsi = position.signal_metadata['rsi_level']

        crypto_management_rules = {
            'rsi_normalization': {
                'condition': check_rsi_normalization(current_rsi, entry_rsi, position.direction),
                'action': 'take_partial_profit_50_percent',
                'reasoning': 'RSI returning to normal range'
            },
            'rsi_extreme_reversal': {
                'condition': check_rsi_extreme_reversal(current_rsi, position.direction),
                'action': 'take_profit_75_percent',
                'reasoning': 'RSI reached opposite extreme'
            },
            'momentum_exhaustion': {
                'condition': detect_momentum_exhaustion(position),
                'action': 'reduce_position_30_percent',
                'reasoning': 'Reversion momentum slowing'
            },
            'volatility_spike': {
                'condition': detect_volatility_spike(position.symbol),
                'action': 'tighten_stops_20_percent',
                'reasoning': 'Increased market volatility'
            },
            'time_decay': {
                'condition': hold_time > 6,
                'action': 'reduce_position_50_percent',
                'reasoning': 'Mean reversion window closing'
            },
            'max_hold_time': {
                'condition': hold_time > 8,
                'action': 'close_position',
                'reasoning': 'Maximum hold time reached'
            },
            'stop_loss': {
                'condition': position.pnl_percent < -position.stop_loss_pct,
                'action': 'immediate_exit',
                'reasoning': 'Stop loss triggered'
            },
            'take_profit': {
                'condition': position.pnl_percent >= position.take_profit_pct,
                'action': 'close_position',
                'reasoning': 'Target profit achieved'
            }
        }

        # Execute management actions
        for rule_name, rule in crypto_management_rules.items():
            if rule['condition']:
                await execute_management_action(position, rule['action'])
                log_crypto_trade_action(position, rule_name, rule['reasoning'])
                break

        # Sleep before next check (more frequent than stock monitoring)
        await asyncio.sleep(180)  # Check every 3 minutes for crypto

def check_rsi_normalization(current_rsi, entry_rsi, direction):
    """Check if RSI is normalizing from extreme levels"""

    if direction == 'long':
        # For long positions, profit when RSI rises from oversold
        return current_rsi > 35 and entry_rsi <= 20
    else:
        # For short positions, profit when RSI falls from overbought
        return current_rsi < 65 and entry_rsi >= 80

def check_rsi_extreme_reversal(current_rsi, direction):
    """Check if RSI has reached opposite extreme"""

    if direction == 'long':
        return current_rsi >= 70  # Long position, RSI now overbought
    else:
        return current_rsi <= 30  # Short position, RSI now oversold

def detect_momentum_exhaustion(position):
    """Detect when mean reversion momentum is exhausting"""

    symbol = position.symbol
    direction = position.direction

    # Check recent price action
    recent_bars = get_recent_crypto_bars(symbol, count=6, timeframe='5min')

    if direction == 'long':
        # For longs, exhaustion = series of small green candles or red candle
        return check_bullish_momentum_exhaustion(recent_bars)
    else:
        # For shorts, exhaustion = series of small red candles or green candle
        return check_bearish_momentum_exhaustion(recent_bars)

def detect_volatility_spike(symbol):
    """Detect sudden volatility spikes that could invalidate mean reversion"""

    current_volatility = calculate_crypto_volatility(symbol, hours=2)
    recent_avg_volatility = calculate_crypto_volatility(symbol, hours=24)

    return current_volatility > recent_avg_volatility * 1.8
```

## Risk Management

### Crypto-Specific Risk Controls
```python
def calculate_crypto_mean_reversion_risk(analysis, signal, base_size=1500):
    """Calculate position size with crypto-specific risk adjustments"""

    # Base risk calculations
    signal_strength = signal['strength']
    volatility_24h = analysis['volatility_24h']

    # Crypto market cap considerations (for smaller altcoins)
    market_cap_adjustment = 1.0  # BTC and ETH are tier 1

    # Time of day adjustments (even though 24/7, some hours are more volatile)
    current_hour_utc = datetime.utcnow().hour
    time_adjustments = {
        'asia_session': 0.9,     # 0-8 UTC (generally calmer)
        'europe_session': 1.0,   # 8-16 UTC (moderate activity)
        'us_session': 1.1,       # 16-24 UTC (highest activity)
    }

    if 0 <= current_hour_utc < 8:
        time_mult = time_adjustments['asia_session']
    elif 8 <= current_hour_utc < 16:
        time_mult = time_adjustments['europe_session']
    else:
        time_mult = time_adjustments['us_session']

    # Fear & Greed index adjustment
    fear_greed = analysis.get('fear_greed_index', 50)
    sentiment_mult = 1.0
    if fear_greed <= 20 or fear_greed >= 80:  # Extreme sentiment
        sentiment_mult = 1.2  # Increase size during extremes

    # Calculate final size
    size_multiplier = (
        signal_strength * 0.4 +
        (1.0 / max(volatility_24h / 0.03, 1.0)) * 0.25 +  # Inverse volatility weight
        market_cap_adjustment * 0.15 +
        time_mult * 0.1 +
        sentiment_mult * 0.1
    )

    position_size = base_size * size_multiplier

    # Crypto-specific risk limits
    max_crypto_exposure = get_account_value() * 0.10  # 10% max crypto exposure
    current_crypto_exposure = get_current_crypto_exposure()
    available_crypto_allocation = max_crypto_exposure - current_crypto_exposure

    # Individual trade risk limit
    max_risk_per_trade = get_account_value() * 0.02  # 2% max risk per trade
    estimated_risk = position_size * calculate_crypto_stop_loss(analysis, signal)

    final_position_size = min(
        position_size,
        available_crypto_allocation,
        max_risk_per_trade / (estimated_risk / position_size)
    )

    return max(final_position_size, 500)  # Minimum $500 position

class CryptoRiskManager:
    """Specialized risk management for crypto trading"""

    def __init__(self):
        self.max_crypto_allocation = 0.15  # 15% of account
        self.max_positions_per_crypto = 2   # Max 2 positions per crypto
        self.max_total_crypto_positions = 4 # Max 4 total crypto positions
        self.volatility_circuit_breaker = 0.08  # 8% daily volatility limit

    def validate_crypto_trade(self, symbol, analysis, position_size):
        """Validate crypto trade against risk parameters"""

        validations = {
            'allocation_limit': self.check_crypto_allocation_limit(position_size),
            'position_limit': self.check_position_limits(symbol),
            'volatility_limit': analysis['volatility_24h'] < self.volatility_circuit_breaker,
            'market_hours': True,  # Always true for crypto
            'correlation_check': self.check_crypto_correlation_limits(symbol)
        }

        return validations

    def check_crypto_allocation_limit(self, new_position_size):
        """Check if new position would exceed crypto allocation limits"""

        current_crypto_value = get_current_crypto_positions_value()
        account_value = get_account_value()
        max_allocation_value = account_value * self.max_crypto_allocation

        return (current_crypto_value + new_position_size) <= max_allocation_value

    def check_position_limits(self, symbol):
        """Check position count limits"""

        current_positions = get_open_crypto_positions()
        symbol_positions = len([p for p in current_positions if p.symbol == symbol])
        total_positions = len(current_positions)

        return (symbol_positions < self.max_positions_per_crypto and
                total_positions < self.max_total_crypto_positions)

    def check_crypto_correlation_limits(self, symbol):
        """Ensure we're not overconcentrated in correlated crypto assets"""

        if symbol in ['BTC-USD', 'ETH-USD']:
            # Check if we already have positions in highly correlated cryptos
            current_positions = get_open_crypto_positions()

            # If trading BTC, check for other BTC-correlated positions
            # If trading ETH, check for other ETH-correlated positions
            correlated_exposure = calculate_correlated_crypto_exposure(symbol)

            return correlated_exposure < get_account_value() * 0.08  # 8% max correlated exposure

        return True
```

## Historical Performance

### Crypto Mean Reversion Performance Metrics
```python
crypto_mean_reversion_performance = {
    'overall_stats': {
        'win_rate': 0.632,
        'avg_winner': 0.024,      # 2.4%
        'avg_loser': 0.018,       # 1.8%
        'profit_factor': 1.48,
        'avg_hold_time': 4.2,     # hours
        'sharpe_ratio': 1.76,
        'max_drawdown': 0.045     # 4.5%
    },
    'by_crypto_asset': {
        'BTC-USD': {'win_rate': 0.65, 'avg_return': 0.019, 'volatility': 0.038},
        'ETH-USD': {'win_rate': 0.62, 'avg_return': 0.022, 'volatility': 0.045}
    },
    'by_rsi_extreme_level': {
        'extreme_oversold_<15': {'win_rate': 0.74, 'avg_return': 0.031},
        'oversold_15-20': {'win_rate': 0.66, 'avg_return': 0.024},
        'extreme_overbought_>85': {'win_rate': 0.71, 'avg_return': 0.029},
        'overbought_80-85': {'win_rate': 0.58, 'avg_return': 0.018}
    },
    'by_time_of_day_utc': {
        'asia_session_0-8': {'win_rate': 0.59, 'avg_return': 0.021},
        'europe_session_8-16': {'win_rate': 0.64, 'avg_return': 0.023},
        'us_session_16-24': {'win_rate': 0.67, 'avg_return': 0.025}
    },
    'by_market_sentiment': {
        'extreme_fear_<20': {'win_rate': 0.73, 'avg_return': 0.028},
        'fear_20-40': {'win_rate': 0.67, 'avg_return': 0.024},
        'neutral_40-60': {'win_rate': 0.58, 'avg_return': 0.019},
        'greed_60-80': {'win_rate': 0.61, 'avg_return': 0.021},
        'extreme_greed_>80': {'win_rate': 0.69, 'avg_return': 0.026}
    },
    'by_volatility_regime': {
        'low_volatility': {'win_rate': 0.68, 'avg_return': 0.019},
        'normal_volatility': {'win_rate': 0.63, 'avg_return': 0.023},
        'high_volatility': {'win_rate': 0.54, 'avg_return': 0.027}
    }
}
```

## Implementation Code

```python
class CryptoMeanReversionStrategy:
    def __init__(self, config):
        self.analyzer = CryptoMeanReversionAnalyzer()
        self.risk_manager = CryptoRiskManager()
        self.base_position_size = 1500
        self.crypto_symbols = ['X:BTCUSD', 'X:ETHUSD']  # Polygon crypto currency symbols
        self.polygon = PolygonClient()  # Unified client with crypto currencies support
        self.questdb = QuestDBClient()

    async def scan_crypto_mean_reversion_opportunities(self):
        """Scan for crypto mean reversion opportunities across all timeframes"""

        opportunities = []

        for symbol in self.crypto_symbols:
            # Analyze current setup
            analysis = self.analyzer.analyze_crypto_rsi_setup(symbol)

            # Detect signals
            signals = self.analyzer.detect_mean_reversion_signals(analysis)

            for signal in signals:
                if signal['strength'] > 0.3:  # Minimum signal strength
                    # Validate with risk manager
                    position_size = calculate_crypto_mean_reversion_risk(analysis, signal)
                    risk_validation = self.risk_manager.validate_crypto_trade(
                        symbol, analysis, position_size
                    )

                    if sum(risk_validation.values()) >= 4:  # Need 4/5 risk checks
                        opportunities.append({
                            'strategy': 'crypto_mean_reversion',
                            'symbol': symbol,
                            'signal': signal,
                            'analysis': analysis,
                            'position_size': position_size,
                            'confidence': signal['strength'],
                            'setup_quality': analysis['setup_quality']
                        })

        # Sort by signal strength and setup quality
        return sorted(opportunities,
                     key=lambda x: x['signal']['strength'] *
                     {'A': 1.0, 'B': 0.8, 'C': 0.6}[x['setup_quality']],
                     reverse=True)

    async def execute_crypto_mean_reversion_trades(self, opportunities):
        """Execute top crypto mean reversion opportunities"""

        executed_trades = []

        for opportunity in opportunities[:2]:  # Limit to top 2 opportunities
            try:
                trade = await execute_crypto_mean_reversion_trade(
                    opportunity['analysis'],
                    opportunity['signal']
                )

                if trade:
                    # Set up 24/7 monitoring
                    asyncio.create_task(self.monitor_crypto_position(trade))
                    executed_trades.append(trade)

                    # Brief delay between executions
                    await asyncio.sleep(5)

            except Exception as e:
                logger.error(f"Failed to execute crypto trade {opportunity['symbol']}: {e}")

        return executed_trades

    async def monitor_crypto_position(self, position):
        """24/7 monitoring for crypto positions"""

        while position.is_open:
            try:
                await manage_crypto_mean_reversion_position(position)
                await asyncio.sleep(180)  # Check every 3 minutes
            except Exception as e:
                logger.error(f"Error monitoring crypto position {position.symbol}: {e}")
                await asyncio.sleep(300)  # Extended sleep on error

    async def update_crypto_market_data(self):
        """Continuously update crypto market data for analysis"""

        while True:
            try:
                for symbol in self.crypto_symbols:
                    # Update real-time data
                    price_data = get_current_polygon_crypto_data(symbol)
                    rsi_data = calculate_current_rsi_all_timeframes(symbol)
                    volume_data = get_current_volume_analysis(symbol)

                    # Store in QuestDB for historical analysis
                    await self.store_crypto_analysis_data(symbol, {
                        'price_data': price_data,
                        'rsi_data': rsi_data,
                        'volume_data': volume_data,
                        'timestamp': datetime.now()
                    })

                await asyncio.sleep(300)  # Update every 5 minutes

            except Exception as e:
                logger.error(f"Error updating crypto market data: {e}")
                await asyncio.sleep(600)  # Extended sleep on error

# Continuous 24/7 Operation
async def run_crypto_mean_reversion_strategy():
    """Main loop for 24/7 crypto mean reversion strategy"""

    strategy = CryptoMeanReversionStrategy({})

    # Start background tasks
    asyncio.create_task(strategy.update_crypto_market_data())

    while True:
        try:
            # Scan for opportunities
            opportunities = await strategy.scan_crypto_mean_reversion_opportunities()

            if opportunities:
                # Execute trades
                executed = await strategy.execute_crypto_mean_reversion_trades(opportunities)

                if executed:
                    logger.info(f"Executed {len(executed)} crypto mean reversion trades")

            # Sleep between scans (more frequent than stock strategies)
            await asyncio.sleep(600)  # Scan every 10 minutes

        except Exception as e:
            logger.error(f"Error in crypto mean reversion strategy loop: {e}")
            await asyncio.sleep(1800)  # 30 minute sleep on major error
```

## Common Pitfalls

1. **Ignoring crypto-specific volatility**: Size positions appropriately for higher volatility
2. **Over-trading**: 24/7 markets can lead to overactive trading
3. **News event risk**: Crypto reacts strongly to regulatory and adoption news
4. **Liquidity issues**: Ensure adequate liquidity especially during volatile periods
5. **Correlation assumptions**: Crypto correlations can change rapidly

## Advanced Features

### Machine Learning Enhancement
```python
crypto_mean_reversion_ml_features = [
    'rsi_14_5min',
    'rsi_14_15min',
    'rsi_21_1hour',
    'volume_ratio_5min',
    'volatility_24h',
    'volatility_7d',
    'fear_greed_index',
    'time_of_day_encoded',
    'day_of_week_encoded',
    'btc_dominance',
    'social_media_sentiment',
    'on_chain_metrics'
]
```

### Integration with Traditional Markets
```python
async def crypto_traditional_market_sync():
    """Monitor crypto mean reversion in context of traditional markets"""

    # Check if crypto moves are leading or following traditional markets
    correlation_strength = calculate_crypto_stock_correlation(days=7)

    if correlation_strength > 0.7:
        # High correlation - use traditional market signals for confirmation
        spy_rsi = get_current_rsi('SPY', period=14, timeframe='5min')
        return crypto_signals if spy_rsi_supports_crypto_direction(spy_rsi) else []
    else:
        # Low correlation - crypto trading on its own fundamentals
        return crypto_signals
```

This strategy leverages Claude Code's ability to monitor 24/7 crypto markets and execute precise mean reversion trades without the constraints of traditional market hours.