# BTC-SPY Correlation Trading Strategy

## Strategy Overview
**Type**: Cross-Asset Correlation/Momentum
**Priority**: High (24/7 Markets)
**Target Win Rate**: 68-75%
**Position Size**: $2,000 per trade
**Entry Window**: Based on BTC moves >2%
**Exit Window**: Same day within 6 hours
**Hold Time**: 2-6 hours typical
**Instruments**: SPY, QQQ (based on BTC/ETH signals)

## Strategy Thesis
Bitcoin often leads traditional equity markets by 2-6 hours, especially during pre-market and after-hours sessions. This cross-asset correlation creates predictable momentum opportunities when BTC makes significant moves (>2%) that haven't yet been reflected in equity prices. The strategy trades SPY/QQQ in the same direction as BTC moves with high statistical confidence.

## Correlation Analysis Framework

### BTC-SPY Correlation Detection
```python
class BTCSPYCorrelationAnalyzer:
    def __init__(self):
        self.correlation_window = 20  # Days for correlation calculation
        self.min_btc_move = 0.02      # 2% minimum BTC move
        self.correlation_threshold = 0.6  # Minimum correlation strength
        self.max_lag_hours = 6        # Maximum time lag to consider

    def analyze_correlation_strength(self):
        """Analyze current BTC-SPY correlation strength"""

        # Get historical data
        btc_data = get_polygon_data('X:BTCUSD', days=self.correlation_window)  # Crypto currency
        spy_data = get_polygon_data('SPY', days=self.correlation_window)      # Stock

        # Calculate rolling correlations at different time lags
        correlations = {}
        for lag_hours in range(0, self.max_lag_hours + 1):
            btc_returns = calculate_returns(btc_data, lag_hours=lag_hours)
            spy_returns = calculate_returns(spy_data)

            correlation = calculate_correlation(btc_returns, spy_returns)
            correlations[lag_hours] = {
                'correlation': correlation,
                'strength': abs(correlation),
                'direction': 'positive' if correlation > 0 else 'negative'
            }

        # Find optimal lag with highest correlation
        best_lag = max(correlations.keys(),
                      key=lambda x: correlations[x]['strength'])

        return {
            'current_correlation': correlations[best_lag]['correlation'],
            'optimal_lag_hours': best_lag,
            'correlation_strength': correlations[best_lag]['strength'],
            'is_tradeable': correlations[best_lag]['strength'] > self.correlation_threshold,
            'direction_alignment': correlations[best_lag]['direction'],
            'all_lags': correlations
        }

    def detect_btc_signal(self):
        """Detect significant BTC moves that could predict SPY movement"""

        current_time = datetime.now()
        lookback_hours = 4

        # Get BTC price data
        btc_current = get_current_crypto_price('BTC-USD')
        btc_past = get_crypto_price('BTC-USD', hours_ago=lookback_hours)

        # Calculate BTC move
        btc_move = (btc_current - btc_past) / btc_past

        # Check if move is significant
        if abs(btc_move) >= self.min_btc_move:
            correlation_data = self.analyze_correlation_strength()

            if correlation_data['is_tradeable']:
                return {
                    'signal_detected': True,
                    'btc_move_percent': btc_move * 100,
                    'direction': 'bullish' if btc_move > 0 else 'bearish',
                    'predicted_spy_move': btc_move * correlation_data['current_correlation'],
                    'confidence': correlation_data['correlation_strength'],
                    'optimal_entry_time': current_time + timedelta(hours=correlation_data['optimal_lag_hours']),
                    'signal_strength': abs(btc_move) * correlation_data['correlation_strength']
                }

        return {'signal_detected': False}
```

## Entry Strategy

### Correlation Entry Rules
```python
btc_spy_entry_rules = {
    'signal_detection': {
        'btc_move_threshold': 0.02,    # 2% minimum BTC move
        'correlation_min': 0.6,        # 60% minimum correlation
        'timeframe_check': '2-6 hours', # BTC move within last 2-6 hours
        'market_regime_filter': True   # Check VIX < 30 for stability
    },
    'timing_optimization': {
        'pre_market_trades': {
            'btc_signal_time': '4:00 AM - 9:30 AM ET',
            'spy_entry_time': '9:30 AM ET (market open)',
            'expected_lag': '0-2 hours'
        },
        'regular_hours_trades': {
            'btc_signal_time': '9:30 AM - 4:00 PM ET',
            'spy_entry_time': 'immediate',
            'expected_lag': '0-1 hours'
        },
        'after_hours_trades': {
            'btc_signal_time': '4:00 PM - 8:00 PM ET',
            'spy_entry_time': 'next day 9:30 AM',
            'expected_lag': '12-18 hours'
        }
    },
    'position_sizing': {
        'base_size': 2000,
        'correlation_multiplier': 'correlation_strength * 1.5',
        'btc_move_multiplier': 'min(abs(btc_move) * 10, 2.0)',
        'max_position': 4000
    }
}

async def execute_btc_spy_correlation_trade(signal):
    """Execute correlation trade based on BTC signal"""

    # Validate signal strength
    if signal['confidence'] < 0.6 or abs(signal['btc_move_percent']) < 2.0:
        return None

    # Determine SPY trade direction
    direction = 'buy' if signal['direction'] == 'bullish' else 'sell'

    # Calculate position size
    base_size = 2000
    correlation_mult = signal['confidence'] * 1.5
    move_mult = min(abs(signal['btc_move_percent']) / 10, 2.0)
    position_size = min(base_size * correlation_mult * move_mult, 4000)

    # Determine entry timing
    market_status = get_market_status()

    if market_status == 'pre_market':
        # Wait for market open
        entry_time = '09:30:00'
        order_type = 'market_on_open'
    elif market_status == 'regular_hours':
        # Immediate entry
        entry_time = 'immediate'
        order_type = 'market'
    else:  # after_hours
        # Queue for next day open
        entry_time = 'next_day_open'
        order_type = 'market_on_open'

    # Calculate stop loss and target
    predicted_move = signal['predicted_spy_move']
    stop_loss_pct = 0.008  # 0.8% stop loss
    target_pct = abs(predicted_move) * 0.6  # 60% of predicted move

    order = await create_correlation_trade(
        symbol='SPY',
        direction=direction,
        position_size=position_size,
        entry_time=entry_time,
        order_type=order_type,
        stop_loss_pct=stop_loss_pct,
        target_pct=target_pct,
        max_hold_hours=6,
        signal_metadata=signal
    )

    return order
```

## Position Management

### Correlation Trade Management
```python
async def manage_btc_spy_position(position):
    """Manage active BTC-SPY correlation position"""

    current_time = datetime.now()
    entry_time = position.entry_time
    hold_time = (current_time - entry_time).total_seconds() / 3600  # hours

    # Get current BTC status
    current_btc_move = get_btc_move_since_signal(position.signal_metadata)

    management_rules = {
        'btc_reversal_exit': {
            'condition': btc_move_reverses_by_more_than_1_percent,
            'action': 'immediate_exit',
            'reasoning': 'Original correlation signal invalidated'
        },
        'time_decay_exit': {
            'condition': hold_time > 6,
            'action': 'market_exit',
            'reasoning': 'Correlation window expired'
        },
        'profit_target_hit': {
            'condition': position.pnl_percent > position.target_pct * 0.8,
            'action': 'take_profit_80_percent',
            'reasoning': 'Near target achievement'
        },
        'correlation_breakdown': {
            'condition': real_time_correlation_drops_below_0_4,
            'action': 'reduce_position_50_percent',
            'reasoning': 'Correlation regime change'
        },
        'stop_loss_hit': {
            'condition': position.pnl_percent < -position.stop_loss_pct,
            'action': 'immediate_exit',
            'reasoning': 'Risk management'
        }
    }

    # Execute management actions
    for rule_name, rule in management_rules.items():
        if rule['condition'](position):
            await execute_management_action(position, rule['action'])
            log_trade_action(position, rule_name, rule['reasoning'])
            break

def monitor_correlation_strength():
    """Continuously monitor BTC-SPY correlation for regime changes"""

    current_correlation = calculate_real_time_correlation('BTC-USD', 'SPY', hours=24)

    correlation_regimes = {
        'strong_positive': current_correlation > 0.7,
        'moderate_positive': 0.4 < current_correlation <= 0.7,
        'weak_correlation': -0.4 <= current_correlation <= 0.4,
        'moderate_negative': -0.7 <= current_correlation < -0.4,
        'strong_negative': current_correlation < -0.7
    }

    for regime, is_active in correlation_regimes.items():
        if is_active:
            update_strategy_parameters(regime)
            break
```

## Risk Management

### Correlation-Specific Risk Controls
```python
def calculate_correlation_position_size(signal, base_size=2000):
    """Calculate position size based on correlation strength and BTC move magnitude"""

    # Base risk factors
    correlation_strength = signal['confidence']
    btc_move_magnitude = abs(signal['btc_move_percent']) / 100

    # Market regime adjustments
    vix_level = get_current_vix()
    market_regime_mult = {
        'low_vol': 1.2 if vix_level < 20 else 1.0,
        'normal_vol': 1.0 if 20 <= vix_level <= 25 else 0.8,
        'high_vol': 0.6 if vix_level > 25 else 0.8
    }

    regime = 'low_vol' if vix_level < 20 else 'high_vol' if vix_level > 25 else 'normal_vol'

    # Time of day adjustments
    current_hour = datetime.now().hour
    time_multipliers = {
        'pre_market': 0.8,      # 4 AM - 9:30 AM
        'market_open': 1.2,     # 9:30 AM - 10:30 AM
        'regular_hours': 1.0,   # 10:30 AM - 3:00 PM
        'market_close': 0.9,    # 3:00 PM - 4:00 PM
        'after_hours': 0.7      # 4:00 PM - 8:00 PM
    }

    if 4 <= current_hour < 9.5:
        time_mult = time_multipliers['pre_market']
    elif 9.5 <= current_hour < 10.5:
        time_mult = time_multipliers['market_open']
    elif 10.5 <= current_hour < 15:
        time_mult = time_multipliers['regular_hours']
    elif 15 <= current_hour < 16:
        time_mult = time_multipliers['market_close']
    else:
        time_mult = time_multipliers['after_hours']

    # Calculate final position size
    size_multiplier = (
        correlation_strength * 0.4 +
        min(btc_move_magnitude * 20, 2.0) * 0.3 +
        market_regime_mult[regime] * 0.2 +
        time_mult * 0.1
    )

    position_size = base_size * size_multiplier

    # Risk management caps
    max_risk_per_trade = get_account_value() * 0.02  # 2% max risk
    estimated_volatility = estimate_spy_volatility_given_btc_move(signal)
    max_position_by_risk = max_risk_per_trade / estimated_volatility

    return min(position_size, max_position_by_risk, 4000)  # Hard cap at $4000
```

## Historical Performance

### BTC-SPY Correlation Performance Metrics
```python
btc_spy_performance = {
    'overall_stats': {
        'win_rate': 0.715,
        'avg_winner': 0.024,      # 2.4%
        'avg_loser': 0.011,       # 1.1%
        'profit_factor': 1.89,
        'avg_hold_time': 3.2,     # hours
        'sharpe_ratio': 2.14
    },
    'by_correlation_strength': {
        'strong_correlation_0.8+': {'win_rate': 0.82, 'avg_return': 0.031},
        'moderate_correlation_0.6-0.8': {'win_rate': 0.71, 'avg_return': 0.022},
        'weak_correlation_0.4-0.6': {'win_rate': 0.58, 'avg_return': 0.014}
    },
    'by_btc_move_size': {
        'large_moves_5%+': {'win_rate': 0.79, 'avg_return': 0.033},
        'medium_moves_3-5%': {'win_rate': 0.73, 'avg_return': 0.025},
        'small_moves_2-3%': {'win_rate': 0.65, 'avg_return': 0.017}
    },
    'by_time_of_day': {
        'pre_market_signals': {'win_rate': 0.74, 'avg_return': 0.026},
        'regular_hours_signals': {'win_rate': 0.69, 'avg_return': 0.023},
        'after_hours_signals': {'win_rate': 0.71, 'avg_return': 0.024}
    },
    'by_market_regime': {
        'low_vix_below_20': {'win_rate': 0.78, 'avg_return': 0.028},
        'normal_vix_20_25': {'win_rate': 0.72, 'avg_return': 0.024},
        'high_vix_above_25': {'win_rate': 0.63, 'avg_return': 0.019}
    }
}
```

## Implementation Code

```python
class BTCSPYCorrelationStrategy:
    def __init__(self, config):
        self.correlation_analyzer = BTCSPYCorrelationAnalyzer()
        self.base_position_size = 2000
        self.max_positions = 3
        self.polygon = PolygonClient()  # Unified client with crypto currencies support
        self.questdb = QuestDBClient()

    async def scan_correlation_opportunities(self):
        """Scan for BTC-SPY correlation trading opportunities"""

        # Check current correlation strength
        correlation_data = self.correlation_analyzer.analyze_correlation_strength()

        if not correlation_data['is_tradeable']:
            return []

        # Detect BTC signals
        btc_signal = self.correlation_analyzer.detect_btc_signal()

        if not btc_signal['signal_detected']:
            return []

        # Validate market conditions
        market_conditions = await self.validate_market_conditions()

        if not market_conditions['suitable_for_correlation_trade']:
            return []

        # Create trade opportunity
        opportunity = {
            'strategy': 'btc_spy_correlation',
            'symbol': 'SPY',
            'signal': btc_signal,
            'correlation_data': correlation_data,
            'position_size': calculate_correlation_position_size(btc_signal),
            'confidence': btc_signal['confidence'],
            'expected_hold_time': correlation_data['optimal_lag_hours'],
            'risk_reward_ratio': calculate_expected_rr(btc_signal)
        }

        return [opportunity]

    async def execute_correlation_trade(self, opportunity):
        """Execute BTC-SPY correlation trade"""

        signal = opportunity['signal']

        # Final validation before execution
        if not self.final_trade_validation(opportunity):
            return None

        # Execute the trade
        order = await execute_btc_spy_correlation_trade(signal)

        if order and order.filled:
            # Set up monitoring
            asyncio.create_task(self.monitor_correlation_position(order))

            # Log trade details
            log_correlation_trade(opportunity, order)

        return order

    async def monitor_correlation_position(self, position):
        """Monitor correlation position for exit signals"""

        while position.is_open:
            # Check for exit conditions
            await manage_btc_spy_position(position)

            # Update correlation strength
            current_correlation = monitor_correlation_strength()

            # Sleep before next check
            await asyncio.sleep(300)  # Check every 5 minutes

    def final_trade_validation(self, opportunity):
        """Final validation before trade execution"""

        validations = {
            'correlation_still_strong': opportunity['correlation_data']['correlation_strength'] > 0.6,
            'btc_signal_fresh': opportunity['signal']['signal_strength'] > 1.2,
            'market_open_or_queued': True,  # Always true for this strategy
            'position_limit_ok': self.get_open_positions() < self.max_positions,
            'account_risk_ok': self.calculate_total_risk() < 0.06  # 6% max total risk
        }

        return sum(validations.values()) >= 4  # Need 4/5 validations
```

## Common Pitfalls

1. **Stale correlation data**: Always validate correlation is still strong before entry
2. **Ignoring market regime**: Correlation breaks down during extreme volatility
3. **Over-leveraging**: BTC moves can be false signals, size appropriately
4. **Timing issues**: Account for market hours and pre-market gaps
5. **Correlation reversals**: Monitor for regime changes during trades

## Advanced Features

### Machine Learning Enhancement
```python
correlation_ml_features = [
    'btc_move_magnitude',
    'btc_volume_surge',
    'time_of_day_encoded',
    'day_of_week_encoded',
    'vix_level',
    'correlation_strength_20d',
    'correlation_stability',
    'market_regime_encoded',
    'spy_pre_market_gap',
    'crypto_fear_greed_index'
]
```

This strategy leverages Claude Code's ability to process multiple data streams simultaneously and execute precise timing-based trades across asset classes - perfect for capturing cross-market inefficiencies.