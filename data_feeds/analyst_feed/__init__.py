"""
Unusual Whales Analyst Feed

Collects analyst reports and ratings from Unusual Whales API and stores in QuestDB.
This feed is crucial for news catalyst momentum and premarket momentum strategies.
"""

__version__ = "1.0.0"
__author__ = "EZBot Trading System"

from .uw_reports import UnusualWhalesAnalystFeed

__all__ = ["UnusualWhalesAnalystFeed"]