# Alpaca MCP Server

Custom Model Context Protocol (MCP) server for comprehensive trading capabilities through Alpaca Markets API within the EZBot trading system.

## Features

### Account Management
- **Account Information**: Get comprehensive account details including balance, buying power, and trading permissions
- **Account Configuration**: View and update account settings including margin settings and options trading levels
- **Portfolio Analytics**: Access detailed portfolio history and performance metrics

### Position Management
- **Position Tracking**: View all open positions with real-time P&L and market values
- **Individual Positions**: Get detailed information for specific symbols
- **Position Closing**: Close individual positions or all positions at once
- **Risk Management**: Built-in position sizing and risk controls

### Order Management
- **Order Tracking**: View all orders with comprehensive filtering options
- **Order Lifecycle**: Submit, modify, and cancel orders with full lifecycle management
- **Order Types**: Support for all major order types (market, limit, stop, stop-limit)
- **Advanced Orders**: Bracket orders with stop-loss and take-profit functionality

### Stock Trading
- **Market Orders**: Instant execution at current market prices
- **Limit Orders**: Price-controlled execution with specified limits
- **Stop Orders**: Risk management with stop-loss and stop-limit orders
- **Fractional Trading**: Trade fractional shares for portfolio optimization
- **Extended Hours**: Pre-market and after-hours trading capabilities

### Options Trading
- **Single-Leg Options**: Buy and sell individual call and put options
- **Multi-Leg Strategies**: Complex strategies like spreads, straddles, and strangles
- **Options Chains**: Real-time options chain data with strike and expiration filtering
- **Risk Management**: Options-specific risk controls and margin requirements

### Market Data
- **Real-time Quotes**: Live bid/ask quotes for stocks and options
- **Trade Data**: Latest execution data with volume and price information
- **Historical Data**: OHLCV bars with multiple timeframes and adjustments
- **Options Data**: Comprehensive options market data including Greeks (when available)

## Tools Available

### Account Tools
- `get_account()` - Get comprehensive account information
- `get_account_configurations()` - Get account configuration settings
- `update_account_configurations(...)` - Update account settings
- `get_portfolio_history(...)` - Get portfolio performance history

### Position Tools
- `get_all_positions()` - Get all open positions
- `get_position(symbol)` - Get position for specific symbol
- `close_position(symbol, qty, percentage)` - Close position or portion
- `close_all_positions(cancel_orders)` - Close all positions

### Order Tools
- `get_orders(status, limit, ...)` - Get orders with filtering
- `get_order_by_id(order_id)` - Get order by ID
- `get_order_by_client_id(client_order_id)` - Get order by client ID
- `cancel_order_by_id(order_id)` - Cancel specific order
- `cancel_all_orders()` - Cancel all open orders

### Stock Trading Tools
- `submit_market_order(symbol, qty, side, ...)` - Submit market order
- `submit_limit_order(symbol, qty, side, limit_price, ...)` - Submit limit order
- `submit_stop_order(symbol, qty, side, stop_price, ...)` - Submit stop order
- `submit_stop_limit_order(symbol, qty, side, stop_price, limit_price, ...)` - Submit stop-limit order

### Options Trading Tools
- `submit_option_market_order(symbol, qty, side, ...)` - Submit option market order
- `submit_option_limit_order(symbol, qty, side, limit_price, ...)` - Submit option limit order
- `submit_multileg_order(legs, qty, order_type, ...)` - Submit multi-leg strategy

### Market Data Tools
- `get_latest_quotes(symbols)` - Get real-time quotes
- `get_latest_trades(symbols)` - Get latest trade data
- `get_stock_bars(symbols, timeframe, ...)` - Get historical price bars
- `get_option_chains(underlying_symbol, ...)` - Get options chain data
- `get_option_quotes(symbols)` - Get options quotes
- `get_option_trades(symbols)` - Get options trade data

## Setup

### 1. Environment Variables
Create a `.env` file in the project root:
```
ALPACA_API_KEY=your_alpaca_api_key_here
ALPACA_SECRET_KEY=your_alpaca_secret_key_here
ALPACA_PAPER_TRADING=true  # Set to 'false' for live trading (use with extreme caution!)
```

### 2. Install Dependencies
```bash
cd mcp/alpaca_mcp
uv sync
```

### 3. Install with FastMCP
```bash
fastmcp install alpaca-server server.py --env-file ../../.env
```

### 4. Manual Installation
```bash
claude mcp add alpaca-server --env-file .env -- uv run server.py
```

## Safety Features

### Paper Trading Default
- **Paper Trading**: Defaults to paper trading environment for safety
- **Real Trading**: Requires explicit environment variable change
- **Risk Controls**: Built-in position and order size validations

### Order Management
- **Client Order IDs**: Automatic generation for order tracking
- **Time in Force**: Proper order duration controls
- **Extended Hours**: Explicit opt-in for after-hours trading

### Options Safety
- **Trading Levels**: Respects account options trading levels
- **Multi-leg Validation**: Proper validation for complex strategies
- **Margin Requirements**: Account margin requirement checks

## Usage Examples

### Get Account Information
```
"Show me my account balance and buying power"
```

### View Positions
```
"What positions do I currently hold?"
```

### Place Stock Order
```
"Buy 100 shares of AAPL at market price"
```

### Place Options Order
```
"Buy 1 AAPL call option expiring this Friday with strike $150"
```

### View Orders
```
"Show me all my open orders"
```

### Get Market Data
```
"Get the latest quote for SPY"
```

### Options Chain Analysis
```
"Show me the options chain for TSLA expiring next Friday"
```

### Multi-Leg Strategy
```
"Execute an iron condor on SPY with strikes 450/455/465/470"
```

## Risk Management

### Built-in Controls
- **Position Sizing**: Automatic validation of position sizes against account equity
- **Order Validation**: Pre-submission validation of all order parameters
- **Rate Limiting**: Built-in API rate limiting to prevent excessive requests
- **Error Handling**: Comprehensive error handling with detailed messaging

### Trading Limits
- **Day Trading**: Automatic pattern day trading rule compliance
- **Buying Power**: Real-time buying power calculations and validations
- **Options Levels**: Respect for account options trading authorization levels
- **Margin Requirements**: Automatic margin requirement calculations

## Configuration

The server uses FastMCP configuration in `fastmcp.json`:
- **Transport**: STDIO for Claude Code integration
- **Dependencies**: Automatically managed via uv
- **Environment**: Loads credentials from .env file
- **Logging**: Configurable log levels for debugging

## Integration with EZBot Trading System

This MCP server integrates seamlessly with the EZBot trading system:
- **Strategy Execution**: Execute automated trading strategies through Claude Code
- **Risk Management**: Real-time position monitoring and risk controls
- **Portfolio Analytics**: Performance tracking and portfolio optimization
- **Market Analysis**: Integration with market data for decision making
- **Options Strategies**: Complex multi-leg options strategy execution

## API Rate Limiting

The server implements intelligent rate limiting:
- **Connection Pooling**: Efficient HTTP connection management
- **Request Queuing**: Automatic request queuing to stay within limits
- **Retry Logic**: Exponential backoff for failed requests
- **Error Recovery**: Graceful handling of rate limit errors

## Error Handling

Comprehensive error handling for all scenarios:
- **Network Issues**: Connection timeouts and network failures
- **API Errors**: Alpaca API error messages and status codes
- **Authentication**: Invalid credentials and permission errors
- **Trading Errors**: Insufficient buying power, invalid symbols, etc.
- **Validation**: Pre-submission order and parameter validation

## Security Considerations

### API Credentials
- **Environment Variables**: Credentials stored in environment variables only
- **No Hardcoding**: No credentials stored in code or configuration files
- **Secure Transport**: All API communications over HTTPS

### Trading Safety
- **Paper Trading Default**: Defaults to paper trading for safety
- **Explicit Real Trading**: Requires explicit environment variable change
- **Order Validation**: Multi-layer validation before order submission
- **Position Monitoring**: Continuous position and risk monitoring

## Support

For issues, questions, or feature requests:
- Review the Alpaca API documentation: https://alpaca.markets/docs/
- Check the FastMCP documentation for setup issues
- Ensure proper environment variable configuration
- Verify account permissions and trading levels

## Disclaimer

**Trading Risk Warning**: Trading stocks and options involves substantial risk of loss. This software is provided for educational and trading purposes. Users are responsible for their own trading decisions and should thoroughly understand the risks involved. Past performance is not indicative of future results.

**Paper Trading Recommended**: Always test strategies in paper trading before using real money. This server defaults to paper trading for safety.

**No Financial Advice**: This tool does not provide financial advice. Users should consult with qualified financial advisors before making trading decisions.