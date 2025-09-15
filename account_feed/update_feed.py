#!/usr/bin/env python3
"""
Trade Updates Feed Monitor
Real-time trade execution and account activity tracking for Alpaca paper trading
"""

import os
import sys
import asyncio
import aiohttp
import yaml
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dotenv import load_dotenv
from pathlib import Path
import json

# Add project root to Python path
sys.path.append('/home/ezb0t/ezbot')
from utils.market_time import market_time

# Load environment variables from specific path
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

def parse_timestamp(timestamp_str: str) -> Optional[datetime]:
    """Parse timestamp string to datetime object"""
    if not timestamp_str:
        return None

    try:
        # Handle different timestamp formats
        if 'T' in timestamp_str:
            # Remove timezone info and parse
            clean_timestamp = timestamp_str.replace('Z', '').split('+')[0].split('-')[0] if '+' in timestamp_str or timestamp_str.endswith('Z') else timestamp_str
            return datetime.fromisoformat(clean_timestamp.replace('Z', ''))
        return None
    except Exception as e:
        print(f"Error parsing timestamp {timestamp_str}: {e}")
        return None

class UpdateFeedClient:
    """Alpaca trade updates monitoring client"""

    def __init__(self):
        # Load settings
        self.settings = load_settings()

        # Alpaca API credentials from environment
        self.api_key = os.getenv('ALPACA_API_KEY')
        self.secret_key = os.getenv('ALPACA_SECRET_KEY')
        self.paper_trading = os.getenv('ALPACA_PAPER_TRADING', 'true').lower() == 'true'

        # API URL
        self.base_url = "https://paper-api.alpaca.markets" if self.paper_trading else "https://api.alpaca.markets"

        print(f"Initializing Alpaca trade updates feed (Paper Trading: {self.paper_trading})")

        # QuestDB connection
        self.questdb_conn = None
        self.questdb_config = self.settings.get('questdb') if self.settings else None

        # HTTP session
        self.session = None

        # Last checked timestamp for incremental updates
        self.last_checked = None

        # Get update intervals from settings
        self.update_intervals = self.settings.get('update_intervals', {}) if self.settings else {}

    async def __aenter__(self):
        # Create HTTP session
        headers = {
            'APCA-API-KEY-ID': self.api_key,
            'APCA-API-SECRET-KEY': self.secret_key,
            'Accept': 'application/json'
        }
        self.session = aiohttp.ClientSession(headers=headers)

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

            # Create trade updates table
            await self._create_trade_updates_table()

        except Exception as e:
            print(f"Failed to connect to QuestDB: {e}")
            raise

    async def _create_trade_updates_table(self):
        """Create QuestDB table for trade updates"""

        trade_updates_sql = """
        CREATE TABLE IF NOT EXISTS trade_updates (
            timestamp TIMESTAMP,
            event_type STRING,
            event_id STRING,
            execution_id STRING,
            order_id STRING,
            client_order_id STRING,
            symbol SYMBOL CAPACITY 1000 CACHE,
            asset_id STRING,
            asset_class STRING,
            side STRING,
            order_type STRING,
            time_in_force STRING,
            order_status STRING,
            qty DOUBLE,
            filled_qty DOUBLE,
            price DOUBLE,
            filled_avg_price DOUBLE,
            limit_price DOUBLE,
            stop_price DOUBLE,
            position_qty DOUBLE,
            notional DOUBLE,
            commission DOUBLE,
            extended_hours BOOLEAN,
            order_class STRING,
            submitted_at TIMESTAMP,
            filled_at TIMESTAMP,
            canceled_at TIMESTAMP,
            expired_at TIMESTAMP,
            failed_at TIMESTAMP,
            replaced_at TIMESTAMP,
            legs_data STRING,
            trail_percent DOUBLE,
            trail_price DOUBLE,
            collected_at TIMESTAMP
        ) TIMESTAMP(timestamp) PARTITION BY DAY WAL;
        """

        cursor = self.questdb_conn.cursor()
        try:
            cursor.execute(trade_updates_sql)
            self.questdb_conn.commit()
            print("Trade updates table created successfully")
        except Exception as e:
            print(f"Error creating trade updates table: {e}")
            self.questdb_conn.rollback()
            raise
        finally:
            cursor.close()

    async def get_account_activities(self) -> List[Dict]:
        """Get account activities from Alpaca REST API"""
        try:
            # Build URL for account activities
            url = f"{self.base_url}/v2/account/activities"

            # Set parameters for filtering
            params = {
                'activity_types': 'FILL,TRANS,DIV,ACATC,ACATS',  # Focus on trading activities
                'page_size': 100
            }

            # Add date filter if we have a last checked timestamp
            if self.last_checked:
                params['after'] = self.last_checked.isoformat()

            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    activities = await response.json()
                    return activities if activities else []
                else:
                    print(f"Error fetching account activities: {response.status}")
                    error_text = await response.text()
                    print(f"Response: {error_text}")
                    return []

        except Exception as e:
            print(f"Error fetching account activities: {e}")
            return []

    def _process_trade_update_from_activity(self, activity: Dict) -> Optional[Dict]:
        """Process account activity into trade update format"""
        try:
            activity_type = activity.get('activity_type', '')

            # Only process FILL activities (actual trades)
            if activity_type != 'FILL':
                return None

            # Extract activity data
            activity_date = activity.get('date', '')
            order_id = activity.get('order_id', '')
            symbol = activity.get('symbol', '')
            side = activity.get('side', '')
            qty = float(activity.get('qty', 0))
            price = float(activity.get('price', 0))

            # Generate event details
            current_time = datetime.now()
            event_id = f"activity_{activity.get('id', '')}"

            processed_update = {
                "timestamp": current_time,
                "event_type": "fill",
                "event_id": event_id,
                "execution_id": activity.get('id', ''),
                "order_id": order_id,
                "client_order_id": "",
                "symbol": symbol,
                "asset_id": "",
                "asset_class": "us_equity",
                "side": side.lower() if side else '',
                "order_type": "market",  # Default since not provided in activities
                "time_in_force": "day",   # Default since not provided in activities
                "order_status": "filled",
                "qty": qty,
                "filled_qty": qty,
                "price": price,
                "filled_avg_price": price,
                "limit_price": 0.0,
                "stop_price": 0.0,
                "position_qty": 0.0,
                "notional": qty * price,
                "commission": 0.0,  # Not provided in activities
                "extended_hours": False,
                "order_class": "",
                "submitted_at": parse_timestamp(activity_date),
                "filled_at": parse_timestamp(activity_date),
                "canceled_at": None,
                "expired_at": None,
                "failed_at": None,
                "replaced_at": None,
                "legs_data": "",
                "trail_percent": 0.0,
                "trail_price": 0.0,
                "collected_at": current_time
            }

            return processed_update

        except Exception as e:
            print(f"Error processing activity: {e}")
            return None

    async def _store_trade_updates_data(self, trade_updates: List[Dict]) -> bool:
        """Store trade updates data in QuestDB"""
        if not trade_updates or not self.questdb_conn:
            return True

        cursor = self.questdb_conn.cursor()

        insert_sql = """
        INSERT INTO trade_updates (
            timestamp, event_type, event_id, execution_id, order_id, client_order_id,
            symbol, asset_id, asset_class, side, order_type, time_in_force, order_status,
            qty, filled_qty, price, filled_avg_price, limit_price, stop_price, position_qty,
            notional, commission, extended_hours, order_class, submitted_at, filled_at,
            canceled_at, expired_at, failed_at, replaced_at, legs_data, trail_percent,
            trail_price, collected_at
        ) VALUES %s
        """

        values = []
        for update in trade_updates:
            try:
                values.append((
                    update['timestamp'],
                    update['event_type'],
                    update['event_id'],
                    update['execution_id'],
                    update['order_id'],
                    update['client_order_id'],
                    update['symbol'],
                    update['asset_id'],
                    update['asset_class'],
                    update['side'],
                    update['order_type'],
                    update['time_in_force'],
                    update['order_status'],
                    update['qty'],
                    update['filled_qty'],
                    update['price'],
                    update['filled_avg_price'],
                    update['limit_price'],
                    update['stop_price'],
                    update['position_qty'],
                    update['notional'],
                    update['commission'],
                    update['extended_hours'],
                    update['order_class'],
                    update['submitted_at'],
                    update['filled_at'],
                    update['canceled_at'],
                    update['expired_at'],
                    update['failed_at'],
                    update['replaced_at'],
                    update['legs_data'],
                    update['trail_percent'],
                    update['trail_price'],
                    update['collected_at']
                ))
            except Exception as e:
                print(f"Error processing update for storage: {e}")
                continue

        try:
            if values:
                batch_size = self.questdb_config.get('batch_size', 100)
                execute_values(cursor, insert_sql, values, template=None, page_size=batch_size)
                self.questdb_conn.commit()
                print(f"Stored {len(values)} trade updates in QuestDB")
            return True

        except Exception as e:
            print(f"Error storing trade updates in QuestDB: {e}")
            self.questdb_conn.rollback()
            return False
        finally:
            cursor.close()

    async def get_trade_updates_data(self) -> List[Dict]:
        """Get trade updates data from Alpaca account activities"""
        try:
            print(f"Collecting trade updates data...")

            activities = await self.get_account_activities()

            if not activities:
                print("No new activities found")
                return []

            trade_updates = []
            for activity in activities:
                update = self._process_trade_update_from_activity(activity)
                if update:
                    trade_updates.append(update)

            print(f"Successfully collected {len(trade_updates)} trade updates")

            # Store in QuestDB if available
            if self.questdb_conn and trade_updates:
                await self._store_trade_updates_data(trade_updates)

            # Update last checked timestamp
            if trade_updates:
                self.last_checked = datetime.now()

            return trade_updates

        except Exception as e:
            print(f"Error collecting trade updates: {e}")
            return []

    def _check_trade_update_alerts(self, trade_updates: List[Dict]):
        """Check for trade update alerts and notifications"""
        if not trade_updates:
            return

        # Get alert thresholds from settings
        thresholds = self.settings.get('trade_monitoring', {}).get('alert_thresholds', {}) if self.settings else {}

        for update in trade_updates:
            # Large trade alert
            notional = update.get('notional', 0)
            if notional > thresholds.get('large_trade_amount', 10000):
                print(f"🚨 LARGE TRADE ALERT: {update['symbol']} - ${notional:,.2f}")

            # New symbol alert
            symbol = update.get('symbol', '')
            if symbol and len(symbol) > 0:
                print(f"📊 Trade executed: {symbol} {update['side'].upper()} {update['qty']} @ ${update['price']:.4f}")

    def print_trade_updates_summary(self, trade_updates: List[Dict]):
        """Print trade updates summary statistics"""
        if not trade_updates:
            print("No trade updates to summarize")
            return

        total_notional = sum(update.get('notional', 0) for update in trade_updates)
        symbols = set(update.get('symbol', '') for update in trade_updates)
        buy_count = len([u for u in trade_updates if u.get('side', '').lower() == 'buy'])
        sell_count = len([u for u in trade_updates if u.get('side', '').lower() == 'sell'])

        print("\n" + "="*80)
        print(" TRADE UPDATES SUMMARY")
        print("="*80)
        print(f" Total Updates: {len(trade_updates)}")
        print(f" Total Notional: ${total_notional:,.2f}")
        print(f" Unique Symbols: {len(symbols)}")
        print(f" Buy Orders: {buy_count}")
        print(f" Sell Orders: {sell_count}")
        print(f" Timestamp: {datetime.now().isoformat()}")
        print("="*80)

        # Check for alerts
        self._check_trade_update_alerts(trade_updates)

    async def start_scheduled_collection(self):
        """Start scheduled collection service with market-aware intervals"""
        print("Trade updates scheduled collection started")
        print(f"Starting at: {datetime.now().isoformat()}")

        while True:
            try:
                # Get market status and appropriate interval from settings
                status = market_time.get_market_status()
                intervals = self.update_intervals

                if status == "MARKET_HOURS":
                    sleep_seconds = intervals.get('market_hours', 30)
                elif status == "EXTENDED_HOURS":
                    sleep_seconds = intervals.get('extended_hours', 120)
                else:
                    sleep_seconds = intervals.get('off_hours', 600)

                interval_minutes = sleep_seconds // 60

                print(f"\n[{datetime.now().isoformat()}] {status} - Collecting trade updates...")

                trade_updates_data = await self.get_trade_updates_data()

                if trade_updates_data:
                    total_notional = sum(update.get('notional', 0) for update in trade_updates_data)
                    print(f"Trade updates collected - {len(trade_updates_data)} updates, ${total_notional:,.2f} total notional")
                else:
                    print("No new trade updates found")

                # Wait for next collection
                print(f"Next collection in {interval_minutes} minutes ({status})...")
                await asyncio.sleep(sleep_seconds)

            except Exception as e:
                print(f"Error in trade updates scheduled collection: {e}")
                print("Retrying in 5 minutes...")
                await asyncio.sleep(300)

async def main():
    """Run trade updates feed - scheduled collection or one-time display"""
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--scheduled":
        # Run scheduled collection for systemd service
        async with UpdateFeedClient() as client:
            await client.start_scheduled_collection()
    else:
        # Display trade updates data (manual mode)
        async with UpdateFeedClient() as client:
            trade_updates_data = await client.get_trade_updates_data()

            if trade_updates_data:
                client.print_trade_updates_summary(trade_updates_data)
            else:
                print("No recent trade updates found")

if __name__ == "__main__":
    asyncio.run(main())