#!/usr/bin/env python3
"""
Unusual Whales Calendar Feed

Collects economic calendar and FDA calendar data from Unusual Whales API and stores in QuestDB.
Provides comprehensive market event tracking for economic indicators and FDA milestones.
"""

import asyncio
import logging
import os
import yaml
import httpx
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime, timedelta, time
from typing import Dict, List, Optional
from dataclasses import dataclass
from dotenv import load_dotenv

# Import market schedule utility
import importlib.util

def _import_market_schedule():
    """Import MarketSchedule from utils directory"""
    utils_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'utils')
    market_schedule_path = os.path.join(utils_path, "market_schedule.py")

    spec = importlib.util.spec_from_file_location("market_schedule", market_schedule_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load market_schedule from {market_schedule_path}")

    market_schedule_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(market_schedule_module)
    return market_schedule_module.MarketSchedule

MarketSchedule = _import_market_schedule()


@dataclass
class EconomicEvent:
    """Economic calendar event structure"""
    event: str
    forecast: Optional[str]
    prev: Optional[str]
    reported_period: Optional[str]
    time: datetime
    event_type: str
    timestamp: datetime


@dataclass
class FDAEvent:
    """FDA calendar event structure"""
    catalyst: str
    description: str
    drug: str
    end_date: datetime
    has_options: Optional[bool]
    indication: str
    marketcap: Optional[str]
    notes: Optional[str]
    outcome: Optional[str]
    outcome_brief: Optional[str]
    source_link: Optional[str]
    start_date: datetime
    status: str
    ticker: str
    timestamp: datetime


class UnusualWhalesCalendarFeed:
    """Calendar data collector for Unusual Whales API"""

    def __init__(self, config_path: str = None):
        """Initialize the calendar feed"""
        # Load environment variables from .env file
        env_path = '/home/ezb0t/ezbot/.env'
        load_dotenv(env_path)

        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), 'settings.yaml')

        self.config = self._load_config(config_path)
        self.logger = self._setup_logging()

        # Get API key
        self.api_key = os.getenv(self.config['api']['token_env_var'])

        if not self.api_key:
            raise ValueError(f"API key not found in environment variable: {self.config['api']['token_env_var']}")

        # Initialize HTTP client
        self.client = httpx.AsyncClient(
            timeout=self.config['api']['timeout'],
            headers={
                'Authorization': f'Bearer {self.api_key}',
                'Accept': 'application/json, text/plain'
            }
        )

        # QuestDB connection
        self.questdb_conn = None
        self.questdb_config = self.config['questdb']

        # Market schedule utility
        self.market_schedule = MarketSchedule()

        self.running = False

    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            raise ValueError(f"Failed to load config from {config_path}: {e}")

    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logger = logging.getLogger('calendar_feed')

        # Clear any existing handlers to avoid duplicates
        logger.handlers.clear()

        # Set logging level
        level = self.config['logging']['level']
        logger.setLevel(getattr(logging, level.upper()) if hasattr(logging, level.upper()) else logging.INFO)

        # Console handler only
        console_handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        return logger

    async def _init_questdb(self):
        """Initialize QuestDB connection and create tables"""
        try:
            self.questdb_conn = psycopg2.connect(
                host=self.questdb_config['host'],
                port=self.questdb_config['port'],
                database=self.questdb_config['database'],
                user='admin',
                password='quest',
                connect_timeout=10
            )

            # Create tables if they don't exist
            await self._create_tables()

        except Exception as e:
            self.logger.error(f"Failed to connect to QuestDB: {e}")
            raise

    async def _create_tables(self):
        """Create QuestDB tables for calendar data"""

        # Economic calendar table
        economic_calendar_sql = """
        CREATE TABLE IF NOT EXISTS economic_calendar (
            timestamp TIMESTAMP,
            event STRING,
            forecast STRING,
            prev STRING,
            reported_period STRING,
            event_time TIMESTAMP,
            event_type SYMBOL CAPACITY 10 CACHE,
            collected_at TIMESTAMP
        ) TIMESTAMP(timestamp) PARTITION BY DAY WAL;
        """

        # FDA calendar table
        fda_calendar_sql = """
        CREATE TABLE IF NOT EXISTS fda_calendar (
            timestamp TIMESTAMP,
            ticker SYMBOL CAPACITY 1000 CACHE,
            catalyst STRING,
            description STRING,
            drug STRING,
            end_date TIMESTAMP,
            has_options BOOLEAN,
            indication STRING,
            marketcap STRING,
            notes STRING,
            outcome STRING,
            outcome_brief STRING,
            source_link STRING,
            start_date TIMESTAMP,
            status SYMBOL CAPACITY 20 CACHE,
            collected_at TIMESTAMP
        ) TIMESTAMP(timestamp) PARTITION BY DAY WAL;
        """

        cursor = self.questdb_conn.cursor()

        try:
            cursor.execute(economic_calendar_sql)
            cursor.execute(fda_calendar_sql)
            self.questdb_conn.commit()
            self.logger.info("QuestDB calendar tables created successfully")
        except Exception as e:
            self.logger.error(f"Error creating tables: {e}")
            self.questdb_conn.rollback()
            raise
        finally:
            cursor.close()

    async def run_collection_cycle(self):
        """Run a complete collection cycle for both calendars"""
        self.logger.info("Starting calendar collection cycle")

        try:
            # Collect economic calendar
            await self._collect_economic_calendar()

            # Collect FDA calendar
            await self._collect_fda_calendar()

            self.logger.info("Calendar collection cycle completed")

        except Exception as e:
            error_msg = f"Error in collection cycle: {e}"
            self.logger.error(error_msg)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ERROR: {error_msg}")

    async def _collect_economic_calendar(self):
        """Collect economic calendar events"""
        try:
            url = f"{self.config['api']['base_url']}{self.config['api']['economic_calendar_endpoint']}"

            self.logger.info(f"Fetching economic calendar: {url}")

            response = await self.client.get(url)
            if response.status_code == 200:
                data = response.json()
                events = data.get('data', [])

                if events:
                    # Process and store events
                    processed_events = self._process_economic_events(events)
                    await self._store_economic_events(processed_events)

                    self.logger.info(f"Retrieved {len(events)} economic calendar events")
                    print(f"Economic Calendar: {len(events)} events collected")

                    # Show significant events
                    significant = [e for e in processed_events if e.event_type in ['fed-speaker', 'fomc']]
                    if significant:
                        print(f"  Significant events: {len(significant)}")
                        for event in significant[:3]:  # Show top 3
                            print(f"    {event.time.strftime('%m/%d %H:%M')} - {event.event} ({event.event_type})")
                else:
                    self.logger.info("No economic calendar events found")
                    print("Economic Calendar: No events found")

            else:
                self.logger.error(f"Economic calendar API request failed: {response.status_code}")

        except Exception as e:
            self.logger.error(f"Error collecting economic calendar: {e}")

    async def _collect_fda_calendar(self):
        """Collect FDA calendar events"""
        try:
            url = f"{self.config['api']['base_url']}{self.config['api']['fda_calendar_endpoint']}"

            # Calculate date range for FDA events
            today = datetime.now().date()
            start_date = today - timedelta(days=self.config['collection']['fda_lookback_days'])
            end_date = today + timedelta(days=self.config['collection']['fda_lookahead_days'])

            params = {
                'limit': self.config['collection']['default_limit'],
                'target_date_min': start_date.strftime('%Y-%m-%d'),
                'target_date_max': end_date.strftime('%Y-%m-%d')
            }

            self.logger.info(f"Fetching FDA calendar: {url} with params: {params}")

            response = await self.client.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                events = data.get('data', [])

                if events:
                    # Filter and process events
                    filtered_events = self._filter_fda_events(events)
                    processed_events = self._process_fda_events(filtered_events)
                    await self._store_fda_events(processed_events)

                    self.logger.info(f"Retrieved {len(events)} FDA calendar events, stored {len(processed_events)}")
                    print(f"FDA Calendar: {len(events)} events found, {len(processed_events)} stored")

                    # Show upcoming PDUFA dates
                    pdufa_events = [e for e in processed_events if 'PDUFA' in e.catalyst]
                    if pdufa_events:
                        print(f"  Upcoming PDUFA dates: {len(pdufa_events)}")
                        for event in pdufa_events[:3]:  # Show top 3
                            print(f"    {event.start_date.strftime('%m/%d')} - {event.ticker}: {event.drug}")
                else:
                    self.logger.info("No FDA calendar events found")
                    print("FDA Calendar: No events found")

            else:
                self.logger.error(f"FDA calendar API request failed: {response.status_code}")

        except Exception as e:
            self.logger.error(f"Error collecting FDA calendar: {e}")

    def _process_economic_events(self, events: List[Dict]) -> List[EconomicEvent]:
        """Process economic calendar events"""
        processed = []
        current_time = datetime.now()

        for event in events:
            try:
                # Parse event time
                event_time = datetime.fromisoformat(event['time'].replace('Z', '+00:00'))

                # Create economic event record
                economic_event = EconomicEvent(
                    event=event['event'],
                    forecast=event.get('forecast'),
                    prev=event.get('prev'),
                    reported_period=event.get('reported_period'),
                    time=event_time.replace(tzinfo=None),  # Remove timezone for QuestDB
                    event_type=event['type'],
                    timestamp=current_time
                )

                # Filter by event type if configured
                if economic_event.event_type in self.config['filters']['economic']['track_event_types']:
                    processed.append(economic_event)

            except Exception as e:
                self.logger.error(f"Error processing economic event: {e}")
                continue

        return processed

    def _filter_fda_events(self, events: List[Dict]) -> List[Dict]:
        """Filter FDA events based on configuration"""
        filtered = []
        fda_config = self.config['filters']['fda']

        for event in events:
            try:
                # Check market cap filter
                if fda_config['min_market_cap'] > 0:
                    marketcap = event.get('marketcap')
                    if marketcap:
                        try:
                            cap_value = float(marketcap)
                            if cap_value < fda_config['min_market_cap']:
                                continue
                        except (ValueError, TypeError):
                            pass

                # Check options requirement
                if fda_config['require_options']:
                    if not event.get('has_options'):
                        continue

                # Check catalyst type filter
                catalyst = event.get('catalyst', '')
                if fda_config['track_catalyst_types']:
                    if not any(track_type in catalyst for track_type in fda_config['track_catalyst_types']):
                        continue

                # Check exclusion filter
                if fda_config['exclude_catalyst_types']:
                    if any(exclude_type in catalyst for exclude_type in fda_config['exclude_catalyst_types']):
                        continue

                filtered.append(event)

            except Exception as e:
                self.logger.error(f"Error filtering FDA event: {e}")
                continue

        return filtered

    def _process_fda_events(self, events: List[Dict]) -> List[FDAEvent]:
        """Process FDA calendar events"""
        processed = []
        current_time = datetime.now()

        for event in events:
            try:
                # Parse dates - handle different formats
                start_date_str = event.get('start_date')
                end_date_str = event.get('end_date')

                # Skip if start_date is missing (end_date can be None for many FDA events)
                if not start_date_str:
                    continue

                # Use start_date as end_date if end_date is missing
                if not end_date_str:
                    end_date_str = start_date_str

                # Try to parse dates with different formats
                def parse_date(date_str):
                    if not date_str:
                        return datetime.now()

                    # Try ISO format first
                    try:
                        return datetime.fromisoformat(date_str)
                    except (ValueError, TypeError):
                        pass

                    # Try common date formats
                    date_formats = [
                        '%Y-%m-%d',
                        '%Y/%m/%d',
                        '%m/%d/%Y',
                        '%m-%d-%Y',
                        '%Y-%m-%dT%H:%M:%S',
                        '%Y-%m-%d %H:%M:%S'
                    ]

                    for fmt in date_formats:
                        try:
                            return datetime.strptime(date_str, fmt)
                        except ValueError:
                            continue

                    # If all fails, return current time
                    return datetime.now()

                start_date = parse_date(start_date_str)
                end_date = parse_date(end_date_str)

                # Create FDA event record
                fda_event = FDAEvent(
                    catalyst=event['catalyst'],
                    description=event['description'],
                    drug=event['drug'],
                    end_date=end_date,
                    has_options=event.get('has_options'),
                    indication=event['indication'],
                    marketcap=event.get('marketcap'),
                    notes=event.get('notes'),
                    outcome=event.get('outcome'),
                    outcome_brief=event.get('outcome_brief'),
                    source_link=event.get('source_link'),
                    start_date=start_date,
                    status=event['status'],
                    ticker=event['ticker'],
                    timestamp=current_time
                )

                processed.append(fda_event)

            except Exception as e:
                self.logger.error(f"Error processing FDA event: {e}")
                continue

        return processed

    async def _store_economic_events(self, events: List[EconomicEvent]):
        """Store economic events in QuestDB"""
        if not events:
            return

        cursor = self.questdb_conn.cursor()

        insert_sql = """
        INSERT INTO economic_calendar (
            timestamp, event, forecast, prev, reported_period, event_time, event_type, collected_at
        ) VALUES %s
        """

        values = [
            (
                e.timestamp, e.event, e.forecast, e.prev, e.reported_period,
                e.time, e.event_type, e.timestamp
            )
            for e in events
        ]

        try:
            execute_values(cursor, insert_sql, values, template=None, page_size=100)
            self.questdb_conn.commit()
            self.logger.info(f"Stored {len(events)} economic events in QuestDB")

        except Exception as e:
            self.logger.error(f"Error storing economic events in QuestDB: {e}")
            self.questdb_conn.rollback()
        finally:
            cursor.close()

    async def _store_fda_events(self, events: List[FDAEvent]):
        """Store FDA events in QuestDB"""
        if not events:
            return

        cursor = self.questdb_conn.cursor()

        insert_sql = """
        INSERT INTO fda_calendar (
            timestamp, ticker, catalyst, description, drug, end_date, has_options,
            indication, marketcap, notes, outcome, outcome_brief, source_link,
            start_date, status, collected_at
        ) VALUES %s
        """

        values = [
            (
                e.timestamp, e.ticker, e.catalyst, e.description, e.drug, e.end_date,
                e.has_options, e.indication, e.marketcap, e.notes, e.outcome,
                e.outcome_brief, e.source_link, e.start_date, e.status, e.timestamp
            )
            for e in events
        ]

        try:
            execute_values(cursor, insert_sql, values, template=None, page_size=100)
            self.questdb_conn.commit()
            self.logger.info(f"Stored {len(events)} FDA events in QuestDB")

        except Exception as e:
            self.logger.error(f"Error storing FDA events in QuestDB: {e}")
            self.questdb_conn.rollback()
        finally:
            cursor.close()

    async def start_scheduled_collection(self):
        """Start the scheduled collection process"""
        self.logger.info("Starting Unusual Whales Calendar Feed")
        self.running = True

        # Initialize QuestDB connection
        await self._init_questdb()

        try:
            while self.running:
                current_datetime = datetime.now()
                current_time = current_datetime.time()
                current_date = current_datetime.date()

                # Check if today is a trading day
                if not self.market_schedule.is_trading_day(current_date):
                    if self.market_schedule.is_weekend(current_date):
                        reason = "weekend"
                    else:
                        reason = "market holiday"

                    next_trading_day = self.market_schedule.get_next_trading_day(current_date)
                    print(f"\\n[{current_datetime.strftime('%H:%M:%S')}] Skipping collection - {reason}. Next trading day: {next_trading_day}")

                    # Sleep for longer on non-trading days
                    await asyncio.sleep(3600)  # 1 hour
                    continue

                if self.config['collection']['development_mode']:
                    # DEVELOPMENT: Run collection immediately for testing
                    print(f"\\n[{current_datetime.strftime('%H:%M:%S')}] Running collection cycle (development mode - trading day)...")
                    await self.run_collection_cycle()
                    # Sleep for configured interval before next collection
                    dev_interval = self.config['collection']['dev_collection_interval']
                    await asyncio.sleep(dev_interval)
                else:
                    # PRODUCTION: Check market hours for collection frequency
                    if self.market_schedule.should_collect_earnings_data(current_datetime):
                        # During extended hours, collect more frequently
                        market_status = self.market_schedule.get_market_status(current_datetime)
                        if market_status in ['premarket', 'open', 'afterhours']:
                            interval = self.config['collection']['poll_interval']
                        else:
                            interval = self.config['collection']['after_hours_interval']

                        print(f"\\n[{current_datetime.strftime('%H:%M:%S')}] Collection time ({market_status})! Starting collection...")
                        await self.run_collection_cycle()
                        await asyncio.sleep(interval)
                    else:
                        print(f"\\n[{current_datetime.strftime('%H:%M:%S')}] Outside collection hours (4 AM - 8 PM ET on trading days)")
                        await asyncio.sleep(1800)  # Sleep 30 minutes outside collection hours

        except KeyboardInterrupt:
            self.logger.info("Shutting down calendar feed")
        finally:
            self.running = False
            await self.client.aclose()
            if self.questdb_conn:
                self.questdb_conn.close()

    async def stop(self):
        """Stop the collection process"""
        self.running = False
        await self.client.aclose()

    def display_market_status(self):
        """Display current market status and schedule"""
        current_datetime = datetime.now()
        current_date = current_datetime.date()

        print(f"Market Status - {current_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
        print("-" * 50)

        is_trading_day = self.market_schedule.is_trading_day(current_date)
        market_status = self.market_schedule.get_market_status(current_datetime)

        print(f"Today ({current_date}):")
        print(f"  Is trading day: {is_trading_day}")
        if not is_trading_day:
            if self.market_schedule.is_weekend(current_date):
                print(f"  Reason: Weekend")
            else:
                print(f"  Reason: Market holiday")
            next_trading = self.market_schedule.get_next_trading_day(current_date)
            print(f"  Next trading day: {next_trading}")

        print(f"  Market status: {market_status}")
        print(f"  Should collect: {self.market_schedule.should_collect_earnings_data(current_datetime)}")

        # Show next few trading days
        print(f"\\nNext 5 trading days:")
        trading_days = self.market_schedule.get_trading_days_in_range(
            current_date,
            current_date + timedelta(days=14)  # Look ahead 2 weeks to find 5 trading days
        )[:5]

        for day in trading_days:
            print(f"  {day} ({day.strftime('%A')})")

        print()


async def main():
    """Main function to run the calendar feed"""
    print("Unusual Whales Calendar Feed")
    print("=" * 60)
    print("Collecting economic calendar events every hour")
    print("Collecting FDA calendar events with 90-day lookahead")
    print("Filtering for liquid stocks with options (FDA)")
    print("Tracking Fed speakers, FOMC, and economic reports")
    print("Storing data in QuestDB for analysis")
    print("Press Ctrl+C to stop")
    print("-" * 60)

    feed = UnusualWhalesCalendarFeed()

    # Display market status
    print("\\n")
    feed.display_market_status()

    # Initialize QuestDB connection
    print("Initializing QuestDB connection...")
    try:
        await feed._init_questdb()
        print("QuestDB connection established successfully")
    except Exception as e:
        print(f"Warning: Could not connect to QuestDB: {e}")
        print("Continuing without database storage...")

    # Run once immediately for testing
    print("\\nRunning initial collection cycle...")
    await feed.run_collection_cycle()

    print("\\nStarting scheduled collection...")
    await feed.start_scheduled_collection()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\\n\\nCalendar feed stopped by user")
    except Exception as e:
        print(f"\\nError: {e}")
        exit(1)