# Polygon Live Feed Data Sources

## Overview
Real-time market data streaming via Polygon WebSocket connections and REST API endpoints using the official Polygon Python SDK. Provides comprehensive coverage for stocks, options, crypto, LULD alerts, and technical indicators.

## Polygon WebSocket Streams

### Stock Market Data

#### Real-Time Trades (T)
```
WebSocket: wss://socket.polygon.io/stocks
Message Type: T (Trades)
```
**Description**: Real-time stock trade executions with tick-by-tick precision.

**Data Fields**:
- **sym**: Stock symbol
- **x**: Exchange ID
- **p**: Trade price
- **s**: Trade size
- **c**: Trade conditions
- **t**: Timestamp (nanoseconds)
- **q**: Sequence number
- **i**: Trade ID
- **z**: Tape (A, B, C)

#### Real-Time Quotes (Q)
```
WebSocket: wss://socket.polygon.io/stocks
Message Type: Q (Quotes)
```
**Description**: Real-time bid/ask quotes with Level 1 market data.

**Data Fields**:
- **sym**: Stock symbol
- **bx**: Bid exchange
- **bp**: Bid price
- **bs**: Bid size
- **ax**: Ask exchange
- **ap**: Ask price
- **as**: Ask size
- **t**: Timestamp (nanoseconds)
- **c**: Quote condition
- **z**: Tape

#### Minute Aggregates (A)
```
WebSocket: wss://socket.polygon.io/stocks
Message Type: A (Aggregates)
```
**Description**: Real-time 1-minute OHLCV bars.

**Data Fields**:
- **sym**: Stock symbol
- **o**: Open price
- **h**: High price
- **l**: Low price
- **c**: Close price
- **v**: Volume
- **av**: Accumulated volume
- **t**: Start timestamp
- **n**: Number of transactions
- **vw**: Volume weighted average price

### Options Market Data

#### Options Trades (T)
```
WebSocket: wss://socket.polygon.io/options
Message Type: T (Options Trades)
```
**Description**: Real-time options trade executions.

**Data Fields**:
- **sym**: Option symbol (OCC format)
- **x**: Exchange ID
- **p**: Trade price
- **s**: Trade size (contracts)
- **c**: Trade conditions
- **t**: Timestamp (nanoseconds)
- **sip_timestamp**: SIP timestamp
- **underlying_ticker**: Underlying stock symbol

#### Options Quotes (Q)
```
WebSocket: wss://socket.polygon.io/options
Message Type: Q (Options Quotes)
```
**Description**: Real-time options bid/ask quotes.

**Data Fields**:
- **sym**: Option symbol
- **bx**: Bid exchange
- **bp**: Bid price
- **bs**: Bid size
- **ax**: Ask exchange
- **ap**: Ask price
- **as**: Ask size
- **t**: Timestamp (nanoseconds)
- **underlying_ticker**: Underlying stock

### Cryptocurrency Data

#### Crypto Trades (XT)
```
WebSocket: wss://socket.polygon.io/crypto
Message Type: XT (Crypto Trades)
```
**Description**: Real-time cryptocurrency trade executions.

**Data Fields**:
- **pair**: Currency pair (e.g., BTC-USD)
- **p**: Trade price
- **s**: Trade size
- **c**: Trade conditions
- **t**: Timestamp (nanoseconds)
- **x**: Exchange ID
- **r**: Received timestamp

#### Crypto Quotes (XQ)
```
WebSocket: wss://socket.polygon.io/crypto
Message Type: XQ (Crypto Quotes)
```
**Description**: Real-time crypto bid/ask quotes.

**Data Fields**:
- **pair**: Currency pair
- **bp**: Bid price
- **bs**: Bid size
- **ap**: Ask price
- **as**: Ask size
- **t**: Timestamp (nanoseconds)
- **x**: Exchange ID
- **lp**: Last trade price

#### Crypto Aggregates (XA)
```
WebSocket: wss://socket.polygon.io/crypto
Message Type: XA (Crypto Aggregates)
```
**Description**: Real-time crypto minute bars.

**Data Fields**:
- **pair**: Currency pair
- **o**: Open price
- **h**: High price
- **l**: Low price
- **c**: Close price
- **v**: Volume
- **t**: Start timestamp
- **n**: Number of transactions
- **vw**: Volume weighted average price

### LULD (Limit Up Limit Down) Data

#### LULD Bands
```
WebSocket: wss://socket.polygon.io/stocks
Message Type: LULD (Limit Up Limit Down)
```
**Description**: Real-time LULD price band updates.

**Data Fields**:
- **sym**: Stock symbol
- **lu**: Limit up price
- **ld**: Limit down price
- **i**: Limit up indicator
- **t**: Timestamp (nanoseconds)
- **p**: Reference price
- **n**: National best bid and offer

## Polygon REST API Endpoints

### Snapshots API

#### All Tickers Snapshot
```
GET /v2/snapshot/locale/us/markets/stocks/tickers
```
**Description**: Current snapshot of all US stock tickers.

**Query Parameters**:
- **tickers**: Comma-separated list of tickers (optional)
- **include_otc**: Include OTC stocks (default: true)

**Response Fields**:
- **ticker**: Stock symbol
- **day**: Day's OHLCV data
- **min**: Latest minute bar
- **prevDay**: Previous day's data
- **updated**: Last update timestamp

#### Options Chain Snapshot
```
GET /v3/snapshot/options/{underlying_ticker}
```
**Description**: Current snapshot of all options for underlying.

**Response Fields**:
- **underlying_ticker**: Stock symbol
- **underlying_price**: Current stock price
- **options**: Array of option contracts
  - **contract_type**: call/put
  - **strike_price**: Strike price
  - **expiration_date**: Expiration date
  - **implied_volatility**: Current IV
  - **delta, gamma, theta, vega**: Greeks
  - **last_quote**: Latest bid/ask

#### Crypto Snapshot
```
GET /v2/snapshot/locale/global/markets/crypto/tickers
```
**Description**: Current snapshot of all crypto pairs.

**Response Fields**:
- **ticker**: Currency pair
- **value**: Current price
- **day**: Day's data
- **min**: Latest minute data
- **updated**: Last update timestamp

### Technical Indicators API

#### Simple Moving Average (SMA)
```
GET /v1/indicators/sma/{ticker}
```
**Query Parameters**:
- **timestamp**: Date (YYYY-MM-DD)
- **timespan**: Timespan (minute, hour, day)
- **window**: Window size (e.g., 20)
- **series_type**: Price type (close, open, high, low)
- **expand_underlying**: Include underlying data
- **order**: Sort order (asc, desc)
- **limit**: Number of results

#### Exponential Moving Average (EMA)
```
GET /v1/indicators/ema/{ticker}
```
**Parameters**: Same as SMA

#### Relative Strength Index (RSI)
```
GET /v1/indicators/rsi/{ticker}
```
**Additional Parameters**:
- **window**: RSI period (default: 14)

#### MACD
```
GET /v1/indicators/macd/{ticker}
```
**Additional Parameters**:
- **short_window**: Fast period (default: 12)
- **long_window**: Slow period (default: 26)
- **signal_window**: Signal period (default: 9)

### Market Status API

#### Market Status
```
GET /v1/marketstatus/now
```
**Description**: Current market status for all exchanges.

**Response Fields**:
- **market**: Market name
- **serverTime**: Server timestamp
- **exchanges**: Array of exchange status
  - **acronym**: Exchange code
  - **name**: Exchange name
  - **operating_mic**: Market identifier
  - **participant_mic**: Participant identifier
  - **type**: Exchange type
  - **market**: Market name
  - **status**: Current status (open, closed, early_close)

#### Market Holidays
```
GET /v1/marketstatus/upcoming
```
**Description**: Upcoming market holidays and early closes.

## Python SDK Integration

### WebSocket Connection
```python
from polygon import WebSocketClient
from polygon.websocket.models import WebSocketMessage
import asyncio

class PolygonLiveStreamClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.ws_client = WebSocketClient(
            api_key=api_key,
            feed='delayed',  # or 'real-time' for paid plans
            market='stocks'  # stocks, options, crypto
        )

    async def start_stock_stream(self, symbols: list):
        """Start real-time stock data stream"""

        def handle_msg(msg: WebSocketMessage):
            # Process incoming messages
            if msg.event_type == 'T':  # Trade
                self.process_trade(msg)
            elif msg.event_type == 'Q':  # Quote
                self.process_quote(msg)
            elif msg.event_type == 'A':  # Aggregate
                self.process_aggregate(msg)

        # Subscribe to streams
        self.ws_client.subscribe_stock_trades(handle_msg, symbols)
        self.ws_client.subscribe_stock_quotes(handle_msg, symbols)
        self.ws_client.subscribe_stock_aggregates(handle_msg, symbols)

        # Start connection
        self.ws_client.run()
```

### REST API Usage
```python
from polygon import RESTClient
import asyncio

class PolygonRESTClient:
    def __init__(self, api_key: str):
        self.client = RESTClient(api_key)

    async def get_snapshot_all_tickers(self):
        """Get snapshot of all tickers"""
        return self.client.get_snapshot_all_tickers()

    async def get_technical_indicator(self, symbol: str, indicator: str):
        """Get technical indicator data"""
        if indicator == 'sma':
            return self.client.get_sma(symbol, window=20, timespan='day')
        elif indicator == 'rsi':
            return self.client.get_rsi(symbol, window=14, timespan='day')
        elif indicator == 'macd':
            return self.client.get_macd(symbol, timespan='day')
```

## Collection Schedules

### Market Hours (9:30 AM - 4:00 PM ET)
- **Stock Trades/Quotes**: Real-time (WebSocket)
- **Options Data**: Real-time (WebSocket)
- **Crypto Data**: Real-time (WebSocket, 24/7)
- **Snapshots**: Every 30 seconds (REST)
- **Technical Indicators**: Every minute (REST)

### Extended Hours (4:00 AM - 9:30 AM, 4:00 PM - 8:00 PM ET)
- **Stock Data**: Real-time (WebSocket)
- **Snapshots**: Every 2 minutes (REST)
- **Technical Indicators**: Every 5 minutes (REST)

### Off Hours
- **Crypto Data**: Real-time (WebSocket, 24/7)
- **Market Status**: Every 15 minutes (REST)
- **End of day snapshots**: Once per day

## Data Quality Features

### Real-Time Validation
- **Timestamp consistency**: Verify message ordering
- **Price validation**: Check for obvious errors
- **Volume validation**: Detect anomalies
- **Sequence numbering**: Ensure no missed messages

### Historical Context
- **Previous day comparison**: Flag unusual moves
- **Volume ratio analysis**: Identify high volume
- **Technical level awareness**: Support/resistance zones

### Error Handling
- **Automatic reconnection**: Handle WebSocket disconnects
- **Rate limit management**: Respect API limits
- **Data buffering**: Handle temporary outages
- **Fallback mechanisms**: Switch to REST when needed

## API Authentication
- **API Key**: POLYGON_API_KEY environment variable
- **Tier Validation**: Automatically detect API plan limitations
- **Rate Limiting**: Built-in request throttling
- **Usage Monitoring**: Track API call consumption

## Storage Integration
- **QuestDB**: Primary time-series storage
- **Real-time Tables**: Separate tables per data type
- **Batch Processing**: Efficient bulk inserts
- **Data Retention**: Configurable retention policies

## Performance Optimizations
- **Connection Pooling**: Reuse WebSocket connections
- **Message Batching**: Batch database inserts
- **Async Processing**: Non-blocking data handling
- **Memory Management**: Efficient data structures
- **Compression**: Enable WebSocket compression

## Notes
- Requires Polygon.io subscription for real-time data
- Free tier provides delayed data (15+ minutes)
- WebSocket connections automatically handle reconnection
- All timestamps are in nanoseconds (Unix timestamp)
- Technical indicators require paid subscription
- LULD data available for major symbols only