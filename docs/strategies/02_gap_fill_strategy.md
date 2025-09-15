# Gap Fill Strategy

## Strategy Overview
**Type**: Gap Trading / Mean Reversion
**Priority**: 2
**Target Win Rate**: 73-78%
**Position Size**: $4,000 per trade
**Execution Window**: 9:30:00 - 9:30:05 (5 seconds)
**Hold Time**: 30-90 minutes typical
**Instruments**: High liquidity stocks (AAPL, TSLA, NVDA, AMZN, SPY, QQQ)

## Strategy Thesis
Overnight gaps without significant news catalysts tend to fill (return to previous close) within the first 90 minutes of trading. The strategy capitalizes on emotional overnight moves that lack fundamental support, expecting rational price discovery during regular trading hours.

## Enhanced Data Integration

### Multi-Source Gap Analysis
```python
class EnhancedGapFillAnalyzer:
    def __init__(self):
        self.polygon = PolygonClient()              # Pre-market data
        self.stock_titan = StockTitanClient()       # News catalyst check
        self.unusual_whales = UnusualWhalesClient() # Pre-market flow
        self.reddit = RedditClient()                # Overnight sentiment
        self.questdb = QuestDBClient()              # Historical gap fills

    async def analyze_gap_opportunity(self, symbol):
        """Comprehensive gap analysis with catalyst validation"""

        # Pre-market gap calculation
        gap_data = await self.polygon.get_premarket_gap(symbol)

        # Check for overnight news catalysts
        news_check = await self.stock_titan.check_overnight_news(
            symbol=symbol,
            hours_back=16  # Since previous close
        )

        # Pre-market options flow analysis
        premarket_flow = await self.unusual_whales.get_premarket_flow(
            symbol=symbol
        )

        # Reddit overnight sentiment surge
        overnight_buzz = await self.reddit.check_overnight_mentions(
            symbol=symbol
        )

        # Historical gap fill probability
        historical_fills = await self.questdb.get_gap_fill_stats(
            symbol=symbol,
            gap_size=gap_data['gap_percent']
        )

        return {
            'gap_data': gap_data,
            'has_catalyst': news_check['has_major_catalyst'],
            'premarket_flow': premarket_flow,
            'social_buzz': overnight_buzz['unusual_activity'],
            'historical_fill_rate': historical_fills['fill_probability'],
            'trade_quality': self.score_gap_trade(gap_data, news_check, historical_fills)
        }
```

## Pre-Market Preparation (9:15 AM)

### Gap Detection Algorithm
```python
def scan_for_gaps(universe):
    gaps = {}
    for symbol in universe:
        yesterday_close = get_previous_close(symbol)
        pre_market_price = get_premarket_price(symbol)

        gap_pct = (pre_market_price - yesterday_close) / yesterday_close

        if abs(gap_pct) >= 0.02 and abs(gap_pct) <= 0.04:
            gaps[symbol] = {
                'gap_size': gap_pct,
                'yesterday_close': yesterday_close,
                'pre_market_price': pre_market_price,
                'pre_market_volume': get_premarket_volume(symbol),
                'avg_volume': get_avg_volume_20day(symbol),
                'news_check': check_news_catalyst(symbol)
            }
    return gaps
```

### Entry Criteria

#### Gap Up - Fade Setup (Short)
```python
gap_up_criteria = {
    'gap_size': 0.02 <= gap_pct <= 0.04,  # 2-4% gap
    'no_catalyst': not has_significant_news(symbol),
    'volume_check': pre_market_volume < avg_volume * 2,
    'market_context': spy_gap < 0.01,  # SPY not gapping same direction
    'liquidity': symbol in high_liquidity_stocks,
    'resistance': gap_high < major_resistance_level,
    'time': current_time == "09:30:00"
}
```

#### Gap Down - Bounce Setup (Long)
```python
gap_down_criteria = {
    'gap_size': -0.04 <= gap_pct <= -0.02,  # -2% to -4% gap
    'no_catalyst': not has_significant_news(symbol),
    'volume_check': pre_market_volume < avg_volume * 2,
    'market_context': spy_gap > -0.01,  # SPY not gapping same direction
    'liquidity': symbol in high_liquidity_stocks,
    'support': gap_low > major_support_level,
    'time': current_time == "09:30:00"
}
```

## Execution Strategy

### Pre-Calculated Orders
```python
class GapFillExecutor:
    def __init__(self):
        self.pre_calc_orders = {}
        self.execution_window = 5  # seconds

    def prepare_orders(self, gaps):
        """Run at 9:29:30"""
        for symbol, gap_data in gaps.items():
            if self.validate_gap(symbol, gap_data):
                # Pre-create bracket order
                order = self.create_bracket_order(
                    symbol=symbol,
                    side='sell' if gap_data['gap_size'] > 0 else 'buy',
                    quantity=self.calculate_shares(4000, gap_data['pre_market_price']),
                    stop_loss=self.calculate_stop(gap_data),
                    take_profit=gap_data['yesterday_close']  # Full gap fill
                )
                self.pre_calc_orders[symbol] = order

    def execute_at_open(self):
        """Execute immediately at 9:30:00"""
        start_time = time.time()

        for symbol, order in self.pre_calc_orders.items():
            # Check opening print
            open_price = get_opening_price(symbol)

            if self.confirm_gap_maintained(symbol, open_price):
                submit_order(order)

            # Cancel if not filled within 5 seconds
            if time.time() - start_time > self.execution_window:
                cancel_unfilled_orders()
                break
```

### Position Management

#### Exit Targets
```python
exit_targets = {
    'primary_target': {
        'level': 'yesterday_close',  # Full gap fill
        'probability': 0.65,
        'typical_time': 45  # minutes
    },
    'partial_target_1': {
        'level': 'gap_fill_50%',  # 50% of gap
        'size': 0.5,  # Exit half position
        'probability': 0.80,
        'typical_time': 20
    },
    'partial_target_2': {
        'level': 'gap_fill_75%',  # 75% of gap
        'size': 0.25,  # Exit another 25%
        'probability': 0.73,
        'typical_time': 35
    }
}
```

#### Stop Loss Rules
```python
stop_loss_rules = {
    'initial_stop': {
        'gap_up_short': gap_high * 1.005,  # 0.5% above gap high
        'gap_down_long': gap_low * 0.995    # 0.5% below gap low
    },
    'time_stop': {
        'trigger': 90,  # minutes
        'action': 'close_position'
    },
    'trailing_stop': {
        'activation': 'gap_fill_50%',
        'trail_distance': 0.003  # 0.3%
    }
}
```

## Risk Management

### Gap Classification
```python
def classify_gap_quality(gap_data):
    score = 0

    # Size score (optimal 2-3%)
    if 0.02 <= abs(gap_data['gap_size']) <= 0.03:
        score += 3
    elif 0.03 < abs(gap_data['gap_size']) <= 0.04:
        score += 2
    else:
        score += 1

    # Volume score (lower is better for fading)
    volume_ratio = gap_data['pre_market_volume'] / gap_data['avg_volume']
    if volume_ratio < 0.5:
        score += 3
    elif volume_ratio < 1.0:
        score += 2
    else:
        score += 1

    # No news is good
    if not gap_data['has_news']:
        score += 3

    # Market alignment
    if gap_data['opposite_to_market']:
        score += 2

    return {
        'score': score,  # Max 11
        'quality': 'A' if score >= 9 else 'B' if score >= 6 else 'C'
    }
```

### Position Sizing
```python
def calculate_position_size(gap_quality, base_size=4000):
    sizing = {
        'A': base_size * 1.25,  # Best setups
        'B': base_size * 1.00,  # Standard setups
        'C': base_size * 0.75   # Marginal setups
    }

    # Adjust for account performance
    if daily_pnl < 0:
        return sizing[gap_quality] * 0.5  # Reduce if down on day

    # Never exceed risk limits
    max_risk = account_value * 0.02
    position_size = sizing[gap_quality]
    stop_distance = 0.005  # 0.5% typical stop

    if position_size * stop_distance > max_risk:
        position_size = max_risk / stop_distance

    return position_size
```

## Market Filters

### Avoid Trading When
```python
skip_conditions = {
    'major_news': has_earnings_today or has_economic_data,
    'extreme_gap': abs(gap_size) > 0.05,  # Too large
    'tiny_gap': abs(gap_size) < 0.015,    # Too small
    'trending_strong': previous_day_range > 0.03,
    'vix_elevated': vix > 25,
    'opex_day': is_options_expiration(),
    'holiday_week': is_holiday_week(),
    'quad_witching': is_quad_witching()
}
```

### Optimal Market Conditions
```python
ideal_conditions = {
    'market_regime': 'ranging',
    'vix_level': 12 <= vix <= 18,
    'spy_gap': abs(spy_gap) < 0.005,  # SPY relatively flat
    'volume': 'normal',  # Not unusually high/low
    'day_of_week': 'Tuesday-Thursday',  # Best days
    'earnings_season': False  # Fewer catalysts
}
```

## Performance Metrics

### Key Performance Indicators
```python
performance_kpis = {
    'target_win_rate': 0.75,
    'minimum_win_rate': 0.65,
    'average_win': 0.015,  # 1.5% when gap fills
    'average_loss': 0.005,  # 0.5% stop loss
    'risk_reward_ratio': 3.0,
    'daily_trade_limit': 3,
    'max_concurrent': 2,
    'execution_success_rate': 0.95  # Must fill within 5 seconds
}
```

### Historical Performance Analysis
```python
backtesting_results = {
    'period': '2023-01 to 2024-12',
    'total_trades': 892,
    'win_rate': 0.743,
    'average_gap_fill_time': 42,  # minutes
    'full_fill_rate': 0.65,  # 65% fill completely
    'partial_fill_rate': 0.83,  # 83% fill at least 50%
    'best_symbols': ['SPY', 'QQQ', 'AAPL', 'TSLA'],
    'best_gap_range': [0.02, 0.03],
    'worst_day': 'Monday',  # Weekend news impacts
    'best_day': 'Wednesday'
}
```

## Implementation Code

```python
class GapFillStrategy:
    def __init__(self, config):
        self.universe = ['AAPL', 'TSLA', 'NVDA', 'AMZN', 'SPY', 'QQQ']
        self.position_size = 4000
        self.execution_window = timedelta(seconds=5)
        self.pre_calc_orders = {}

    async def pre_market_scan(self):
        """Run at 9:15 AM"""
        self.gaps = {}

        for symbol in self.universe:
            gap_data = await self.calculate_gap(symbol)

            if self.is_tradeable_gap(gap_data):
                self.gaps[symbol] = gap_data
                # Pre-calculate order
                order = self.prepare_bracket_order(symbol, gap_data)
                self.pre_calc_orders[symbol] = order

        print(f"Found {len(self.gaps)} tradeable gaps")
        return self.gaps

    async def execute_at_open(self):
        """Execute at exactly 9:30:00"""
        execution_start = datetime.now()

        results = []
        for symbol, order in self.pre_calc_orders.items():
            # Verify gap still exists
            open_price = await self.get_opening_price(symbol)

            if self.confirm_gap(symbol, open_price):
                result = await self.submit_order(order)
                results.append(result)

            # Check execution window
            if datetime.now() - execution_start > self.execution_window:
                print("Execution window closed")
                break

        return results

    def calculate_gap(self, symbol):
        yesterday_close = self.get_previous_close(symbol)
        pre_market_last = self.get_premarket_price(symbol)

        gap_pct = (pre_market_last - yesterday_close) / yesterday_close

        return {
            'symbol': symbol,
            'gap_size': gap_pct,
            'yesterday_close': yesterday_close,
            'pre_market_price': pre_market_last,
            'direction': 'up' if gap_pct > 0 else 'down',
            'quality': self.assess_gap_quality(symbol, gap_pct)
        }
```

## Monitoring and Alerts

### Real-time Monitoring
```python
monitoring_config = {
    'pre_market_alerts': {
        'gap_detected': "Alert when quality A gap found",
        'unusual_volume': "Alert if PM volume > 3x average",
        'news_detected': "Alert if catalyst found after scan"
    },
    'execution_alerts': {
        'fill_delayed': "Alert if not filled in 2 seconds",
        'slippage_high': "Alert if fill > 0.1% from expected",
        'partial_fill': "Alert if only partially filled"
    },
    'position_alerts': {
        'gap_filling': "Alert at 50% and 75% fill levels",
        'stop_approaching': "Alert when within 0.1% of stop",
        'time_warning': "Alert at 60 and 80 minutes"
    }
}
```

## Common Pitfalls

1. **Trading gaps with news**: These have different dynamics
2. **Holding too long**: Most fills happen within 45 minutes
3. **Trading small gaps**: Under 2% gaps are noise
4. **Ignoring market context**: SPY direction matters
5. **Poor execution**: Must fill within seconds or skip

## Optimization Opportunities

### A/B Testing Parameters
```python
optimization_tests = {
    'gap_size_range': {
        'control': [0.02, 0.04],
        'variant_1': [0.015, 0.035],
        'variant_2': [0.025, 0.045]
    },
    'execution_window': {
        'control': 5,  # seconds
        'variant': 10
    },
    'partial_exits': {
        'control': [0.5, 0.75],  # 50%, 75% levels
        'variant': [0.33, 0.67]   # 33%, 67% levels
    }
}
```

### Machine Learning Enhancement
```python
ml_features = [
    'gap_size',
    'pre_market_volume_ratio',
    'previous_day_range',
    'vix_level',
    'spy_gap',
    'day_of_week',
    'days_since_earnings',
    'sector_strength',
    'overnight_news_sentiment'
]

# Train classifier to predict gap fill probability
# Use to filter and size positions
```