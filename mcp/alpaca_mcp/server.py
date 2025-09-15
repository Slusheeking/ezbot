#!/usr/bin/env python3
"""
Custom Alpaca MCP Server for EZBot Trading System
Provides comprehensive trading capabilities through Alpaca Markets API
"""

import asyncio
import json
import os
import uuid
from datetime import datetime, date
from typing import Dict, List, Any, Optional, Union
from dotenv import load_dotenv
from fastmcp import FastMCP
import httpx
from decimal import Decimal

# Load environment variables from project root
load_dotenv("/home/ezb0t/ezbot/.env")

# Initialize FastMCP server
mcp = FastMCP(
    name="alpaca-trading",
    instructions="""
    This server provides comprehensive trading capabilities through Alpaca Markets API.
    Use these tools to manage your trading account, positions, orders, and execute trades for both stocks and options.
    All trading is done through Alpaca's professional trading platform with proper risk management and compliance.
    """
)

class AlpacaClient:
    """Alpaca Markets API client with rate limiting and error handling"""

    def __init__(self):
        self.api_key = os.getenv("ALPACA_API_KEY")
        self.secret_key = os.getenv("ALPACA_SECRET_KEY")
        if not self.api_key or not self.secret_key:
            raise ValueError("ALPACA_API_KEY and ALPACA_SECRET_KEY not found in environment variables")

        # Use paper trading base URL by default for safety
        self.paper_trading = os.getenv("ALPACA_PAPER_TRADING", "true").lower() == "true"
        if self.paper_trading:
            self.base_url = "https://paper-api.alpaca.markets"
        else:
            self.base_url = "https://api.alpaca.markets"

        self.session = None

    async def _get_session(self):
        """Get or create HTTP session"""
        if self.session is None:
            self.session = httpx.AsyncClient(
                timeout=30.0,
                limits=httpx.Limits(max_keepalive_connections=20, max_connections=100)
            )
        return self.session

    async def _make_request(self, endpoint: str, method: str = "GET", params: Dict = None, data: Dict = None) -> Dict:
        """Make authenticated API request with error handling"""
        session = await self._get_session()

        url = f"{self.base_url}{endpoint}"
        headers = {
            "APCA-API-KEY-ID": self.api_key,
            "APCA-API-SECRET-KEY": self.secret_key,
            "accept": "application/json"
        }

        if data:
            headers["Content-Type"] = "application/json"

        try:
            if method.upper() == "GET":
                response = await session.get(url, headers=headers, params=params)
            elif method.upper() == "POST":
                response = await session.post(url, headers=headers, json=data)
            elif method.upper() == "DELETE":
                response = await session.delete(url, headers=headers)
            elif method.upper() == "PATCH":
                response = await session.patch(url, headers=headers, json=data)
            else:
                return {"error": f"Unsupported HTTP method: {method}"}

            response.raise_for_status()

            # Handle empty responses
            if not response.content:
                return {"success": True}

            return response.json()

        except httpx.HTTPStatusError as e:
            error_detail = "Unknown error"
            try:
                error_response = e.response.json()
                error_detail = error_response.get("message", str(e))
            except:
                error_detail = str(e)

            return {
                "error": f"HTTP {e.response.status_code}: {error_detail}",
                "status_code": e.response.status_code
            }
        except Exception as e:
            return {"error": f"Request failed: {str(e)}"}


# Initialize client
alpaca_client = AlpacaClient()

# Account Management Tools
@mcp.tool
async def get_account() -> Dict[str, Any]:
    """
    Get comprehensive account information.

    Returns:
        Account details including balance, buying power, positions value, and trading permissions
    """
    return await alpaca_client._make_request("/v2/account")

@mcp.tool
async def get_account_configurations() -> Dict[str, Any]:
    """
    Get account configuration settings.

    Returns:
        Configuration settings including trading permissions, margin settings, and options level
    """
    return await alpaca_client._make_request("/v2/account/configurations")

@mcp.tool
async def update_account_configurations(
    dtbp_check: Optional[str] = None,
    trade_confirm_email: Optional[str] = None,
    suspend_trade: Optional[bool] = None,
    fractional_trading: Optional[bool] = None
) -> Dict[str, Any]:
    """
    Update account configuration settings.

    Args:
        dtbp_check: Day trading buying power check (none, entry, exit)
        trade_confirm_email: Email confirmation for trades (all, none)
        suspend_trade: Whether to suspend trading
        fractional_trading: Whether to enable fractional trading

    Returns:
        Updated configuration settings
    """
    data = {}
    if dtbp_check is not None:
        data["dtbp_check"] = dtbp_check
    if trade_confirm_email is not None:
        data["trade_confirm_email"] = trade_confirm_email
    if suspend_trade is not None:
        data["suspend_trade"] = suspend_trade
    if fractional_trading is not None:
        data["fractional_trading"] = fractional_trading

    return await alpaca_client._make_request("/v2/account/configurations", method="PATCH", data=data)

# Position Management Tools
@mcp.tool
async def get_all_positions() -> Dict[str, Any]:
    """
    Get all open positions.

    Returns:
        List of all current positions with details including quantity, market value, and P&L
    """
    return await alpaca_client._make_request("/v2/positions")

@mcp.tool
async def get_position(symbol: str) -> Dict[str, Any]:
    """
    Get position for a specific symbol.

    Args:
        symbol: The symbol to get position for (e.g., 'AAPL', 'SPY')

    Returns:
        Position details for the specified symbol
    """
    return await alpaca_client._make_request(f"/v2/positions/{symbol}")

@mcp.tool
async def close_position(symbol: str, qty: Optional[str] = None, percentage: Optional[str] = None) -> Dict[str, Any]:
    """
    Close a position or a portion of it.

    Args:
        symbol: The symbol to close position for
        qty: Specific quantity to close (optional)
        percentage: Percentage of position to close (optional)

    Returns:
        Order details for the closing transaction
    """
    data = {}
    if qty is not None:
        data["qty"] = qty
    if percentage is not None:
        data["percentage"] = percentage

    return await alpaca_client._make_request(f"/v2/positions/{symbol}", method="DELETE", data=data)

@mcp.tool
async def close_all_positions(cancel_orders: bool = False) -> Dict[str, Any]:
    """
    Close all open positions.

    Args:
        cancel_orders: Whether to cancel all open orders as well

    Returns:
        List of orders created to close all positions
    """
    params = {"cancel_orders": str(cancel_orders).lower()}
    return await alpaca_client._make_request("/v2/positions", method="DELETE", params=params)

# Order Management Tools
@mcp.tool
async def get_orders(
    status: Optional[str] = None,
    limit: Optional[int] = None,
    after: Optional[str] = None,
    until: Optional[str] = None,
    direction: Optional[str] = None,
    nested: Optional[bool] = None,
    symbols: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get orders with optional filtering.

    Args:
        status: Order status to filter by (open, closed, all)
        limit: Maximum number of orders to return
        after: Filter orders after this timestamp
        until: Filter orders until this timestamp
        direction: Order direction (asc, desc)
        nested: Whether to include nested multi-leg orders
        symbols: Comma-separated symbols to filter by

    Returns:
        List of orders matching the criteria
    """
    params = {}
    if status:
        params["status"] = status
    if limit:
        params["limit"] = limit
    if after:
        params["after"] = after
    if until:
        params["until"] = until
    if direction:
        params["direction"] = direction
    if nested is not None:
        params["nested"] = str(nested).lower()
    if symbols:
        params["symbols"] = symbols

    return await alpaca_client._make_request("/v2/orders", params=params)

@mcp.tool
async def get_order_by_id(order_id: str) -> Dict[str, Any]:
    """
    Get order by order ID.

    Args:
        order_id: The order ID to retrieve

    Returns:
        Order details
    """
    return await alpaca_client._make_request(f"/v2/orders/{order_id}")

@mcp.tool
async def get_order_by_client_id(client_order_id: str) -> Dict[str, Any]:
    """
    Get order by client order ID.

    Args:
        client_order_id: The client order ID to retrieve

    Returns:
        Order details
    """
    return await alpaca_client._make_request(f"/v2/orders:by_client_order_id", params={"client_order_id": client_order_id})

@mcp.tool
async def cancel_order_by_id(order_id: str) -> Dict[str, Any]:
    """
    Cancel order by order ID.

    Args:
        order_id: The order ID to cancel

    Returns:
        Cancellation status
    """
    return await alpaca_client._make_request(f"/v2/orders/{order_id}", method="DELETE")

@mcp.tool
async def cancel_all_orders() -> Dict[str, Any]:
    """
    Cancel all open orders.

    Returns:
        List of canceled orders
    """
    return await alpaca_client._make_request("/v2/orders", method="DELETE")

# Stock Trading Tools
@mcp.tool
async def submit_market_order(
    symbol: str,
    qty: Optional[str] = None,
    notional: Optional[str] = None,
    side: str = "buy",
    time_in_force: str = "day",
    client_order_id: Optional[str] = None,
    extended_hours: bool = False,
    stop_loss_stop_price: Optional[str] = None,
    stop_loss_limit_price: Optional[str] = None,
    take_profit_limit_price: Optional[str] = None
) -> Dict[str, Any]:
    """
    Submit a market order for stocks.

    Args:
        symbol: Stock symbol to trade
        qty: Quantity of shares (use either qty or notional)
        notional: Dollar amount to trade (use either qty or notional)
        side: Order side ('buy' or 'sell')
        time_in_force: Time in force ('day', 'gtc', 'ioc', 'fok')
        client_order_id: Custom client order ID for tracking
        extended_hours: Whether to allow extended hours trading
        stop_loss_stop_price: Stop loss stop price for bracket orders
        stop_loss_limit_price: Stop loss limit price for bracket orders
        take_profit_limit_price: Take profit limit price for bracket orders

    Returns:
        Order confirmation details
    """
    data = {
        "symbol": symbol,
        "side": side,
        "type": "market",
        "time_in_force": time_in_force
    }

    if qty:
        data["qty"] = qty
    elif notional:
        data["notional"] = notional
    else:
        return {"error": "Either qty or notional must be specified"}

    if client_order_id:
        data["client_order_id"] = client_order_id
    else:
        data["client_order_id"] = f"order_{uuid.uuid4().hex[:8]}"

    if extended_hours:
        data["extended_hours"] = extended_hours

    # Add bracket order legs if specified
    if stop_loss_stop_price or take_profit_limit_price:
        data["order_class"] = "bracket"
        if stop_loss_stop_price:
            stop_loss = {"stop_price": stop_loss_stop_price}
            if stop_loss_limit_price:
                stop_loss["limit_price"] = stop_loss_limit_price
            data["stop_loss"] = stop_loss
        if take_profit_limit_price:
            data["take_profit"] = {"limit_price": take_profit_limit_price}

    return await alpaca_client._make_request("/v2/orders", method="POST", data=data)

@mcp.tool
async def submit_limit_order(
    symbol: str,
    qty: Optional[str] = None,
    notional: Optional[str] = None,
    side: str = "buy",
    limit_price: str = "0",
    time_in_force: str = "day",
    client_order_id: Optional[str] = None,
    extended_hours: bool = False,
    stop_loss_stop_price: Optional[str] = None,
    stop_loss_limit_price: Optional[str] = None,
    take_profit_limit_price: Optional[str] = None
) -> Dict[str, Any]:
    """
    Submit a limit order for stocks.

    Args:
        symbol: Stock symbol to trade
        qty: Quantity of shares (use either qty or notional)
        notional: Dollar amount to trade (use either qty or notional)
        side: Order side ('buy' or 'sell')
        limit_price: Limit price for the order
        time_in_force: Time in force ('day', 'gtc', 'ioc', 'fok')
        client_order_id: Custom client order ID for tracking
        extended_hours: Whether to allow extended hours trading
        stop_loss_stop_price: Stop loss stop price for bracket orders
        stop_loss_limit_price: Stop loss limit price for bracket orders
        take_profit_limit_price: Take profit limit price for bracket orders

    Returns:
        Order confirmation details
    """
    data = {
        "symbol": symbol,
        "side": side,
        "type": "limit",
        "limit_price": limit_price,
        "time_in_force": time_in_force
    }

    if qty:
        data["qty"] = qty
    elif notional:
        data["notional"] = notional
    else:
        return {"error": "Either qty or notional must be specified"}

    if client_order_id:
        data["client_order_id"] = client_order_id
    else:
        data["client_order_id"] = f"order_{uuid.uuid4().hex[:8]}"

    if extended_hours:
        data["extended_hours"] = extended_hours

    # Add bracket order legs if specified
    if stop_loss_stop_price or take_profit_limit_price:
        data["order_class"] = "bracket"
        if stop_loss_stop_price:
            stop_loss = {"stop_price": stop_loss_stop_price}
            if stop_loss_limit_price:
                stop_loss["limit_price"] = stop_loss_limit_price
            data["stop_loss"] = stop_loss
        if take_profit_limit_price:
            data["take_profit"] = {"limit_price": take_profit_limit_price}

    return await alpaca_client._make_request("/v2/orders", method="POST", data=data)

@mcp.tool
async def submit_stop_order(
    symbol: str,
    qty: str,
    side: str,
    stop_price: str,
    time_in_force: str = "day",
    client_order_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Submit a stop order for stocks.

    Args:
        symbol: Stock symbol to trade
        qty: Quantity of shares
        side: Order side ('buy' or 'sell')
        stop_price: Stop price that triggers the order
        time_in_force: Time in force ('day', 'gtc', 'ioc', 'fok')
        client_order_id: Custom client order ID for tracking

    Returns:
        Order confirmation details
    """
    data = {
        "symbol": symbol,
        "qty": qty,
        "side": side,
        "type": "stop",
        "stop_price": stop_price,
        "time_in_force": time_in_force,
        "client_order_id": client_order_id or f"order_{uuid.uuid4().hex[:8]}"
    }

    return await alpaca_client._make_request("/v2/orders", method="POST", data=data)

@mcp.tool
async def submit_stop_limit_order(
    symbol: str,
    qty: str,
    side: str,
    stop_price: str,
    limit_price: str,
    time_in_force: str = "day",
    client_order_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Submit a stop-limit order for stocks.

    Args:
        symbol: Stock symbol to trade
        qty: Quantity of shares
        side: Order side ('buy' or 'sell')
        stop_price: Stop price that triggers the order
        limit_price: Limit price once triggered
        time_in_force: Time in force ('day', 'gtc', 'ioc', 'fok')
        client_order_id: Custom client order ID for tracking

    Returns:
        Order confirmation details
    """
    data = {
        "symbol": symbol,
        "qty": qty,
        "side": side,
        "type": "stop_limit",
        "stop_price": stop_price,
        "limit_price": limit_price,
        "time_in_force": time_in_force,
        "client_order_id": client_order_id or f"order_{uuid.uuid4().hex[:8]}"
    }

    return await alpaca_client._make_request("/v2/orders", method="POST", data=data)

# Options Trading Tools
@mcp.tool
async def submit_option_market_order(
    symbol: str,
    qty: str,
    side: str,
    time_in_force: str = "day",
    client_order_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Submit a market order for options.

    Args:
        symbol: Option symbol (e.g., 'AAPL230120C00150000')
        qty: Number of contracts
        side: Order side ('buy_to_open', 'sell_to_open', 'buy_to_close', 'sell_to_close')
        time_in_force: Time in force ('day', 'gtc', 'ioc', 'fok')
        client_order_id: Custom client order ID for tracking

    Returns:
        Order confirmation details
    """
    data = {
        "symbol": symbol,
        "qty": qty,
        "side": side,
        "type": "market",
        "time_in_force": time_in_force,
        "client_order_id": client_order_id or f"option_{uuid.uuid4().hex[:8]}"
    }

    return await alpaca_client._make_request("/v2/orders", method="POST", data=data)

@mcp.tool
async def submit_option_limit_order(
    symbol: str,
    qty: str,
    side: str,
    limit_price: str,
    time_in_force: str = "day",
    client_order_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Submit a limit order for options.

    Args:
        symbol: Option symbol (e.g., 'AAPL230120C00150000')
        qty: Number of contracts
        side: Order side ('buy_to_open', 'sell_to_open', 'buy_to_close', 'sell_to_close')
        limit_price: Limit price per contract
        time_in_force: Time in force ('day', 'gtc', 'ioc', 'fok')
        client_order_id: Custom client order ID for tracking

    Returns:
        Order confirmation details
    """
    data = {
        "symbol": symbol,
        "qty": qty,
        "side": side,
        "type": "limit",
        "limit_price": limit_price,
        "time_in_force": time_in_force,
        "client_order_id": client_order_id or f"option_{uuid.uuid4().hex[:8]}"
    }

    return await alpaca_client._make_request("/v2/orders", method="POST", data=data)

@mcp.tool
async def submit_multileg_order(
    legs: List[Dict[str, Any]],
    qty: str,
    order_type: str = "market",
    limit_price: Optional[str] = None,
    time_in_force: str = "day",
    client_order_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Submit a multi-leg options order (spreads, straddles, etc.).

    Args:
        legs: List of leg dictionaries with symbol, side, and ratio
        qty: Number of strategy units
        order_type: Order type ('market' or 'limit')
        limit_price: Net limit price for limit orders
        time_in_force: Time in force ('day', 'gtc')
        client_order_id: Custom client order ID for tracking

    Returns:
        Order confirmation details
    """
    data = {
        "qty": qty,
        "order_class": "multileg",
        "type": order_type,
        "time_in_force": time_in_force,
        "legs": legs,
        "client_order_id": client_order_id or f"multileg_{uuid.uuid4().hex[:8]}"
    }

    if order_type == "limit" and limit_price:
        data["limit_price"] = limit_price

    return await alpaca_client._make_request("/v2/orders", method="POST", data=data)


# Utility Functions
async def cleanup():
    """Cleanup resources on shutdown"""
    if alpaca_client.session:
        await alpaca_client.session.aclose()

if __name__ == "__main__":
    mcp.run()