"""
Market Time Utilities
Centralized market hours and timing logic for all data feeds
"""

from datetime import datetime
import pytz


class MarketTime:
    """Utility class for market timing operations"""

    def __init__(self):
        self.et_tz = pytz.timezone('US/Eastern')

    def get_current_et(self) -> datetime:
        """Get current time in Eastern timezone"""
        return datetime.now(self.et_tz)

    def is_market_hours(self) -> bool:
        """Check if current time is during market hours (9:30 AM - 4:00 PM ET)"""
        now_et = self.get_current_et()

        # Skip weekends
        if now_et.weekday() >= 5:  # Saturday = 5, Sunday = 6
            return False

        # Market hours: 9:30 AM - 4:00 PM ET
        market_open = now_et.replace(hour=9, minute=30, second=0, microsecond=0)
        market_close = now_et.replace(hour=16, minute=0, second=0, microsecond=0)

        return market_open <= now_et <= market_close

    def is_extended_hours(self) -> bool:
        """Check if current time is during extended hours (4:00 AM - 9:30 AM ET, 4:00 PM - 8:00 PM ET)"""
        now_et = self.get_current_et()

        # Skip weekends
        if now_et.weekday() >= 5:  # Saturday = 5, Sunday = 6
            return False

        # Pre-market: 4:00 AM - 9:30 AM ET
        premarket_start = now_et.replace(hour=4, minute=0, second=0, microsecond=0)
        premarket_end = now_et.replace(hour=9, minute=30, second=0, microsecond=0)

        # After-hours: 4:00 PM - 8:00 PM ET
        afterhours_start = now_et.replace(hour=16, minute=0, second=0, microsecond=0)
        afterhours_end = now_et.replace(hour=20, minute=0, second=0, microsecond=0)

        return (premarket_start <= now_et < premarket_end) or (afterhours_start < now_et <= afterhours_end)

    def is_weekend(self) -> bool:
        """Check if current time is weekend"""
        now_et = self.get_current_et()
        return now_et.weekday() >= 5

    def get_market_status(self) -> str:
        """Get current market status as string"""
        if self.is_market_hours():
            return "MARKET_HOURS"
        elif self.is_extended_hours():
            return "EXTENDED_HOURS"
        elif self.is_weekend():
            return "WEEKEND"
        else:
            return "OFF_HOURS"

    def get_collection_interval(self, market_interval: int = 180, extended_interval: int = 600, off_hours_interval: int = 1800) -> int:
        """Get appropriate collection interval in seconds based on market status"""
        status = self.get_market_status()

        if status == "MARKET_HOURS":
            return market_interval  # Default: 3 minutes
        elif status == "EXTENDED_HOURS":
            return extended_interval  # Default: 10 minutes
        else:  # OFF_HOURS or WEEKEND
            return off_hours_interval  # Default: 30 minutes


# Create singleton instance
market_time = MarketTime()