#!/usr/bin/env python3
"""
Live Feed Module

This module provides real-time data feeds for the agentic AI trading system.
Combines all Polygon API streams (stocks, options, crypto) with TA-Lib technical analysis.

Components:
- PolygonDataFeed: Comprehensive real-time data feed with technical indicators
- QuestDB integration for time-series data storage
- WebSocket streams for live market data
- Technical analysis calculations using TA-Lib

Usage:
    from live_feed import PolygonDataFeed

    feed = PolygonDataFeed()
    await feed.start()
"""

from .polygon_data_feed import PolygonDataFeed

__all__ = ['PolygonDataFeed']
__version__ = '1.0.0'