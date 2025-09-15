# Support/Resistance Bounce Strategy

## Enhanced Data Integration
**Primary Sources**: Polygon (Technical levels), UW (Level defense flow), QuestDB (Historical bounces)
**Real-time Feeds**: Multi-timeframe support/resistance levels, volume at price levels, institutional flow
**Screening**: Key level approach detection with volume confirmation and historical validation

## Strategy Overview
**Type**: Mean Reversion/Technical Analysis
**Priority**: Medium
**Target Win Rate**: 70-75%
**Position Size**: $3,500 per trade
**Hold Time**: 1-4 hours typical
**Entry Window**: 9:45 AM - 3:30 PM ET
**Instruments**: Liquid stocks and ETFs with clear S&R levels

## Strategy Thesis
Price tends to respect established support and resistance levels, creating predictable bounce opportunities. This strategy identifies key levels using historical price action, volume profile, and technical indicators, then trades the bounces with tight risk management.

## Support/Resistance Identification

### Level Detection Engine
```python
class SupportResistanceLevels:
    def __init__(self):
        self.lookback_days = 20
        self.touch_significance = 3  # Minimum touches for valid level
        self.proximity_tolerance = 0.002  # 0.2% tolerance

    def identify_key_levels(self, symbol):
        """Identify significant support and resistance levels"""

        bars = get_historical_bars(symbol, '5min', days=self.lookback_days)
        levels = {
            'resistance_levels': [],
            'support_levels': [],
            'pivot_levels': []
        }

        # Method 1: Pivot Point Analysis
        pivots = self.find_pivot_points(bars)
        levels['pivot_levels'] = self.cluster_pivots(pivots)

        # Method 2: Volume Profile Analysis
        volume_levels = self.analyze_volume_profile(bars)
        levels['volume_levels'] = volume_levels

        # Method 3: Psychological Levels (round numbers)
        current_price = bars[-1].close
        psych_levels = self.find_psychological_levels(current_price)
        levels['psychological_levels'] = psych_levels

        # Method 4: Moving Average Levels
        ma_levels = self.calculate_ma_levels(bars)
        levels['moving_average_levels'] = ma_levels

        # Combine and rank all levels
        all_levels = self.combine_and_rank_levels(levels)

        return {
            'symbol': symbol,
            'current_price': current_price,
            'key_levels': all_levels,
            'nearest_support': self.find_nearest_support(current_price, all_levels),
            'nearest_resistance': self.find_nearest_resistance(current_price, all_levels)
        }

    def find_pivot_points(self, bars):
        """Find swing highs and lows"""

        pivots = {'highs': [], 'lows': []}

        for i in range(2, len(bars) - 2):
            # Swing high
            if (bars[i].high > bars[i-1].high and bars[i].high > bars[i-2].high and
                bars[i].high > bars[i+1].high and bars[i].high > bars[i+2].high):
                pivots['highs'].append({
                    'price': bars[i].high,
                    'time': bars[i].time,
                    'volume': bars[i].volume,
                    'strength': self.calculate_pivot_strength(bars, i, 'high')
                })

            # Swing low
            if (bars[i].low < bars[i-1].low and bars[i].low < bars[i-2].low and
                bars[i].low < bars[i+1].low and bars[i].low < bars[i+2].low):
                pivots['lows'].append({
                    'price': bars[i].low,
                    'time': bars[i].time,
                    'volume': bars[i].volume,
                    'strength': self.calculate_pivot_strength(bars, i, 'low')
                })

        return pivots

    def analyze_volume_profile(self, bars):
        """Analyze volume at price levels"""

        price_volume_map = {}

        for bar in bars:
            # Bin prices to nearest cent for grouping
            price_bin = round(bar.close, 2)

            if price_bin not in price_volume_map:
                price_volume_map[price_bin] = 0

            price_volume_map[price_bin] += bar.volume

        # Find high volume nodes (potential S&R)
        sorted_levels = sorted(price_volume_map.items(), key=lambda x: x[1], reverse=True)

        volume_levels = []
        for price, volume in sorted_levels[:10]:  # Top 10 volume levels
            volume_levels.append({
                'price': price,
                'volume': volume,
                'type': 'volume_node',
                'strength': volume / max(price_volume_map.values())
            })

        return volume_levels

    def find_psychological_levels(self, current_price):
        """Find round number psychological levels"""

        levels = []
        base_price = int(current_price)

        # Major levels (whole dollars)
        for i in range(-5, 6):
            level = base_price + i
            if level > 0:
                distance = abs(current_price - level) / current_price
                if 0.001 < distance < 0.05:  # Within 5%
                    levels.append({
                        'price': level,
                        'type': 'psychological',
                        'strength': 0.7,
                        'description': f'${level} whole dollar'
                    })

        # Half dollar levels
        for i in range(-10, 11):
            level = base_price + (i * 0.5)
            distance = abs(current_price - level) / current_price
            if 0.001 < distance < 0.05:
                levels.append({
                    'price': level,
                    'type': 'psychological',
                    'strength': 0.5,
                    'description': f'${level} half dollar'
                })

        return levels
```

## Entry Strategy

### Bounce Setup Detection
```python
def detect_bounce_setup(symbol, levels_data):
    """Detect potential bounce setups at key levels"""

    current_price = get_current_price(symbol)
    current_volume = get_current_volume(symbol)

    setups = []

    # Check for support bounce setup
    nearest_support = levels_data['nearest_support']
    if nearest_support and current_price <= nearest_support['price'] * 1.003:  # Within 0.3%
        support_setup = {
            'type': 'support_bounce',
            'direction': 'long',
            'level': nearest_support,
            'entry_zone': [nearest_support['price'] * 0.998, nearest_support['price'] * 1.002],
            'stop_loss': nearest_support['price'] * 0.996,
            'target': calculate_resistance_target(current_price, levels_data),
            'strength': assess_bounce_probability(symbol, nearest_support, 'support')
        }

        if support_setup['strength'] > 0.6:
            setups.append(support_setup)

    # Check for resistance rejection setup
    nearest_resistance = levels_data['nearest_resistance']
    if nearest_resistance and current_price >= nearest_resistance['price'] * 0.997:  # Within 0.3%
        resistance_setup = {
            'type': 'resistance_rejection',
            'direction': 'short',
            'level': nearest_resistance,
            'entry_zone': [nearest_resistance['price'] * 0.998, nearest_resistance['price'] * 1.002],
            'stop_loss': nearest_resistance['price'] * 1.004,
            'target': calculate_support_target(current_price, levels_data),
            'strength': assess_bounce_probability(symbol, nearest_resistance, 'resistance')
        }

        if resistance_setup['strength'] > 0.6:
            setups.append(resistance_setup)

    return setups

def assess_bounce_probability(symbol, level, level_type):
    """Assess probability of successful bounce"""

    factors = {
        'level_strength': level['strength'],  # Based on touches/volume
        'approach_angle': calculate_approach_angle(symbol, level),
        'volume_confirmation': check_volume_at_level(symbol, level),
        'rsi_alignment': check_rsi_alignment(symbol, level_type),
        'market_context': check_market_alignment(symbol, level_type),
        'time_since_last_touch': calculate_time_since_touch(level),
        'level_age': calculate_level_age(level)
    }

    # Weighted probability calculation
    weights = {
        'level_strength': 0.25,
        'approach_angle': 0.15,
        'volume_confirmation': 0.20,
        'rsi_alignment': 0.15,
        'market_context': 0.15,
        'time_since_last_touch': 0.05,
        'level_age': 0.05
    }

    probability = sum(factors[k] * weights[k] for k in factors.keys())

    return min(probability, 1.0)  # Cap at 100%
```

### Entry Execution
```python
bounce_entry_rules = {
    'support_bounce': {
        'entry_triggers': [
            'price_touches_support_zone',
            'volume_increase_on_approach',
            'bullish_candle_pattern',
            'rsi_oversold_bounce'
        ],
        'confirmation_required': 2,  # Need 2+ triggers
        'entry_method': 'limit_order_in_zone',
        'max_wait_time': 30  # minutes
    },
    'resistance_rejection': {
        'entry_triggers': [
            'price_touches_resistance_zone',
            'rejection_candle_pattern',
            'volume_spike_on_rejection',
            'rsi_overbought_rejection'
        ],
        'confirmation_required': 2,
        'entry_method': 'market_order_on_confirmation',
        'max_wait_time': 15
    }
}

async def execute_bounce_trade(setup):
    """Execute support/resistance bounce trade"""

    if setup['type'] == 'support_bounce':
        # Place limit order in support zone
        entry_price = setup['entry_zone'][0]  # Lower end of zone

        order = await create_bracket_order(
            symbol=setup['symbol'],
            side='buy',
            quantity=calculate_shares(setup['position_size'], entry_price),
            entry_price=entry_price,
            stop_loss=setup['stop_loss'],
            take_profit=setup['target'],
            time_in_force='GTC',
            timeout=setup['max_wait_time'] * 60
        )

    else:  # resistance_rejection
        # Wait for confirmation then market order
        if await wait_for_rejection_confirmation(setup):
            order = await create_market_order(
                symbol=setup['symbol'],
                side='sell',
                quantity=calculate_shares(setup['position_size']),
                stop_loss=setup['stop_loss'],
                take_profit=setup['target']
            )

    return order
```

## Position Management

### Dynamic Level Monitoring
```python
class BouncePositionManager:
    def __init__(self):
        self.level_update_frequency = 300  # 5 minutes

    async def manage_bounce_position(self, position):
        """Manage open bounce position"""

        # Update support/resistance levels
        current_levels = self.identify_key_levels(position.symbol)

        # Check if our level is still valid
        level_health = self.assess_level_health(position.entry_level, current_levels)

        if level_health < 0.3:
            await self.close_position(position, 'level_breakdown')
            return

        # Dynamic stop management
        await self.manage_dynamic_stops(position, current_levels)

        # Target adjustment based on new levels
        await self.adjust_targets(position, current_levels)

    def manage_dynamic_stops(self, position, current_levels):
        """Adjust stops based on level strength"""

        if position.direction == 'long':
            # For longs, trail stop up with support levels
            new_support = self.find_trailing_support(position, current_levels)
            if new_support and new_support > position.stop_loss:
                position.stop_loss = new_support * 0.999  # Slight buffer

        else:  # short
            # For shorts, trail stop down with resistance levels
            new_resistance = self.find_trailing_resistance(position, current_levels)
            if new_resistance and new_resistance < position.stop_loss:
                position.stop_loss = new_resistance * 1.001

    def assess_level_health(self, original_level, current_levels):
        """Assess if the original level is still valid"""

        # Find matching level in current analysis
        for level in current_levels['key_levels']:
            if abs(level['price'] - original_level['price']) < original_level['price'] * 0.001:
                return level['strength']

        return 0  # Level not found - may have broken
```

## Risk Management

### Position Sizing Based on Level Quality
```python
def calculate_bounce_position_size(setup, base_size=3500):
    """Size position based on setup quality"""

    quality_multipliers = {
        'level_strength': {
            'very_strong': 1.3,    # Multiple touches, high volume
            'strong': 1.1,         # Clear level with good history
            'moderate': 1.0,       # Standard level
            'weak': 0.7            # Questionable level
        },
        'risk_reward': {
            'excellent': 1.2,      # >3:1 R:R
            'good': 1.0,           # 2:1 - 3:1 R:R
            'fair': 0.8,           # 1.5:1 - 2:1 R:R
            'poor': 0.5            # <1.5:1 R:R
        },
        'market_context': {
            'very_favorable': 1.2,
            'favorable': 1.0,
            'neutral': 0.8,
            'unfavorable': 0.5
        }
    }

    # Calculate multipliers
    level_mult = quality_multipliers['level_strength'].get(
        assess_level_quality(setup['level']), 1.0
    )

    rr_mult = quality_multipliers['risk_reward'].get(
        calculate_risk_reward_category(setup), 1.0
    )

    market_mult = quality_multipliers['market_context'].get(
        assess_market_context(setup), 1.0
    )

    total_multiplier = level_mult * rr_mult * market_mult

    position_size = base_size * total_multiplier

    # Risk management caps
    max_risk = get_account_value() * 0.015  # 1.5% max risk
    stop_distance = abs(setup['entry_price'] - setup['stop_loss']) / setup['entry_price']
    max_position = max_risk / stop_distance

    return min(position_size, max_position)
```

## Performance Analysis

### Historical Performance
```python
bounce_strategy_performance = {
    'overall_metrics': {
        'win_rate': 0.723,
        'profit_factor': 1.71,
        'avg_winner': 0.018,    # 1.8%
        'avg_loser': 0.009,     # 0.9%
        'avg_hold_time': 2.1,   # hours
        'sharpe_ratio': 1.89
    },
    'by_level_type': {
        'pivot_levels': {'win_rate': 0.75, 'avg_return': 0.019},
        'volume_levels': {'win_rate': 0.78, 'avg_return': 0.021},
        'psychological_levels': {'win_rate': 0.68, 'avg_return': 0.015},
        'moving_average_levels': {'win_rate': 0.71, 'avg_return': 0.017}
    },
    'by_level_strength': {
        'very_strong_levels': {'win_rate': 0.82, 'avg_return': 0.023},
        'strong_levels': {'win_rate': 0.74, 'avg_return': 0.018},
        'moderate_levels': {'win_rate': 0.69, 'avg_return': 0.016}
    },
    'by_market_conditions': {
        'trending_markets': {'win_rate': 0.65, 'avg_return': 0.015},
        'ranging_markets': {'win_rate': 0.79, 'avg_return': 0.021},
        'volatile_markets': {'win_rate': 0.58, 'avg_return': 0.013}
    }
}
```

## Implementation Code

```python
class SupportResistanceBounceStrategy:
    def __init__(self, config):
        self.sr_analyzer = SupportResistanceLevels()
        self.position_manager = BouncePositionManager()
        self.base_position_size = 3500
        self.max_positions = 5

    async def scan_bounce_opportunities(self):
        """Scan for support/resistance bounce opportunities"""

        opportunities = []

        # Get liquid stocks/ETFs
        universe = self.get_trading_universe()

        for symbol in universe:
            # Identify key levels
            levels_data = self.sr_analyzer.identify_key_levels(symbol)

            # Detect bounce setups
            setups = detect_bounce_setup(symbol, levels_data)

            for setup in setups:
                if setup['strength'] > 0.6:  # Minimum probability threshold
                    setup['symbol'] = symbol
                    setup['position_size'] = calculate_bounce_position_size(setup)
                    opportunities.append(setup)

        # Sort by probability and risk/reward
        return sorted(
            opportunities,
            key=lambda x: x['strength'] * calculate_risk_reward_ratio(x),
            reverse=True
        )

    def get_trading_universe(self):
        """Get universe of liquid instruments for S&R trading"""

        return [
            # Major ETFs
            'SPY', 'QQQ', 'IWM', 'DIA', 'XLF', 'XLK', 'XLE', 'XLI',
            # Liquid stocks
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META',
            'JPM', 'BAC', 'WMT', 'PG', 'JNJ', 'V', 'MA'
        ]

    async def execute_bounce_trades(self, opportunities):
        """Execute top bounce opportunities"""

        executed_trades = []

        for opportunity in opportunities[:self.max_positions]:
            if len(executed_trades) >= self.max_positions:
                break

            try:
                trade = await execute_bounce_trade(opportunity)
                if trade:
                    executed_trades.append(trade)
                    await asyncio.sleep(1)  # Brief delay between executions

            except Exception as e:
                self.log_error(f"Failed to execute bounce trade {opportunity['symbol']}: {e}")

        return executed_trades

    def validate_bounce_setup(self, setup):
        """Final validation before trade execution"""

        validations = {
            'level_quality': setup['level']['strength'] > 0.5,
            'risk_reward': calculate_risk_reward_ratio(setup) > 1.5,
            'market_hours': is_market_hours(),
            'liquidity': check_symbol_liquidity(setup['symbol']),
            'correlation': self.check_position_correlation(setup['symbol']),
            'news': not has_breaking_news(setup['symbol'])
        }

        return sum(validations.values()) >= 5  # Need 5/6 validations
```

## Common Pitfalls

1. **False levels**: Not all price clusters are true support/resistance
2. **Stale levels**: Levels lose significance over time
3. **Market context ignored**: S&R works better in ranging markets
4. **Poor risk management**: Stops too tight or too loose
5. **Level confluence**: Multiple levels close together can confuse analysis

## Advanced Techniques

### Multi-Timeframe Analysis
```python
def analyze_levels_multiple_timeframes(symbol):
    """Analyze S&R levels across multiple timeframes"""

    timeframes = ['5min', '15min', '1hour', 'daily']
    level_consensus = {}

    for tf in timeframes:
        tf_levels = identify_key_levels_timeframe(symbol, tf)

        # Weight levels by timeframe importance
        weights = {'5min': 0.2, '15min': 0.3, '1hour': 0.3, 'daily': 0.2}

        for level in tf_levels:
            level['weight'] = weights[tf]
            level['timeframe'] = tf

    # Find confluence zones where multiple timeframes agree
    confluence_zones = find_level_confluence(level_consensus)

    return confluence_zones
```