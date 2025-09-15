#!/usr/bin/env python3
"""
Account Feed Monitor
Real-time account balance and buying power tracking for Alpaca paper trading
"""

import os
import sys
import asyncio
import yaml
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime
from typing import Dict, Optional
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

class AccountFeedClient:
    """Alpaca account monitoring client"""

    def __init__(self):
        # Load settings
        self.settings = load_settings()

        # Alpaca API credentials from environment
        self.api_key = os.getenv('ALPACA_API_KEY')
        self.secret_key = os.getenv('ALPACA_SECRET_KEY')
        self.paper_trading = os.getenv('ALPACA_PAPER_TRADING', 'true').lower() == 'true'

        print(f"Initializing Alpaca client (Paper Trading: {self.paper_trading})")
        print(f"API Key: {self.api_key[:8]}...")

        # QuestDB connection
        self.questdb_conn = None
        self.questdb_config = self.settings.get('questdb') if self.settings else None

        # Account monitoring settings
        self.account_config = self.settings.get('account_monitoring', {}) if self.settings else {}

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

    async def get_account_data(self) -> Optional[Dict]:
        """Get current account data from Alpaca"""
        try:
            print("Fetching account data from Alpaca...")

            # Import and use MCP Alpaca tools
            import sys
            sys.path.append('/home/ezb0t/ezbot/mcp/alpaca_mcp/src')

            # Get account data using MCP tool
            account_response = await self._get_alpaca_account()

            if account_response:
                processed_data = self._process_account_data(account_response)

                # Store in QuestDB if available
                if self.questdb_conn and processed_data:
                    print("Storing account data in QuestDB...")
                    await self._store_account_data(processed_data)

                    # Check alert thresholds if configured
                    await self._check_account_alerts(processed_data)

                return processed_data
            else:
                print("No account data received")
                return None

        except Exception as e:
            print(f"Error fetching account data: {e}")
            return None

    async def _get_alpaca_account(self):
        """Use MCP alpaca client to get account data"""
        try:
            # This will use the MCP alpaca client
            from mcp_alpaca_trading import get_account
            return await get_account()
        except ImportError:
            # Fallback to direct API call if MCP not available
            import requests

            base_url = "https://paper-api.alpaca.markets" if self.paper_trading else "https://api.alpaca.markets"
            headers = {
                "APCA-API-KEY-ID": self.api_key,
                "APCA-API-SECRET-KEY": self.secret_key
            }

            response = requests.get(f"{base_url}/v2/account", headers=headers)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Alpaca API error: {response.status_code} - {response.text}")
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

            # Create account data table
            await self._create_account_table()

        except Exception as e:
            print(f"Failed to connect to QuestDB: {e}")
            raise

    async def _create_account_table(self):
        """Create QuestDB table for account data"""

        account_data_sql = """
        CREATE TABLE IF NOT EXISTS account (
            timestamp TIMESTAMP,
            account_id STRING,
            account_number STRING,
            status STRING,
            currency STRING,
            cash DOUBLE,
            portfolio_value DOUBLE,
            buying_power DOUBLE,
            regt_buying_power DOUBLE,
            daytrading_buying_power DOUBLE,
            non_marginable_buying_power DOUBLE,
            accrued_fees DOUBLE,
            pending_transfer_out DOUBLE,
            pending_transfer_in DOUBLE,
            equity DOUBLE,
            last_equity DOUBLE,
            multiplier INT,
            sma DOUBLE,
            daytrade_count INT,
            last_maintenance_margin DOUBLE,
            maintenance_margin DOUBLE,
            long_market_value DOUBLE,
            short_market_value DOUBLE,
            position_market_value DOUBLE,
            initial_margin DOUBLE,
            pattern_day_trader BOOLEAN,
            trading_blocked BOOLEAN,
            transfers_blocked BOOLEAN,
            account_blocked BOOLEAN,
            created_at TIMESTAMP,
            trade_suspended_by_user BOOLEAN,
            collected_at TIMESTAMP
        ) TIMESTAMP(timestamp) PARTITION BY DAY WAL;
        """

        cursor = self.questdb_conn.cursor()
        try:
            cursor.execute(account_data_sql)
            self.questdb_conn.commit()
            print("Account data table created successfully")
        except Exception as e:
            print(f"Error creating account data table: {e}")
            self.questdb_conn.rollback()
            raise
        finally:
            cursor.close()

    def _process_account_data(self, account_data: Dict) -> Dict:
        """Process raw account data from Alpaca"""
        try:
            current_time = datetime.now()

            return {
                "timestamp": current_time,
                "account_id": account_data.get('id', ''),
                "account_number": account_data.get('account_number', ''),
                "status": account_data.get('status', ''),
                "currency": account_data.get('currency', 'USD'),
                "cash": float(account_data.get('cash', 0)),
                "portfolio_value": float(account_data.get('portfolio_value', 0)),
                "buying_power": float(account_data.get('buying_power', 0)),
                "regt_buying_power": float(account_data.get('regt_buying_power', 0)),
                "daytrading_buying_power": float(account_data.get('daytrading_buying_power', 0)),
                "non_marginable_buying_power": float(account_data.get('non_marginable_buying_power', 0)),
                "accrued_fees": float(account_data.get('accrued_fees', 0)),
                "pending_transfer_out": float(account_data.get('pending_transfer_out', 0)),
                "pending_transfer_in": float(account_data.get('pending_transfer_in', 0)),
                "equity": float(account_data.get('equity', 0)),
                "last_equity": float(account_data.get('last_equity', 0)),
                "multiplier": int(account_data.get('multiplier', 1)),
                "sma": float(account_data.get('sma', 0)),
                "daytrade_count": int(account_data.get('daytrade_count', 0)),
                "last_maintenance_margin": float(account_data.get('last_maintenance_margin', 0)),
                "maintenance_margin": float(account_data.get('maintenance_margin', 0)),
                "long_market_value": float(account_data.get('long_market_value', 0)),
                "short_market_value": float(account_data.get('short_market_value', 0)),
                "position_market_value": float(account_data.get('position_market_value', 0)),
                "initial_margin": float(account_data.get('initial_margin', 0)),
                "pattern_day_trader": account_data.get('pattern_day_trader', False),
                "trading_blocked": account_data.get('trading_blocked', False),
                "transfers_blocked": account_data.get('transfers_blocked', False),
                "account_blocked": account_data.get('account_blocked', False),
                "created_at": account_data.get('created_at', current_time),
                "trade_suspended_by_user": account_data.get('trade_suspended_by_user', False),
                "collected_at": current_time
            }

        except Exception as e:
            print(f"Error processing account data: {e}")
            return None

    async def _store_account_data(self, account_data: Dict) -> bool:
        """Store account data in QuestDB"""
        if not account_data or not self.questdb_conn:
            return True

        cursor = self.questdb_conn.cursor()

        insert_sql = """
        INSERT INTO account (
            timestamp, account_id, account_number, status, currency, cash,
            portfolio_value, buying_power, regt_buying_power, daytrading_buying_power,
            non_marginable_buying_power, accrued_fees, pending_transfer_out,
            pending_transfer_in, equity, last_equity, multiplier, sma,
            daytrade_count, last_maintenance_margin, maintenance_margin,
            long_market_value, short_market_value, position_market_value,
            initial_margin, pattern_day_trader, trading_blocked, transfers_blocked,
            account_blocked, created_at, trade_suspended_by_user, collected_at
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """

        try:
            cursor.execute(insert_sql, (
                account_data['timestamp'],
                account_data['account_id'],
                account_data['account_number'],
                account_data['status'],
                account_data['currency'],
                account_data['cash'],
                account_data['portfolio_value'],
                account_data['buying_power'],
                account_data['regt_buying_power'],
                account_data['daytrading_buying_power'],
                account_data['non_marginable_buying_power'],
                account_data['accrued_fees'],
                account_data['pending_transfer_out'],
                account_data['pending_transfer_in'],
                account_data['equity'],
                account_data['last_equity'],
                account_data['multiplier'],
                account_data['sma'],
                account_data['daytrade_count'],
                account_data['last_maintenance_margin'],
                account_data['maintenance_margin'],
                account_data['long_market_value'],
                account_data['short_market_value'],
                account_data['position_market_value'],
                account_data['initial_margin'],
                account_data['pattern_day_trader'],
                account_data['trading_blocked'],
                account_data['transfers_blocked'],
                account_data['account_blocked'],
                account_data['created_at'],
                account_data['trade_suspended_by_user'],
                account_data['collected_at']
            ))

            self.questdb_conn.commit()
            print("Stored account data in QuestDB")
            return True

        except Exception as e:
            print(f"Error storing account data in QuestDB: {e}")
            self.questdb_conn.rollback()
            return False
        finally:
            cursor.close()

    async def _check_account_alerts(self, account_data: Dict):
        """Check account data against alert thresholds"""
        if not self.account_config.get('alert_thresholds'):
            return

        thresholds = self.account_config['alert_thresholds']

        # Low buying power alert
        if account_data['buying_power'] < thresholds.get('low_buying_power', 1000):
            print(f"⚠️ LOW BUYING POWER ALERT: ${account_data['buying_power']:,.2f}")

        # High day trade count alert
        if account_data['daytrade_count'] >= thresholds.get('high_day_trade_count', 2):
            print(f"⚠️ DAY TRADE COUNT ALERT: {account_data['daytrade_count']}/3 used")

        # Portfolio drop alert
        if account_data['last_equity'] > 0:
            drop_percent = ((account_data['last_equity'] - account_data['equity']) / account_data['last_equity']) * 100
            if drop_percent >= thresholds.get('portfolio_drop_percent', 5.0):
                print(f"⚠️ PORTFOLIO DROP ALERT: -{drop_percent:.2f}% (${account_data['equity']:,.2f})")

    def print_account_summary(self, account_data: Dict):
        """Print account summary to console"""
        if not account_data:
            print("No account data available")
            return

        print("\n" + "="*80)
        print(" ALPACA ACCOUNT SUMMARY")
        print("="*80)
        print(f" Account ID: {account_data['account_id']}")
        print(f" Status: {account_data['status']}")
        print(f" Paper Trading: {self.paper_trading}")
        print(f" Timestamp: {account_data['timestamp'].isoformat()}")
        print("="*80)

        print(f"\n=� CASH & EQUITY:")
        print(f"  Cash: ${account_data['cash']:,.2f}")
        print(f"  Portfolio Value: ${account_data['portfolio_value']:,.2f}")
        print(f"  Equity: ${account_data['equity']:,.2f}")
        print(f"  Last Equity: ${account_data['last_equity']:,.2f}")

        print(f"\n=� BUYING POWER:")
        print(f"  Total Buying Power: ${account_data['buying_power']:,.2f}")
        print(f"  RegT Buying Power: ${account_data['regt_buying_power']:,.2f}")
        print(f"  Daytrading Buying Power: ${account_data['daytrading_buying_power']:,.2f}")
        print(f"  Non-Marginable BP: ${account_data['non_marginable_buying_power']:,.2f}")

        print(f"\n=� POSITIONS:")
        print(f"  Long Market Value: ${account_data['long_market_value']:,.2f}")
        print(f"  Short Market Value: ${account_data['short_market_value']:,.2f}")
        print(f"  Position Market Value: ${account_data['position_market_value']:,.2f}")

        print(f"\n�  TRADING STATUS:")
        print(f"  Day Trades Used: {account_data['daytrade_count']}/3")
        print(f"  Pattern Day Trader: {account_data['pattern_day_trader']}")
        print(f"  Trading Blocked: {account_data['trading_blocked']}")
        print(f"  Account Blocked: {account_data['account_blocked']}")
        print(f"  Multiplier: {account_data['multiplier']}x")

        print("="*80)

    async def start_scheduled_collection(self):
        """Start scheduled collection service with market-aware intervals"""
        print("Account feed scheduled collection started")
        print(f"Starting at: {datetime.now().isoformat()}")

        while True:
            try:
                # Get market status and appropriate interval from settings
                status = market_time.get_market_status()
                intervals = self.settings.get('collection_intervals', {})

                if status == "MARKET_HOURS":
                    sleep_seconds = intervals.get('market_hours', 60)
                elif status == "EXTENDED_HOURS":
                    sleep_seconds = intervals.get('extended_hours', 300)
                else:
                    sleep_seconds = intervals.get('off_hours', 1800)

                interval_minutes = sleep_seconds // 60

                print(f"\n[{datetime.now().isoformat()}] {status} - Collecting account data...")

                account_data = await self.get_account_data()

                if account_data:
                    print(f"Account data collected - Portfolio: ${account_data['portfolio_value']:,.2f}")
                else:
                    print("No account data collected")

                # Wait for next collection
                print(f"Next collection in {interval_minutes} minutes ({status})...")
                await asyncio.sleep(sleep_seconds)

            except Exception as e:
                print(f"Error in account scheduled collection: {e}")
                print("Retrying in 5 minutes...")
                await asyncio.sleep(300)

async def main():
    """Run account feed - scheduled collection or one-time display"""
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--scheduled":
        # Run scheduled collection for systemd service
        async with AccountFeedClient() as client:
            await client.start_scheduled_collection()
    else:
        # Display account data (manual mode)
        async with AccountFeedClient() as client:
            account_data = await client.get_account_data()

            if account_data:
                client.print_account_summary(account_data)
            else:
                print("Failed to retrieve account data")

if __name__ == "__main__":
    asyncio.run(main())