# VIX Feed Data Sources

## Yahoo Finance - VIX Data
**Source**: Yahoo Finance API via yfinance library

### Primary VIX Metrics
- **^VIX**: CBOE Volatility Index (30-day implied volatility)
- **^VIX9D**: CBOE Short-term Volatility Index (9-day implied volatility)
- **^VVIX**: CBOE VIX Volatility Index (volatility of volatility)
- **^SKEW**: CBOE SKEW Index (tail risk measure)

### VIX Term Structure Symbols
- **^VIX**: Current (30-day)
- **^VIX9D**: 9-day
- **VX1**: Front month VIX futures
- **VX2**: Second month VIX futures
- **VX3**: Third month VIX futures
- **VX4**: Fourth month VIX futures
- **VX5**: Fifth month VIX futures
- **VX6**: Sixth month VIX futures
- **VX7**: Seventh month VIX futures
- **VX8**: Eighth month VIX futures

### Data Fields Collected
For each symbol:
- **Open**: Opening price
- **High**: Daily high
- **Low**: Daily low
- **Close**: Closing price
- **Volume**: Trading volume
- **Timestamp**: Data timestamp

### Collection Schedule
- **Market Hours**: Every 5 minutes during market hours
- **After Hours**: Every 30 minutes
- **Weekends**: Hourly (for international volatility tracking)

### Data Quality Features
- **Validation**: Price range validation and spike detection
- **Completeness**: Gap filling for missing data points
- **Term Structure**: Contango/backwardation analysis
- **Historical Context**: Percentile rankings and Z-scores

### Usage Examples
```python
# VIX current level
GET /api/vix/current

# VIX term structure
GET /api/vix/term-structure

# VIX historical percentiles
GET /api/vix/percentiles?period=252

# VIX spike detection
GET /api/vix/spikes?threshold=20
```

### Notes
- All data sourced from Yahoo Finance public API
- Updates every 5 minutes during market hours
- Includes comprehensive volatility metrics beyond basic VIX
- Term structure data enables contango/backwardation analysis