# Unusual Whales MCP Server

A Model Context Protocol (MCP) server that provides access to Unusual Whales financial data including options flow, institutional activity, dark pool trades, and market alerts.

## Features

- **Options Flow Alerts**: Real-time unusual options activity with comprehensive filtering
- **Stock Alerts**: Unusual stock volume and price movements
- **Dark Pool Activity**: Dark pool trading data and analysis
- **Institutional Holdings**: Institutional ownership changes and activity
- **Earnings Calendar**: Upcoming earnings announcements and estimates
- **Options Chains**: Complete options chain data with Greeks
- **ETF Activity**: ETF unusual activity and flow analysis
- **Insider Trades**: Corporate insider trading activity
- **Congressional Trades**: Political trading disclosures
- **Market Overview**: Overall market sentiment and unusual activity summary

## Setup

1. Ensure you have an Unusual Whales API token
2. Add your token to the `.env` file in the project root:
   ```
   UNUSUAL_WHALES_API_TOKEN=your_token_here
   ```

## Available Tools

### get_flow_alerts
Get options flow alerts with extensive filtering capabilities including:
- Contract type (calls/puts)
- Trade side (ask/bid)
- Floor vs electronic execution
- Size, premium, and volume thresholds
- Date range filtering
- Ticker symbol filtering

### get_stock_alerts
Retrieve stock alerts for unusual volume and price activity.

### get_dark_pool_trades
Access dark pool trading data with size and timing information.

### get_institutional_activity
Get institutional holdings changes and quarterly filings.

### get_earnings_calendar
Upcoming earnings announcements with estimates and timing.

### get_options_chains
Complete options chain data for any ticker with Greeks and pricing.

### get_etf_activity
ETF unusual activity and flow analysis.

### get_insider_trades
Corporate insider trading activity and disclosures.

### get_congress_trades
Congressional trading disclosures and activity.

### get_market_overview
Overall market summary with key unusual activity highlights.

## Configuration

The server is configured via `fastmcp.json` and requires:
- Python 3.10+
- FastMCP 2.10.0+
- httpx for HTTP requests
- polars for data processing
- python-dotenv for environment variables

## Usage

The server runs as a FastMCP server and can be used with any MCP-compatible client. All endpoints return structured JSON data with comprehensive error handling and rate limiting support.