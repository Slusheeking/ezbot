#!/usr/bin/env python3
"""
Unusual Whales Earnings Feed

Collects both premarket and afterhours earnings data from Unusual Whales API and stores in QuestDB.
Includes functionality to track upcoming earnings and historical performance.
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
class EarningsRecord:
    """Earnings record structure"""
    symbol: str
    report_date: str
    report_time: str
    actual_eps: Optional[str]
    street_mean_est: Optional[str]
    expected_move: Optional[str]
    expected_move_perc: Optional[str]
    full_name: str
    sector: str
    marketcap: Optional[str]
    has_options: Optional[bool]
    is_s_p_500: bool
    source: str
    pre_earnings_close: Optional[str]
    post_earnings_close: Optional[str]
    reaction: Optional[str]
    continent: str
    country_code: str
    country_name: str
    ending_fiscal_quarter: Optional[str]
    pre_earnings_date: Optional[str]
    post_earnings_date: Optional[str]
    earnings_type: str  # 'premarket' or 'afterhours'
    timestamp: datetime


class UnusualWhalesEarningsFeed:
    """Combined earnings data collector for Unusual Whales API"""

    def __init__(self, config_path: str = None):
        """Initialize the earnings feed"""
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
        logger = logging.getLogger('earnings_feed')
        logger.setLevel(getattr(logging, self.config['logging']['level']))

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

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
        """Create QuestDB tables for earnings data"""

        # Combined earnings table for both premarket and afterhours
        earnings_sql = """
        CREATE TABLE IF NOT EXISTS earnings (\n            timestamp TIMESTAMP,
            symbol SYMBOL CAPACITY 1000 CACHE,
            report_date DATE,
            report_time SYMBOL CAPACITY 20 CACHE,
            actual_eps DOUBLE,
            street_mean_est DOUBLE,
            expected_move DOUBLE,
            expected_move_perc DOUBLE,
            full_name STRING,
            sector SYMBOL CAPACITY 50 CACHE,
            marketcap LONG,
            has_options BOOLEAN,
            is_s_p_500 BOOLEAN,
            source SYMBOL CAPACITY 20 CACHE,
            pre_earnings_close DOUBLE,
            post_earnings_close DOUBLE,
            reaction DOUBLE,
            continent SYMBOL CAPACITY 50 CACHE,
            country_code SYMBOL CAPACITY 10 CACHE,
            ending_fiscal_quarter DATE,
            pre_earnings_date DATE,
            post_earnings_date DATE,
            earnings_type SYMBOL CAPACITY 20 CACHE,
            collected_at TIMESTAMP
        ) TIMESTAMP(timestamp) PARTITION BY DAY WAL;
        """

        # Historical earnings table for symbols
        historical_earnings_sql = """
        CREATE TABLE IF NOT EXISTS historical_earnings (
            timestamp TIMESTAMP,
            symbol SYMBOL CAPACITY 1000 CACHE,
            report_date DATE,
            report_time SYMBOL CAPACITY 20 CACHE,
            actual_eps DOUBLE,
            street_mean_est DOUBLE,
            ending_fiscal_quarter DATE,
            expected_move DOUBLE,
            expected_move_perc DOUBLE,
            post_earnings_move_1d DOUBLE,
            post_earnings_move_1w DOUBLE,
            post_earnings_move_2w DOUBLE,
            post_earnings_move_3d DOUBLE,
            pre_earnings_move_1d DOUBLE,
            pre_earnings_move_1w DOUBLE,
            pre_earnings_move_2w DOUBLE,
            pre_earnings_move_3d DOUBLE,
            long_straddle_1d DOUBLE,
            long_straddle_1w DOUBLE,
            short_straddle_1d DOUBLE,
            short_straddle_1w DOUBLE,
            source SYMBOL CAPACITY 20 CACHE,
            collected_at TIMESTAMP
        ) TIMESTAMP(timestamp) PARTITION BY DAY WAL;
        """

        cursor = self.questdb_conn.cursor()
        cursor.execute(earnings_sql)
        cursor.execute(historical_earnings_sql)
        self.questdb_conn.commit()
        cursor.close()

        self.logger.info("QuestDB earnings tables created successfully")

    async def get_earnings(self, earnings_type: str, date: str = None, limit: int = None, page: int = 0) -> List[EarningsRecord]:
        """
        Fetch earnings data from Unusual Whales API

        Args:
            earnings_type: 'premarket' or 'afterhours'
            date: Trading date in YYYY-MM-DD format (optional)
            limit: Number of items to return (1-100, default from config)
            page: Page number for pagination

        Returns:
            List of EarningsRecord objects
        """
        try:
            if earnings_type == 'premarket':
                endpoint = self.config['api']['premarket_endpoint']
            elif earnings_type == 'afterhours':
                endpoint = self.config['api']['afterhours_endpoint']
            else:
                raise ValueError(f"Invalid earnings_type: {earnings_type}")

            url = f"{self.config['api']['base_url']}{endpoint}"

            params = {}
            if date:
                params['date'] = date
            if limit:
                params['limit'] = min(limit, 100)  # API max is 100
            else:
                params['limit'] = self.config['collection']['default_limit']
            if page > 0:
                params['page'] = page

            self.logger.info(f"Fetching {earnings_type} earnings: {url} with params: {params}")

            response = await self.client.get(url, params=params)
            response.raise_for_status()

            data = response.json()

            if 'data' not in data:
                self.logger.warning("No 'data' field in API response")
                return []

            earnings = []
            current_time = datetime.now()

            for item in data['data']:
                # Apply filters
                if not self._passes_filters(item):
                    continue

                earning = EarningsRecord(
                    symbol=item.get('symbol', ''),
                    report_date=item.get('report_date', ''),
                    report_time=item.get('report_time', ''),
                    actual_eps=item.get('actual_eps'),
                    street_mean_est=item.get('street_mean_est'),
                    expected_move=item.get('expected_move'),
                    expected_move_perc=item.get('expected_move_perc'),
                    full_name=item.get('full_name', ''),
                    sector=item.get('sector', ''),
                    marketcap=item.get('marketcap'),
                    has_options=item.get('has_options'),
                    is_s_p_500=item.get('is_s_p_500', False),
                    source=item.get('source', ''),
                    pre_earnings_close=item.get('pre_earnings_close'),
                    post_earnings_close=item.get('post_earnings_close'),
                    reaction=item.get('reaction'),
                    continent=item.get('continent', ''),
                    country_code=item.get('country_code', ''),
                    country_name=item.get('country_name', ''),
                    ending_fiscal_quarter=item.get('ending_fiscal_quarter'),
                    pre_earnings_date=item.get('pre_earnings_date'),
                    post_earnings_date=item.get('post_earnings_date'),
                    earnings_type=earnings_type,
                    timestamp=current_time
                )
                earnings.append(earning)

            self.logger.info(f"Retrieved {len(earnings)} {earnings_type} earnings records")
            return earnings

        except httpx.HTTPError as e:
            self.logger.error(f"HTTP error fetching {earnings_type} earnings: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Error fetching {earnings_type} earnings: {e}")
            return []

    def _passes_filters(self, item: Dict) -> bool:
        """Apply filters to earnings data"""
        filters = self.config['filters']

        # Market cap filter
        if filters.get('min_market_cap'):
            marketcap = item.get('marketcap')
            if marketcap:
                try:
                    if float(marketcap) < filters['min_market_cap']:
                        return False
                except (ValueError, TypeError):
                    return False

        # Options requirement
        if filters.get('require_options', False):
            if not item.get('has_options', False):
                return False

        # Expected move filter
        if filters.get('min_expected_move_percent'):
            expected_move_perc = item.get('expected_move_perc')
            if expected_move_perc:
                try:
                    move_pct = float(expected_move_perc) * 100  # Convert to percentage
                    if move_pct < filters['min_expected_move_percent']:
                        return False
                except (ValueError, TypeError):
                    return False

        # Sector filter
        track_sectors = filters.get('track_sectors', [])
        if track_sectors:
            if item.get('sector', '') not in track_sectors:
                return False

        return True

    async def get_upcoming_earnings(self, days_ahead: int = 5) -> List[Dict]:
        """
        Get upcoming earnings for the next few days

        Args:
            days_ahead: Number of days to look ahead

        Returns:
            List of upcoming earnings
        """
        upcoming = []
        today = datetime.now().date()

        for i in range(1, days_ahead + 1):
            target_date = (today + timedelta(days=i)).strftime('%Y-%m-%d')

            # Get both premarket and afterhours for the date
            premarket = await self.get_earnings('premarket', date=target_date)
            afterhours = await self.get_earnings('afterhours', date=target_date)

            for earning in premarket + afterhours:
                upcoming.append({
                    'symbol': earning.symbol,
                    'report_date': earning.report_date,
                    'report_time': earning.report_time,
                    'earnings_type': earning.earnings_type,
                    'expected_move_perc': earning.expected_move_perc,
                    'sector': earning.sector,
                    'full_name': earning.full_name,
                    'has_options': earning.has_options,
                    'marketcap': earning.marketcap
                })

        return upcoming

    async def get_historical_earnings(self, symbol: str) -> List[Dict]:
        """
        Get historical earnings data for a specific symbol

        Args:
            symbol: Stock ticker symbol

        Returns:
            List of historical earnings data
        """
        try:
            url = f"{self.config['api']['base_url']}{self.config['api']['historical_endpoint']}/{symbol}"

            self.logger.info(f"Fetching historical earnings for {symbol}: {url}")

            response = await self.client.get(url)
            response.raise_for_status()

            data = response.json()
            return data.get('data', [])

        except httpx.HTTPError as e:
            self.logger.error(f"HTTP error fetching historical earnings for {symbol}: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Error fetching historical earnings for {symbol}: {e}")
            return []

    async def store_earnings_data(self, earnings: List[EarningsRecord]) -> bool:
        """Store earnings data in QuestDB"""
        if not earnings:
            return True

        if not self.questdb_conn:
            self.logger.error("QuestDB connection not initialized")
            return False

        cursor = self.questdb_conn.cursor()

        # Prepare insert SQL
        insert_sql = """
        INSERT INTO earnings (
            timestamp, symbol, report_date, report_time, actual_eps,
            street_mean_est, expected_move, expected_move_perc, full_name,
            sector, marketcap, has_options, is_s_p_500, source,
            pre_earnings_close, post_earnings_close, reaction,
            continent, country_code, country_name, ending_fiscal_quarter,
            pre_earnings_date, post_earnings_date, earnings_type, collected_at
        ) VALUES %s
        """

        # Convert dataclass objects to tuples for insertion
        values = []
        for earning in earnings:
            try:
                # Convert string values to appropriate types
                actual_eps = float(earning.actual_eps) if earning.actual_eps else None
                street_mean_est = float(earning.street_mean_est) if earning.street_mean_est else None
                expected_move = float(earning.expected_move) if earning.expected_move else None
                expected_move_perc = float(earning.expected_move_perc) if earning.expected_move_perc else None
                marketcap = int(float(earning.marketcap)) if earning.marketcap else None
                pre_earnings_close = float(earning.pre_earnings_close) if earning.pre_earnings_close else None
                post_earnings_close = float(earning.post_earnings_close) if earning.post_earnings_close else None
                reaction = float(earning.reaction) if earning.reaction else None

                values.append((
                    earning.timestamp,
                    earning.symbol,
                    earning.report_date,
                    earning.report_time,
                    actual_eps,
                    street_mean_est,
                    expected_move,
                    expected_move_perc,
                    earning.full_name,
                    earning.sector,
                    marketcap,
                    earning.has_options,
                    earning.is_s_p_500,
                    earning.source,
                    pre_earnings_close,
                    post_earnings_close,
                    reaction,
                    earning.continent,
                    earning.country_code,
                    earning.country_name,
                    earning.ending_fiscal_quarter,
                    earning.pre_earnings_date,
                    earning.post_earnings_date,
                    earning.earnings_type,
                    datetime.now()
                ))
            except Exception as e:
                self.logger.warning(f"Error processing earning record {earning.symbol}: {e}")
                continue

        try:
            if values:
                execute_values(cursor, insert_sql, values, template=None, page_size=100)
                self.questdb_conn.commit()
                self.logger.info(f"Stored {len(values)} earnings records in QuestDB")
            return True

        except Exception as e:
            self.logger.error(f"Error storing earnings data in QuestDB: {e}")
            self.questdb_conn.rollback()
            return False
        finally:
            cursor.close()

    async def store_historical_earnings(self, symbol: str, historical_data: List[Dict]) -> bool:
        """Store historical earnings data in QuestDB"""
        if not historical_data or not self.questdb_conn:
            return False

        cursor = self.questdb_conn.cursor()

        insert_sql = """
        INSERT INTO historical_earnings (
            timestamp, symbol, report_date, report_time, actual_eps,
            street_mean_est, ending_fiscal_quarter, expected_move,
            expected_move_perc, post_earnings_move_1d, post_earnings_move_1w,
            post_earnings_move_2w, post_earnings_move_3d, pre_earnings_move_1d,
            pre_earnings_move_1w, pre_earnings_move_2w, pre_earnings_move_3d,
            long_straddle_1d, long_straddle_1w, short_straddle_1d,
            short_straddle_1w, source, collected_at
        ) VALUES %s
        """

        values = []
        for record in historical_data:
            try:
                values.append((
                    datetime.now(),
                    symbol,
                    record.get('report_date'),
                    record.get('report_time'),
                    float(record.get('actual_eps')) if record.get('actual_eps') else None,
                    float(record.get('street_mean_est')) if record.get('street_mean_est') else None,
                    record.get('ending_fiscal_quarter'),
                    float(record.get('expected_move')) if record.get('expected_move') else None,
                    float(record.get('expected_move_perc')) if record.get('expected_move_perc') else None,
                    float(record.get('post_earnings_move_1d')) if record.get('post_earnings_move_1d') else None,
                    float(record.get('post_earnings_move_1w')) if record.get('post_earnings_move_1w') else None,
                    float(record.get('post_earnings_move_2w')) if record.get('post_earnings_move_2w') else None,
                    float(record.get('post_earnings_move_3d')) if record.get('post_earnings_move_3d') else None,
                    float(record.get('pre_earnings_move_1d')) if record.get('pre_earnings_move_1d') else None,
                    float(record.get('pre_earnings_move_1w')) if record.get('pre_earnings_move_1w') else None,
                    float(record.get('pre_earnings_move_2w')) if record.get('pre_earnings_move_2w') else None,
                    float(record.get('pre_earnings_move_3d')) if record.get('pre_earnings_move_3d') else None,
                    float(record.get('long_straddle_1d')) if record.get('long_straddle_1d') else None,
                    float(record.get('long_straddle_1w')) if record.get('long_straddle_1w') else None,
                    float(record.get('short_straddle_1d')) if record.get('short_straddle_1d') else None,
                    float(record.get('short_straddle_1w')) if record.get('short_straddle_1w') else None,
                    record.get('source', 'company'),
                    datetime.now()
                ))
            except Exception as e:
                self.logger.warning(f"Error processing historical record for {symbol}: {e}")
                continue

        try:
            if values:
                execute_values(cursor, insert_sql, values, template=None, page_size=100)
                self.questdb_conn.commit()
                self.logger.info(f"Stored {len(values)} historical earnings records for {symbol}")
            return True

        except Exception as e:
            self.logger.error(f"Error storing historical earnings: {e}")
            self.questdb_conn.rollback()
            return False
        finally:
            cursor.close()

    async def check_for_alerts(self, earnings: List[EarningsRecord]):
        """Check for significant earnings that should trigger alerts"""
        if not self.config['alerts']['enabled']:
            return

        alerts = []

        for earning in earnings:
            # High expected move alert
            if self.config['alerts']['high_expected_move']['enabled']:
                if earning.expected_move_perc:
                    try:
                        move_pct = float(earning.expected_move_perc) * 100
                        if move_pct >= self.config['alerts']['high_expected_move']['min_expected_move']:
                            alerts.append(f"HIGH MOVE: {earning.symbol} ({earning.earnings_type}) - {move_pct:.1f}% expected move")
                    except (ValueError, TypeError):
                        pass

        # Log alerts
        for alert in alerts:
            self.logger.warning(f"ALERT: {alert}")

    async def run_collection_cycle(self):
        """Run a single collection cycle for both premarket and afterhours"""
        try:
            self.logger.info("Starting earnings collection cycle")

            # Get today's premarket and afterhours earnings
            premarket_earnings = await self.get_earnings('premarket')
            afterhours_earnings = await self.get_earnings('afterhours')

            all_earnings = premarket_earnings + afterhours_earnings

            if all_earnings:
                # Store in database
                await self.store_earnings_data(all_earnings)

                # Check for alerts
                await self.check_for_alerts(all_earnings)

                # Log summary and print to console
                summary_msg = f"Collected {len(premarket_earnings)} premarket, {len(afterhours_earnings)} afterhours earnings"
                self.logger.info(summary_msg)
                print(f"[{datetime.now().strftime('%H:%M:%S')}] {summary_msg}")

                # Print key earnings by type
                if premarket_earnings:
                    print("\\nKey premarket earnings:")
                    for earning in premarket_earnings[:5]:
                        move = earning.expected_move_perc
                        if move:
                            try:
                                move_pct = float(move) * 100
                                print(f"  - {earning.symbol}: {move_pct:.1f}% expected move")
                            except:
                                print(f"  - {earning.symbol}")
                        else:
                            print(f"  - {earning.symbol}")

                if afterhours_earnings:
                    print("\\nKey afterhours earnings:")
                    for earning in afterhours_earnings[:5]:
                        move = earning.expected_move_perc
                        if move:
                            try:
                                move_pct = float(move) * 100
                                print(f"  - {earning.symbol}: {move_pct:.1f}% expected move")
                            except:
                                print(f"  - {earning.symbol}")
                        else:
                            print(f"  - {earning.symbol}")
            else:
                msg = "No earnings data collected"
                self.logger.info(msg)
                print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

        except Exception as e:
            error_msg = f"Error in collection cycle: {e}"
            self.logger.error(error_msg)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ERROR: {error_msg}")

    async def start_scheduled_collection(self):
        """Start the scheduled collection process"""
        self.logger.info("Starting Unusual Whales Earnings Feed")
        self.running = True

        # Initialize QuestDB connection
        await self._init_questdb()

        try:
            while self.running:
                current_datetime = datetime.now()
                current_time = current_datetime.time()
                current_date = current_datetime.date()
                premarket_time = time.fromisoformat(self.config['collection']['premarket_time'])
                afterhours_time = time.fromisoformat(self.config['collection']['afterhours_time'])

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
                    # PRODUCTION: Check if it's time to collect and we should collect earnings data
                    if not self.market_schedule.should_collect_earnings_data(current_datetime):
                        print(f"\\n[{current_datetime.strftime('%H:%M:%S')}] Outside collection hours (4 AM - 8 PM ET on trading days)")
                        await asyncio.sleep(1800)  # Sleep 30 minutes outside collection hours
                        continue

                    current_minutes = current_time.hour * 60 + current_time.minute
                    premarket_minutes = premarket_time.hour * 60 + premarket_time.minute
                    afterhours_minutes = afterhours_time.hour * 60 + afterhours_time.minute

                    if (abs(current_minutes - premarket_minutes) <= 1 or
                        abs(current_minutes - afterhours_minutes) <= 1):
                        collection_type = "premarket" if abs(current_minutes - premarket_minutes) <= 1 else "afterhours"
                        print(f"\\n[{current_datetime.strftime('%H:%M:%S')}] {collection_type.title()} collection time reached! Starting collection...")
                        await self.run_collection_cycle()
                        # Sleep for 2 minutes to avoid multiple collections
                        await asyncio.sleep(120)
                    else:
                        # Check at configured interval
                        check_interval = self.config['collection']['production_check_interval']
                        await asyncio.sleep(check_interval)

        except KeyboardInterrupt:
            self.logger.info("Shutting down earnings feed")
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
    """Main function to run the earnings feed"""
    print("Unusual Whales Earnings Feed")
    print("=" * 60)
    print("Collecting premarket earnings at 6:00 AM EST daily")
    print("Collecting afterhours earnings at 6:00 PM EST daily")
    print("Filtering for liquid stocks with options")
    print("Tracking expected moves and earnings surprises")
    print("Alerting on significant earnings events")
    print("Storing data in QuestDB for analysis")
    print("Press Ctrl+C to stop")
    print("-" * 60)

    feed = UnusualWhalesEarningsFeed()

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

    # Show and store upcoming earnings
    print("\\nGetting upcoming earnings...")
    days_ahead = feed.config['collection']['upcoming_earnings_days']
    max_display = feed.config['collection']['max_display_upcoming']
    
    # Collect all upcoming earnings as EarningsRecord objects for storage
    all_upcoming_earnings = []
    today = datetime.now().date()
    
    for i in range(1, days_ahead + 1):
        target_date = (today + timedelta(days=i)).strftime('%Y-%m-%d')
        # Get earnings records for storage
        premarket = await feed.get_earnings('premarket', date=target_date)
        afterhours = await feed.get_earnings('afterhours', date=target_date)
        all_upcoming_earnings.extend(premarket + afterhours)
    
    # Store upcoming earnings in database
    if all_upcoming_earnings:
        await feed.store_earnings_data(all_upcoming_earnings)
        print(f"Stored {len(all_upcoming_earnings)} upcoming earnings in database")
        
        # Display upcoming earnings
        print(f"Found {len(all_upcoming_earnings)} upcoming earnings in next {days_ahead} days:")
        for earning in all_upcoming_earnings[:max_display]:  # Show configured number
            move = earning.expected_move_perc
            if move:
                try:
                    move_pct = f"{float(move) * 100:.1f}%"
                except:
                    move_pct = "N/A"
            else:
                move_pct = "N/A"
            print(f"  - {earning.symbol} ({earning.earnings_type}) - {earning.report_date} - Expected move: {move_pct}")
    else:
        print("No upcoming earnings found")

    # Fetch and store historical data for upcoming earnings
    if all_upcoming_earnings:
        print("\\nFetching historical data for upcoming earnings...")
        max_historical = feed.config['collection']['max_historical_symbols']
        for earning in all_upcoming_earnings[:max_historical]:  # Get historical for configured number
            symbol = earning.symbol
            print(f"  Getting historical data for {symbol}...")
            historical = await feed.get_historical_earnings(symbol)
            if historical:
                await feed.store_historical_earnings(symbol, historical)
                print(f"    Stored {len(historical)} historical records for {symbol}")

    print(f"\\nStarting scheduled collection...")
    print("Monitoring for collection times...")
    await feed.start_scheduled_collection()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\\n\\nEarnings feed stopped by user")