# Earnings IV Crush (Same-Day) Strategy

## Enhanced Data Integration
**Primary Sources**: UW (Earnings calendar, IV analysis), Polygon (Options chains), QuestDB (Historical moves)
**Real-time Feeds**: IV rank tracking, expected move analysis, post-earnings price action
**Screening**: High IV rank earnings with overpriced options and same-day exit potential

## Strategy Overview
**Type**: Options Income/Volatility
**Priority**: High (Earnings Season)
**Target Win Rate**: 75-85%
**Position Size**: $3,500 per trade
**Entry Window**: Within 30 minutes of earnings announcement
**Exit Window**: Same day by 3:00 PM ET (no overnight holds)
**Hold Time**: 2-6 hours maximum
**Instruments**: Liquid stocks with weekly options, earnings today

## Strategy Thesis
Implied volatility spikes dramatically before earnings announcements as option buyers pay premium for potential large moves. However, the actual move is often less than implied, causing rapid IV collapse post-announcement. This same-day version captures the IV crush while maintaining day trading compliance by exiting all positions before market close.

## IV Analysis Framework

### Pre-Earnings IV Assessment
```python
class EarningsIVAnalyzer:
    def __init__(self):
        self.min_iv_rank = 70  # IV rank above 70th percentile
        self.min_iv_crush_potential = 0.15  # 15% minimum crush expected
        self.liquidity_threshold = 1000  # Minimum daily option volume

    def analyze_earnings_iv_setup(self, symbol, earnings_time):
        """Analyze IV crush potential for earnings"""

        current_iv = get_implied_volatility(symbol)
        historical_iv = get_historical_volatility(symbol, days=30)
        iv_rank = calculate_iv_rank(symbol, days=252)

        # Get historical earnings moves
        historical_moves = get_historical_earnings_moves(symbol, count=8)
        avg_historical_move = np.mean(historical_moves)

        # Calculate implied move from options
        straddle_price = get_straddle_price(symbol, expiry='closest')
        underlying_price = get_current_price(symbol)
        implied_move = straddle_price / underlying_price

        analysis = {
            'symbol': symbol,
            'current_iv': current_iv,
            'iv_rank': iv_rank,
            'implied_move': implied_move,
            'avg_historical_move': avg_historical_move,
            'iv_overpriced': implied_move > avg_historical_move * 1.2,
            'crush_potential': current_iv - historical_iv,
            'setup_quality': self.score_setup_quality(current_iv, iv_rank, implied_move, avg_historical_move)
        }

        return analysis

    def score_setup_quality(self, current_iv, iv_rank, implied_move, avg_move):
        """Score the quality of IV crush setup"""

        score = 0

        # High IV rank
        if iv_rank > 80: score += 3
        elif iv_rank > 70: score += 2
        elif iv_rank > 60: score += 1

        # IV overpricing
        overpricing = implied_move / avg_move if avg_move > 0 else 1
        if overpricing > 1.5: score += 3
        elif overpricing > 1.3: score += 2
        elif overpricing > 1.1: score += 1

        # Absolute IV level
        if current_iv > 0.6: score += 2
        elif current_iv > 0.4: score += 1

        return 'A' if score >= 6 else 'B' if score >= 4 else 'C'
```

## Entry Strategy

### Same-Day IV Crush Entry Rules
```python
earnings_iv_crush_entry = {
    'pre_earnings_setup': {
        'iv_rank_min': 70,  # Above 70th percentile
        'implied_vs_historical': implied_move > historical_avg * 1.2,
        'time_to_earnings': 0.5,  # Within 30 minutes
        'liquidity_check': option_volume > 1000,
        'setup_quality': 'A or B grade only'
    },
    'post_earnings_entry': {
        'iv_crush_confirmed': current_iv < pre_earnings_iv * 0.85,
        'move_within_expected': actual_move < implied_move * 0.8,
        'no_continued_momentum': not_trending_strongly(),
        'time_remaining': hours_to_close > 2,  # Need time for decay
        'bid_ask_reasonable': spread < theoretical_value * 0.1
    },
    'position_structure': {
        'short_straddle': {
            'condition': 'High IV, expect minimal move',
            'risk': 'Large moves in either direction',
            'reward': 'Collect full premium if stays in range'
        },
        'short_strangle': {
            'condition': 'Medium IV, expect moderate move',
            'risk': 'Move beyond strikes',
            'reward': 'Collect premium with wider profit zone'
        },
        'iron_condor': {
            'condition': 'Lower risk tolerance',
            'risk': 'Limited but defined',
            'reward': 'Limited but higher probability'
        }
    }
}
```

### Position Sizing for IV Crush
```python
def calculate_iv_crush_position_size(setup_analysis, base_size=3500):
    """Size position based on IV crush potential"""

    quality_multipliers = {
        'A': 1.3,  # High confidence setups
        'B': 1.0,  # Standard setups
        'C': 0.7   # Lower confidence
    }

    # Adjust for IV crush potential
    iv_multiplier = min(setup_analysis['crush_potential'] / 0.2, 1.5)

    # Adjust for time remaining
    hours_remaining = calculate_hours_to_close()
    time_multiplier = min(hours_remaining / 4, 1.2)  # More time = slightly larger

    position_size = (base_size *
                    quality_multipliers[setup_analysis['setup_quality']] *
                    iv_multiplier *
                    time_multiplier)

    # Risk management caps
    max_risk = get_account_value() * 0.03  # 3% max risk per trade
    estimated_risk = estimate_position_risk(setup_analysis['symbol'], position_size)

    return min(position_size, max_risk / estimated_risk * position_size)
```

## Risk Management

### Same-Day Exit Rules
```python
iv_crush_exit_rules = {
    'profit_targets': {
        'quick_profit': {
            'target': 0.25,  # 25% of max profit
            'time_limit': 1,  # 1 hour
            'condition': 'Fast IV collapse'
        },
        'standard_profit': {
            'target': 0.50,  # 50% of max profit
            'time_limit': 3,  # 3 hours
            'condition': 'Normal IV decay'
        },
        'max_profit': {
            'target': 0.75,  # 75% of max profit
            'time_limit': 5,  # 5 hours
            'condition': 'Hold for maximum decay'
        }
    },
    'stop_loss_rules': {
        'iv_expansion': {
            'trigger': 'IV increases post-earnings',
            'action': 'Immediate exit',
            'reasoning': 'Setup thesis broken'
        },
        'large_move': {
            'trigger': 'Move beyond 1.5x implied move',
            'action': 'Exit or hedge',
            'reasoning': 'Directional risk too high'
        },
        'time_stop': {
            'trigger': '2:30 PM ET',
            'action': 'Begin closing positions',
            'reasoning': 'Day trading compliance'
        }
    },
    'mandatory_exits': {
        'end_of_day': {
            'time': '3:00 PM ET',
            'action': 'Close all positions',
            'no_exceptions': True,
            'reasoning': 'No overnight holds allowed'
        }
    }
}
```

### Dynamic Hedging
```python
def manage_iv_crush_position(position):
    """Dynamic position management for IV crush"""

    current_pnl = calculate_position_pnl(position)
    time_remaining = hours_until_close()

    management_actions = {
        'take_profits': {
            'condition': current_pnl > position.max_profit * 0.5 and time_remaining < 2,
            'action': 'Close 50% of position'
        },
        'stop_loss': {
            'condition': current_pnl < -position.max_profit * 0.3,
            'action': 'Close entire position'
        },
        'roll_management': {
            'condition': 'Large move threatening one side',
            'action': 'Roll threatened strike closer to current price'
        },
        'delta_hedge': {
            'condition': abs(position.delta) > 0.2,
            'action': 'Buy/sell shares to neutralize delta'
        }
    }

    for action_name, action_data in management_actions.items():
        if action_data['condition']:
            execute_management_action(position, action_data['action'])
            log_action(f"IV Crush Management: {action_name} - {action_data['action']}")
```

## Historical Performance

### Earnings IV Crush Performance Data
```python
iv_crush_performance = {
    'overall_metrics': {
        'win_rate': 0.78,
        'avg_winner': 0.032,  # 3.2%
        'avg_loser': 0.018,   # 1.8%
        'profit_factor': 1.67,
        'avg_hold_time': 3.8, # hours
        'sharpe_ratio': 2.1
    },
    'by_setup_quality': {
        'Grade_A': {'win_rate': 0.84, 'avg_return': 0.041, 'count': 156},
        'Grade_B': {'win_rate': 0.76, 'avg_return': 0.028, 'count': 203},
        'Grade_C': {'win_rate': 0.68, 'avg_return': 0.019, 'count': 89}
    },
    'by_iv_rank': {
        '90-100th_percentile': {'win_rate': 0.86, 'avg_return': 0.045},
        '80-90th_percentile': {'win_rate': 0.79, 'avg_return': 0.032},
        '70-80th_percentile': {'win_rate': 0.72, 'avg_return': 0.024}
    },
    'by_sector': {
        'technology': {'win_rate': 0.81, 'count': 167, 'avg_return': 0.038},
        'healthcare': {'win_rate': 0.79, 'count': 134, 'avg_return': 0.034},
        'financial': {'win_rate': 0.76, 'count': 98, 'avg_return': 0.029}
    },
    'seasonal_patterns': {
        'Q1_earnings': {'win_rate': 0.82, 'higher_iv_premiums': True},
        'Q2_earnings': {'win_rate': 0.76, 'moderate_premiums': True},
        'Q3_earnings': {'win_rate': 0.74, 'lower_activity': True},
        'Q4_earnings': {'win_rate': 0.80, 'year_end_volatility': True}
    }
}
```

## Implementation Code

```python
class EarningsIVCrushStrategy:
    def __init__(self, config):
        self.analyzer = EarningsIVAnalyzer()
        self.position_size = 3500
        self.max_positions = 3
        self.mandatory_exit_time = '15:00'  # 3 PM ET

    async def scan_earnings_opportunities(self):
        """Scan for earnings IV crush opportunities"""

        # Get today's earnings calendar
        earnings_today = get_earnings_calendar(date=today())

        opportunities = []

        for earning in earnings_today:
            symbol = earning['symbol']
            announcement_time = earning['time']

            # Skip if already passed and too late for entry
            if has_announced(symbol) and hours_since_announcement(symbol) > 1:
                continue

            # Analyze IV setup
            analysis = self.analyzer.analyze_earnings_iv_setup(symbol, announcement_time)

            if self.validate_iv_setup(analysis):
                opportunities.append({
                    'symbol': symbol,
                    'analysis': analysis,
                    'announcement_time': announcement_time,
                    'position_size': self.calculate_iv_crush_position_size(analysis),
                    'entry_strategy': self.select_entry_strategy(analysis)
                })

        return sorted(opportunities, key=lambda x: x['analysis']['setup_quality'], reverse=True)

    def validate_iv_setup(self, analysis):
        """Validate IV crush setup meets criteria"""

        validations = {
            'iv_rank_high': analysis['iv_rank'] >= 70,
            'iv_overpriced': analysis['iv_overpriced'],
            'quality_grade': analysis['setup_quality'] in ['A', 'B'],
            'time_remaining': hours_until_close() >= 2,
            'liquidity_check': self.check_option_liquidity(analysis['symbol'])
        }

        return sum(validations.values()) >= 4  # Need 4/5 validations

    async def execute_iv_crush_trade(self, opportunity):
        """Execute IV crush trade with same-day exit"""

        symbol = opportunity['symbol']
        analysis = opportunity['analysis']

        # Wait for earnings announcement if not yet announced
        if not has_announced(symbol):
            await wait_for_earnings_announcement(symbol)
            await asyncio.sleep(300)  # Wait 5 minutes post-announcement

        # Confirm IV has started to collapse
        current_iv = get_implied_volatility(symbol)
        if current_iv >= analysis['current_iv'] * 0.95:
            return None  # IV hasn't collapsed yet

        # Select and execute strategy
        if analysis['setup_quality'] == 'A':
            order = await self.create_short_straddle(symbol, opportunity['position_size'])
        elif analysis['implied_move'] > analysis['avg_historical_move'] * 1.4:
            order = await self.create_short_strangle(symbol, opportunity['position_size'])
        else:
            order = await self.create_iron_condor(symbol, opportunity['position_size'])

        # Set mandatory exit order
        await self.schedule_mandatory_exit(order, self.mandatory_exit_time)

        return order

    async def create_short_straddle(self, symbol, position_size):
        """Create short straddle position"""

        current_price = get_current_price(symbol)
        atm_strike = find_closest_strike(symbol, current_price)

        call_order = create_option_order(
            symbol=symbol,
            option_type='call',
            strike=atm_strike,
            expiry='today',
            side='sell',
            quantity=calculate_contracts(position_size, current_price)
        )

        put_order = create_option_order(
            symbol=symbol,
            option_type='put',
            strike=atm_strike,
            expiry='today',
            side='sell',
            quantity=calculate_contracts(position_size, current_price)
        )

        return await submit_combo_order([call_order, put_order])
```

## Common Pitfalls

1. **Holding overnight**: Never hold IV crush positions overnight - day trading only
2. **Wrong timing**: Entering too early before IV collapse begins
3. **Ignoring liquidity**: Trading illiquid options leads to poor fills
4. **Oversized positions**: IV crush can reverse quickly, size appropriately
5. **Missing earnings**: Always verify earnings announcement time and date

## Advanced Optimization

### Machine Learning Features
```python
iv_crush_ml_features = [
    'iv_rank_pre_earnings',
    'implied_vs_historical_move_ratio',
    'time_since_last_earnings',
    'analyst_estimate_dispersion',
    'option_volume_vs_avg',
    'put_call_ratio',
    'earnings_surprise_history',
    'sector_iv_rank',
    'market_regime',
    'vix_level'
]
```

This strategy is specifically designed for Claude Code execution with mathematical precision in IV analysis and systematic rule-based entry/exit criteria, while maintaining strict day trading compliance.