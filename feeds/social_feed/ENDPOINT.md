# Social Feed Data Sources

## Reddit API - Trending Symbols
**Source**: Reddit API via PRAW (Python Reddit API Wrapper)

### Subreddits Monitored
- **r/wallstreetbets**: Primary retail trading sentiment
- **r/stocks**: General stock discussions
- **r/cryptocurrency**: Crypto sentiment and trends
- **r/pennystocks**: Small cap speculation
- **r/options**: Options trading strategies
- **r/investing**: Long-term investment discussions
- **r/SecurityAnalysis**: Fundamental analysis discussions

### Collection Strategies
- **Hot**: Currently trending posts
- **New**: Latest submissions
- **Rising**: Posts gaining momentum
- **Top**: Best performing posts by time period

### Symbol Extraction Features
- **Cashtag Detection**: `$TICKER` format (95% confidence)
- **Bracket Notation**: `[TICKER]` format (85% confidence)
- **Explicit Mentions**: "ticker: SYMBOL" (90% confidence)
- **Context Analysis**: Financial keyword proximity scoring
- **Crypto Mappings**: Bitcoin ’ BTC, Ethereum ’ ETH, etc.
- **Stopword Filtering**: Excludes common false positives

### Sentiment Analysis
- **Bullish Indicators**: moon, rocket, squeeze, calls, long, breakout
- **Bearish Indicators**: crash, dump, puts, short, dead, correction
- **Neutral**: Balanced or unclear sentiment
- **Confidence Scoring**: Multi-factor validation

### Trending Metrics
- **Mention Count**: Total symbol mentions
- **Unique Authors**: Number of different users mentioning
- **Unique Posts**: Number of different posts containing symbol
- **Momentum**: Mentions per hour across timeframes (1h, 6h, 24h)
- **Velocity**: Rate of change in momentum
- **Engagement**: Average score, upvote ratio, comments

### Trend Classifications
- **Viral**: High velocity, accelerating mentions
- **Rising**: Positive momentum trend
- **Hot**: High sustained activity
- **Active**: Moderate consistent mentions
- **Emerging**: New but growing interest
- **Falling**: Declining momentum

### Data Quality Features
- **Deduplication**: Prevent counting same post multiple times
- **Confidence Scoring**: Symbol extraction reliability
- **Context Validation**: Financial relevance checking
- **Author Diversity**: Prevent single-user manipulation
- **Minimum Thresholds**: Quality filters for trending status

### API Endpoints
```python
# Current trending symbols
GET /api/social/trending?limit=20

# Symbol-specific sentiment
GET /api/social/sentiment/{symbol}

# Trending by subreddit
GET /api/social/trending?subreddit=wallstreetbets

# Historical trend data
GET /api/social/history/{symbol}?period=7d
```

### Data Fields
- **Symbol**: Ticker symbol
- **Mention Count**: Total mentions in period
- **Unique Authors**: Number of unique users
- **Sentiment Distribution**: Bullish/bearish/neutral counts
- **Momentum**: Mentions per hour metrics
- **Velocity**: Rate of change
- **Confidence Score**: Overall data quality score
- **Related Symbols**: Co-mentioned tickers
- **Top Subreddit**: Primary discussion location

### Collection Schedule
- **Peak Hours**: Every 5 minutes (9 AM - 4 PM ET)
- **Normal Hours**: Every 15 minutes
- **Overnight**: Every 30 minutes
- **Weekends**: Hourly monitoring

### Notes
- Requires Reddit API credentials (CLIENT_ID, CLIENT_SECRET, USERNAME, PASSWORD)
- Intelligent filtering prevents common false positives
- Real-time sentiment and momentum tracking
- Comprehensive symbol universe validation available