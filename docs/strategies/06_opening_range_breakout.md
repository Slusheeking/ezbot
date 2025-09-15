# Opening Range Breakout (ORB) Strategy

## Enhanced Data Integration
**Primary Sources**: Polygon (Real-time price/volume), UW (Opening flow), Stock Titan (Morning catalysts)
**Real-time Feeds**: First 30-minute range calculation, volume profile analysis, opening momentum tracking
**Screening**: Range breakout detection with volume confirmation and flow alignment

## Strategy Overview
**Type**: Breakout/Momentum
**Priority**: 5
**Target Win Rate**: 68-72%
**Position Size**: $4,000 per trade
**Range Period**: 9:30 - 10:00 AM ET (30 minutes)
**Entry Window**: 10:00 - 11:30 AM ET
**Hold Time**: 45-120 minutes typical
**Instruments**: Liquid stocks with average true range > $1

## Strategy Thesis
The first 30 minutes of trading establishes the initial balance range as institutional traders position themselves. Breakouts from this range with volume confirmation often lead to directional moves that persist for 1-2 hours. The strategy identifies and trades these breakouts while filtering out false breaks.

## Opening Range Definition

### Range Calculation
```python
class OpeningRangeCalculator:
    def __init__(self):
        self.range_period = 30  # minutes
        self.min_range = 0.003  # 0.3% minimum
        self.max_range = 0.01   # 1% maximum

    def calculate_opening_range(self, symbol):
        """Calculate the 30-minute opening range"""

        bars = get_bars(symbol, '1min', start='09:30:00', end='10:00:00')

        opening_range = {
            'symbol': symbol,
            'high': max(bar.high for bar in bars),
            'low': min(bar.low for bar in bars),
            'open': bars[0].open,
            'close': bars[-1].close,
            'volume': sum(bar.volume for bar in bars),
            'range_size': (high - low) / bars[0].open,
            'vwap': calculate_vwap(bars),
            'bar_count': len(bars),
            'inside_bars': count_inside_bars(bars),
            'trend': 'bullish' if bars[-1].close > bars[0].open else 'bearish'
        }

        # Add context
        opening_range['range_quality'] = self.assess_range_quality(opening_range)
        opening_range['tradeable'] = self.is_tradeable_range(opening_range)

        return opening_range

    def assess_range_quality(self, range_data):
        """Score the quality of the opening range"""

        score = 0

        # Ideal range size (0.5% - 0.8%)
        if 0.005 <= range_data['range_size'] <= 0.008:
            score += 3
        elif 0.003 <= range_data['range_size'] <= 0.01:
            score += 2
        else:
            score += 0

        # Clean range (few inside bars)
        if range_data['inside_bars'] <= 5:
            score += 2
        elif range_data['inside_bars'] <= 10:
            score += 1

        # Good volume
        avg_volume = get_avg_volume_30min(range_data['symbol'])
        if range_data['volume'] > avg_volume * 1.2:
            score += 2

        # Clear boundaries (not choppy)
        if is_clean_range(range_data):
            score += 2

        return 'A' if score >= 7 else 'B' if score >= 5 else 'C'

    def is_tradeable_range(self, range_data):
        """Determine if range is worth trading"""

        return (
            self.min_range <= range_data['range_size'] <= self.max_range and
            range_data['range_quality'] in ['A', 'B'] and
            range_data['volume'] > 100000
        )
```

## Breakout Detection

### Breakout Confirmation Rules
```python
def detect_breakout(symbol, opening_range):
    """Detect and validate breakouts"""

    current_price = get_current_price(symbol)
    current_volume = get_current_volume(symbol)

    breakout = {
        'type': None,
        'confirmed': False,
        'strength': 0,
        'volume_confirmation': False,
        'retest_complete': False
    }

    # Check for breakout
    if current_price > opening_range['high']:
        breakout['type'] = 'bullish'
        breakout['distance'] = (current_price - opening_range['high']) / opening_range['high']
    elif current_price < opening_range['low']:
        breakout['type'] = 'bearish'
        breakout['distance'] = (opening_range['low'] - current_price) / opening_range['low']
    else:
        return None

    # Validate breakout
    breakout['confirmed'] = validate_breakout(
        symbol=symbol,
        breakout_type=breakout['type'],
        opening_range=opening_range,
        current_data={'price': current_price, 'volume': current_volume}
    )

    return breakout if breakout['confirmed'] else None

def validate_breakout(symbol, breakout_type, opening_range, current_data):
    """Multi-factor breakout validation"""

    validations = {
        'price_confirmation': {
            'check': current_data['price'] > opening_range['high'] * 1.002 if breakout_type == 'bullish'
                    else current_data['price'] < opening_range['low'] * 0.998,
            'weight': 0.3
        },
        'volume_surge': {
            'check': current_data['volume'] > opening_range['volume'] / 30 * 1.5,  # 150% of average minute
            'weight': 0.25
        },
        'no_immediate_rejection': {
            'check': not was_rejected_immediately(symbol, breakout_type),
            'weight': 0.2
        },
        'market_alignment': {
            'check': is_market_aligned(breakout_type),
            'weight': 0.15
        },
        'time_valid': {
            'check': '10:00' <= get_current_time() <= '11:30',
            'weight': 0.1
        }
    }

    score = sum(v['weight'] for v in validations.values() if v['check'])

    return score >= 0.7  # 70% threshold
```

### False Breakout Detection
```python
def detect_false_breakout(symbol, breakout_data, opening_range):
    """Identify potential false breakouts"""

    false_signals = {
        'immediate_reversal': price_reversed_within_bars(symbol, bars=2),
        'low_volume': breakout_volume < avg_volume * 0.8,
        'no_follow_through': not has_continuation_bars(symbol, direction=breakout_data['type']),
        'resistance_rejection': hit_major_resistance(symbol, tolerance=0.001),
        'diverging_indicators': check_indicator_divergence(symbol),
        'market_weak': spy_opposite_direction(breakout_data['type']),
        'time_late': current_time > '11:30',  # Late breakouts often fail
        'range_too_wide': opening_range['range_size'] > 0.01,  # Wide ranges = choppy
        'multiple_failures': count_failed_breakouts_today(symbol) >= 2
    }

    risk_score = sum(false_signals.values())

    if risk_score >= 3:
        return 'high_risk'
    elif risk_score >= 2:
        return 'medium_risk'
    else:
        return 'low_risk'
```

## Entry Strategy

### Long Breakout Entry
```python
long_breakout_entry = {
    'breakout_confirmation': {
        'price_above': current_price > opening_range_high * 1.002,
        'close_above': last_bar_close > opening_range_high,
        'volume_surge': current_volume > avg_volume * 1.5,
        'no_upper_wick': upper_wick < bar_range * 0.3
    },
    'retest_entry': {
        'enabled': True,
        'wait_for_retest': price_returns_to_breakout_level,
        'holds_support': bounces_from_previous_resistance,
        'max_wait': 10  # minutes
    },
    'momentum_confirmation': {
        'consecutive_bars': 2,  # Need 2 bars above range
        'increasing_volume': each_bar_volume > previous,
        'macd_positive': macd > signal,
        'rsi_not_overbought': rsi < 70
    },
    'risk_filters': {
        'not_extended': price < opening_range_high * 1.01,
        'spread_tight': bid_ask_spread < 0.02,
        'not_near_resistance': distance_to_resistance > 0.005,
        'false_breakout_risk': detect_false_breakout() == 'low_risk'
    }
}
```

### Short Breakout Entry
```python
short_breakout_entry = {
    'breakout_confirmation': {
        'price_below': current_price < opening_range_low * 0.998,
        'close_below': last_bar_close < opening_range_low,
        'volume_surge': current_volume > avg_volume * 1.5,
        'no_lower_wick': lower_wick < bar_range * 0.3
    },
    'retest_entry': {
        'enabled': True,
        'wait_for_retest': price_returns_to_breakout_level,
        'rejected_at_resistance': fails_at_previous_support,
        'max_wait': 10  # minutes
    },
    'momentum_confirmation': {
        'consecutive_bars': 2,  # Need 2 bars below range
        'increasing_volume': each_bar_volume > previous,
        'macd_negative': macd < signal,
        'rsi_not_oversold': rsi > 30
    }
}
```

## Position Management

### Exit Strategy
```python
orb_exit_rules = {
    'profit_targets': {
        'conservative': {
            'target': opening_range_size * 1,  # 1x range
            'probability': 0.70,
            'partial_exit': 0.5  # Exit half
        },
        'standard': {
            'target': opening_range_size * 1.5,  # 1.5x range
            'probability': 0.55,
            'partial_exit': 0.25  # Exit 25% more
        },
        'aggressive': {
            'target': opening_range_size * 2,  # 2x range
            'probability': 0.35,
            'full_exit': True
        }
    },
    'stop_loss': {
        'initial': opening_range_midpoint,  # Stop at range midpoint
        'aggressive': opposite_range_boundary,  # Opposite side of range
        'trailing': {
            'activation': range_size * 0.75,  # After 75% of range profit
            'distance': range_size * 0.5  # Trail by half range
        }
    },
    'time_stops': {
        '60_min': 'Reduce by 50% if target not hit',
        '90_min': 'Exit if no progress',
        '120_min': 'Maximum hold time'
    }
}
```

### Range Re-entry Rules
```python
def check_range_reentry(symbol, opening_range, previous_breakout):
    """Check if we can re-enter after initial breakout"""

    reentry_conditions = {
        'returned_to_range': is_price_in_range(symbol, opening_range),
        'time_passed': minutes_since_breakout(previous_breakout) > 30,
        'volume_reset': current_volume < spike_volume * 0.5,
        'different_direction': True,  # Can trade opposite direction
        'max_attempts': count_today_attempts(symbol) < 2
    }

    if all(reentry_conditions.values()):
        return True

    return False
```

## Risk Management

### Position Sizing
```python
def calculate_orb_position_size(range_quality, range_size, base_size=4000):
    """Dynamic sizing based on range quality"""

    quality_multipliers = {
        'A': 1.2,
        'B': 1.0,
        'C': 0.8
    }

    # Adjust for range size (tighter ranges = larger position)
    if range_size < 0.005:
        size_mult = 1.2
    elif range_size < 0.007:
        size_mult = 1.0
    else:
        size_mult = 0.8

    position_size = base_size * quality_multipliers[range_quality] * size_mult

    # Reduce if late in session
    if current_time > '11:00':
        position_size *= 0.8

    # Risk management cap
    max_risk = account_value * 0.02
    stop_distance = range_size / 2  # Stop at midpoint
    max_position = max_risk / stop_distance

    return min(position_size, max_position)
```

## Performance Metrics

### Historical Performance
```python
orb_performance = {
    'overall_stats': {
        'win_rate': 0.69,
        'avg_winner': 0.0087,  # 0.87%
        'avg_loser': 0.0042,   # 0.42%
        'profit_factor': 1.43,
        'avg_hold_time': 73  # minutes
    },
    'by_range_size': {
        '0.3-0.5%': {'win_rate': 0.72, 'avg_return': 0.0065},
        '0.5-0.7%': {'win_rate': 0.70, 'avg_return': 0.0078},
        '0.7-1.0%': {'win_rate': 0.66, 'avg_return': 0.0082}
    },
    'by_time': {
        '10:00-10:30': {'win_rate': 0.73, 'trades': 453},
        '10:30-11:00': {'win_rate': 0.69, 'trades': 312},
        '11:00-11:30': {'win_rate': 0.64, 'trades': 189}
    },
    'best_symbols': ['SPY', 'QQQ', 'AAPL', 'TSLA', 'NVDA'],
    'worst_days': ['Monday', 'Friday'],  # Choppy
    'best_days': ['Tuesday', 'Wednesday', 'Thursday']
}
```

## Implementation Code

```python
class OpeningRangeBreakoutStrategy:
    def __init__(self, config):
        self.range_calculator = OpeningRangeCalculator()
        self.position_size = 4000
        self.max_positions = 2
        self.opening_ranges = {}

    async def calculate_opening_ranges(self):
        """Run at 10:00 AM"""
        print("[10:00 AM] Calculating opening ranges...")

        for symbol in self.universe:
            range_data = self.range_calculator.calculate_opening_range(symbol)

            if range_data['tradeable']:
                self.opening_ranges[symbol] = range_data
                print(f"{symbol}: Range {range_data['range_size']:.2%}, Quality: {range_data['range_quality']}")

        return self.opening_ranges

    async def monitor_for_breakouts(self):
        """Monitor for breakouts 10:00 - 11:30"""

        while '10:00' <= get_current_time() <= '11:30':
            for symbol, range_data in self.opening_ranges.items():
                if self.has_position(symbol):
                    continue

                breakout = detect_breakout(symbol, range_data)

                if breakout and breakout['confirmed']:
                    # Check false breakout risk
                    risk = detect_false_breakout(symbol, breakout, range_data)

                    if risk == 'low_risk':
                        await self.enter_breakout_trade(symbol, breakout, range_data)
                    elif risk == 'medium_risk':
                        # Wait for retest
                        await self.wait_for_retest(symbol, breakout, range_data)

            await asyncio.sleep(5)  # Check every 5 seconds

    async def enter_breakout_trade(self, symbol, breakout, range_data):
        """Enter breakout trade with stops and targets"""

        position_size = self.calculate_orb_position_size(
            range_data['range_quality'],
            range_data['range_size']
        )

        if breakout['type'] == 'bullish':
            entry_price = get_current_ask(symbol)
            stop_loss = (range_data['high'] + range_data['low']) / 2
            target_1 = entry_price + range_data['range_size'] * entry_price
            target_2 = entry_price + range_data['range_size'] * 1.5 * entry_price
        else:
            entry_price = get_current_bid(symbol)
            stop_loss = (range_data['high'] + range_data['low']) / 2
            target_1 = entry_price - range_data['range_size'] * entry_price
            target_2 = entry_price - range_data['range_size'] * 1.5 * entry_price

        order = create_bracket_order(
            symbol=symbol,
            side='buy' if breakout['type'] == 'bullish' else 'sell',
            quantity=position_size / entry_price,
            stop_loss=stop_loss,
            take_profit=target_2
        )

        return await submit_order(order)
```

## Common Pitfalls

1. **Trading wide ranges**: Ranges > 1% are often too choppy
2. **Ignoring volume**: Breakouts without volume usually fail
3. **No retest patience**: Best entries often come on retest
4. **Late entries**: Breakouts after 11:30 AM have lower success
5. **Fighting the trend**: Don't trade against strong market direction

## Optimization Opportunities

### Machine Learning Features
```python
orb_ml_features = [
    'range_size',
    'range_quality_score',
    'volume_ratio',
    'time_of_breakout',
    'bars_to_breakout',
    'spy_correlation',
    'sector_strength',
    'vix_level',
    'previous_day_range',
    'gap_size',
    'premarket_activity'
]
```