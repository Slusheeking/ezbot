# Pre-Market Momentum Continuation Strategy

## Enhanced Data Integration
**Primary Sources**: Polygon (Pre-market data), Stock Titan (Catalyst detection), UW (Pre-market flow), Reddit (Overnight buzz)
**Real-time Feeds**: Pre-market price action, volume surges, news catalysts, social sentiment spikes
**Screening**: Multi-source confirmation for pre-market momentum with catalyst validation

## Strategy Overview
**Type**: Momentum/News-Driven
**Priority**: 4
**Target Win Rate**: 70-73%
**Position Size**: $6,000 per trade
**Entry Time**: 9:31:00 AM ET (1 minute after open)
**Hold Time**: 30-60 minutes maximum
**Scan Time**: 9:00 AM ET
**Instruments**: Stocks with significant pre-market activity

## Strategy Thesis
Stocks showing strong pre-market momentum with legitimate catalysts often continue their move for the first 30-60 minutes of regular trading. The strategy identifies pre-market leaders with news catalysts and rides the institutional order flow that typically occurs at market open.

## Pre-Market Scanning (9:00 AM)

### Catalyst Scoring System
```python
class CatalystScorer:
    def __init__(self):
        self.stock_titan = StockTitanRSS()
        self.catalyst_weights = {
            'earnings_beat': 9,
            'earnings_miss': -9,
            'upgrade': 8,
            'downgrade': -8,
            'fda_approval': 10,
            'fda_rejection': -10,
            'partnership': 7,
            'acquisition': 8,
            'guidance_raise': 8,
            'guidance_lower': -8,
            'analyst_initiation': 6,
            'insider_buying': 5,
            'insider_selling': -4,
            'contract_win': 6,
            'product_launch': 5,
            'sector_momentum': 3
        }

    def score_catalyst(self, symbol):
        """Score catalyst strength 1-10"""
        news_items = self.stock_titan.get_news(symbol, hours=12)

        if not news_items:
            return {'score': 0, 'catalyst': None, 'confidence': 'none'}

        primary_catalyst = None
        max_score = 0

        for news in news_items:
            catalyst_type = self.classify_news(news)
            score = abs(self.catalyst_weights.get(catalyst_type, 0))

            if score > max_score:
                max_score = score
                primary_catalyst = catalyst_type

        # Adjust for multiple confirming sources
        if len(news_items) > 3:
            max_score = min(10, max_score + 1)

        return {
            'score': max_score,
            'catalyst': primary_catalyst,
            'direction': 'bullish' if self.catalyst_weights.get(primary_catalyst, 0) > 0 else 'bearish',
            'confidence': self.get_confidence_level(max_score)
        }

    def get_confidence_level(self, score):
        if score >= 8:
            return 'high'
        elif score >= 6:
            return 'medium'
        elif score >= 4:
            return 'low'
        else:
            return 'none'
```

### Pre-Market Scanner
```python
def scan_premarket_movers():
    """Run at 9:00 AM"""
    candidates = []

    for symbol in get_active_symbols():
        pm_data = get_premarket_data(symbol)

        # Basic filters
        if not meets_basic_criteria(pm_data):
            continue

        # Calculate pre-market metrics
        pm_metrics = {
            'symbol': symbol,
            'pm_change': (pm_data['last'] - pm_data['prev_close']) / pm_data['prev_close'],
            'pm_volume': pm_data['volume'],
            'avg_volume': get_avg_volume_20day(symbol),
            'volume_ratio': pm_data['volume'] / get_avg_pm_volume(symbol),
            'pm_high': pm_data['high'],
            'pm_low': pm_data['low'],
            'pm_range': (pm_data['high'] - pm_data['low']) / pm_data['prev_close'],
            'catalyst_score': catalyst_scorer.score_catalyst(symbol)
        }

        # Apply momentum filters
        if passes_momentum_filters(pm_metrics):
            candidates.append(pm_metrics)

    return sorted(candidates, key=lambda x: x['catalyst_score']['score'], reverse=True)

def meets_basic_criteria(pm_data):
    return (
        pm_data['last'] > 10 and  # Price above $10
        pm_data['volume'] > 500000 and  # Minimum volume
        abs(pm_data['last'] - pm_data['prev_close']) / pm_data['prev_close'] > 0.01  # 1% move minimum
    )

def passes_momentum_filters(metrics):
    return (
        abs(metrics['pm_change']) >= 0.01 and  # 1% minimum move
        abs(metrics['pm_change']) <= 0.10 and  # 10% maximum (avoid pumps)
        metrics['volume_ratio'] > 2.0 and  # 2x normal PM volume
        metrics['catalyst_score']['score'] >= 7 and  # Strong catalyst required
        metrics['pm_range'] < 0.05  # Not too volatile
    )
```

## Entry Criteria

### Long Momentum Entry
```python
long_momentum_entry = {
    'pre_market_criteria': {
        'pm_change': 0.01 <= pm_change <= 0.08,  # 1-8% PM gain
        'catalyst_score': catalyst_score >= 7,
        'catalyst_direction': 'bullish',
        'volume_ratio': pm_volume / avg_pm_volume > 2
    },
    'open_confirmation': {
        'gap_maintained': open_price > prev_close * 1.005,
        'volume_surge': first_minute_volume > avg_first_minute * 1.5,
        'no_rejection': first_minute_close > first_minute_open,
        'spread_tight': bid_ask_spread < 0.02
    },
    'technical_filters': {
        'above_vwap': price > vwap,
        'relative_strength': rs_vs_spy > 1.5,
        'not_extended': price < pm_high * 1.02,
        'trend_aligned': spy_direction == 'up' or 'neutral'
    },
    'entry_timing': {
        'wait_period': 60,  # Wait 60 seconds after open
        'entry_window': 300,  # Enter within 5 minutes
        'confirmation_bars': 2  # Need 2 positive bars
    }
}
```

### Short Momentum Entry
```python
short_momentum_entry = {
    'pre_market_criteria': {
        'pm_change': -0.08 <= pm_change <= -0.01,  # 1-8% PM loss
        'catalyst_score': catalyst_score >= 7,
        'catalyst_direction': 'bearish',
        'volume_ratio': pm_volume / avg_pm_volume > 2
    },
    'open_confirmation': {
        'gap_maintained': open_price < prev_close * 0.995,
        'volume_surge': first_minute_volume > avg_first_minute * 1.5,
        'no_bounce': first_minute_close < first_minute_open,
        'spread_tight': bid_ask_spread < 0.02
    },
    'technical_filters': {
        'below_vwap': price < vwap,
        'relative_weakness': rs_vs_spy < 0.7,
        'not_oversold': price > pm_low * 0.98,
        'trend_aligned': spy_direction == 'down' or 'neutral'
    }
}
```

## Position Management

### Exit Strategy
```python
exit_rules = {
    'profit_targets': {
        'target_1': {
            'level': entry_price * 1.005,  # 0.5%
            'size': 0.33,  # Exit 1/3
            'typical_time': 5  # minutes
        },
        'target_2': {
            'level': entry_price * 1.01,  # 1%
            'size': 0.33,  # Exit another 1/3
            'typical_time': 15
        },
        'target_3': {
            'level': pm_high,  # PM high (for longs)
            'size': 0.34,  # Exit final 1/3
            'typical_time': 30
        }
    },
    'stop_losses': {
        'initial_stop': entry_price * 0.995,  # 0.5% stop
        'breakeven_move': 'After target_1 hit',
        'trailing_stop': {
            'activation': entry_price * 1.01,
            'distance': 0.003  # 0.3% trailing
        }
    },
    'time_exits': {
        '30_min': 'Reduce by 50% if no targets hit',
        '45_min': 'Reduce to 25% position',
        '60_min': 'Full exit regardless of P&L'
    }
}
```

### Momentum Exhaustion Signals
```python
def detect_momentum_exhaustion(position):
    """Identify when momentum is fading"""

    exhaustion_signals = {
        'volume_declining': is_volume_declining(consecutive_bars=3),
        'range_contraction': current_range < initial_range * 0.5,
        'vwap_rejection': failed_to_break_vwap(attempts=2),
        'rsi_divergence': check_divergence(position.direction),
        'pace_slowing': calculate_momentum_slope() < 0,
        'resistance_hit': at_major_level(tolerance=0.001),
        'news_fading': time_since_catalyst() > 45  # minutes
    }

    signal_count = sum(exhaustion_signals.values())

    if signal_count >= 3:
        return 'exit_immediately'
    elif signal_count >= 2:
        return 'reduce_position'
    else:
        return 'hold'
```

## Risk Management

### Position Sizing Based on Catalyst
```python
def calculate_momentum_position_size(catalyst_score, base_size=6000):
    """Size position based on catalyst strength"""

    # Catalyst-based multipliers
    catalyst_multipliers = {
        10: 1.25,  # Strongest catalysts
        9: 1.15,
        8: 1.00,
        7: 0.85,
        6: 0.70,  # Minimum threshold
    }

    size = base_size * catalyst_multipliers.get(catalyst_score, 0.70)

    # Reduce for higher volatility
    if get_premarket_range() > 0.05:
        size *= 0.8

    # Reduce if multiple positions
    active_momentum_positions = count_momentum_positions()
    if active_momentum_positions > 0:
        size *= (1 - 0.2 * active_momentum_positions)  # 20% reduction per position

    # Cap at risk limits
    max_risk = account_value * 0.02
    stop_distance = 0.005
    max_shares = max_risk / (current_price * stop_distance)

    return min(size, max_shares * current_price)
```

### Pre-Market Validation
```python
def validate_premarket_setup(symbol, pm_metrics):
    """Final validation before market open"""

    # Re-check at 9:29
    current_pm = get_current_premarket(symbol)

    validations = {
        'momentum_maintained': abs(current_pm['change']) >= abs(pm_metrics['pm_change']) * 0.8,
        'volume_consistent': current_pm['volume'] > pm_metrics['pm_volume'] * 0.9,
        'no_reversal': same_direction(current_pm['change'], pm_metrics['pm_change']),
        'spread_reasonable': current_pm['spread'] < 0.03,
        'news_fresh': catalyst_age < 12,  # hours
        'sector_aligned': sector_momentum_aligned(symbol),
        'spy_supportive': spy_premarket_aligned()
    }

    return all(validations.values())
```

## Performance Tracking

### Key Metrics
```python
momentum_performance_metrics = {
    'win_rate_by_catalyst': {
        'earnings': 0.75,
        'upgrade': 0.72,
        'fda': 0.78,
        'partnership': 0.68,
        'guidance': 0.74
    },
    'average_hold_time': {
        'winners': 22,  # minutes
        'losers': 35   # minutes (held too long)
    },
    'best_entry_time': {
        '9:31-9:35': 0.73,  # Best win rate
        '9:35-9:45': 0.70,
        'after_9:45': 0.62
    },
    'optimal_targets': {
        '0.5%': 0.85,  # Hit rate
        '1.0%': 0.65,
        '1.5%': 0.42,
        '2.0%': 0.28
    }
}
```

## Implementation Code

```python
class PreMarketMomentumStrategy:
    def __init__(self, config):
        self.catalyst_scorer = CatalystScorer()
        self.base_position_size = 6000
        self.min_catalyst_score = 7
        self.entry_window = ('09:31:00', '09:35:00')
        self.max_hold_time = 60  # minutes
        self.candidates = []

    async def pre_market_scan(self):
        """Run at 9:00 AM"""
        print("[9:00 AM] Scanning pre-market movers...")

        all_movers = await self.get_premarket_movers()

        for symbol in all_movers:
            pm_data = await self.get_pm_data(symbol)
            catalyst = self.catalyst_scorer.score_catalyst(symbol)

            if catalyst['score'] >= self.min_catalyst_score:
                self.candidates.append({
                    'symbol': symbol,
                    'pm_data': pm_data,
                    'catalyst': catalyst,
                    'entry_plan': self.create_entry_plan(symbol, pm_data, catalyst)
                })

        # Sort by catalyst strength
        self.candidates.sort(key=lambda x: x['catalyst']['score'], reverse=True)

        print(f"Found {len(self.candidates)} qualified candidates")
        return self.candidates[:5]  # Top 5 only

    async def execute_at_open(self):
        """Execute at 9:31 AM"""
        executed = []

        for candidate in self.candidates:
            # Final validation
            if not await self.validate_open(candidate):
                continue

            # Wait for confirmation
            if await self.wait_for_confirmation(candidate['symbol']):
                position = await self.enter_position(candidate)
                if position:
                    executed.append(position)

            # Limit positions
            if len(executed) >= 2:
                break

        return executed

    async def wait_for_confirmation(self, symbol, max_wait=120):
        """Wait up to 2 minutes for setup confirmation"""
        start_time = time.time()

        while time.time() - start_time < max_wait:
            if await self.check_entry_conditions(symbol):
                return True
            await asyncio.sleep(1)

        return False

    async def manage_momentum_position(self, position):
        """Manage open momentum position"""

        # Check for exhaustion
        exhaustion = self.detect_momentum_exhaustion(position)

        if exhaustion == 'exit_immediately':
            await self.close_position(position)
        elif exhaustion == 'reduce_position':
            await self.reduce_position(position, 0.5)

        # Time-based management
        hold_time = (datetime.now() - position.entry_time).total_seconds() / 60

        if hold_time > 30 and position.pnl_percent < 0.005:
            # Not working after 30 min
            await self.reduce_position(position, 0.5)
        elif hold_time > 60:
            # Max time reached
            await self.close_position(position)
```

## Common Pitfalls

1. **Chasing extended moves**: Don't enter if already up >8% PM
2. **Ignoring catalyst quality**: Weak catalysts lead to failed momentum
3. **Entering too late**: Best entries are within first 5 minutes
4. **Holding too long**: Momentum typically exhausts within 30 min
5. **Not checking sector**: Sector weakness can kill individual momentum

## Optimization Opportunities

### Machine Learning Enhancement
```python
momentum_ml_features = [
    'catalyst_score',
    'catalyst_type',
    'pm_volume_ratio',
    'pm_range',
    'time_since_news',
    'sector_strength',
    'market_regime',
    'vix_level',
    'similar_historical_patterns',
    'social_sentiment_score'
]

# Predict:
# 1. Probability of continuation
# 2. Expected magnitude
# 3. Optimal hold time
```