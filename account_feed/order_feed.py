#!/usr/bin/env python3
"""
Order Feed Monitor
Real-time order execution and status tracking for Alpaca paper trading
"""

import os
import sys
import asyncio
import yaml
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dotenv import load_dotenv
from pathlib import Path

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

class OrderFeedClient:
    """Alpaca order monitoring client"""

    def __init__(self):
        # Load settings
        self.settings = load_settings()

        # Alpaca API credentials from environment
        self.api_key = os.getenv('ALPACA_API_KEY')
        self.secret_key = os.getenv('ALPACA_SECRET_KEY')
        self.paper_trading = os.getenv('ALPACA_PAPER_TRADING', 'true').lower() == 'true'

        print(f"Initializing Alpaca order feed (Paper Trading: {self.paper_trading})")

        # QuestDB connection
        self.questdb_conn = None
        self.questdb_config = self.settings.get('questdb') if self.settings else None

        # Order monitoring settings
        self.order_config = self.settings.get('order_monitoring', {}) if self.settings else {}

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

    async def get_orders_data(self, status: str = "all", limit: int = None) -> List[Dict]:
        """Get orders data from Alpaca"""
        try:
            # Get limit from settings if not provided
            if limit is None:
                limit = self.order_config.get('max_orders_per_request', 500)

            print(f"Fetching {status} orders from Alpaca (limit: {limit})...")

            # Use direct API call for orders
            orders_response = await self._get_alpaca_orders(status, limit)

            if orders_response:
                processed_orders = []
                for order in orders_response:
                    processed_order = self._process_order_data(order)
                    if processed_order:
                        processed_orders.append(processed_order)

                # Store in QuestDB if available
                if self.questdb_conn and processed_orders:
                    print(f"Storing {len(processed_orders)} orders in QuestDB...")
                    await self._store_orders_data(processed_orders)

                return processed_orders
            else:
                print("No orders data received")
                return []

        except Exception as e:
            print(f"Error fetching orders data: {e}")
            return []

    async def _get_alpaca_orders(self, status: str, limit: int):
        """Get orders using direct API call"""
        try:
            import requests

            base_url = "https://paper-api.alpaca.markets" if self.paper_trading else "https://api.alpaca.markets"
            headers = {
                "APCA-API-KEY-ID": self.api_key,
                "APCA-API-SECRET-KEY": self.secret_key
            }

            params = {
                "status": status,
                "limit": limit,
                "direction": "desc"
            }

            response = requests.get(f"{base_url}/v2/orders", headers=headers, params=params)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Alpaca orders API error: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            print(f"Error calling Alpaca orders API: {e}")
            return None

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

            # Create orders table
            await self._create_orders_table()

        except Exception as e:
            print(f"Failed to connect to QuestDB: {e}")
            raise

    async def _create_orders_table(self):
        """Create QuestDB table for orders data"""

        orders_sql = """
        CREATE TABLE IF NOT EXISTS orders (
            timestamp TIMESTAMP,
            order_id STRING,
            client_order_id STRING,
            symbol SYMBOL CAPACITY 1000 CACHE,
            asset_id STRING,
            asset_class STRING,
            order_type STRING,
            side STRING,
            qty DOUBLE,
            filled_qty DOUBLE,
            filled_avg_price DOUBLE,
            order_status STRING,
            time_in_force STRING,
            limit_price DOUBLE,
            stop_price DOUBLE,
            trail_price DOUBLE,
            trail_percent DOUBLE,
            submitted_at TIMESTAMP,
            filled_at TIMESTAMP,
            expired_at TIMESTAMP,
            canceled_at TIMESTAMP,
            failed_at TIMESTAMP,
            replaced_at TIMESTAMP,
            replaced_by STRING,
            replaces STRING,
            legs STRING,
            commission DOUBLE,
            extended_hours BOOLEAN,
            collected_at TIMESTAMP
        ) TIMESTAMP(timestamp) PARTITION BY DAY WAL;
        """

        cursor = self.questdb_conn.cursor()
        try:
            cursor.execute(orders_sql)
            self.questdb_conn.commit()
            print("Orders table created successfully")
        except Exception as e:
            print(f"Error creating orders table: {e}")
            self.questdb_conn.rollback()
            raise
        finally:
            cursor.close()

    def _process_order_data(self, order_data: Dict) -> Optional[Dict]:
        """Process raw order data from Alpaca"""
        try:
            current_time = datetime.now()

            # Parse timestamps
            def parse_timestamp(ts_str):
                if ts_str:
                    try:
                        return datetime.fromisoformat(ts_str.replace('Z', '+00:00')).replace(tzinfo=None)
                    except:
                        return None
                return None

            return {
                "timestamp": current_time,
                "order_id": order_data.get('id', ''),
                "client_order_id": order_data.get('client_order_id', ''),
                "symbol": order_data.get('symbol', ''),
                "asset_id": order_data.get('asset_id', ''),
                "asset_class": order_data.get('asset_class', ''),
                "order_type": order_data.get('order_type', ''),
                "side": order_data.get('side', ''),
                "qty": float(order_data.get('qty', 0)),
                "filled_qty": float(order_data.get('filled_qty', 0)),
                "filled_avg_price": float(order_data.get('filled_avg_price', 0)) if order_data.get('filled_avg_price') else 0,
                "order_status": order_data.get('status', ''),
                "time_in_force": order_data.get('time_in_force', ''),
                "limit_price": float(order_data.get('limit_price', 0)) if order_data.get('limit_price') else 0,
                "stop_price": float(order_data.get('stop_price', 0)) if order_data.get('stop_price') else 0,
                "trail_price": float(order_data.get('trail_price', 0)) if order_data.get('trail_price') else 0,
                "trail_percent": float(order_data.get('trail_percent', 0)) if order_data.get('trail_percent') else 0,
                "submitted_at": parse_timestamp(order_data.get('submitted_at')),
                "filled_at": parse_timestamp(order_data.get('filled_at')),
                "expired_at": parse_timestamp(order_data.get('expired_at')),
                "canceled_at": parse_timestamp(order_data.get('canceled_at')),
                "failed_at": parse_timestamp(order_data.get('failed_at')),
                "replaced_at": parse_timestamp(order_data.get('replaced_at')),
                "replaced_by": order_data.get('replaced_by', ''),
                "replaces": order_data.get('replaces', ''),
                "legs": str(order_data.get('legs', [])) if order_data.get('legs') else '',
                "commission": float(order_data.get('commission', 0)) if order_data.get('commission') else 0,
                "extended_hours": order_data.get('extended_hours', False),
                "collected_at": current_time
            }

        except Exception as e:
            print(f"Error processing order data: {e}")
            return None

    async def _store_orders_data(self, orders_data: List[Dict]) -> bool:
        """Store orders data in QuestDB"""
        if not orders_data or not self.questdb_conn:
            return True

        cursor = self.questdb_conn.cursor()

        insert_sql = """
        INSERT INTO orders (
            timestamp, order_id, client_order_id, symbol, asset_id, asset_class,
            order_type, side, qty, filled_qty, filled_avg_price, order_status,
            time_in_force, limit_price, stop_price, trail_price, trail_percent,
            submitted_at, filled_at, expired_at, canceled_at, failed_at,
            replaced_at, replaced_by, replaces, legs, commission, extended_hours,
            collected_at
        ) VALUES %s
        """

        values = []
        for order in orders_data:
            try:
                values.append((
                    order['timestamp'],
                    order['order_id'],
                    order['client_order_id'],
                    order['symbol'],
                    order['asset_id'],
                    order['asset_class'],
                    order['order_type'],
                    order['side'],
                    order['qty'],
                    order['filled_qty'],
                    order['filled_avg_price'],
                    order['order_status'],
                    order['time_in_force'],
                    order['limit_price'],
                    order['stop_price'],
                    order['trail_price'],
                    order['trail_percent'],
                    order['submitted_at'],
                    order['filled_at'],
                    order['expired_at'],
                    order['canceled_at'],
                    order['failed_at'],
                    order['replaced_at'],
                    order['replaced_by'],
                    order['replaces'],
                    order['legs'],
                    order['commission'],
                    order['extended_hours'],
                    order['collected_at']
                ))
            except Exception as e:
                print(f"Error processing order for storage: {e}")
                continue

        try:
            if values:
                batch_size = self.questdb_config.get('batch_size', 100)
                execute_values(cursor, insert_sql, values, template=None, page_size=batch_size)
                self.questdb_conn.commit()
                print(f"Stored {len(values)} orders in QuestDB")
            return True

        except Exception as e:
            print(f"Error storing orders data in QuestDB: {e}")
            self.questdb_conn.rollback()
            return False
        finally:
            cursor.close()

    def print_orders_summary(self, orders_data: List[Dict]):
        """Print orders summary to console"""
        if not orders_data:
            print("No orders data available")
            return

        print("\n" + "="*80)
        print(" ALPACA ORDERS SUMMARY")
        print("="*80)
        print(f" Total Orders: {len(orders_data)}")
        print(f" Paper Trading: {self.paper_trading}")
        print(f" Timestamp: {datetime.now().isoformat()}")
        print("="*80)

        # Group by status
        by_status = {}
        by_symbol = {}
        total_filled_value = 0

        for order in orders_data:
            status = order['order_status']
            symbol = order['symbol']

            by_status[status] = by_status.get(status, 0) + 1
            by_symbol[symbol] = by_symbol.get(symbol, 0) + 1

            if order['filled_qty'] > 0 and order['filled_avg_price'] > 0:
                total_filled_value += order['filled_qty'] * order['filled_avg_price']

        print(f"\n=� ORDER STATUS:")
        for status, count in sorted(by_status.items()):
            print(f"  {status}: {count}")

        print(f"\n=� EXECUTION SUMMARY:")
        print(f"  Total Filled Value: ${total_filled_value:,.2f}")

        print(f"\n= TOP SYMBOLS:")
        for symbol, count in sorted(by_symbol.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {symbol}: {count} orders")

        # Show recent orders
        print(f"\n=� RECENT ORDERS:")
        recent_orders = sorted(orders_data, key=lambda x: x['submitted_at'] or datetime.min, reverse=True)[:5]

        for order in recent_orders:
            status_symbol = "" if order['order_status'] == 'filled' else "�" if order['order_status'] == 'new' else "L"
            print(f"  {status_symbol} {order['symbol']} {order['side']} {order['qty']} @ {order['limit_price'] or 'MKT'} - {order['order_status']}")

        print("="*80)

    async def start_scheduled_collection(self):
        """Start scheduled collection service with market-aware intervals"""
        print("Order feed scheduled collection started")
        print(f"Starting at: {datetime.now().isoformat()}")

        while True:
            try:
                # Get market status and appropriate interval from settings
                status = market_time.get_market_status()
                intervals = self.settings.get('order_intervals', {})

                if status == "MARKET_HOURS":
                    sleep_seconds = intervals.get('market_hours', 30)
                elif status == "EXTENDED_HOURS":
                    sleep_seconds = intervals.get('extended_hours', 120)
                else:
                    sleep_seconds = intervals.get('off_hours', 600)

                interval_minutes = sleep_seconds // 60 if sleep_seconds >= 60 else f"{sleep_seconds}s"

                print(f"\n[{datetime.now().isoformat()}] {status} - Collecting orders data...")

                orders_data = await self.get_orders_data(status="all")

                if orders_data:
                    print(f"Orders data collected - {len(orders_data)} orders")
                else:
                    print("No orders data collected")

                # Wait for next collection
                print(f"Next collection in {interval_minutes} ({'minutes' if isinstance(interval_minutes, int) else ''}) ({status})...")
                await asyncio.sleep(sleep_seconds)

            except Exception as e:
                print(f"Error in orders scheduled collection: {e}")
                print("Retrying in 5 minutes...")
                await asyncio.sleep(300)

async def main():
    """Run order feed - scheduled collection or one-time display"""
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--scheduled":
        # Run scheduled collection for systemd service
        async with OrderFeedClient() as client:
            await client.start_scheduled_collection()
    else:
        # Display orders data (manual mode)
        async with OrderFeedClient() as client:
            orders_data = await client.get_orders_data(status="all")
            if orders_data:
                client.print_orders_summary(orders_data)
            else:
                print("No orders data available")

if __name__ == "__main__":
    asyncio.run(main())