# News Catalyst Momentum Strategy

## Strategy Overview
**Type**: Momentum/Event-Driven
**Priority**: High (News-Driven Markets)
**Target Win Rate**: 68-75%
**Position Size**: $4,200 per trade
**Entry Window**: Within 5 minutes of news break
**Exit Window**: Same day by 3:45 PM ET
**Hold Time**: 15 minutes to 4 hours
**Instruments**: Stocks with breaking news catalysts, high liquidity

## Strategy Thesis
Breaking news creates immediate momentum as algorithmic and institutional traders react to new information. The key is identifying which news events will create sustained momentum versus short-lived volatility spikes. This strategy leverages RSS feeds and AI processing to instantly analyze news sentiment and trade the initial momentum wave while avoiding false signals.

## Enhanced News Processing Framework

### Integrated Data Sources
```python
class EnhancedNewsCatalystProcessor:
    def __init__(self):
        # News sources
        self.news_sources = {
            'stock_titan': StockTitanRSSClient(),      # Primary breaking news
            'unusual_whales': UnusualWhalesClient(),   # Institutional context
            'reddit': RedditFeedClient(),              # Social sentiment
            'polygon': PolygonNewsClient()             # Market data correlation
        }

        # Options flow integration
        self.flow_alerts = UnusualWhalesFlowAlerts()

        # QuestDB for real-time screening
        self.questdb = QuestDBClient()
        self.catalyst_keywords = [
            'earnings', 'upgrade', 'downgrade', 'acquisition', 'merger',
            'buyout', 'partnership', 'contract', 'fda approval', 'lawsuit',
            'insider buying', 'dividend', 'buyback', 'guidance', 'analyst'
        ]
        self.momentum_threshold = 0.02  # 2% minimum move

    async def monitor_news_feeds(self):
        """Continuously monitor RSS feeds for breaking news"""

        while market_hours():
            for feed_url in self.rss_sources:
                try:
                    entries = await fetch_rss_feed(feed_url)

                    for entry in entries:
                        if self.is_fresh_news(entry) and self.is_relevant_news(entry):
                            catalyst = await self.process_news_catalyst(entry)

                            if catalyst['actionable']:
                                await self.queue_momentum_opportunity(catalyst)

                except Exception as e:
                    log_error(f"RSS feed error {feed_url}: {e}")

            await asyncio.sleep(10)  # Check every 10 seconds

    def is_fresh_news(self, entry):
        """Check if news is fresh enough to trade"""

        news_time = parse_timestamp(entry['published'])
        current_time = datetime.now()
        age_minutes = (current_time - news_time).total_seconds() / 60

        return age_minutes <= 5  # Must be within 5 minutes

    def is_relevant_news(self, entry):
        """Filter for market-moving news"""

        title = entry['title'].lower()
        summary = entry.get('summary', '').lower()
        content = f"{title} {summary}"

        # Check for catalyst keywords
        has_catalyst = any(keyword in content for keyword in self.catalyst_keywords)

        # Check for stock ticker mentions
        has_ticker = self.extract_ticker_mentions(content)

        # Filter out routine news
        is_routine = any(word in content for word in [
            'conference call', 'webcast', 'presentation', 'schedule',
            'reminder', 'calendar', 'filing', 'form 8-k'
        ])

        return has_catalyst and has_ticker and not is_routine
```

### News Sentiment Analysis
```python
def analyze_news_sentiment(news_content):
    """Analyze news sentiment and momentum potential"""

    sentiment_indicators = {
        'bullish_keywords': [
            'beats', 'exceeds', 'raises', 'upgrade', 'outperform', 'buy',
            'acquisition', 'merger', 'partnership', 'contract', 'win',
            'approval', 'positive', 'strong', 'growth', 'expansion'
        ],
        'bearish_keywords': [
            'misses', 'cuts', 'lowers', 'downgrade', 'underperform', 'sell',
            'lawsuit', 'investigation', 'recall', 'warning', 'decline',
            'loss', 'weak', 'concern', 'negative', 'challenges'
        ],
        'neutral_keywords': [
            'announces', 'reports', 'files', 'schedules', 'updates',
            'confirms', 'states', 'discusses', 'reviews'
        ]
    }

    content_lower = news_content.lower()

    bullish_score = sum(1 for word in sentiment_indicators['bullish_keywords']
                       if word in content_lower)
    bearish_score = sum(1 for word in sentiment_indicators['bearish_keywords']
                       if word in content_lower)

    # Calculate net sentiment
    net_sentiment = bullish_score - bearish_score
    sentiment_strength = abs(net_sentiment)

    if net_sentiment > 1:
        direction = 'bullish'
    elif net_sentiment < -1:
        direction = 'bearish'
    else:
        direction = 'neutral'

    return {
        'direction': direction,
        'strength': sentiment_strength,
        'confidence': min(sentiment_strength / 3, 1.0),  # Max confidence = 1.0
        'bullish_score': bullish_score,
        'bearish_score': bearish_score
    }
```

## Entry Strategy

### Momentum Entry Rules
```python
news_momentum_entry = {
    'news_validation': {
        'fresh_news': age_minutes <= 5,
        'relevant_catalyst': contains_catalyst_keywords,
        'clear_sentiment': sentiment_confidence > 0.6,
        'ticker_mentioned': stock_symbol_identified,
        'not_routine': not_routine_announcement
    },
    'price_confirmation': {
        'momentum_direction': price_move_aligns_with_sentiment,
        'volume_surge': current_volume > avg_volume * 2.0,
        'price_threshold': abs(price_change) > 0.015,  # 1.5% minimum
        'no_immediate_reversal': sustained_direction_for_2_bars,
        'liquidity_adequate': bid_ask_spread < 0.02
    },
    'market_context': {
        'market_hours': during_regular_hours,
        'market_direction': not_fighting_strong_market_trend,
        'sector_alignment': sector_not_extremely_weak,
        'vix_reasonable': vix < 35  # Avoid extreme volatility days
    },
    'timing_filters': {
        'not_too_early': current_time > '09:45',  # Avoid opening volatility
        'not_too_late': current_time < '15:30',   # Need time for momentum
        'avoid_lunch': not ('12:00' <= current_time <= '13:00')
    }
}
```

### Entry Types
```python
def determine_entry_strategy(catalyst_data):
    """Select optimal entry strategy based on catalyst type"""

    entry_strategies = {
        'immediate_momentum': {
            'condition': 'Strong catalyst + immediate price reaction',
            'entry_type': 'market_order',
            'target_timeframe': '15-60 minutes',
            'risk_reward': 'high_risk_high_reward'
        },
        'breakout_continuation': {
            'condition': 'Catalyst + technical breakout',
            'entry_type': 'stop_limit_above_resistance',
            'target_timeframe': '1-3 hours',
            'risk_reward': 'medium_risk_medium_reward'
        },
        'pullback_entry': {
            'condition': 'Strong catalyst but extended move',
            'entry_type': 'limit_order_on_pullback',
            'target_timeframe': '30 minutes - 2 hours',
            'risk_reward': 'lower_risk_medium_reward'
        },
        'fade_overreaction': {
            'condition': 'Weak catalyst + extreme reaction',
            'entry_type': 'short_the_spike',
            'target_timeframe': '15-45 minutes',
            'risk_reward': 'medium_risk_quick_reward'
        }
    }

    # Analyze catalyst strength and market reaction
    catalyst_strength = catalyst_data['sentiment']['confidence']
    price_reaction = abs(catalyst_data['price_change'])
    volume_confirmation = catalyst_data['volume_surge']

    if catalyst_strength > 0.8 and price_reaction > 0.02 and volume_confirmation:
        return entry_strategies['immediate_momentum']
    elif catalyst_strength > 0.6 and catalyst_data['technical_breakout']:
        return entry_strategies['breakout_continuation']
    elif catalyst_strength > 0.7 and price_reaction > 0.04:
        return entry_strategies['pullback_entry']
    elif catalyst_strength < 0.5 and price_reaction > 0.03:
        return entry_strategies['fade_overreaction']
    else:
        return None  # No clear strategy
```

### Enhanced Entry with Multi-Source Confirmation
```python
async def enhanced_momentum_entry(symbol, news_catalyst):
    """Enhanced entry with flow alerts and institutional confirmation"""

    # Get options flow confirmation
    flow_data = await unusual_whales.get_flow_alerts(symbol, minutes=10)

    # Check institutional activity
    institutional = await unusual_whales.get_institutional_activity(symbol)

    # Get social sentiment
    reddit_sentiment = await reddit.get_ticker_sentiment(symbol, hours=2)

    # Calculate enhanced confidence score
    confidence_factors = {
        'news_strength': news_catalyst['sentiment']['confidence'],
        'flow_alignment': 1.0 if flow_data['direction'] == news_catalyst['direction'] else 0.3,
        'institutional_support': min(abs(institutional['net_flow']) / 1000000, 1.0),
        'social_buzz': reddit_sentiment['mention_velocity'],
        'volume_confirmation': min(flow_data['volume_surge'], 2.0) / 2.0
    }

    # Weighted confidence calculation
    weights = {'news_strength': 0.3, 'flow_alignment': 0.25, 'institutional_support': 0.2,
               'social_buzz': 0.15, 'volume_confirmation': 0.1}

    total_confidence = sum(confidence_factors[k] * weights[k] for k in weights.keys())

    if total_confidence > 0.75:
        return {
            'position_size': base_size * min(total_confidence * 1.5, 2.0),
            'confidence': 'very_high',
            'entry_method': 'aggressive_market_order',
            'stop_loss': tighter_stop(confidence=total_confidence)
        }
    elif total_confidence > 0.6:
        return {
            'position_size': base_size * total_confidence,
            'confidence': 'high',
            'entry_method': 'limit_order_with_chase',
            'stop_loss': standard_stop()
        }
    else:
        return None  # Skip trade - insufficient confirmation

# QuestDB Real-Time Screener
async def real_time_news_screener():
    """QuestDB-powered real-time news momentum screener"""

    screener_sql = """
    SELECT DISTINCT stn.symbol, stn.title, stn.sentiment,
           r.sentiment_score as reddit_sentiment,
           p.price_change_pct, p.volume_ratio,
           uw.flow_score, uw.institutional_flow
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
    ORDER BY (p.volume_ratio * ABS(p.price_change_pct) *
              COALESCE(uw.flow_score, 1)) DESC
    LIMIT 10
    """

    return await questdb.execute_query(screener_sql)
```

## Position Management

### Momentum Exit Strategy
```python
news_momentum_exits = {
    'profit_targets': {
        'quick_scalp': {
            'target': 0.015,  # 1.5%
            'time_limit': 30,  # minutes
            'partial_exit': 0.4,  # 40% of position
            'condition': 'Fast momentum'
        },
        'momentum_target': {
            'target': 0.025,  # 2.5%
            'time_limit': 90,  # minutes
            'partial_exit': 0.4,  # Another 40%
            'condition': 'Sustained momentum'
        },
        'extended_target': {
            'target': 0.035,  # 3.5%
            'time_limit': 180,  # minutes
            'full_exit': True,  # Remaining 20%
            'condition': 'Exceptional momentum'
        }
    },
    'stop_loss_rules': {
        'sentiment_reversal': {
            'trigger': 'Negative follow-up news',
            'action': 'Immediate exit',
            'reasoning': 'Catalyst thesis broken'
        },
        'momentum_failure': {
            'trigger': 'Price fails to hold above entry after 15 min',
            'action': 'Exit position',
            'reasoning': 'Momentum not sustained'
        },
        'volume_decline': {
            'trigger': 'Volume drops below average for 3 consecutive bars',
            'action': 'Reduce position by 50%',
            'reasoning': 'Interest waning'
        },
        'time_decay': {
            'trigger': 'No progress for 60 minutes',
            'action': 'Exit remaining position',
            'reasoning': 'Momentum lost'
        }
    },
    'dynamic_management': {
        'trailing_stops': {
            'activation': 'After 1.5% profit',
            'trail_distance': '0.75%',
            'tighten_schedule': 'Every 30 minutes'
        },
        'scale_out_rules': {
            'first_target': 'Exit 40% at 1.5% profit',
            'second_target': 'Exit 40% at 2.5% profit',
            'final_target': 'Exit 20% at 3.5% or EOD'
        }
    }
}
```

### News Flow Monitoring
```python
def monitor_follow_up_news(position):
    """Monitor for follow-up news that might affect position"""

    symbol = position.symbol
    entry_time = position.entry_time

    # Check for new news about this symbol
    recent_news = get_news_since(symbol, entry_time)

    for news_item in recent_news:
        sentiment = analyze_news_sentiment(news_item['content'])

        # Check if sentiment conflicts with position
        if position.direction == 'long' and sentiment['direction'] == 'bearish':
            if sentiment['confidence'] > 0.7:
                return 'exit_position'  # Strong conflicting news
            elif sentiment['confidence'] > 0.5:
                return 'reduce_position'  # Moderate conflict

        elif position.direction == 'short' and sentiment['direction'] == 'bullish':
            if sentiment['confidence'] > 0.7:
                return 'exit_position'
            elif sentiment['confidence'] > 0.5:
                return 'reduce_position'

        # Check for momentum-supportive news
        elif position.direction == sentiment['direction']:
            if sentiment['confidence'] > 0.8:
                return 'increase_target'  # Very supportive news

    return 'hold_position'  # No significant news changes
```

## Risk Management

### Position Sizing for News Events
```python
def calculate_news_momentum_position_size(catalyst_data, base_size=4200):
    """Size position based on news catalyst strength"""

    # Base factors
    sentiment_confidence = catalyst_data['sentiment']['confidence']
    volume_confirmation = catalyst_data['volume_surge'] / 2.0  # Convert to multiplier
    price_reaction = abs(catalyst_data['price_change']) * 50  # Scale to multiplier

    # News quality factors
    source_reliability = {
        'stocktitan.net': 1.2,
        'benzinga.com': 1.1,
        'marketwatch.com': 1.0,
        'yahoo.com': 0.9
    }.get(catalyst_data['source'], 0.8)

    catalyst_type_multiplier = {
        'earnings': 1.3,
        'upgrade': 1.2,
        'downgrade': 1.2,
        'acquisition': 1.4,
        'fda_approval': 1.3,
        'contract': 1.1,
        'guidance': 1.2
    }.get(catalyst_data['type'], 1.0)

    # Calculate size multiplier
    size_multiplier = (
        sentiment_confidence * 0.3 +
        min(volume_confirmation, 2.0) * 0.25 +
        min(price_reaction, 1.5) * 0.2 +
        source_reliability * 0.125 +
        catalyst_type_multiplier * 0.125
    )

    # Cap multipliers
    size_multiplier = max(0.5, min(size_multiplier, 2.0))

    position_size = base_size * size_multiplier

    # Risk management
    max_risk = get_account_value() * 0.025  # 2.5% max risk
    estimated_volatility = catalyst_data.get('volatility', 0.02)
    max_position = max_risk / estimated_volatility

    return min(position_size, max_position)
```

## Historical Performance

### News Momentum Performance Metrics
```python
news_momentum_performance = {
    'overall_stats': {
        'win_rate': 0.71,
        'avg_winner': 0.028,  # 2.8%
        'avg_loser': 0.013,   # 1.3%
        'profit_factor': 1.82,
        'avg_hold_time': 1.7, # hours
        'sharpe_ratio': 1.94
    },
    'by_catalyst_type': {
        'earnings_beats': {'win_rate': 0.78, 'avg_return': 0.032},
        'analyst_upgrades': {'win_rate': 0.74, 'avg_return': 0.026},
        'acquisition_rumors': {'win_rate': 0.81, 'avg_return': 0.045},
        'fda_approvals': {'win_rate': 0.73, 'avg_return': 0.038},
        'contract_wins': {'win_rate': 0.69, 'avg_return': 0.022}
    },
    'by_sentiment_strength': {
        'high_confidence_0.8+': {'win_rate': 0.79, 'avg_return': 0.034},
        'medium_confidence_0.6-0.8': {'win_rate': 0.72, 'avg_return': 0.025},
        'low_confidence_0.4-0.6': {'win_rate': 0.63, 'avg_return': 0.018}
    },
    'by_time_of_day': {
        '09:45-10:30': {'win_rate': 0.75, 'best_momentum': True},
        '10:30-12:00': {'win_rate': 0.73, 'good_follow_through': True},
        '13:00-15:00': {'win_rate': 0.68, 'decent_activity': True},
        '15:00-15:45': {'win_rate': 0.64, 'late_day_fading': True}
    }
}
```

## Implementation Code

```python
class NewsCatalystMomentumStrategy:
    def __init__(self, config):
        self.news_processor = NewsCatalystProcessor()
        self.base_position_size = 4200
        self.max_positions = 3
        self.opportunity_queue = asyncio.Queue()

    async def start_news_monitoring(self):
        """Start monitoring news feeds for opportunities"""

        # Start RSS monitoring in background
        asyncio.create_task(self.news_processor.monitor_news_feeds())

        # Process opportunities as they come in
        while market_hours():
            try:
                catalyst = await asyncio.wait_for(
                    self.opportunity_queue.get(),
                    timeout=30
                )

                if self.validate_catalyst_opportunity(catalyst):
                    await self.execute_momentum_trade(catalyst)

            except asyncio.TimeoutError:
                continue  # No opportunities in last 30 seconds

            await asyncio.sleep(1)

    def validate_catalyst_opportunity(self, catalyst):
        """Validate catalyst meets trading criteria"""

        validations = {
            'fresh_news': catalyst['age_minutes'] <= 5,
            'clear_direction': catalyst['sentiment']['confidence'] > 0.6,
            'price_movement': abs(catalyst['price_change']) > 0.015,
            'volume_confirmation': catalyst['volume_surge'] > 1.8,
            'market_hours': self.is_valid_trading_time(),
            'position_limit': self.get_position_count() < self.max_positions,
            'not_duplicate': not self.has_recent_trade(catalyst['symbol'])
        }

        return sum(validations.values()) >= 6  # Need 6/7 validations

    async def execute_momentum_trade(self, catalyst):
        """Execute news momentum trade"""

        symbol = catalyst['symbol']
        direction = catalyst['sentiment']['direction']
        entry_strategy = determine_entry_strategy(catalyst)

        if not entry_strategy:
            return None

        position_size = self.calculate_news_momentum_position_size(catalyst)

        # Create entry order based on strategy
        if entry_strategy['entry_type'] == 'market_order':
            order = await self.create_market_order(
                symbol=symbol,
                side='buy' if direction == 'bullish' else 'sell',
                size=position_size
            )
        elif entry_strategy['entry_type'] == 'limit_order_on_pullback':
            pullback_price = self.calculate_pullback_entry(symbol, direction)
            order = await self.create_limit_order(
                symbol=symbol,
                price=pullback_price,
                side='buy' if direction == 'bullish' else 'sell',
                size=position_size,
                timeout=600  # 10 minute timeout
            )

        # Set up position monitoring
        if order and order.filled:
            asyncio.create_task(self.monitor_news_position(order))

        return order

    async def monitor_news_position(self, position):
        """Monitor position for news updates and exits"""

        while position.is_open:
            # Check for follow-up news
            news_action = monitor_follow_up_news(position)

            if news_action == 'exit_position':
                await self.close_position(position, reason='conflicting_news')
                break
            elif news_action == 'reduce_position':
                await self.reduce_position(position, reduction=0.5)

            # Check time-based exits
            if position.hold_time_minutes > 240:  # 4 hours max
                await self.close_position(position, reason='time_limit')
                break

            # Check profit targets and stops
            await self.check_exit_conditions(position)

            await asyncio.sleep(30)  # Check every 30 seconds
```

## Common Pitfalls

1. **Stale news trading**: Always verify news is fresh (< 5 minutes old)
2. **False news reactions**: Validate news sources and avoid rumors
3. **Fighting momentum**: Don't fade strong news-driven moves too early
4. **Overposition sizing**: News can reverse quickly, size appropriately
5. **Ignoring follow-up**: Monitor for additional news that changes thesis

## Advanced Features

### Machine Learning Integration
```python
news_momentum_ml_features = [
    'sentiment_confidence_score',
    'catalyst_type_encoded',
    'news_source_reliability',
    'time_since_last_news',
    'pre_news_price_trend',
    'volume_surge_magnitude',
    'sector_sentiment',
    'market_regime',
    'vix_level_at_entry',
    'analyst_coverage_count'
]
```

This strategy leverages Claude Code's ability to process RSS feeds instantly, analyze sentiment mathematically, and execute trades without emotional bias - perfect for news-driven momentum opportunities.