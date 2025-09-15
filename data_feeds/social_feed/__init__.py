"""
Social Feed Data Collection Package

This package provides social media data collection from multiple sources:
- Reddit Posts and Comments API

All feeds store data in QuestDB time-series database for analysis and alerting.
"""

from .reddit_feed import RedditFeedClient