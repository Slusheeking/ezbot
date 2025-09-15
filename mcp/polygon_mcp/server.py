#!/usr/bin/env python3
"""
Custom Polygon MCP Server for EZBot Trading System
Provides financial market data through Polygon.io API
"""

import asyncio
import json
import os
from datetime import datetime, date
from typing import Dict, List, Any, Optional, Union
from dotenv import load_dotenv
from fastmcp import FastMCP
import httpx

# Load environment variables from project root
load_dotenv("/home/ezb0t/ezbot/.env")

# Initialize FastMCP server
mcp = FastMCP(
    name="polygon-financial-data",
    instructions="""
    This server provides comprehensive financial market data through Polygon.io API.
    Use these tools to get real-time and historical market data for stocks, options, crypto, and more.
    All data is sourced from Polygon.io's professional-grade financial data platform.
    """
)

class PolygonClient:
    """Polygon.io API client with rate limiting and error handling"""

    def __init__(self):
        self.api_key = os.getenv("POLYGON_API_KEY")
        if not self.api_key:
            raise ValueError("POLYGON_API_KEY not found in environment variables")

        self.base_url = "https://api.polygon.io"
        self.session = None

    async def _get_session(self):
        """Get or create HTTP session"""
        if self.session is None:
            self.session = httpx.AsyncClient(
                timeout=30.0,
                limits=httpx.Limits(max_keepalive_connections=20, max_connections=100)
            )
        return self.session

    async def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """Make authenticated API request with error handling"""
        session = await self._get_session()

        # Add API key to params
        if params is None:
            params = {}
        params["apikey"] = self.api_key

        url = f"{self.base_url}{endpoint}"

        try:
            response = await session.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            return {"error": f"HTTP error: {str(e)}"}
        except json.JSONDecodeError as e:
            return {"error": f"JSON decode error: {str(e)}"}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}

# Initialize Polygon client
polygon_client = PolygonClient()

@mcp.tool
async def get_stock_price(symbol: str) -> Dict[str, Any]:
    """
    Get the latest stock price for a symbol.

    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL', 'MSFT')

    Returns:
        Latest price data including current price, change, and volume
    """
    endpoint = f"/v2/aggs/ticker/{symbol}/prev"
    result = await polygon_client._make_request(endpoint)

    if "error" in result:
        return result

    if result.get("resultsCount", 0) > 0 and "results" in result:
        data = result["results"][0]
        return {
            "symbol": symbol,
            "price": data.get("c"),  # close price
            "change": data.get("c", 0) - data.get("o", 0),  # change from open
            "change_percent": ((data.get("c", 0) - data.get("o", 0)) / data.get("o", 1)) * 100,
            "volume": data.get("v"),
            "high": data.get("h"),
            "low": data.get("l"),
            "open": data.get("o"),
            "timestamp": data.get("t")
        }

    return {"error": f"No data found for symbol {symbol}"}

@mcp.tool
async def get_stock_aggregates(
    symbol: str,
    multiplier: int = 1,
    timespan: str = "day",
    from_date: str = None,
    to_date: str = None,
    limit: int = 100
) -> Dict[str, Any]:
    """
    Get aggregate bars for a stock over a given date range.

    Args:
        symbol: Stock ticker symbol
        multiplier: Size of the timespan multiplier (e.g., 1, 5, 15)
        timespan: Size of the time window (minute, hour, day, week, month, quarter, year)
        from_date: Start date (YYYY-MM-DD format, defaults to 30 days ago)
        to_date: End date (YYYY-MM-DD format, defaults to today)
        limit: Number of results to return (max 50000)

    Returns:
        Historical price data with OHLCV values
    """
    if from_date is None:
        from datetime import timedelta
        from_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

    if to_date is None:
        to_date = datetime.now().strftime("%Y-%m-%d")

    endpoint = f"/v2/aggs/ticker/{symbol}/range/{multiplier}/{timespan}/{from_date}/{to_date}"
    params = {
        "adjusted": "true",
        "sort": "asc",
        "limit": limit
    }

    result = await polygon_client._make_request(endpoint, params)

    if "error" in result:
        return result

    # Format the response
    if result.get("resultsCount", 0) > 0 and "results" in result:
        formatted_results = []
        for bar in result["results"]:
            formatted_results.append({
                "timestamp": bar.get("t"),
                "open": bar.get("o"),
                "high": bar.get("h"),
                "low": bar.get("l"),
                "close": bar.get("c"),
                "volume": bar.get("v"),
                "volume_weighted_average_price": bar.get("vw"),
                "number_of_transactions": bar.get("n")
            })

        return {
            "symbol": symbol,
            "query_count": result.get("queryCount"),
            "results_count": result.get("resultsCount"),
            "adjusted": result.get("adjusted"),
            "results": formatted_results,
            "status": result.get("status"),
            "request_id": result.get("request_id"),
            "next_url": result.get("next_url")
        }

    return {"error": f"No aggregate data found for {symbol}"}

@mcp.tool
async def get_market_status() -> Dict[str, Any]:
    """
    Get current market status and trading hours.

    Returns:
        Market status information including open/closed status and trading hours
    """
    endpoint = "/v1/marketstatus/now"
    result = await polygon_client._make_request(endpoint)

    if "error" in result:
        return result

    return {
        "market": result.get("market"),
        "server_time": result.get("serverTime"),
        "exchanges": result.get("exchanges", {}),
        "currencies": result.get("currencies", {})
    }

@mcp.tool
async def get_ticker_details(symbol: str) -> Dict[str, Any]:
    """
    Get detailed information about a ticker symbol.

    Args:
        symbol: Stock ticker symbol

    Returns:
        Comprehensive ticker information including company details, market cap, etc.
    """
    endpoint = f"/v3/reference/tickers/{symbol}"
    result = await polygon_client._make_request(endpoint)

    if "error" in result:
        return result

    if "results" in result:
        ticker_info = result["results"]
        return {
            "ticker": ticker_info.get("ticker"),
            "name": ticker_info.get("name"),
            "market": ticker_info.get("market"),
            "locale": ticker_info.get("locale"),
            "primary_exchange": ticker_info.get("primary_exchange"),
            "type": ticker_info.get("type"),
            "active": ticker_info.get("active"),
            "currency_name": ticker_info.get("currency_name"),
            "cik": ticker_info.get("cik"),
            "composite_figi": ticker_info.get("composite_figi"),
            "share_class_figi": ticker_info.get("share_class_figi"),
            "market_cap": ticker_info.get("market_cap"),
            "phone_number": ticker_info.get("phone_number"),
            "address": ticker_info.get("address", {}),
            "description": ticker_info.get("description"),
            "sic_code": ticker_info.get("sic_code"),
            "sic_description": ticker_info.get("sic_description"),
            "ticker_root": ticker_info.get("ticker_root"),
            "homepage_url": ticker_info.get("homepage_url"),
            "total_employees": ticker_info.get("total_employees"),
            "list_date": ticker_info.get("list_date"),
            "branding": ticker_info.get("branding", {}),
            "share_class_shares_outstanding": ticker_info.get("share_class_shares_outstanding"),
            "weighted_shares_outstanding": ticker_info.get("weighted_shares_outstanding")
        }

    return {"error": f"No details found for ticker {symbol}"}

@mcp.tool
async def get_market_news(
    ticker: str = None,
    limit: int = 10,
    order: str = "desc"
) -> Dict[str, Any]:
    """
    Get the latest market news articles.

    Args:
        ticker: Filter news by ticker symbol (optional)
        limit: Number of articles to return (1-1000)
        order: Sort order (asc or desc)

    Returns:
        List of news articles with titles, descriptions, and URLs
    """
    endpoint = "/v2/reference/news"
    params = {
        "limit": min(limit, 1000),
        "order": order
    }

    if ticker:
        params["ticker"] = ticker

    result = await polygon_client._make_request(endpoint, params)

    if "error" in result:
        return result

    if "results" in result:
        articles = []
        for article in result["results"]:
            articles.append({
                "id": article.get("id"),
                "publisher": article.get("publisher", {}).get("name"),
                "title": article.get("title"),
                "author": article.get("author"),
                "published_utc": article.get("published_utc"),
                "article_url": article.get("article_url"),
                "tickers": article.get("tickers", []),
                "amp_url": article.get("amp_url"),
                "image_url": article.get("image_url"),
                "description": article.get("description"),
                "keywords": article.get("keywords", [])
            })

        return {
            "status": result.get("status"),
            "request_id": result.get("request_id"),
            "count": len(articles),
            "results": articles,
            "next_url": result.get("next_url")
        }

    return {"error": "No news articles found"}

@mcp.tool
async def get_options_contracts(
    underlying_ticker: str,
    contract_type: str = None,
    expiration_date: str = None,
    limit: int = 100
) -> Dict[str, Any]:
    """
    Get options contracts for an underlying ticker.

    Args:
        underlying_ticker: Underlying stock ticker (e.g., 'AAPL')
        contract_type: Filter by call or put ('call' or 'put')
        expiration_date: Filter by expiration date (YYYY-MM-DD)
        limit: Number of contracts to return

    Returns:
        List of options contracts with strike prices and expiration dates
    """
    endpoint = "/v3/reference/options/contracts"
    params = {
        "underlying_ticker": underlying_ticker,
        "limit": min(limit, 1000),
        "order": "asc"
    }

    if contract_type:
        params["contract_type"] = contract_type
    if expiration_date:
        params["expiration_date"] = expiration_date

    result = await polygon_client._make_request(endpoint, params)

    if "error" in result:
        return result

    if "results" in result:
        contracts = []
        for contract in result["results"]:
            contracts.append({
                "ticker": contract.get("ticker"),
                "underlying_ticker": contract.get("underlying_ticker"),
                "contract_type": contract.get("contract_type"),
                "expiration_date": contract.get("expiration_date"),
                "strike_price": contract.get("strike_price"),
                "shares_per_contract": contract.get("shares_per_contract"),
                "exercise_style": contract.get("exercise_style"),
                "additional_underlyings": contract.get("additional_underlyings")
            })

        return {
            "status": result.get("status"),
            "request_id": result.get("request_id"),
            "count": len(contracts),
            "results": contracts,
            "next_url": result.get("next_url")
        }

    return {"error": f"No options contracts found for {underlying_ticker}"}

@mcp.tool
async def get_crypto_price(symbol: str, base_currency: str = "USD") -> Dict[str, Any]:
    """
    Get the latest cryptocurrency price.

    Args:
        symbol: Cryptocurrency symbol (e.g., 'BTC', 'ETH')
        base_currency: Base currency for pricing (default: USD)

    Returns:
        Latest crypto price and market data
    """
    pair = f"X:{symbol}{base_currency}"
    endpoint = f"/v2/aggs/ticker/{pair}/prev"
    result = await polygon_client._make_request(endpoint)

    if "error" in result:
        return result

    if result.get("resultsCount", 0) > 0 and "results" in result:
        data = result["results"][0]
        return {
            "symbol": f"{symbol}/{base_currency}",
            "price": data.get("c"),
            "change": data.get("c", 0) - data.get("o", 0),
            "change_percent": ((data.get("c", 0) - data.get("o", 0)) / data.get("o", 1)) * 100,
            "volume": data.get("v"),
            "high": data.get("h"),
            "low": data.get("l"),
            "open": data.get("o"),
            "timestamp": data.get("t")
        }

    return {"error": f"No data found for {symbol}/{base_currency}"}

async def cleanup():
    """Cleanup resources on shutdown"""
    if polygon_client.session:
        await polygon_client.session.aclose()

if __name__ == "__main__":
    try:
        mcp.run()
    finally:
        asyncio.run(cleanup())