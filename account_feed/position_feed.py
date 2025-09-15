#!/usr/bin/env python3
"""
Position Feed Monitor
Real-time position tracking and P&L monitoring for Alpaca paper trading
"""

import os
import sys
import asyncio
import yaml
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime
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

class PositionFeedClient:
    """Alpaca position monitoring client"""

    def __init__(self):
        # Load settings
        self.settings = load_settings()

        # Alpaca API credentials from environment
        self.api_key = os.getenv('ALPACA_API_KEY')
        self.secret_key = os.getenv('ALPACA_SECRET_KEY')
        self.paper_trading = os.getenv('ALPACA_PAPER_TRADING', 'true').lower() == 'true'

        print(f"Initializing Alpaca position feed (Paper Trading: {self.paper_trading})")

        # QuestDB connection
        self.questdb_conn = None
        self.questdb_config = self.settings.get('questdb') if self.settings else None

        # Position monitoring settings
        self.position_config = self.settings.get('position_monitoring', {}) if self.settings else {}

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

    async def get_positions_data(self) -> List[Dict]:
        """Get positions data from Alpaca"""
        try:
            print("Fetching positions from Alpaca...")

            # Use direct API call for positions
            positions_response = await self._get_alpaca_positions()

            if positions_response:
                processed_positions = []
                for position in positions_response:
                    processed_position = self._process_position_data(position)
                    if processed_position:
                        processed_positions.append(processed_position)

                # Store in QuestDB if available
                if self.questdb_conn and processed_positions:
                    print(f"Storing {len(processed_positions)} positions in QuestDB...")
                    await self._store_positions_data(processed_positions)

                    # Check position alerts if configured
                    await self._check_position_alerts(processed_positions)

                return processed_positions
            else:
                print("No positions data received")
                return []

        except Exception as e:
            print(f"Error fetching positions data: {e}")
            return []

    async def _get_alpaca_positions(self):
        """Get positions using direct API call"""
        try:
            import requests

            base_url = "https://paper-api.alpaca.markets" if self.paper_trading else "https://api.alpaca.markets"
            headers = {
                "APCA-API-KEY-ID": self.api_key,
                "APCA-API-SECRET-KEY": self.secret_key
            }

            response = requests.get(f"{base_url}/v2/positions", headers=headers)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Alpaca positions API error: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            print(f"Error calling Alpaca positions API: {e}")
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

            # Create positions table
            await self._create_positions_table()

        except Exception as e:
            print(f"Failed to connect to QuestDB: {e}")
            raise

    async def _create_positions_table(self):
        """Create QuestDB table for positions data"""

        positions_sql = """
        CREATE TABLE IF NOT EXISTS positions (
            timestamp TIMESTAMP,
            symbol SYMBOL CAPACITY 1000 CACHE,
            asset_id STRING,
            asset_class STRING,
            avg_entry_price DOUBLE,
            qty DOUBLE,
            side STRING,
            market_value DOUBLE,
            cost_basis DOUBLE,
            unrealized_pl DOUBLE,
            unrealized_plpc DOUBLE,
            unrealized_intraday_pl DOUBLE,
            unrealized_intraday_plpc DOUBLE,
            current_price DOUBLE,
            lastday_price DOUBLE,
            change_today DOUBLE,
            exchange STRING,
            qty_available DOUBLE,
            collected_at TIMESTAMP
        ) TIMESTAMP(timestamp) PARTITION BY DAY WAL;
        """

        cursor = self.questdb_conn.cursor()
        try:
            cursor.execute(positions_sql)
            self.questdb_conn.commit()
            print("Positions table created successfully")
        except Exception as e:
            print(f"Error creating positions table: {e}")
            self.questdb_conn.rollback()
            raise
        finally:
            cursor.close()

    def _process_position_data(self, position_data: Dict) -> Optional[Dict]:
        """Process raw position data from Alpaca"""
        try:
            current_time = datetime.now()

            return {
                "timestamp": current_time,
                "symbol": position_data.get('symbol', ''),
                "asset_id": position_data.get('asset_id', ''),
                "asset_class": position_data.get('asset_class', ''),
                "avg_entry_price": float(position_data.get('avg_entry_price', 0)),
                "qty": float(position_data.get('qty', 0)),
                "side": position_data.get('side', ''),
                "market_value": float(position_data.get('market_value', 0)),
                "cost_basis": float(position_data.get('cost_basis', 0)),
                "unrealized_pl": float(position_data.get('unrealized_pl', 0)),
                "unrealized_plpc": float(position_data.get('unrealized_plpc', 0)),
                "unrealized_intraday_pl": float(position_data.get('unrealized_intraday_pl', 0)),
                "unrealized_intraday_plpc": float(position_data.get('unrealized_intraday_plpc', 0)),
                "current_price": float(position_data.get('current_price', 0)),
                "lastday_price": float(position_data.get('lastday_price', 0)),
                "change_today": float(position_data.get('change_today', 0)),
                "exchange": position_data.get('exchange', ''),
                "qty_available": float(position_data.get('qty_available', 0)),
                "collected_at": current_time
            }

        except Exception as e:
            print(f"Error processing position data: {e}")
            return None

    async def _store_positions_data(self, positions_data: List[Dict]) -> bool:
        """Store positions data in QuestDB"""
        if not positions_data or not self.questdb_conn:
            return True

        cursor = self.questdb_conn.cursor()

        insert_sql = """
        INSERT INTO positions (
            timestamp, symbol, asset_id, asset_class, avg_entry_price, qty,
            side, market_value, cost_basis, unrealized_pl, unrealized_plpc,
            unrealized_intraday_pl, unrealized_intraday_plpc, current_price,
            lastday_price, change_today, exchange, qty_available, collected_at
        ) VALUES %s
        """

        values = []
        for position in positions_data:
            try:
                values.append((
                    position['timestamp'],
                    position['symbol'],
                    position['asset_id'],
                    position['asset_class'],
                    position['avg_entry_price'],
                    position['qty'],
                    position['side'],
                    position['market_value'],
                    position['cost_basis'],
                    position['unrealized_pl'],
                    position['unrealized_plpc'],
                    position['unrealized_intraday_pl'],
                    position['unrealized_intraday_plpc'],
                    position['current_price'],
                    position['lastday_price'],
                    position['change_today'],
                    position['exchange'],
                    position['qty_available'],
                    position['collected_at']
                ))
            except Exception as e:
                print(f"Error processing position for storage: {e}")
                continue

        try:
            if values:
                batch_size = self.questdb_config.get('batch_size', 100)
                execute_values(cursor, insert_sql, values, template=None, page_size=batch_size)
                self.questdb_conn.commit()
                print(f"Stored {len(values)} positions in QuestDB")
            return True

        except Exception as e:
            print(f"Error storing positions data in QuestDB: {e}")
            self.questdb_conn.rollback()
            return False
        finally:
            cursor.close()

    async def _check_position_alerts(self, positions_data: List[Dict]):
        """Check positions against alert thresholds"""
        if not self.position_config.get('alert_thresholds'):
            return

        thresholds = self.position_config['alert_thresholds']

        for position in positions_data:
            symbol = position['symbol']
            unrealized_plpc = position['unrealized_plpc']
            market_value = position['market_value']

            # Position loss alert
            loss_threshold = thresholds.get('position_loss_percent', 10.0)
            if unrealized_plpc <= -loss_threshold:
                print(f"🔴 POSITION LOSS ALERT: {symbol} -{abs(unrealized_plpc):.2f}% (${market_value:,.2f})")

            # Position gain alert
            gain_threshold = thresholds.get('position_gain_percent', 20.0)
            if unrealized_plpc >= gain_threshold:
                print(f"🟢 POSITION GAIN ALERT: {symbol} +{unrealized_plpc:.2f}% (${market_value:,.2f})")

    def print_positions_summary(self, positions_data: List[Dict]):
        """Print positions summary to console"""
        if not positions_data:
            print("No positions found")
            return

        print("\n" + "="*80)
        print(" ALPACA POSITIONS SUMMARY")
        print("="*80)
        print(f" Total Positions: {len(positions_data)}")
        print(f" Paper Trading: {self.paper_trading}")
        print(f" Timestamp: {datetime.now().isoformat()}")
        print("="*80)

        # Calculate totals
        total_market_value = sum(pos['market_value'] for pos in positions_data)
        total_cost_basis = sum(pos['cost_basis'] for pos in positions_data)
        total_unrealized_pl = sum(pos['unrealized_pl'] for pos in positions_data)
        total_intraday_pl = sum(pos['unrealized_intraday_pl'] for pos in positions_data)

        print(f"\n=� PORTFOLIO SUMMARY:")
        print(f"  Total Market Value: ${total_market_value:,.2f}")
        print(f"  Total Cost Basis: ${total_cost_basis:,.2f}")
        print(f"  Total Unrealized P&L: ${total_unrealized_pl:,.2f} ({(total_unrealized_pl/total_cost_basis*100):+.2f}%)" if total_cost_basis > 0 else "  Total Unrealized P&L: $0.00")
        print(f"  Total Intraday P&L: ${total_intraday_pl:,.2f}")

        # Group by asset class
        by_asset_class = {}
        for position in positions_data:
            asset_class = position['asset_class']
            if asset_class not in by_asset_class:
                by_asset_class[asset_class] = {'count': 0, 'market_value': 0, 'unrealized_pl': 0}
            by_asset_class[asset_class]['count'] += 1
            by_asset_class[asset_class]['market_value'] += position['market_value']
            by_asset_class[asset_class]['unrealized_pl'] += position['unrealized_pl']

        print(f"\n=� BY ASSET CLASS:")
        for asset_class, data in by_asset_class.items():
            print(f"  {asset_class}: {data['count']} positions, ${data['market_value']:,.2f} value, ${data['unrealized_pl']:+,.2f} P&L")

        # Show individual positions
        print(f"\n=� INDIVIDUAL POSITIONS:")

        # Sort by unrealized P&L (descending)
        sorted_positions = sorted(positions_data, key=lambda x: x['unrealized_pl'], reverse=True)

        for position in sorted_positions:
            symbol = position['symbol']
            side = position['side']
            qty = position['qty']
            current_price = position['current_price']
            market_value = position['market_value']
            unrealized_pl = position['unrealized_pl']
            unrealized_plpc = position['unrealized_plpc']

            # P&L color coding
            pl_symbol = "=�" if unrealized_pl >= 0 else "=4"

            print(f"  {pl_symbol} {symbol} ({side}) {qty:,.0f} @ ${current_price:.4f}")
            print(f"      Market Value: ${market_value:,.2f} | P&L: ${unrealized_pl:+,.2f} ({unrealized_plpc:+.2f}%)")

        print("="*80)

    async def start_scheduled_collection(self):
        """Start scheduled collection service with market-aware intervals"""
        print("Position feed scheduled collection started")
        print(f"Starting at: {datetime.now().isoformat()}")

        while True:
            try:
                # Get market status and appropriate interval from settings
                status = market_time.get_market_status()
                intervals = self.settings.get('position_intervals', {})

                if status == "MARKET_HOURS":
                    sleep_seconds = intervals.get('market_hours', 30)
                elif status == "EXTENDED_HOURS":
                    sleep_seconds = intervals.get('extended_hours', 120)
                else:
                    sleep_seconds = intervals.get('off_hours', 600)

                interval_minutes = sleep_seconds // 60 if sleep_seconds >= 60 else f"{sleep_seconds}s"

                print(f"\n[{datetime.now().isoformat()}] {status} - Collecting positions data...")

                positions_data = await self.get_positions_data()

                if positions_data:
                    total_value = sum(pos['market_value'] for pos in positions_data)
                    total_pl = sum(pos['unrealized_pl'] for pos in positions_data)
                    print(f"Positions data collected - {len(positions_data)} positions, ${total_value:,.2f} value, ${total_pl:+,.2f} P&L")
                else:
                    print("No positions data collected")

                # Wait for next collection
                print(f"Next collection in {interval_minutes} ({'minutes' if isinstance(interval_minutes, int) else ''}) ({status})...")
                await asyncio.sleep(sleep_seconds)

            except Exception as e:
                print(f"Error in positions scheduled collection: {e}")
                print("Retrying in 5 minutes...")
                await asyncio.sleep(300)

async def main():
    """Run position feed - scheduled collection or one-time display"""
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--scheduled":
        # Run scheduled collection for systemd service
        async with PositionFeedClient() as client:
            await client.start_scheduled_collection()
    else:
        # Display positions data (manual mode)
        async with PositionFeedClient() as client:
            positions_data = await client.get_positions_data()
            if positions_data:
                client.print_positions_summary(positions_data)
            else:
                print("No positions data available")

if __name__ == "__main__":
    asyncio.run(main())