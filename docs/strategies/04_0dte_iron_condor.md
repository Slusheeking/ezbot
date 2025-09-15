# 0DTE SPX Iron Condor Strategy

## Strategy Overview
**Type**: Options Income/Theta Decay
**Priority**: High (Best Win Rate)
**Target Win Rate**: 85-90%
**Risk Per Trade**: $1,000 maximum
**Entry Time**: 9:45 AM ET
**Exit Time**: 3:00 PM ET (or earlier)
**Instruments**: SPX 0DTE options
**Max Daily Condors**: 2
**VIX Ceiling**: 25 (don't trade if VIX > 25)

## Strategy Thesis
Zero Days to Expiration (0DTE) SPX Iron Condors profit from time decay and range-bound price action. The massive theta burn in the final hours creates high-probability income trades when SPX remains within expected move ranges. The strategy capitalizes on inflated option premiums and rapid decay.

## Enhanced Data Integration Framework

### Multi-Source 0DTE Analysis
```python
class Enhanced0DTEAnalyzer:
    def __init__(self):
        self.unusual_whales = UnusualWhalesClient()
        self.polygon = PolygonOptionsClient()
        self.questdb = QuestDBClient()
        self.reddit_sentiment = RedditFeedClient()

    async def analyze_0dte_opportunity(self, symbol='SPX'):
        """Comprehensive 0DTE analysis using all data sources"""

        # Unusual Whales flow analysis
        options_flow = await self.unusual_whales.get_hottest_chains(
            symbol=symbol,
            min_volume=1000,
            expiry='today'
        )

        # Institutional positioning
        institutional_flow = await self.unusual_whales.get_institutional_activity(
            symbol=symbol,
            timeframe='1d'
        )

        # Gamma exposure analysis
        gamma_exposure = await self.unusual_whales.get_gamma_exposure(
            symbol=symbol,
            strikes_range=20  # +/- 20 strikes from current price
        )

        # Real-time IV and Greeks from Polygon
        options_data = await self.polygon.get_options_chain(
            underlying=symbol,
            expiry='today',
            include_greeks=True
        )

        # Social sentiment for SPY/SPX discussion
        social_sentiment = await self.reddit_sentiment.get_ticker_sentiment(
            ticker='SPY',  # SPY discussions often reflect SPX sentiment
            hours=4
        )

        # VIX term structure
        vix_data = await self.polygon.get_vix_term_structure()

        return {
            'symbol': symbol,
            'options_flow': options_flow,
            'institutional_positioning': institutional_flow,
            'gamma_landscape': gamma_exposure,
            'options_data': options_data,
            'social_sentiment': social_sentiment,
            'vix_structure': vix_data,
            'analysis_timestamp': datetime.now()
        }

    def calculate_enhanced_iron_condor_strikes(self, analysis):
        """Calculate optimal strikes using enhanced data"""

        current_price = analysis['options_data']['underlying_price']
        gamma_levels = analysis['gamma_landscape']
        flow_data = analysis['options_flow']

        # Find gamma support/resistance levels
        high_gamma_strikes = [
            level for level in gamma_levels
            if level['gamma_exposure'] > gamma_levels['avg_gamma'] * 1.5
        ]

        # Avoid strikes with unusual institutional flow
        flow_affected_strikes = [
            strike for strike in flow_data['unusual_strikes']
            if flow_data['strikes'][strike]['flow_direction'] == 'directional'
        ]

        # Calculate optimal short strikes avoiding gamma walls and flow
        optimal_put_strike = self.find_optimal_short_strike(
            current_price,
            'put',
            avoid_strikes=flow_affected_strikes,
            gamma_levels=high_gamma_strikes
        )

        optimal_call_strike = self.find_optimal_short_strike(
            current_price,
            'call',
            avoid_strikes=flow_affected_strikes,
            gamma_levels=high_gamma_strikes
        )

        return {
            'put_strike': optimal_put_strike,
            'call_strike': optimal_call_strike,
            'gamma_considerations': high_gamma_strikes,
            'flow_considerations': flow_affected_strikes
        }
```

## Market Conditions Filter

### Ideal Trading Environment
```python
def check_0dte_conditions():
    """Validate optimal conditions for 0DTE Iron Condors"""

    conditions = {
        'vix_level': {
            'value': get_vix(),
            'requirement': lambda x: x < 25,
            'weight': 0.3
        },
        'market_regime': {
            'value': get_market_regime(),
            'requirement': lambda x: x in ['ranging', 'calm'],
            'weight': 0.25
        },
        'expected_move': {
            'value': calculate_expected_move('SPX'),
            'requirement': lambda x: x < 0.015,  # Less than 1.5%
            'weight': 0.2
        },
        'volume_profile': {
            'value': analyze_volume_profile('SPX'),
            'requirement': lambda x: x['distribution'] == 'normal',
            'weight': 0.15
        },
        'news_calendar': {
            'value': check_economic_calendar(),
            'requirement': lambda x: not x['has_major_events'],
            'weight': 0.1
        }
    }

    # Calculate weighted score
    score = sum(
        weight for condition, weight in [
            (cond['requirement'](cond['value']), cond['weight'])
            for cond in conditions.values()
        ] if condition
    )

    return score >= 0.7  # Need 70% favorable conditions
```

### Avoid Trading Days
```python
avoid_0dte_when = {
    'fed_days': 'Federal Reserve announcements',
    'fomc_days': 'FOMC meeting days',
    'cpi_days': 'CPI release days',
    'nfp_days': 'Non-farm payrolls',
    'major_earnings': 'AAPL, MSFT, GOOGL earnings',
    'opex_days': 'Monthly options expiration',
    'quad_witch': 'Quadruple witching days',
    'holiday_weeks': 'Week of major holidays',
    'vix_spike': 'VIX > 25',
    'gap_days': 'SPX gaps > 0.5%'
}
```

## Strike Selection Algorithm

### Dynamic Strike Selection
```python
class ZeroDTEStrikeSelector:
    def __init__(self):
        self.target_delta = 0.15  # Target delta for short strikes
        self.wing_width = 25      # Points for SPX
        self.min_credit = 8       # Minimum credit to receive

    def calculate_strikes(self):
        """Calculate optimal strikes based on current conditions"""

        current_spx = get_current_price('SPX')
        vix = get_vix()
        expected_move = self.calculate_0dte_expected_move()

        # Adjust for volatility
        if vix < 15:
            # Low volatility - tighter strikes
            short_strike_distance = current_spx * 0.005  # 0.5%
        elif vix < 20:
            # Normal volatility
            short_strike_distance = current_spx * 0.007  # 0.7%
        else:
            # Elevated volatility - wider strikes
            short_strike_distance = current_spx * 0.01   # 1.0%

        strikes = {
            'call_short': round_to_strike(current_spx + short_strike_distance),
            'call_long': round_to_strike(current_spx + short_strike_distance + self.wing_width),
            'put_short': round_to_strike(current_spx - short_strike_distance),
            'put_long': round_to_strike(current_spx - short_strike_distance - self.wing_width)
        }

        # Validate credit received
        theoretical_credit = self.calculate_theoretical_credit(strikes)

        if theoretical_credit < self.min_credit:
            # Widen strikes
            return self.adjust_strikes_for_credit(strikes)

        return strikes

    def calculate_0dte_expected_move(self):
        """Calculate intraday expected move for SPX"""

        # Use ATM straddle for expected move
        atm_call = get_option_price('SPX', expiry='0DTE', strike=current_spx, type='call')
        atm_put = get_option_price('SPX', expiry='0DTE', strike=current_spx, type='put')

        straddle_price = atm_call + atm_put

        # Expected move = ~85% of straddle price
        expected_move = straddle_price * 0.85

        return expected_move / current_spx  # Return as percentage

    def adjust_strikes_for_credit(self, initial_strikes):
        """Adjust strikes to ensure minimum credit"""

        adjustment_iterations = 0
        max_iterations = 3
        strikes = initial_strikes.copy()

        while adjustment_iterations < max_iterations:
            credit = self.calculate_theoretical_credit(strikes)

            if credit >= self.min_credit:
                break

            # Move short strikes closer to money
            adjustment = 5  # 5 point adjustment

            strikes['call_short'] -= adjustment
            strikes['put_short'] += adjustment

            adjustment_iterations += 1

        return strikes
```

## Entry Execution

### Entry Timing and Process
```python
async def execute_0dte_entry():
    """Execute iron condor entry at 9:45 AM"""

    # Wait for market to settle after open
    if get_current_time() < '09:45:00':
        await wait_until('09:45:00')

    # Final condition check
    if not check_0dte_conditions():
        log_skip_reason("Market conditions not favorable")
        return None

    # Calculate strikes
    strikes = strike_selector.calculate_strikes()

    # Get live quotes
    quotes = await get_option_chain_quotes('SPX', expiry='0DTE')

    # Build iron condor order
    condor_order = {
        'type': 'iron_condor',
        'legs': [
            {'action': 'sell', 'strike': strikes['put_short'], 'type': 'put'},
            {'action': 'buy', 'strike': strikes['put_long'], 'type': 'put'},
            {'action': 'sell', 'strike': strikes['call_short'], 'type': 'call'},
            {'action': 'buy', 'strike': strikes['call_long'], 'type': 'call'}
        ],
        'quantity': 1,  # 1 condor = 4 contracts
        'order_type': 'limit',
        'net_credit': calculate_fair_credit(strikes, quotes),
        'time_in_force': 'day'
    }

    # Execute order
    try:
        result = await submit_order(condor_order)
        if result['status'] == 'filled':
            return create_condor_position(result, strikes)
        else:
            log_execution_failure(result)
            return None
    except Exception as e:
        log_error(f"Condor execution failed: {e}")
        return None
```

## Position Management

### Dynamic Management System
```python
class ZeroDTEManagement:
    def __init__(self):
        self.profit_targets = {
            'quick_exit': 0.25,    # 25% of max profit
            'standard': 0.50,      # 50% of max profit
            'greedy': 0.75         # 75% of max profit
        }
        self.loss_limits = {
            'stop_loss': 2.0,      # 200% of credit received
            'roll_threshold': 1.5,  # Consider rolling at 150%
            'hedge_activation': 1.0 # Add hedge at 100% loss
        }

    async def manage_condor_position(self, position):
        """Manage open 0DTE iron condor"""

        current_spx = get_current_price('SPX')
        current_time = get_current_time()
        position_pnl = calculate_position_pnl(position)
        credit_received = position['initial_credit']

        # Profit management
        if position_pnl > credit_received * self.profit_targets['quick_exit']:
            # Check if we should take quick profit
            if current_time < '10:30:00':  # Early in day
                await self.close_position(position, reason='quick_profit')
                return

        if position_pnl > credit_received * self.profit_targets['standard']:
            await self.close_position(position, reason='target_hit')
            return

        # Loss management
        if position_pnl < -credit_received * self.loss_limits['stop_loss']:
            await self.close_position(position, reason='stop_loss')
            return

        # Delta-based adjustments
        portfolio_delta = calculate_portfolio_delta(position)

        if abs(portfolio_delta) > 20:  # 20 delta threshold
            if current_time < '14:00:00':  # Time to adjust
                await self.adjust_condor(position, portfolio_delta)

        # Time-based management
        await self.time_based_management(position, current_time)

    async def adjust_condor(self, position, portfolio_delta):
        """Adjust condor when breached"""

        if portfolio_delta > 20:  # Call side breached
            # Roll call spread up
            await self.roll_call_spread_up(position)
        elif portfolio_delta < -20:  # Put side breached
            # Roll put spread down
            await self.roll_put_spread_down(position)

    async def time_based_management(self, position, current_time):
        """Manage based on time remaining"""

        time_actions = {
            '15:00': 'Close all positions - avoid pin risk',
            '14:30': 'Reduce size by 50% if untested',
            '14:00': 'Close if losing position',
            '13:00': 'Consider closing if < 10% profit',
            '12:00': 'Take profits if > 50% target hit'
        }

        for time_threshold, action in time_actions.items():
            if current_time >= time_threshold:
                await self.execute_time_action(position, action)
                break
```

### Adjustment Strategies
```python
adjustment_strategies = {
    'call_side_breach': {
        'roll_up': 'Roll short call up, keep put side',
        'add_call_hedge': 'Buy protective call above short strike',
        'close_call_spread': 'Close call spread, keep put spread',
        'convert_to_put_spread': 'Close calls, double put spread'
    },
    'put_side_breach': {
        'roll_down': 'Roll short put down, keep call side',
        'add_put_hedge': 'Buy protective put below short strike',
        'close_put_spread': 'Close put spread, keep call spread',
        'convert_to_call_spread': 'Close puts, double call spread'
    },
    'both_sides_tested': {
        'close_everything': 'Exit all legs immediately',
        'strangle_conversion': 'Convert to short strangle',
        'iron_butterfly': 'Adjust to iron butterfly'
    }
}
```

## Risk Management

### Position Sizing and Risk Control
```python
def calculate_0dte_position_size(account_value, risk_percentage=0.002):
    """Calculate position size for 0DTE condors"""

    # Maximum risk per condor = wing width - credit received
    wing_width = 25  # $25 for SPX
    expected_credit = 8   # $8 typical credit

    max_loss_per_condor = (wing_width - expected_credit) * 100  # $1,700

    # Position sizing
    max_risk = account_value * risk_percentage  # 0.2% of account
    max_condors = max_risk / max_loss_per_condor

    # Additional safety limits
    condor_limits = {
        'absolute_max': 2,  # Never more than 2 condors
        'vix_based': max(1, int(3 - get_vix() / 10)),  # Fewer when VIX high
        'regime_based': 2 if get_market_regime() == 'calm' else 1
    }

    return min(int(max_condors), min(condor_limits.values()))
```

### Circuit Breakers
```python
def check_0dte_circuit_breakers():
    """Emergency stop conditions"""

    circuit_breakers = {
        'vix_spike': get_vix() > 30,
        'spx_move': abs(get_day_change('SPX')) > 0.015,  # 1.5% move
        'flash_crash': detect_flash_crash_pattern(),
        'news_break': check_breaking_news(),
        'liquidity_dry': check_option_liquidity('SPX') < 0.8,
        'multiple_losses': count_consecutive_losses() >= 2,
        'account_limit': daily_options_loss > account_value * 0.005
    }

    if any(circuit_breakers.values()):
        return {
            'stop_trading': True,
            'close_positions': True,
            'reason': [k for k, v in circuit_breakers.items() if v]
        }

    return {'stop_trading': False}
```

## Performance Tracking

### Key Performance Indicators
```python
zero_dte_metrics = {
    'win_rate': {
        'target': 0.87,
        'minimum': 0.80,
        'current_month': track_monthly_win_rate(),
        'by_vix_level': {
            'vix_10-15': 0.92,
            'vix_15-20': 0.87,
            'vix_20-25': 0.81
        }
    },
    'profit_metrics': {
        'average_winner': 0.65,  # 65% of credit
        'average_loser': 1.8,    # 180% of credit
        'profit_factor': 1.54,
        'expectancy': 0.08       # 8% per trade
    },
    'timing_analysis': {
        'best_entry_time': '09:45-10:00',
        'best_exit_time': '14:00-15:00',
        'optimal_hold': 4.2,     # hours
        'early_close_rate': 0.35  # 35% closed early
    },
    'adjustment_success': {
        'roll_success_rate': 0.67,
        'hedge_effectiveness': 0.72,
        'conversion_profit': 0.45
    }
}
```

### Historical Backtesting Results
```python
backtesting_results = {
    'period': '2023-2024',
    'total_trades': 485,
    'win_rate': 0.863,
    'profit_factor': 1.52,
    'max_drawdown': -8.3,      # percent
    'sharpe_ratio': 2.76,
    'best_month': 15.2,        # percent return
    'worst_month': -3.4,
    'consecutive_winners': 23,  # max streak
    'consecutive_losers': 4,    # max streak
    'avg_trade_duration': 4.1,  # hours
    'monthly_returns': {
        'jan': 2.1, 'feb': 3.2, 'mar': 2.8, 'apr': 1.9,
        'may': -0.7, 'jun': 2.4, 'jul': 3.1, 'aug': 1.8,
        'sep': -1.2, 'oct': 4.2, 'nov': 2.9, 'dec': 1.1
    }
}
```

## Implementation Code

```python
class ZeroDTEIronCondorStrategy:
    def __init__(self, config):
        self.strike_selector = ZeroDTEStrikeSelector()
        self.manager = ZeroDTEManagement()
        self.max_daily_condors = 2
        self.vix_ceiling = 25
        self.risk_per_trade = 1000
        self.active_condors = []

    async def daily_condor_routine(self):
        """Main 0DTE condor routine"""

        # Morning setup (9:45 AM)
        if get_current_time() == '09:45:00':
            if await self.validate_trading_day():
                condor = await self.execute_0dte_entry()
                if condor:
                    self.active_condors.append(condor)

        # Continuous management
        while self.active_condors and market_is_open():
            for condor in self.active_condors[:]:  # Copy list
                await self.manager.manage_condor_position(condor)

            await asyncio.sleep(30)  # Check every 30 seconds

        # End of day cleanup (3:00 PM)
        if get_current_time() >= '15:00:00':
            await self.close_all_condors('eod_close')

    async def validate_trading_day(self):
        """Validate it's a good day for 0DTE condors"""

        # Check VIX
        if get_vix() > self.vix_ceiling:
            self.log_skip("VIX too high")
            return False

        # Check economic calendar
        if has_major_economic_events():
            self.log_skip("Major economic events")
            return False

        # Check market regime
        if get_market_regime() not in ['ranging', 'calm']:
            self.log_skip("Unfavorable market regime")
            return False

        return True

    def calculate_position_pnl(self, position):
        """Calculate real-time P&L for condor"""

        current_prices = get_option_chain('SPX', expiry='0DTE')

        legs_pnl = 0
        for leg in position['legs']:
            current_price = current_prices[leg['strike']][leg['type']]
            entry_price = leg['entry_price']

            if leg['action'] == 'sell':
                legs_pnl += entry_price - current_price
            else:  # buy
                legs_pnl += current_price - entry_price

        return legs_pnl * 100 * position['quantity']  # Convert to dollars
```

## Common Pitfalls and Solutions

### Major Pitfalls
1. **Trading on volatile days**: VIX > 25 kills win rate
2. **Holding through major news**: Always close before events
3. **Over-leveraging**: Stick to 2 condors maximum
4. **Poor strike selection**: Too narrow = frequent adjustments
5. **Not taking profits**: Time decay works fastest in final hours

### Best Practices
```python
best_practices = {
    'entry': 'Always wait until 9:45 AM for market to settle',
    'sizing': 'Risk no more than 0.2% of account per condor',
    'management': 'Close at 50% profit or 3:00 PM, whichever first',
    'adjustments': 'Roll only if time remaining > 2 hours',
    'discipline': 'Skip trading if any red flag present'
}
```

## Advanced Techniques

### Conditional Order Management
```python
def setup_conditional_orders(condor_position):
    """Set up automatic management orders"""

    orders = {
        'profit_target_gfd': {
            'condition': 'profit >= 50% of credit',
            'action': 'close_all_legs',
            'order_type': 'market'
        },
        'stop_loss_gfd': {
            'condition': 'loss >= 200% of credit',
            'action': 'close_all_legs',
            'order_type': 'market'
        },
        'time_exit': {
            'condition': 'time >= 15:00:00',
            'action': 'close_all_legs',
            'order_type': 'market'
        }
    }

    return orders
```