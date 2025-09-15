"""
VIX Feed Data Collection Package

This package provides VIX (volatility index) data collection from Yahoo Finance:
- VIX (CBOE Volatility Index)
- VIX9D (9-day Volatility)
- VIX3M (3-month Volatility)
- VIX6M (6-month Volatility)
- VIX ETFs/ETNs (UVXY, SVXY, VXX, VIXY, VIXM)

All feeds store data in QuestDB time-series database for trading strategy analysis.
"""

from .yfinance_vix_feed import VIXFeedClient