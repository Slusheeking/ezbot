#!/usr/bin/env python3
"""
Unusual Whales Sector ETF Tide Feed
Sector ETF tide and flow data collection from Unusual Whales API for sector rotation strategies
"""

import os
import sys
import asyncio
import aiohttp
import yaml
import psycopg2
import numpy as np
import pandas as pd
from psycopg2.extras import execute_values
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import time
from dotenv import load_dotenv

# Add project root to Python path
sys.path.append('/home/ezb0t/ezbot')
from utils.market_time import market_time

# Load environment variables
load_dotenv('/home/ezb0t/ezbot/.env')

def load_settings():
    """Load settings from YAML file"""
    settings_path = Path(__file__).parent / "settings.yaml"
    try:
        with open(settings_path, 'r') as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        print(f"Settings file not found at {settings_path}")
        return None
    except yaml.YAMLError as e:
        print(f"Error parsing settings file: {e}")
        return None

class SectorETFTideFeedClient:
    """Unusual Whales Sector ETF Tide feed client for sector rotation data collection"""

    def __init__(self):
        # Load settings
        self.settings = load_settings()
        if not self.settings:
            raise ValueError("Failed to load settings")

        # Get API key from environment
        self.api_key = os.getenv('UNUSUAL_WHALES_API_KEY')
        if not self.api_key:
            raise ValueError("UNUSUAL_WHALES_API_KEY not found in environment variables")

        # API configuration
        self.api_config = self.settings.get('api', {}).get('unusual_whales', {})
        self.base_url = self.api_config.get('base_url', 'https://api.unusualwhales.com/api')
        self.timeout = self.api_config.get('timeout', 30)
        self.max_retries = self.api_config.get('max_retries', 3)
        self.retry_delay = self.api_config.get('retry_delay', 5)
        self.rate_limit_delay = self.api_config.get('rate_limit_delay', 1.0)

        # Collection configuration
        self.collection = self.settings.get('collection', {})
        self.sector_etfs = self.collection.get('sector_etfs', [])
        self.market_etfs = self.collection.get('market_etfs', [])
        self.all_etfs = self.sector_etfs + self.market_etfs

        # Processing configuration
        self.processing = self.settings.get('processing', {})
        self.tide_thresholds = self.processing.get('tide_thresholds', {})

        # QuestDB connection
        self.questdb_conn = None
        self.questdb_config = self.settings.get('questdb', {})

        # HTTP session
        self.session = None

        print(f"Sector ETF Tide Feed initialized with {len(self.all_etfs)} ETFs")

    async def __aenter__(self):
        # Initialize HTTP session
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout),
            headers={'Authorization': f'Bearer {self.api_key}'}
        )

        # Initialize QuestDB connection
        if self.questdb_config:
            try:
                await self._init_questdb()
            except Exception as e:
                print(f"Could not initialize QuestDB: {e}")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
        if self.questdb_conn:
            self.questdb_conn.close()

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

            # Create all required tables
            await self._create_tables()

        except Exception as e:
            print(f"Failed to connect to QuestDB: {e}")
            raise

    async def _create_tables(self):
        """Create QuestDB tables for ETF data"""

        tables = {
            'etf_tide': """
                CREATE TABLE IF NOT EXISTS etf_tide (
                    timestamp TIMESTAMP,
                    ticker SYMBOL CAPACITY 20 CACHE,
                    date STRING,
                    net_call_premium DOUBLE,
                    net_put_premium DOUBLE,
                    net_volume LONG,
                    tide_direction SYMBOL CAPACITY 10 CACHE,
                    tide_strength SYMBOL CAPACITY 15 CACHE,
                    collected_at TIMESTAMP
                ) TIMESTAMP(timestamp) PARTITION BY DAY WAL;
            """,

            'etf_holdings': """
                CREATE TABLE IF NOT EXISTS etf_holdings (
                    timestamp TIMESTAMP,
                    etf_ticker SYMBOL CAPACITY 20 CACHE,
                    holding_ticker SYMBOL CAPACITY 20 CACHE,
                    name STRING,
                    sector SYMBOL CAPACITY 30 CACHE,
                    shares LONG,
                    weight DOUBLE,
                    close_price DOUBLE,
                    volume LONG,
                    call_premium DOUBLE,
                    put_premium DOUBLE,
                    call_volume LONG,
                    put_volume LONG,
                    bullish_premium DOUBLE,
                    bearish_premium DOUBLE,
                    has_options BOOLEAN,
                    collected_at TIMESTAMP
                ) TIMESTAMP(timestamp) PARTITION BY DAY WAL;
            """,

            'etf_exposure': """
                CREATE TABLE IF NOT EXISTS etf_exposure (
                    timestamp TIMESTAMP,
                    ticker SYMBOL CAPACITY 20 CACHE,
                    etf SYMBOL CAPACITY 20 CACHE,
                    full_name STRING,
                    shares LONG,
                    weight DOUBLE,
                    last_price DOUBLE,
                    prev_price DOUBLE,
                    collected_at TIMESTAMP
                ) TIMESTAMP(timestamp) PARTITION BY DAY WAL;
            """,

            'etf_weights': """
                CREATE TABLE IF NOT EXISTS etf_weights (
                    timestamp TIMESTAMP,
                    etf_ticker SYMBOL CAPACITY 20 CACHE,
                    category_type SYMBOL CAPACITY 10 CACHE,
                    category_name SYMBOL CAPACITY 50 CACHE,
                    weight DOUBLE,
                    collected_at TIMESTAMP
                ) TIMESTAMP(timestamp) PARTITION BY DAY WAL;
            """,

            'etf_inflow_outflow': """
                CREATE TABLE IF NOT EXISTS etf_inflow_outflow (
                    timestamp TIMESTAMP,
                    ticker SYMBOL CAPACITY 20 CACHE,
                    date STRING,
                    change_volume LONG,
                    change_premium DOUBLE,
                    close_price DOUBLE,
                    volume LONG,
                    is_fomc BOOLEAN,
                    collected_at TIMESTAMP
                ) TIMESTAMP(timestamp) PARTITION BY DAY WAL;
            """
        }

        cursor = self.questdb_conn.cursor()
        try:
            for table_name, sql in tables.items():
                cursor.execute(sql)
                self.questdb_conn.commit()
                print(f"Created/verified table: {table_name}")
        except Exception as e:
            print(f"Error creating tables: {e}")
            self.questdb_conn.rollback()
            raise
        finally:
            cursor.close()

    async def _make_api_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Make API request to Unusual Whales with retry logic"""
        url = f"{self.base_url}/{endpoint}"

        for attempt in range(self.max_retries):
            try:
                await asyncio.sleep(self.rate_limit_delay)  # Rate limiting

                async with self.session.get(url, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 429:  # Rate limited
                        print(f"Rate limited, waiting {self.retry_delay * 2} seconds...")
                        await asyncio.sleep(self.retry_delay * 2)
                        continue
                    else:
                        print(f"API request failed with status {response.status}: {await response.text()}")

            except Exception as e:
                print(f"Attempt {attempt + 1} failed for {endpoint}: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
                else:
                    print(f"Failed to fetch {endpoint} after {self.max_retries} attempts")

        return None

    async def get_etf_tide_data(self, ticker: str, date: str = None) -> Optional[Dict]:
        """Get ETF tide data for a specific ticker"""
        endpoint = f"market/{ticker}/etf-tide"
        params = {}
        if date:
            params['date'] = date

        return await self._make_api_request(endpoint, params)

    async def get_etf_holdings(self, ticker: str) -> Optional[Dict]:
        """Get ETF holdings data"""
        endpoint = f"etfs/{ticker}/holdings"
        return await self._make_api_request(endpoint)

    async def get_etf_exposure(self, ticker: str) -> Optional[Dict]:
        """Get ETF exposure data"""
        endpoint = f"etfs/{ticker}/exposure"
        return await self._make_api_request(endpoint)

    async def get_etf_weights(self, ticker: str) -> Optional[Dict]:
        """Get ETF sector and country weights"""
        endpoint = f"etfs/{ticker}/weights"
        return await self._make_api_request(endpoint)

    async def get_etf_inflow_outflow(self, ticker: str) -> Optional[Dict]:
        """Get ETF inflow and outflow data"""
        endpoint = f"etfs/{ticker}/in-outflow"
        return await self._make_api_request(endpoint)

    def _analyze_tide_direction(self, net_call_premium: float, net_put_premium: float) -> Tuple[str, str]:
        """Analyze tide direction and strength based on premium flows"""
        net_premium = net_call_premium + net_put_premium

        # Determine direction
        if net_premium > self.tide_thresholds.get('neutral_high', 25000000):
            direction = 'bullish'
        elif net_premium < self.tide_thresholds.get('neutral_low', -25000000):
            direction = 'bearish'
        else:
            direction = 'neutral'

        # Determine strength
        abs_premium = abs(net_premium)
        if abs_premium > self.tide_thresholds.get('strong_bullish', 100000000):
            strength = 'strong'
        elif abs_premium > self.tide_thresholds.get('moderate_bullish', 50000000):
            strength = 'moderate'
        else:
            strength = 'weak'

        return direction, strength

    async def collect_all_etf_data(self) -> Dict[str, List[Dict]]:
        """Collect all ETF data for all configured ETFs"""
        print(f"Collecting data for {len(self.all_etfs)} ETFs...")

        all_data = {
            'tide': [],
            'holdings': [],
            'exposure': [],
            'weights': [],
            'inflow_outflow': []
        }

        current_time = datetime.now()

        for ticker in self.all_etfs:
            print(f"Processing {ticker}...")

            try:
                # Get ETF tide data
                if self.collection.get('include_tide', True):
                    tide_data = await self.get_etf_tide_data(ticker)
                    if tide_data and 'data' in tide_data:
                        for item in tide_data['data']:
                            # Safely convert to float, handling None values
                            net_call_premium = float(item.get('net_call_premium') or 0)
                            net_put_premium = float(item.get('net_put_premium') or 0)
                            net_volume = int(item.get('net_volume') or 0)

                            direction, strength = self._analyze_tide_direction(
                                net_call_premium, net_put_premium
                            )

                            processed_item = {
                                'ticker': ticker,
                                'timestamp': item.get('timestamp'),
                                'date': item.get('date'),
                                'net_call_premium': net_call_premium,
                                'net_put_premium': net_put_premium,
                                'net_volume': net_volume,
                                'tide_direction': direction,
                                'tide_strength': strength,
                                'collected_at': current_time
                            }
                            all_data['tide'].append(processed_item)

                # Get ETF holdings data
                if self.collection.get('include_holdings', True):
                    holdings_data = await self.get_etf_holdings(ticker)
                    if holdings_data and 'data' in holdings_data:
                        for holding in holdings_data['data']:
                            processed_holding = {
                                'etf_ticker': ticker,
                                'timestamp': current_time,
                                'holding_ticker': holding.get('ticker'),
                                'name': holding.get('name'),
                                'sector': holding.get('sector'),
                                'shares': int(holding.get('shares') or 0),
                                'weight': float(holding.get('weight') or 0),
                                'close_price': float(holding.get('close') or 0),
                                'volume': int(holding.get('volume') or 0),
                                'call_premium': float(holding.get('call_premium') or 0),
                                'put_premium': float(holding.get('put_premium') or 0),
                                'call_volume': int(holding.get('call_volume') or 0),
                                'put_volume': int(holding.get('put_volume') or 0),
                                'bullish_premium': float(holding.get('bullish_premium') or 0),
                                'bearish_premium': float(holding.get('bearish_premium') or 0),
                                'has_options': holding.get('has_options', False),
                                'collected_at': current_time
                            }
                            all_data['holdings'].append(processed_holding)

                # Get ETF exposure data
                if self.collection.get('include_exposure', True):
                    exposure_data = await self.get_etf_exposure(ticker)
                    if exposure_data and 'data' in exposure_data:
                        for exposure in exposure_data['data']:
                            processed_exposure = {
                                'ticker': ticker,
                                'timestamp': current_time,
                                'etf': exposure.get('etf'),
                                'full_name': exposure.get('full_name'),
                                'shares': int(exposure.get('shares') or 0),
                                'weight': float(exposure.get('weight') or 0),
                                'last_price': float(exposure.get('last_price') or 0),
                                'prev_price': float(exposure.get('prev_price') or 0),
                                'collected_at': current_time
                            }
                            all_data['exposure'].append(processed_exposure)

                # Get ETF weights data
                if self.collection.get('include_weights', True):
                    weights_data = await self.get_etf_weights(ticker)
                    if weights_data:
                        # Process sector weights
                        for sector in weights_data.get('sector', []):
                            processed_weight = {
                                'etf_ticker': ticker,
                                'timestamp': current_time,
                                'category_type': 'sector',
                                'category_name': sector.get('sector'),
                                'weight': float(sector.get('weight') or 0),
                                'collected_at': current_time
                            }
                            all_data['weights'].append(processed_weight)

                        # Process country weights
                        for country in weights_data.get('country', []):
                            processed_weight = {
                                'etf_ticker': ticker,
                                'timestamp': current_time,
                                'category_type': 'country',
                                'category_name': country.get('country'),
                                'weight': float(country.get('weight') or 0),
                                'collected_at': current_time
                            }
                            all_data['weights'].append(processed_weight)

                # Get ETF inflow/outflow data
                if self.collection.get('include_inflow_outflow', True):
                    inflow_data = await self.get_etf_inflow_outflow(ticker)
                    if inflow_data and 'data' in inflow_data:
                        for flow in inflow_data['data']:
                            processed_flow = {
                                'ticker': ticker,
                                'timestamp': current_time,
                                'date': flow.get('date'),
                                'change_volume': int(flow.get('change') or 0),
                                'change_premium': float(flow.get('change_prem') or 0),
                                'close_price': float(flow.get('close') or 0),
                                'volume': int(flow.get('volume') or 0),
                                'is_fomc': flow.get('is_fomc', False),
                                'collected_at': current_time
                            }
                            all_data['inflow_outflow'].append(processed_flow)

                print(f"  Successfully collected data for {ticker}")

            except Exception as e:
                print(f"Error collecting data for {ticker}: {e}")
                continue

        # Store all data in QuestDB
        if self.questdb_conn:
            await self._store_all_data(all_data)

        return all_data

    async def _store_all_data(self, all_data: Dict[str, List[Dict]]) -> bool:
        """Store all collected data in QuestDB"""
        cursor = self.questdb_conn.cursor()

        try:
            # Store tide data
            if all_data['tide']:
                await self._store_tide_data(all_data['tide'], cursor)

            # Store holdings data
            if all_data['holdings']:
                await self._store_holdings_data(all_data['holdings'], cursor)

            # Store exposure data
            if all_data['exposure']:
                await self._store_exposure_data(all_data['exposure'], cursor)

            # Store weights data
            if all_data['weights']:
                await self._store_weights_data(all_data['weights'], cursor)

            # Store inflow/outflow data
            if all_data['inflow_outflow']:
                await self._store_inflow_outflow_data(all_data['inflow_outflow'], cursor)

            self.questdb_conn.commit()
            print(f"Successfully stored all ETF data in QuestDB")
            return True

        except Exception as e:
            print(f"Error storing data in QuestDB: {e}")
            self.questdb_conn.rollback()
            return False
        finally:
            cursor.close()

    async def _store_tide_data(self, tide_data: List[Dict], cursor) -> None:
        """Store ETF tide data in QuestDB"""
        insert_sql = """
        INSERT INTO etf_tide (
            timestamp, ticker, date, net_call_premium, net_put_premium,
            net_volume, tide_direction, tide_strength, collected_at
        ) VALUES %s
        """

        values = []
        for data in tide_data:
            # Parse timestamp
            timestamp = data['timestamp']
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            if hasattr(timestamp, 'astimezone'):
                timestamp = timestamp.astimezone(timezone.utc).replace(tzinfo=None)

            collected_at = data['collected_at']
            if hasattr(collected_at, 'astimezone'):
                collected_at = collected_at.astimezone(timezone.utc).replace(tzinfo=None)

            values.append((
                timestamp,
                data['ticker'],
                data['date'],
                data['net_call_premium'],
                data['net_put_premium'],
                data['net_volume'],
                data['tide_direction'],
                data['tide_strength'],
                collected_at
            ))

        if values:
            execute_values(cursor, insert_sql, values, template=None, page_size=100)
            print(f"Stored {len(values)} ETF tide records")

    async def _store_holdings_data(self, holdings_data: List[Dict], cursor) -> None:
        """Store ETF holdings data in QuestDB"""
        insert_sql = """
        INSERT INTO etf_holdings (
            timestamp, etf_ticker, holding_ticker, name, sector, shares, weight,
            close_price, volume, call_premium, put_premium, call_volume,
            put_volume, bullish_premium, bearish_premium, has_options, collected_at
        ) VALUES %s
        """

        values = []
        for data in holdings_data:
            timestamp = data['timestamp']
            if hasattr(timestamp, 'astimezone'):
                timestamp = timestamp.astimezone(timezone.utc).replace(tzinfo=None)

            collected_at = data['collected_at']
            if hasattr(collected_at, 'astimezone'):
                collected_at = collected_at.astimezone(timezone.utc).replace(tzinfo=None)

            values.append((
                timestamp,
                data['etf_ticker'],
                data['holding_ticker'],
                data['name'],
                data['sector'],
                data['shares'],
                data['weight'],
                data['close_price'],
                data['volume'],
                data['call_premium'],
                data['put_premium'],
                data['call_volume'],
                data['put_volume'],
                data['bullish_premium'],
                data['bearish_premium'],
                data['has_options'],
                collected_at
            ))

        if values:
            execute_values(cursor, insert_sql, values, template=None, page_size=100)
            print(f"Stored {len(values)} ETF holdings records")

    async def _store_exposure_data(self, exposure_data: List[Dict], cursor) -> None:
        """Store ETF exposure data in QuestDB"""
        insert_sql = """
        INSERT INTO etf_exposure (
            timestamp, ticker, etf, full_name, shares, weight,
            last_price, prev_price, collected_at
        ) VALUES %s
        """

        values = []
        for data in exposure_data:
            timestamp = data['timestamp']
            if hasattr(timestamp, 'astimezone'):
                timestamp = timestamp.astimezone(timezone.utc).replace(tzinfo=None)

            collected_at = data['collected_at']
            if hasattr(collected_at, 'astimezone'):
                collected_at = collected_at.astimezone(timezone.utc).replace(tzinfo=None)

            values.append((
                timestamp,
                data['ticker'],
                data['etf'],
                data['full_name'],
                data['shares'],
                data['weight'],
                data['last_price'],
                data['prev_price'],
                collected_at
            ))

        if values:
            execute_values(cursor, insert_sql, values, template=None, page_size=100)
            print(f"Stored {len(values)} ETF exposure records")

    async def _store_weights_data(self, weights_data: List[Dict], cursor) -> None:
        """Store ETF weights data in QuestDB"""
        insert_sql = """
        INSERT INTO etf_weights (
            timestamp, etf_ticker, category_type, category_name, weight, collected_at
        ) VALUES %s
        """

        values = []
        for data in weights_data:
            timestamp = data['timestamp']
            if hasattr(timestamp, 'astimezone'):
                timestamp = timestamp.astimezone(timezone.utc).replace(tzinfo=None)

            collected_at = data['collected_at']
            if hasattr(collected_at, 'astimezone'):
                collected_at = collected_at.astimezone(timezone.utc).replace(tzinfo=None)

            values.append((
                timestamp,
                data['etf_ticker'],
                data['category_type'],
                data['category_name'],
                data['weight'],
                collected_at
            ))

        if values:
            execute_values(cursor, insert_sql, values, template=None, page_size=100)
            print(f"Stored {len(values)} ETF weights records")

    async def _store_inflow_outflow_data(self, inflow_data: List[Dict], cursor) -> None:
        """Store ETF inflow/outflow data in QuestDB"""
        insert_sql = """
        INSERT INTO etf_inflow_outflow (
            timestamp, ticker, date, change_volume, change_premium,
            close_price, volume, is_fomc, collected_at
        ) VALUES %s
        """

        values = []
        for data in inflow_data:
            timestamp = data['timestamp']
            if hasattr(timestamp, 'astimezone'):
                timestamp = timestamp.astimezone(timezone.utc).replace(tzinfo=None)

            collected_at = data['collected_at']
            if hasattr(collected_at, 'astimezone'):
                collected_at = collected_at.astimezone(timezone.utc).replace(tzinfo=None)

            values.append((
                timestamp,
                data['ticker'],
                data['date'],
                data['change_volume'],
                data['change_premium'],
                data['close_price'],
                data['volume'],
                data['is_fomc'],
                collected_at
            ))

        if values:
            execute_values(cursor, insert_sql, values, template=None, page_size=100)
            print(f"Stored {len(values)} ETF inflow/outflow records")

    async def start_scheduled_collection(self):
        """Start scheduled collection service with market-aware intervals"""
        print("Sector ETF Tide feed scheduled collection started")
        print(f"Starting at: {datetime.now().isoformat()}")

        while True:
            try:
                # Get market status and appropriate interval
                status = market_time.get_market_status()

                if status == "MARKET_OPEN":
                    sleep_seconds = self.collection.get('market_hours_interval', 300)  # 5 minutes
                elif status in ["PRE_MARKET", "AFTER_HOURS"]:
                    sleep_seconds = self.collection.get('after_hours_interval', 900)  # 15 minutes
                else:  # CLOSED/WEEKEND
                    sleep_seconds = self.collection.get('weekend_interval', 1800)  # 30 minutes

                interval_minutes = sleep_seconds // 60

                print(f"\n[{datetime.now().isoformat()}] {status} - Collecting ETF data...")

                etf_data = await self.collect_all_etf_data()

                if etf_data:
                    total_records = sum(len(data) for data in etf_data.values())
                    print(f"Collected {total_records} total ETF data records")
                else:
                    print("No ETF data collected")

                # Wait for next collection
                print(f"Next collection in {interval_minutes} minutes ({status})...")
                await asyncio.sleep(sleep_seconds)

            except Exception as e:
                print(f"Error in ETF scheduled collection: {e}")
                print("Retrying in 5 minutes...")
                await asyncio.sleep(300)

async def main():
    """Run Sector ETF Tide feed - scheduled collection or one-time display"""
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--scheduled":
        # Run scheduled collection for systemd service
        async with SectorETFTideFeedClient() as client:
            await client.start_scheduled_collection()
    else:
        # Display ETF data (manual mode)
        async with SectorETFTideFeedClient() as client:
            print("\n" + "="*80)
            print(" SECTOR ETF TIDE FEED")
            print("="*80)
            print(f" Timestamp: {datetime.now().isoformat()}")
            print("="*80)

            etf_data = await client.collect_all_etf_data()

            if not etf_data or not any(etf_data.values()):
                print("\nNo ETF data found.")
                return

            total_records = sum(len(data) for data in etf_data.values())
            print(f"\nTotal ETF data records: {total_records}\n")
            print("-"*80)

            # Display tide data summary
            if etf_data['tide']:
                print("\nETF TIDE SUMMARY:")
                tide_summary = {}
                for tide in etf_data['tide']:
                    ticker = tide['ticker']
                    if ticker not in tide_summary:
                        tide_summary[ticker] = {
                            'net_call': 0,
                            'net_put': 0,
                            'net_volume': 0,
                            'direction': tide['tide_direction'],
                            'strength': tide['tide_strength']
                        }
                    tide_summary[ticker]['net_call'] += tide['net_call_premium']
                    tide_summary[ticker]['net_put'] += tide['net_put_premium']
                    tide_summary[ticker]['net_volume'] += tide['net_volume']

                for ticker, summary in tide_summary.items():
                    net_premium = summary['net_call'] + summary['net_put']
                    print(f"{ticker:>6} | Net Premium: ${net_premium:>12,.0f} | Volume: {summary['net_volume']:>8,} | {summary['direction'].upper()} ({summary['strength']})")

            # Display sector holdings summary
            if etf_data['holdings']:
                print(f"\nETF HOLDINGS: {len(etf_data['holdings'])} records collected")
                sector_summary = {}
                for holding in etf_data['holdings']:
                    sector = holding['sector'] or 'Unknown'
                    if sector not in sector_summary:
                        sector_summary[sector] = {'count': 0, 'total_weight': 0}
                    sector_summary[sector]['count'] += 1
                    sector_summary[sector]['total_weight'] += holding['weight']

                print("\nSECTOR BREAKDOWN:")
                for sector, data in sorted(sector_summary.items(), key=lambda x: x[1]['total_weight'], reverse=True)[:10]:
                    print(f"{sector:>25} | Holdings: {data['count']:>3} | Total Weight: {data['total_weight']:>6.2f}%")

if __name__ == "__main__":
    asyncio.run(main())