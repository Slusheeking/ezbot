# Polygon MCP Server

Custom Model Context Protocol (MCP) server for accessing Polygon.io financial market data within the EZBot trading system.

## Features

- **Real-time Stock Data**: Get current prices, volume, and market data
- **Historical Data**: Access historical price aggregates with customizable timeframes
- **Market Information**: Check market status, trading hours, and holidays
- **Company Details**: Get comprehensive ticker information and company data
- **News Integration**: Access market news filtered by ticker or general market news
- **Options Data**: Retrieve options contracts and chain data
- **Cryptocurrency**: Get crypto prices and market data
- **Rate Limited**: Built-in rate limiting and error handling

## Tools Available

### Stock Data
- `get_stock_price(symbol)` - Get latest stock price and basic market data
- `get_stock_aggregates(symbol, multiplier, timespan, from_date, to_date, limit)` - Get historical OHLCV data
- `get_ticker_details(symbol)` - Get detailed company information

### Market Information
- `get_market_status()` - Check if markets are open/closed with trading hours
- `get_market_news(ticker, limit, order)` - Get latest market news articles

### Options
- `get_options_contracts(underlying_ticker, contract_type, expiration_date, limit)` - Get options contract data

### Cryptocurrency
- `get_crypto_price(symbol, base_currency)` - Get crypto prices in various base currencies

## Setup

1. **Environment Variables**: Create a `.env` file in the project root:
   ```
   POLYGON_API_KEY=your_polygon_api_key_here
   ```

2. **Install Dependencies**:
   ```bash
   cd mcp/polygon_mcp
   uv sync
   ```

3. **Install with FastMCP**:
   ```bash
   fastmcp install claude-code server.py --env-file ../../.env
   ```

4. **Manual Installation**:
   ```bash
   claude mcp add polygon-server --env-file .env -- uv run server.py
   ```

## Usage Examples

### Get Stock Price
```
"Get the current price of AAPL"
```

### Historical Data
```
"Get 1-minute bars for SPY from yesterday"
```

### Market News
```
"Get the latest news for TSLA"
```

### Options Data
```
"Show me AAPL call options expiring this Friday"
```

## Configuration

The server uses FastMCP configuration in `fastmcp.json`:
- **Transport**: STDIO for Claude Code integration
- **Dependencies**: Automatically managed via uv
- **Environment**: Loads API key from .env file

## Rate Limiting

The server implements intelligent rate limiting to stay within Polygon.io API limits:
- HTTP connection pooling for efficiency
- Automatic retry with exponential backoff
- Error handling for API limits and network issues

## Integration with EZBot Trading System

This MCP server is designed to integrate seamlessly with the EZBot trading system:
- Provides market data for strategy backtesting
- Real-time price feeds for live trading decisions
- News sentiment analysis for market regime classification
- Options data for volatility-based strategies

## Error Handling

All API calls include comprehensive error handling:
- Network connectivity issues
- API rate limits
- Invalid symbols or parameters
- JSON parsing errors
- Authentication failures

Errors are returned in a standardized format for easy handling by Claude Code.