#!/usr/bin/env python3
"""
Custom Unusual Whales MCP Server for EZBot Trading System
Provides options flow, stock alerts, and institutional data through Unusual Whales API
"""

import asyncio
import json
import os
import inspect
import logging
import sys
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional, Union
from dotenv import load_dotenv
from fastmcp import FastMCP
import httpx

# Setup logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables from project root
logger.info("Loading environment variables from /home/ezb0t/ezbot/.env")
load_dotenv("/home/ezb0t/ezbot/.env")
logger.info("Environment variables loaded")

# Initialize FastMCP server
mcp = FastMCP(
    name="unusual-whales-data",
    instructions="""
    This server provides comprehensive options flow, stock alerts, and institutional data through Unusual Whales API.
    Use these tools to get real-time and historical options flow, unusual activity alerts, institutional holdings,
    earnings data, and dark pool activity. All data is sourced from Unusual Whales' professional trading platform.
    """
)

class UnusualWhalesClient:
    """Unusual Whales API client with rate limiting and error handling"""

    def __init__(self):
        logger.info("Initializing UnusualWhalesClient")
        self.api_token = os.getenv("UNUSUAL_WHALES_API_KEY")
        logger.info(f"API token found: {'Yes' if self.api_token else 'No'}")
        if not self.api_token:
            logger.error("UNUSUAL_WHALES_API_KEY not found in environment variables")
            raise ValueError("UNUSUAL_WHALES_API_KEY not found in environment variables")

        logger.info(f"API token loaded: {self.api_token[:10]}...")
        self.base_url = "https://api.unusualwhales.com/api"
        self.headers = {
            'Accept': 'application/json, text/plain',
            'Authorization': self.api_token
        }
        self.session = None
        logger.info("UnusualWhalesClient initialized successfully")

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
        url = f"{self.base_url}{endpoint}"

        try:
            response = await session.get(url, params=params, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                return {"error": "Invalid or missing API key"}
            elif e.response.status_code == 404:
                return {"error": f"Resource not found: {e.response.text}"}
            elif e.response.status_code == 429:
                return {"error": "Rate limit exceeded"}
            else:
                return {"error": f"HTTP error: {e.response.status_code} - {e.response.text}"}
        except httpx.RequestError as e:
            return {"error": f"Network error: {str(e)}"}
        except httpx.TimeoutException:
            return {"error": "Request timed out"}
        except json.JSONDecodeError as e:
            return {"error": f"JSON decode error: {str(e)}"}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}

# Initialize Unusual Whales client
logger.info("Creating UnusualWhalesClient instance")
try:
    uw_client = UnusualWhalesClient()
    logger.info("UnusualWhalesClient instance created successfully")
except Exception as e:
    logger.error(f"Failed to create UnusualWhalesClient: {e}")
    raise

@mcp.tool
async def get_flow_alerts(
    all_opening: bool = False,
    is_ask_side: bool = False,
    is_bid_side: bool = False,
    is_call: bool = False,
    is_floor: bool = False,
    is_otm: bool = False,
    is_put: bool = False,
    is_sweep: bool = False,
    issue_types: str = None,
    limit: int = 200,
    max_diff: float = 0.0,
    max_dte: int = 0,
    max_open_interest: int = 0,
    max_premium: int = 0,
    max_size: int = 0,
    max_volume: int = 0,
    max_volume_oi_ratio: float = 0.0,
    min_diff: float = 0.0,
    min_dte: int = 0,
    min_open_interest: int = 0,
    min_premium: int = 0,
    min_size: int = 0,
    min_volume: int = 0,
    min_volume_oi_ratio: float = 0.0,
    newer_than: str = None,
    older_than: str = None,
    rule_name: str = None,
    ticker_symbol: str = None
) -> Dict[str, Any]:
    """
    Get options flow alerts from Unusual Whales API.

    Args:
        all_opening: If True, only include trades where every transaction was an opening trade
        is_ask_side: If true, only include trades on the ask side
        is_bid_side: If true, only include trades on the bid side
        is_call: If true, only include call trades
        is_floor: If true, only include floor-executed trades
        is_otm: If true, only include out-of-the-money trades
        is_put: If true, only include put trades
        is_sweep: If true, only include intermarket sweep trades
        issue_types: Comma-separated values: 'Common Stock', 'ETF', 'Index', 'ADR'
        limit: Maximum number of results to return (max 200)
        max_diff: Maximum difference (as decimal) between strike and underlying
        max_dte: Maximum days to expiration
        max_open_interest: Maximum open interest for the option
        max_premium: Maximum premium for the option
        max_size: Maximum number of contracts in the trade
        max_volume: Maximum volume for the option
        max_volume_oi_ratio: Maximum volume to open interest ratio
        min_diff: Minimum difference (as decimal) between strike and underlying
        min_dte: Minimum days to expiration
        min_open_interest: Minimum open interest for the option
        min_premium: Minimum premium for the option
        min_size: Minimum number of contracts in the trade
        min_volume: Minimum volume for the option
        min_volume_oi_ratio: Minimum volume to open interest ratio
        newer_than: ISO 8601 formatted date string for filtering results
        older_than: ISO 8601 formatted date string for filtering results
        rule_name: Comma-separated rule names
        ticker_symbol: Ticker symbol, use 'AAPL,INTC' for multiple, '-AAPL,INTC' to exclude

    Returns:
        Flow alerts data with trade details and analysis
    """
    endpoint = "/option-trades/flow-alerts"

    # Build parameters, excluding defaults and None values
    params = {}
    for name, value in locals().items():
        if name not in ('endpoint', 'params') and value is not None:
            if isinstance(value, bool) and value:
                params[name] = value
            elif not isinstance(value, bool) and value != 0 and value != 0.0:
                params[name] = value

    result = await uw_client._make_request(endpoint, params)
    return result

@mcp.tool
async def get_stock_alerts(
    ticker_symbol: str = None,
    limit: int = 100,
    newer_than: str = None,
    older_than: str = None,
    alert_type: str = None
) -> Dict[str, Any]:
    """
    Get stock alerts and unusual activity.

    Args:
        ticker_symbol: Specific ticker to filter by
        limit: Maximum number of results (max 500)
        newer_than: ISO 8601 date string for filtering newer alerts
        older_than: ISO 8601 date string for filtering older alerts
        alert_type: Type of alert to filter by

    Returns:
        Stock alerts with unusual volume and price activity
    """
    endpoint = "/alerts"
    params = {k: v for k, v in locals().items()
             if k not in ('endpoint', 'params') and v is not None}

    result = await uw_client._make_request(endpoint, params)
    return result

@mcp.tool
async def get_dark_pool_trades(
    ticker_symbol: str = None,
    limit: int = 100,
    newer_than: str = None,
    older_than: str = None,
    min_size: int = 0,
    min_premium: int = 0
) -> Dict[str, Any]:
    """
    Get dark pool trading activity.

    Args:
        ticker_symbol: Specific ticker to filter by
        limit: Maximum number of results
        newer_than: ISO 8601 date string for filtering
        older_than: ISO 8601 date string for filtering
        min_size: Minimum trade size
        min_premium: Minimum premium value

    Returns:
        Dark pool trading data with size and timing information
    """
    endpoint = "/darkpool/trades"
    params = {k: v for k, v in locals().items()
             if k not in ('endpoint', 'params') and v is not None and v != 0}

    result = await uw_client._make_request(endpoint, params)
    return result

@mcp.tool
async def get_institutional_activity(
    ticker_symbol: str = None,
    limit: int = 100,
    quarter: str = None,
    min_value: int = 0,
    activity_type: str = None
) -> Dict[str, Any]:
    """
    Get institutional holdings and activity.

    Args:
        ticker_symbol: Specific ticker to analyze
        limit: Maximum number of results
        quarter: Quarter to analyze (e.g., "2024Q1")
        min_value: Minimum holding value
        activity_type: Type of activity ('buy', 'sell', 'hold')

    Returns:
        Institutional holdings and recent changes
    """
    endpoint = "/institutional/activity"
    params = {k: v for k, v in locals().items()
             if k not in ('endpoint', 'params') and v is not None and v != 0}

    result = await uw_client._make_request(endpoint, params)
    return result

@mcp.tool
async def get_earnings_calendar(
    ticker_symbol: str = None,
    from_date: str = None,
    to_date: str = None,
    limit: int = 100
) -> Dict[str, Any]:
    """
    Get upcoming earnings announcements.

    Args:
        ticker_symbol: Specific ticker to filter by
        from_date: Start date (YYYY-MM-DD format)
        to_date: End date (YYYY-MM-DD format)
        limit: Maximum number of results

    Returns:
        Earnings calendar with dates and estimates
    """
    if from_date is None:
        from_date = datetime.now().strftime("%Y-%m-%d")
    if to_date is None:
        to_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")

    endpoint = "/market/events"
    params = {k: v for k, v in locals().items()
             if k not in ('endpoint', 'params') and v is not None}

    result = await uw_client._make_request(endpoint, params)
    return result

@mcp.tool
async def get_options_chains(
    ticker_symbol: str,
    expiration_date: str = None,
    strike_price: float = None,
    option_type: str = None
) -> Dict[str, Any]:
    """
    Get options chain data for a ticker.

    Args:
        ticker_symbol: Stock ticker symbol (required)
        expiration_date: Specific expiration date (YYYY-MM-DD)
        strike_price: Specific strike price
        option_type: Filter by 'call' or 'put'

    Returns:
        Options chain with strikes, premiums, and Greeks
    """
    endpoint = f"/stock/{ticker_symbol}/options-chains"
    params = {k: v for k, v in locals().items()
             if k not in ('endpoint', 'params', 'ticker_symbol') and v is not None}

    result = await uw_client._make_request(endpoint, params)
    return result

@mcp.tool
async def get_etf_activity(
    ticker_symbol: str = None,
    limit: int = 100,
    activity_type: str = None,
    min_volume: int = 0
) -> Dict[str, Any]:
    """
    Get ETF unusual activity and flow.

    Args:
        ticker_symbol: Specific ETF ticker
        limit: Maximum number of results
        activity_type: Type of activity to filter
        min_volume: Minimum volume threshold

    Returns:
        ETF activity data with volume and flow information
    """
    endpoint = "/etf/activity"
    params = {k: v for k, v in locals().items()
             if k not in ('endpoint', 'params') and v is not None and v != 0}

    result = await uw_client._make_request(endpoint, params)
    return result

@mcp.tool
async def get_insider_trades(
    ticker_symbol: str = None,
    limit: int = 100,
    newer_than: str = None,
    trade_type: str = None,
    min_value: int = 0
) -> Dict[str, Any]:
    """
    Get insider trading activity.

    Args:
        ticker_symbol: Specific ticker to analyze
        limit: Maximum number of results
        newer_than: ISO 8601 date string for filtering
        trade_type: Type of trade ('buy', 'sell')
        min_value: Minimum trade value

    Returns:
        Insider trading data with executive details and trade sizes
    """
    endpoint = "/insider/trades"
    params = {k: v for k, v in locals().items()
             if k not in ('endpoint', 'params') and v is not None and v != 0}

    result = await uw_client._make_request(endpoint, params)
    return result

@mcp.tool
async def get_congress_trades(
    ticker_symbol: str = None,
    limit: int = 100,
    newer_than: str = None,
    politician: str = None,
    trade_type: str = None
) -> Dict[str, Any]:
    """
    Get congressional trading activity.

    Args:
        ticker_symbol: Specific ticker to analyze
        limit: Maximum number of results
        newer_than: ISO 8601 date string for filtering
        politician: Specific politician name
        trade_type: Type of trade ('buy', 'sell')

    Returns:
        Congressional trading data with politician details
    """
    endpoint = "/market/congress"
    params = {k: v for k, v in locals().items()
             if k not in ('endpoint', 'params') and v is not None}

    result = await uw_client._make_request(endpoint, params)
    return result

@mcp.tool
async def get_market_overview() -> Dict[str, Any]:
    """
    Get overall market overview and unusual activity summary.

    Returns:
        Market overview with key metrics and unusual activity highlights
    """
    endpoint = "/market/status"
    result = await uw_client._make_request(endpoint)
    return result

@mcp.tool
async def get_alerts_configuration(
    limit: int = 100
) -> Dict[str, Any]:
    """
    Get custom alerts configuration details.

    Args:
        limit: Maximum number of results

    Returns:
        Details about existing custom alerts configuration
    """
    endpoint = "/alerts/configuration"
    params = {"limit": limit}
    result = await uw_client._make_request(endpoint, params)
    return result

@mcp.tool
async def get_etf_exposure(
    ticker_symbol: str,
    limit: int = 100
) -> Dict[str, Any]:
    """
    Get ETF exposure data.

    Args:
        ticker_symbol: ETF ticker symbol
        limit: Maximum number of results

    Returns:
        ETF exposure information
    """
    endpoint = f"/etf/{ticker_symbol}/exposure"
    params = {"limit": limit}
    result = await uw_client._make_request(endpoint, params)
    return result

@mcp.tool
async def get_etf_holdings(
    ticker_symbol: str,
    limit: int = 100
) -> Dict[str, Any]:
    """
    Get ETF holdings data.

    Args:
        ticker_symbol: ETF ticker symbol
        limit: Maximum number of results

    Returns:
        ETF holdings information
    """
    endpoint = f"/etf/{ticker_symbol}/holdings"
    params = {"limit": limit}
    result = await uw_client._make_request(endpoint, params)
    return result

@mcp.tool
async def get_etf_info(
    ticker_symbol: str
) -> Dict[str, Any]:
    """
    Get ETF information.

    Args:
        ticker_symbol: ETF ticker symbol

    Returns:
        ETF basic information
    """
    endpoint = f"/etf/{ticker_symbol}/info"
    result = await uw_client._make_request(endpoint)
    return result

@mcp.tool
async def get_etf_weights(
    ticker_symbol: str,
    limit: int = 100
) -> Dict[str, Any]:
    """
    Get ETF weights data.

    Args:
        ticker_symbol: ETF ticker symbol
        limit: Maximum number of results

    Returns:
        ETF weights information
    """
    endpoint = f"/etf/{ticker_symbol}/weights"
    params = {"limit": limit}
    result = await uw_client._make_request(endpoint, params)
    return result

@mcp.tool
async def get_option_contract_history(
    ticker_symbol: str,
    expiry: str,
    strike: float,
    option_type: str,
    from_date: str = None,
    to_date: str = None
) -> Dict[str, Any]:
    """
    Get historical data for a single option contract.

    Args:
        ticker_symbol: Stock ticker symbol
        expiry: Option expiration date (YYYY-MM-DD)
        strike: Strike price
        option_type: 'call' or 'put'
        from_date: Start date (YYYY-MM-DD)
        to_date: End date (YYYY-MM-DD)

    Returns:
        Historical option contract data
    """
    endpoint = f"/option-contract/{ticker_symbol}/{expiry}/{strike}/{option_type}/history"
    params = {}
    if from_date:
        params["from_date"] = from_date
    if to_date:
        params["to_date"] = to_date

    result = await uw_client._make_request(endpoint, params)
    return result

@mcp.tool
async def get_flow_per_expiry(
    ticker_symbol: str,
    limit: int = 100
) -> Dict[str, Any]:
    """
    Get options flow data per expiration date.

    Args:
        ticker_symbol: Stock ticker symbol
        limit: Maximum number of results

    Returns:
        Options flow grouped by expiration
    """
    endpoint = f"/stock/{ticker_symbol}/flow-per-expiry"
    params = {"limit": limit}
    result = await uw_client._make_request(endpoint, params)
    return result

@mcp.tool
async def get_flow_per_strike(
    ticker_symbol: str,
    limit: int = 100
) -> Dict[str, Any]:
    """
    Get options flow data per strike price.

    Args:
        ticker_symbol: Stock ticker symbol
        limit: Maximum number of results

    Returns:
        Options flow grouped by strike price
    """
    endpoint = f"/stock/{ticker_symbol}/flow-per-strike"
    params = {"limit": limit}
    result = await uw_client._make_request(endpoint, params)
    return result

async def cleanup():
    """Cleanup resources on shutdown"""
    if uw_client.session:
        await uw_client.session.aclose()

if __name__ == "__main__":
    logger.info("Starting MCP server")
    try:
        logger.info("Calling mcp.run()")
        mcp.run()
        logger.info("MCP server started successfully")
    except Exception as e:
        logger.error(f"MCP server failed to start: {e}", exc_info=True)
        raise
    finally:
        logger.info("Running cleanup")
        asyncio.run(cleanup())
        logger.info("Cleanup completed")