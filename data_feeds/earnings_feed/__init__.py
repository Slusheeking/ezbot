"""
Unusual Whales Earnings Feed

Collects combined premarket and afterhours earnings data from Unusual Whales API and stores in QuestDB.
Includes historical earnings analysis for upcoming reporting symbols.
"""

from .uw_earnings import UnusualWhalesEarningsFeed

__all__ = ["UnusualWhalesEarningsFeed"]