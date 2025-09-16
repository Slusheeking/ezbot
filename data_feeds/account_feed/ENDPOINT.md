# Account Feed Data Sources

## Alpaca Markets API - Account Monitoring
**Source**: Alpaca Markets Trading API with MCP Integration

### Account Data Endpoints

#### Get Account Information
```
GET /v2/account
```
**Description**: Retrieve comprehensive account information including balance, buying power, and account status.

**Response Fields**:
- **account_id**: Unique account identifier
- **account_number**: Account number
- **status**: Account status (ACTIVE, SUSPENDED, etc.)
- **currency**: Account base currency (USD)
- **cash**: Available cash balance
- **portfolio_value**: Total portfolio value
- **equity**: Account equity value
- **buying_power**: Total buying power available
- **regt_buying_power**: Regulation T buying power
- **daytrading_buying_power**: Day trading buying power
- **non_marginable_buying_power**: Non-marginable buying power
- **multiplier**: Account leverage multiplier
- **sma**: Special memorandum account value
- **daytrade_count**: Number of day trades in rolling 5-day period
- **pattern_day_trader**: Pattern day trader designation
- **trading_blocked**: Whether trading is blocked
- **account_blocked**: Whether account is blocked
- **transfers_blocked**: Whether transfers are blocked

### Position Data Endpoints

#### Get All Positions
```
GET /v2/positions
```
**Description**: Retrieve all current open positions with P&L information.

**Response Fields**:
- **symbol**: Stock/asset symbol
- **asset_id**: Unique asset identifier
- **asset_class**: Asset class (us_equity, crypto, etc.)
- **qty**: Position quantity (positive for long, negative for short)
- **side**: Position side (long/short)
- **avg_entry_price**: Average entry price
- **current_price**: Current market price
- **market_value**: Current market value of position
- **cost_basis**: Total cost basis
- **unrealized_pl**: Unrealized profit/loss
- **unrealized_plpc**: Unrealized P&L percentage
- **unrealized_intraday_pl**: Intraday unrealized P&L
- **unrealized_intraday_plpc**: Intraday unrealized P&L percentage
- **change_today**: Today's price change
- **exchange**: Trading exchange
- **qty_available**: Quantity available for trading

### Order Data Endpoints

#### Get Orders
```
GET /v2/orders
```
**Description**: Retrieve order history and status information.

**Query Parameters**:
- **status**: Order status filter (open, closed, filled, canceled, all)
- **limit**: Maximum number of orders to return
- **after**: Filter orders after timestamp
- **until**: Filter orders until timestamp
- **direction**: Sort direction (asc, desc)

**Response Fields**:
- **id**: Unique order identifier
- **client_order_id**: Custom client order ID
- **symbol**: Asset symbol
- **asset_id**: Unique asset identifier
- **asset_class**: Asset class
- **qty**: Order quantity
- **filled_qty**: Quantity filled
- **side**: Order side (buy/sell)
- **order_type**: Order type (market, limit, stop, etc.)
- **time_in_force**: Time in force (day, gtc, ioc, fok)
- **limit_price**: Limit price (if applicable)
- **stop_price**: Stop price (if applicable)
- **status**: Current order status
- **submitted_at**: Order submission timestamp
- **filled_at**: Order fill timestamp
- **canceled_at**: Order cancellation timestamp
- **updated_at**: Last update timestamp
- **legs**: Multi-leg order information (for spreads)

### Collection Features

#### Real-Time Monitoring
- **Account Updates**: Real-time account balance and buying power tracking
- **Position Updates**: Live P&L monitoring and position changes
- **Order Updates**: Order status changes and fill notifications
- **Market-Aware Intervals**: Collection frequency adjusts based on market hours

#### Alert System
- **Low Buying Power**: Alert when buying power falls below threshold
- **Day Trade Limits**: Warning when approaching PDT limits
- **Position Losses**: Alert on significant position losses
- **Position Gains**: Notification of significant gains
- **Order Fills**: Real-time order execution notifications

#### Data Validation
- **Account Status**: Monitor for account restrictions
- **Balance Reconciliation**: Verify cash and equity calculations
- **Position Consistency**: Cross-check position data
- **Order Validation**: Ensure order data integrity

### Collection Schedule
- **Market Hours**: Every 30 seconds (positions), 1 minute (account)
- **Extended Hours**: Every 2 minutes (positions), 5 minutes (account)
- **Off Hours**: Every 10 minutes (positions), 30 minutes (account)

### Paper Trading Support
- **Environment**: Automatic detection of paper vs live trading
- **Separate Endpoints**: Uses paper-api.alpaca.markets for paper trading
- **Full Feature Parity**: All monitoring features available in paper mode

### Database Schema

#### Account Table
```sql
CREATE TABLE account (
    timestamp TIMESTAMP,
    account_id STRING,
    cash DOUBLE,
    portfolio_value DOUBLE,
    buying_power DOUBLE,
    equity DOUBLE,
    daytrade_count INT,
    pattern_day_trader BOOLEAN,
    trading_blocked BOOLEAN
) TIMESTAMP(timestamp) PARTITION BY DAY;
```

#### Positions Table
```sql
CREATE TABLE positions (
    timestamp TIMESTAMP,
    symbol SYMBOL,
    qty DOUBLE,
    market_value DOUBLE,
    unrealized_pl DOUBLE,
    unrealized_plpc DOUBLE,
    current_price DOUBLE
) TIMESTAMP(timestamp) PARTITION BY DAY;
```

#### Orders Table
```sql
CREATE TABLE orders (
    timestamp TIMESTAMP,
    order_id STRING,
    symbol SYMBOL,
    side STRING,
    qty DOUBLE,
    filled_qty DOUBLE,
    status STRING,
    order_type STRING,
    submitted_at TIMESTAMP,
    filled_at TIMESTAMP
) TIMESTAMP(timestamp) PARTITION BY DAY;
```

### API Authentication
- **API Key**: ALPACA_API_KEY environment variable
- **Secret Key**: ALPACA_SECRET_KEY environment variable
- **Paper Trading**: ALPACA_PAPER_TRADING environment variable (true/false)

### Usage Examples
```python
# Get current account status
GET /api/account/status

# Get portfolio summary
GET /api/account/portfolio

# Get recent order activity
GET /api/account/orders?status=filled&limit=50

# Get position P&L summary
GET /api/account/positions/summary
```

### Error Handling
- **Rate Limiting**: Automatic backoff and retry
- **Connection Issues**: Fallback and reconnection logic
- **Data Validation**: Input sanitization and validation
- **Alert Integration**: Error notifications and monitoring

### Notes
- Requires valid Alpaca Markets account and API credentials
- Paper trading environment recommended for testing
- Real-time data subject to market hours and data availability
- MCP integration provides enhanced functionality and error handling