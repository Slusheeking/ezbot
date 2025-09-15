#!/usr/bin/env python3
"""
Yahoo Finance VIX Feed
VIX volatility data collection from Yahoo Finance for trading strategies
"""

import os
import sys
import asyncio
import argparse
import yfinance as yf
import yaml
import psycopg2
import numpy as np
import pandas as pd
from psycopg2.extras import execute_values
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional
from pathlib import Path
import time

# Add project root to Python path
sys.path.append('/home/ezb0t/ezbot')
from utils.market_time import market_time

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

class VIXFeedClient:
    """Yahoo Finance VIX feed client for volatility data collection"""

    def __init__(self):
        # Load settings
        self.settings = load_settings()
        if not self.settings:
            raise ValueError("Failed to load settings")

        # Yahoo Finance configuration
        self.yf_config = self.settings.get('api', {}).get('yfinance', {})
        self.timeout = self.yf_config.get('timeout', 30)
        self.max_retries = self.yf_config.get('max_retries', 3)
        self.retry_delay = self.yf_config.get('retry_delay', 5)

        # Collection configuration
        self.collection = self.settings.get('collection', {})
        self.vix_indices = self.collection.get('vix_indices', [])
        self.vix_products = self.collection.get('vix_products', [])
        self.all_symbols = self.vix_indices + self.vix_products

        # Processing configuration
        self.processing = self.settings.get('processing', {})
        self.vix_levels = self.processing.get('vix_levels', {})
        self.term_structure = self.processing.get('term_structure', {})

        # QuestDB connection
        self.questdb_conn = None
        self.questdb_config = self.settings.get('questdb', {})

        print(f"VIX Feed initialized with {len(self.all_symbols)} symbols")

    async def __aenter__(self):
        # Initialize QuestDB connection
        if self.questdb_config:
            try:
                await self._init_questdb()
            except Exception as e:
                print(f"Could not initialize QuestDB: {e}")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
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

            # Create VIX data table
            await self._create_vix_table()

        except Exception as e:
            print(f"Failed to connect to QuestDB: {e}")
            raise

    async def _create_vix_table(self):
        """Create QuestDB table for VIX data"""

        vix_table_sql = """
        CREATE TABLE IF NOT EXISTS vix (
            timestamp TIMESTAMP,
            symbol SYMBOL CAPACITY 20 CACHE,
            open_price DOUBLE,
            high_price DOUBLE,
            low_price DOUBLE,
            close_price DOUBLE,
            price DOUBLE,
            volume LONG,
            change DOUBLE,
            change_percent DOUBLE,
            high_52w DOUBLE,
            low_52w DOUBLE,
            percentile_rank DOUBLE,
            vix_regime SYMBOL CAPACITY 10 CACHE,
            collected_at TIMESTAMP
        ) TIMESTAMP(timestamp) PARTITION BY DAY WAL;
        """

        cursor = self.questdb_conn.cursor()
        try:
            cursor.execute(vix_table_sql)
            self.questdb_conn.commit()
            print("VIX data table created successfully")
        except Exception as e:
            print(f"Error creating VIX data table: {e}")
            self.questdb_conn.rollback()
            raise
        finally:
            cursor.close()

    async def get_vix_data(self) -> List[Dict]:
        """Get VIX data from Yahoo Finance"""
        print(f"Fetching VIX data for {len(self.all_symbols)} symbols...")

        vix_data = []
        current_time = datetime.now()

        # Get collection parameters
        period = self.collection.get('period', '1d')
        interval = self.collection.get('interval', '5m')

        for symbol in self.all_symbols:
            for attempt in range(self.max_retries):
                try:
                    print(f"Fetching data for {symbol}...")

                    # Create ticker object
                    ticker = yf.Ticker(symbol)

                    # Get current data
                    hist = ticker.history(
                        period=period,
                        interval=interval,
                        auto_adjust=self.yf_config.get('auto_adjust', True),
                        prepost=self.yf_config.get('prepost', False)
                    )

                    if hist.empty:
                        print(f"No data received for {symbol}")
                        break

                    # Get the latest data point
                    latest = hist.iloc[-1]
                    latest_time = hist.index[-1]

                    # Calculate additional metrics
                    processed_data = await self._process_vix_data(symbol, latest, hist, latest_time)
                    if processed_data:
                        vix_data.append(processed_data)

                    print(f"  Successfully fetched data for {symbol}: {latest['Close']:.2f}")
                    break

                except Exception as e:
                    print(f"Attempt {attempt + 1} failed for {symbol}: {e}")
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay)
                    else:
                        print(f"Failed to fetch data for {symbol} after {self.max_retries} attempts")

        print(f"Successfully collected data for {len(vix_data)} symbols")

        # Store in QuestDB if available
        if self.questdb_conn and vix_data:
            print("Storing VIX data in QuestDB...")
            await self._store_vix_data(vix_data)
        elif not self.questdb_conn:
            print("QuestDB connection not available - skipping storage")

        return vix_data

    async def _process_vix_data(self, symbol: str, latest_data, hist_data, timestamp) -> Optional[Dict]:
        """Process and enrich VIX data"""
        try:
            # Basic OHLCV data
            open_price = float(latest_data['Open'])
            high_price = float(latest_data['High'])
            low_price = float(latest_data['Low'])
            close_price = float(latest_data['Close'])
            volume = int(latest_data['Volume']) if not pd.isna(latest_data['Volume']) else 0

            # Calculate change
            if len(hist_data) > 1:
                prev_close = float(hist_data.iloc[-2]['Close'])
                change = close_price - prev_close
                change_percent = (change / prev_close) * 100 if prev_close != 0 else 0
            else:
                change = 0
                change_percent = 0

            # Calculate 52-week high/low
            year_data = hist_data.tail(252 * 78)  # Approximate 1 year of 5-min data
            if len(year_data) > 0:
                high_52w = float(year_data['High'].max())
                low_52w = float(year_data['Low'].min())

                # Calculate percentile rank
                if high_52w != low_52w:
                    percentile_rank = (close_price - low_52w) / (high_52w - low_52w) * 100
                else:
                    percentile_rank = 50.0
            else:
                high_52w = high_price
                low_52w = low_price
                percentile_rank = 50.0

            # Determine VIX regime (only for VIX indices)
            vix_regime = 'unknown'
            if symbol.startswith('^VIX'):
                if close_price < self.vix_levels.get('low', 15):
                    vix_regime = 'low'
                elif close_price < self.vix_levels.get('medium', 25):
                    vix_regime = 'medium'
                elif close_price < self.vix_levels.get('high', 35):
                    vix_regime = 'high'
                else:
                    vix_regime = 'extreme'

            return {
                'symbol': symbol,
                'timestamp': timestamp,
                'open_price': open_price,
                'high_price': high_price,
                'low_price': low_price,
                'close_price': close_price,
                'price': close_price,  # Alias for close_price
                'volume': volume,
                'change': change,
                'change_percent': change_percent,
                'high_52w': high_52w,
                'low_52w': low_52w,
                'percentile_rank': percentile_rank,
                'vix_regime': vix_regime,
                'collected_at': datetime.now()
            }

        except Exception as e:
            print(f"Error processing data for {symbol}: {e}")
            return None

    async def _store_vix_data(self, vix_data: List[Dict]) -> bool:
        """Store VIX data in QuestDB"""
        if not vix_data or not self.questdb_conn:
            return True

        cursor = self.questdb_conn.cursor()

        insert_sql = """
        INSERT INTO vix (
            timestamp, symbol, open_price, high_price, low_price, close_price,
            price, volume, change, change_percent, high_52w, low_52w,
            percentile_rank, vix_regime, collected_at
        ) VALUES %s
        """

        values = []

        for data in vix_data:
            try:
                # Convert timezone-aware timestamps to UTC naive timestamps
                timestamp = data['timestamp']
                if hasattr(timestamp, 'tz_localize'):
                    timestamp = timestamp.tz_convert('UTC').tz_localize(None)
                elif hasattr(timestamp, 'astimezone'):
                    timestamp = timestamp.astimezone(timezone.utc).replace(tzinfo=None)

                collected_at = data['collected_at']
                if hasattr(collected_at, 'astimezone'):
                    collected_at = collected_at.astimezone(timezone.utc).replace(tzinfo=None)

                values.append((
                    timestamp,
                    data['symbol'],
                    data['open_price'],
                    data['high_price'],
                    data['low_price'],
                    data['close_price'],
                    data['price'],
                    data['volume'],
                    data['change'],
                    data['change_percent'],
                    data['high_52w'],
                    data['low_52w'],
                    data['percentile_rank'],
                    data['vix_regime'],
                    collected_at
                ))
            except Exception as e:
                print(f"Error processing VIX data point: {e}")
                continue

        try:
            if values:
                batch_size = self.questdb_config.get('batch_size', 50)
                execute_values(cursor, insert_sql, values, template=None, page_size=batch_size)
                self.questdb_conn.commit()
                print(f"Stored {len(values)} VIX data points in QuestDB")
            return True

        except Exception as e:
            print(f"Error storing VIX data in QuestDB: {e}")
            self.questdb_conn.rollback()
            return False
        finally:
            cursor.close()


    async def display_vix_data(self):
        """Display VIX data in manual mode"""
        print("=" * 80)
        print("VIX VOLATILITY DATA")
        print("=" * 80)

        vix_data = await self.get_vix_data()

        if not vix_data:
            print("No VIX data available")
            return

        # Sort by symbol for consistent display
        vix_data.sort(key=lambda x: x['symbol'])

        print(f"\nData collected at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("-" * 80)

        for data in vix_data:
            symbol = data['symbol']
            price = data['price']
            change = data['change']
            change_pct = data['change_percent']
            regime = data.get('vix_regime', 'N/A')
            percentile = data.get('percentile_rank', 0)

            # Format change display
            change_sign = "+" if change >= 0 else ""
            change_color = "↑" if change >= 0 else "↓"

            print(f"{symbol:<12} {price:>8.2f} {change_sign}{change:>7.2f} ({change_sign}{change_pct:>5.1f}%) {change_color}")

            if symbol.startswith('^VIX'):
                print(f"             Regime: {regime:<8} Percentile: {percentile:>5.1f}%")

            print()

        # Display market summary
        vix_main = next((d for d in vix_data if d['symbol'] == '^VIX'), None)
        if vix_main:
            print("-" * 80)
            print("MARKET VOLATILITY SUMMARY")
            print("-" * 80)

            regime = vix_main.get('vix_regime', 'unknown')
            price = vix_main['price']

            if regime == 'low':
                summary = f"Low volatility environment (VIX: {price:.2f})"
            elif regime == 'medium':
                summary = f"Moderate volatility environment (VIX: {price:.2f})"
            elif regime == 'high':
                summary = f"High volatility environment (VIX: {price:.2f})"
            elif regime == 'extreme':
                summary = f"Extreme volatility environment (VIX: {price:.2f})"
            else:
                summary = f"Current VIX level: {price:.2f}"

            print(summary)

            # Term structure info if available
            ts_ratio = vix_main.get('term_structure_ratio')
            ts_type = vix_main.get('term_structure_type', 'unknown')

            if ts_ratio and ts_type != 'unknown':
                print(f"Term structure: {ts_type} (ratio: {ts_ratio:.3f})")

        print("=" * 80)

    async def start_scheduled_collection(self):
        """Start scheduled collection service with market-aware intervals"""
        print("VIX feed scheduled collection started")
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

                print(f"\n[{datetime.now().isoformat()}] {status} - Collecting VIX data...")

                vix_data = await self.get_vix_data()

                if vix_data:
                    print(f"Collected VIX data for {len(vix_data)} symbols")
                else:
                    print("No VIX data collected")

                # Wait for next collection
                print(f"Next collection in {interval_minutes} minutes ({status})...")
                await asyncio.sleep(sleep_seconds)

            except Exception as e:
                print(f"Error in VIX scheduled collection: {e}")
                print("Retrying in 5 minutes...")
                await asyncio.sleep(300)

async def main():
    """Main function - run VIX feed in scheduled or manual mode"""
    parser = argparse.ArgumentParser(description='VIX Volatility Feed Collector')
    parser.add_argument('--scheduled', action='store_true',
                        help='Run in scheduled collection mode (default: manual display mode)')

    args = parser.parse_args()

    async with VIXFeedClient() as client:
        if args.scheduled:
            print("Running VIX feed in scheduled collection mode...")
            await client.start_scheduled_collection()
        else:
            print("Running VIX feed in manual display mode...")
            await client.display_vix_data()

if __name__ == "__main__":
    asyncio.run(main())