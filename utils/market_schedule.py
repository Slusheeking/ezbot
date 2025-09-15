#!/usr/bin/env python3
"""
Market Schedule Utility

Provides trading days logic including US market holidays and weekend detection.
Can be used across multiple data feeds to determine when markets are open.
"""

import datetime
from typing import Set, List
from dataclasses import dataclass


@dataclass
class MarketHours:
    """Market hours configuration"""
    regular_open: str = "09:30"
    regular_close: str = "16:00"
    premarket_open: str = "04:00"
    afterhours_close: str = "20:00"


class MarketSchedule:
    """US stock market schedule utility"""

    def __init__(self):
        self.market_hours = MarketHours()

    def get_us_market_holidays(self, year: int) -> Set[datetime.date]:
        """Get US stock market holidays for a given year"""
        holidays = set()

        # New Year's Day
        new_years = datetime.date(year, 1, 1)
        if new_years.weekday() == 5:  # Saturday
            holidays.add(datetime.date(year, 1, 3))  # Monday
        elif new_years.weekday() == 6:  # Sunday
            holidays.add(datetime.date(year, 1, 2))  # Monday
        else:
            holidays.add(new_years)

        # Martin Luther King Jr. Day (3rd Monday in January)
        holidays.add(self._get_nth_weekday(year, 1, 0, 3))

        # Presidents Day (3rd Monday in February)
        holidays.add(self._get_nth_weekday(year, 2, 0, 3))

        # Good Friday (2 days before Easter)
        easter = self._get_easter(year)
        good_friday = easter - datetime.timedelta(days=2)
        holidays.add(good_friday)

        # Memorial Day (last Monday in May)
        holidays.add(self._get_last_weekday(year, 5, 0))

        # Juneteenth (June 19th)
        juneteenth = datetime.date(year, 6, 19)
        if juneteenth.weekday() == 5:  # Saturday
            holidays.add(datetime.date(year, 6, 18))  # Friday
        elif juneteenth.weekday() == 6:  # Sunday
            holidays.add(datetime.date(year, 6, 20))  # Monday
        else:
            holidays.add(juneteenth)

        # Independence Day (July 4th)
        independence = datetime.date(year, 7, 4)
        if independence.weekday() == 5:  # Saturday
            holidays.add(datetime.date(year, 7, 3))  # Friday
        elif independence.weekday() == 6:  # Sunday
            holidays.add(datetime.date(year, 7, 5))  # Monday
        else:
            holidays.add(independence)

        # Labor Day (1st Monday in September)
        holidays.add(self._get_nth_weekday(year, 9, 0, 1))

        # Thanksgiving (4th Thursday in November)
        holidays.add(self._get_nth_weekday(year, 11, 3, 4))

        # Christmas Day (December 25th)
        christmas = datetime.date(year, 12, 25)
        if christmas.weekday() == 5:  # Saturday
            holidays.add(datetime.date(year, 12, 24))  # Friday
        elif christmas.weekday() == 6:  # Sunday
            holidays.add(datetime.date(year, 12, 26))  # Monday
        else:
            holidays.add(christmas)

        return holidays

    def _get_nth_weekday(self, year: int, month: int, weekday: int, n: int) -> datetime.date:
        """Get the nth occurrence of a weekday in a month"""
        first_day = datetime.date(year, month, 1)
        first_weekday = first_day.weekday()

        # Days to add to get to the first occurrence of the target weekday
        days_to_add = (weekday - first_weekday) % 7
        first_occurrence = first_day + datetime.timedelta(days=days_to_add)

        # Add weeks to get to the nth occurrence
        target_date = first_occurrence + datetime.timedelta(weeks=n-1)

        return target_date

    def _get_last_weekday(self, year: int, month: int, weekday: int) -> datetime.date:
        """Get the last occurrence of a weekday in a month"""
        # Start from the last day of the month
        if month == 12:
            last_day = datetime.date(year + 1, 1, 1) - datetime.timedelta(days=1)
        else:
            last_day = datetime.date(year, month + 1, 1) - datetime.timedelta(days=1)

        # Go backwards to find the last occurrence of the weekday
        days_to_subtract = (last_day.weekday() - weekday) % 7
        return last_day - datetime.timedelta(days=days_to_subtract)

    def _get_easter(self, year: int) -> datetime.date:
        """Calculate Easter Sunday using the algorithm"""
        # Anonymous Gregorian algorithm
        a = year % 19
        b = year // 100
        c = year % 100
        d = b // 4
        e = b % 4
        f = (b + 8) // 25
        g = (b - f + 1) // 3
        h = (19 * a + b - d - g + 15) % 30
        i = c // 4
        k = c % 4
        l = (32 + 2 * e + 2 * i - h - k) % 7
        m = (a + 11 * h + 22 * l) // 451
        month = (h + l - 7 * m + 114) // 31
        day = ((h + l - 7 * m + 114) % 31) + 1

        return datetime.date(year, month, day)

    def is_trading_day(self, date: datetime.date) -> bool:
        """Check if a given date is a trading day (not weekend or holiday)"""
        # Check if weekend
        if date.weekday() >= 5:  # Saturday = 5, Sunday = 6
            return False

        # Check if holiday
        holidays = self.get_us_market_holidays(date.year)
        if date in holidays:
            return False

        return True

    def is_weekend(self, date: datetime.date) -> bool:
        """Check if a given date is a weekend"""
        return date.weekday() >= 5

    def is_holiday(self, date: datetime.date) -> bool:
        """Check if a given date is a market holiday"""
        holidays = self.get_us_market_holidays(date.year)
        return date in holidays

    def get_next_trading_day(self, date: datetime.date) -> datetime.date:
        """Get the next trading day after the given date"""
        next_day = date + datetime.timedelta(days=1)
        while not self.is_trading_day(next_day):
            next_day += datetime.timedelta(days=1)
        return next_day

    def get_previous_trading_day(self, date: datetime.date) -> datetime.date:
        """Get the previous trading day before the given date"""
        prev_day = date - datetime.timedelta(days=1)
        while not self.is_trading_day(prev_day):
            prev_day -= datetime.timedelta(days=1)
        return prev_day

    def get_trading_days_in_range(self, start_date: datetime.date, end_date: datetime.date) -> List[datetime.date]:
        """Get all trading days between start_date and end_date (inclusive)"""
        trading_days = []
        current_date = start_date

        while current_date <= end_date:
            if self.is_trading_day(current_date):
                trading_days.append(current_date)
            current_date += datetime.timedelta(days=1)

        return trading_days

    def should_collect_earnings_data(self, dt: datetime.datetime = None) -> bool:
        """
        Determine if earnings data should be collected at the given time.
        Returns True during trading days or extended hours on trading days.
        """
        if dt is None:
            dt = datetime.datetime.now()

        date = dt.date()

        # Don't collect on non-trading days
        if not self.is_trading_day(date):
            return False

        # On trading days, collect during extended hours (4 AM - 8 PM ET)
        time_str = dt.strftime("%H:%M")
        return "04:00" <= time_str <= "20:00"

    def get_market_status(self, dt: datetime.datetime = None) -> str:
        """Get current market status: closed, premarket, open, afterhours"""
        if dt is None:
            dt = datetime.datetime.now()

        if not self.is_trading_day(dt.date()):
            return "closed"

        time_str = dt.strftime("%H:%M")

        if time_str < self.market_hours.premarket_open:
            return "closed"
        elif time_str < self.market_hours.regular_open:
            return "premarket"
        elif time_str < self.market_hours.regular_close:
            return "open"
        elif time_str < self.market_hours.afterhours_close:
            return "afterhours"
        else:
            return "closed"


def main():
    """Test the market schedule utility"""
    schedule = MarketSchedule()
    today = datetime.date.today()

    print(f"Market Schedule Utility Test - {today}")
    print("-" * 50)

    print(f"Today ({today}):")
    print(f"  Is trading day: {schedule.is_trading_day(today)}")
    print(f"  Is weekend: {schedule.is_weekend(today)}")
    print(f"  Is holiday: {schedule.is_holiday(today)}")

    if not schedule.is_trading_day(today):
        next_trading = schedule.get_next_trading_day(today)
        print(f"  Next trading day: {next_trading}")

    current_time = datetime.datetime.now()
    print(f"\nCurrent time ({current_time.strftime('%H:%M')}):")
    print(f"  Should collect earnings: {schedule.should_collect_earnings_data(current_time)}")
    print(f"  Market status: {schedule.get_market_status(current_time)}")

    # Show next 10 days
    print(f"\nNext 10 days trading schedule:")
    for i in range(10):
        check_date = today + datetime.timedelta(days=i)
        is_trading = schedule.is_trading_day(check_date)
        day_name = check_date.strftime("%A")
        status = "TRADING" if is_trading else "CLOSED"
        print(f"  {check_date} ({day_name}): {status}")

    # Show holidays for current year
    holidays = schedule.get_us_market_holidays(today.year)
    print(f"\n{today.year} Market Holidays:")
    for holiday in sorted(holidays):
        print(f"  {holiday} ({holiday.strftime('%A')})")


if __name__ == "__main__":
    main()