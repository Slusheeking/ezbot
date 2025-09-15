"""
Unusual Whales Calendar Feed

Collects economic calendar and FDA calendar data from Unusual Whales API and stores in QuestDB.
Includes both economic indicators/events and FDA milestones for pharmaceutical companies.
"""

__version__ = "1.0.0"
__author__ = "EZBot Trading System"

from .uw_calendar import UnusualWhalesCalendarFeed

__all__ = ["UnusualWhalesCalendarFeed"]