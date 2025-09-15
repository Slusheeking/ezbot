"""
News Feed Data Collection Package

This package provides financial news data collection from multiple sources:
- Unusual Whales Headlines API
- Stock Titan RSS Feed
- Polygon.io News API

All feeds store data in QuestDB time-series database for analysis and alerting.
"""

from .uw_news_feed import UnusualWhalesHeadlinesClient
from .stocktitan_news_feed import StockTitanRSSClient
from .polygon_news_feed import PolygonNewsClient

__version__ = "1.0.0"
__author__ = "ezbot Financial Data Systems"

# Available news feed clients
__all__ = [
    "UnusualWhalesHeadlinesClient",
    "StockTitanRSSClient",
    "PolygonNewsClient"
]

# Feed configuration
SUPPORTED_FEEDS = {
    "unusual_whales": {
        "client": UnusualWhalesHeadlinesClient,
        "description": "Real-time financial headlines with sentiment and ticker analysis",
        "api_required": True,
        "rate_limit": "60 requests/minute"
    },
    "stock_titan": {
        "client": StockTitanRSSClient,
        "description": "RSS-based stock market news and analysis",
        "api_required": False,
        "rate_limit": "RSS polling interval"
    },
    "polygon": {
        "client": PolygonNewsClient,
        "description": "Professional-grade financial news with comprehensive metadata",
        "api_required": True,
        "rate_limit": "60 requests/minute"
    }
}

def get_available_feeds():
    """Return list of available news feed sources"""
    return list(SUPPORTED_FEEDS.keys())

def get_feed_info(feed_name):
    """Get information about a specific feed"""
    return SUPPORTED_FEEDS.get(feed_name, {})