#!/usr/bin/env python3
"""
Unusual Whales Analyst Reports Feed

Collects analyst reports and ratings from Unusual Whales API and stores in QuestDB.
This feed is crucial for news catalyst momentum and premarket momentum strategies.
"""

import asyncio
import aiohttp
import logging
import os
import yaml
from datetime import datetime, timedelta, timezone
from typing import Dict, List
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv


class UnusualWhalesAnalystFeed:
    def __init__(self, config_path: str = None):
        """Initialize the analyst feed"""
        # Load environment variables from .env file
        env_path = '/home/ezb0t/ezbot/.env'
        load_dotenv(env_path)

        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), 'settings.yaml')

        self.config = self._load_config(config_path)
        self.api_key = os.getenv(self.config['api']['token_env_var'])

        if not self.api_key:
            raise ValueError(f"API key not found in environment variable: {self.config['api']['token_env_var']}")

        self.session = None
        self.questdb_conn = None
        self.logger = self._setup_logging()

        # Track last collection time to avoid duplicates
        self.last_collection = datetime.now(timezone.utc) - timedelta(hours=24)

    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            raise ValueError(f"Failed to load config from {config_path}: {e}")

    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logger = logging.getLogger('analyst_feed')

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

    async def start_collection(self):
        """Start the analyst feed collection process"""
        self.logger.info("Starting Unusual Whales Analyst Feed")

        # Initialize connections
        await self._init_session()
        await self._init_questdb()
        try:
            while True:
                current_time = datetime.now()

                # Determine collection interval based on market hours
                if self._is_market_hours(current_time):
                    interval = self.config['collection']['poll_interval']
                elif self._is_extended_hours(current_time):
                    interval = self.config['collection']['after_hours_interval']
                else:
                    # Outside trading hours, check less frequently
                    interval = self.config['collection']['after_hours_interval'] * 2

                # Collect analyst reports
                await self._collect_analyst_reports()

                # Sleep until next collection
                self.logger.info(f"Next collection in {interval} seconds")
                await asyncio.sleep(interval)

        except KeyboardInterrupt:
            self.logger.info("Shutting down analyst feed")
        except Exception as e:
            self.logger.error(f"Error in collection loop: {e}")
            raise
        finally:
            await self._cleanup()

    async def _init_session(self):
        """Initialize HTTP session"""
        connector = aiohttp.TCPConnector(limit=10)
        timeout = aiohttp.ClientTimeout(total=self.config['api']['timeout'])
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                'Accept': 'application/json, text/plain',
                'Authorization': f'Bearer {self.api_key}'
            }
        )

    async def _init_questdb(self):
        """Initialize QuestDB connection and create tables"""
        try:
            self.questdb_conn = psycopg2.connect(
                host=self.config['questdb']['host'],
                port=self.config['questdb']['port'],
                database=self.config['questdb']['database'],
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
        """Create QuestDB tables for analyst data"""

        # Main analyst reports table
        analyst_reports_sql = """
        CREATE TABLE IF NOT EXISTS analyst_reports (
            timestamp TIMESTAMP,
            ticker SYMBOL CAPACITY 1000 CACHE,
            analyst_name STRING,
            firm STRING,
            action SYMBOL CAPACITY 20 CACHE,
            recommendation SYMBOL CAPACITY 10 CACHE,
            target_price DOUBLE,
            sector SYMBOL CAPACITY 50 CACHE,
            report_timestamp TIMESTAMP,
            significance_score DOUBLE,
            collected_at TIMESTAMP
        ) TIMESTAMP(timestamp) PARTITION BY DAY WAL;
        """

        cursor = self.questdb_conn.cursor()
        cursor.execute(analyst_reports_sql)
        self.questdb_conn.commit()
        cursor.close()

        self.logger.info("QuestDB analyst_reports table created successfully")

    async def _collect_analyst_reports(self):
        """Collect analyst reports from Unusual Whales API"""
        try:
            # Get recent reports
            reports = await self._fetch_analyst_reports()

            if reports:
                # Process and filter reports
                processed_reports = self._process_reports(reports)

                # Store in QuestDB
                await self._store_reports(processed_reports)

                # Generate alerts for significant reports
                await self._check_alerts(processed_reports)

                self.logger.info(f"Collected {len(processed_reports)} analyst reports")
                print(f"Collected {len(processed_reports)} analyst reports at {datetime.now().strftime('%H:%M:%S')}")

                # Print significant reports to console
                significant = [r for r in processed_reports if r['significance_score'] > 0.6]
                if significant:
                    print(f"Found {len(significant)} significant reports:")
                    for report in significant[:3]:  # Show top 3
                        print(f"   {report['ticker']} - {report['action']} by {report['firm']} (Score: {report['significance_score']:.2f})")
            else:
                self.logger.info("No new analyst reports found")
                print(f"No new reports at {datetime.now().strftime('%H:%M:%S')}")

        except Exception as e:
            self.logger.error(f"Error collecting analyst reports: {e}")

    async def _fetch_analyst_reports(self) -> List[Dict]:
        """Fetch analyst reports from Unusual Whales API"""
        url = f"{self.config['api']['base_url']}{self.config['api']['endpoint']}"

        params = {
            'limit': self.config['collection']['default_limit']
        }

        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('data', [])
                else:
                    self.logger.error(f"API request failed: {response.status}")
                    return []
        except Exception as e:
            self.logger.error(f"Error fetching analyst reports: {e}")
            return []

    def _process_reports(self, reports: List[Dict]) -> List[Dict]:
        """Process and filter analyst reports"""
        processed = []
        current_time = datetime.now(timezone.utc)
        skipped_old = 0
        skipped_action = 0

        for report in reports:
            try:
                # Parse timestamp - keep timezone-aware for comparison
                report_time = datetime.fromisoformat(
                    report['timestamp'].replace('Z', '+00:00')
                )

                # Skip if too old
                if report_time < self.last_collection:
                    skipped_old += 1
                    continue

                # Filter by action
                if report['action'] not in self.config['filters']['track_actions']:
                    skipped_action += 1
                    continue

                # Calculate significance score
                significance = self._calculate_significance(report)

                # Prepare processed report
                processed_report = {
                    'timestamp': current_time.replace(tzinfo=None),  # Remove timezone for QuestDB
                    'ticker': report['ticker'],
                    'analyst_name': report['analyst_name'],
                    'firm': report['firm'],
                    'action': report['action'],
                    'recommendation': report['recommendation'],
                    'target_price': float(report['target']) if report['target'] else None,
                    'sector': report.get('sector', ''),
                    'report_timestamp': report_time.replace(tzinfo=None),  # Remove timezone for QuestDB
                    'significance_score': significance,
                    'collected_at': current_time.replace(tzinfo=None)  # Remove timezone for QuestDB
                }

                processed.append(processed_report)

            except Exception as e:
                self.logger.error(f"Error processing report: {e}")
                continue

        # Update last collection time
        if processed:
            self.last_collection = max(
                datetime.fromisoformat(r['report_timestamp'].isoformat()).replace(tzinfo=timezone.utc)
                for r in processed
            )

        return processed

    def _calculate_significance(self, report: Dict) -> float:
        """Calculate significance score for analyst report"""
        score = 0.0

        # Base score by action
        action_scores = {
            'upgraded': 0.8,
            'downgraded': 0.8,
            'initiated': 0.6,
            'target raised': 0.5,
            'target lowered': 0.5,
            'maintained': 0.2,
            'reiterated': 0.2
        }

        score += action_scores.get(report['action'], 0.2)

        # Recommendation weight
        rec_scores = {
            'buy': 0.2,
            'sell': 0.2,
            'hold': 0.1
        }

        score += rec_scores.get(report['recommendation'], 0.0)

        # High target price gets bonus
        if report['target']:
            target = float(report['target'])
            if target > 100:
                score += 0.1
            elif target > 50:
                score += 0.05

        return min(score, 1.0)

    async def _store_reports(self, reports: List[Dict]):
        """Store analyst reports in QuestDB"""
        if not reports:
            return

        cursor = self.questdb_conn.cursor()

        # Insert into analyst_reports table
        insert_sql = """
        INSERT INTO analyst_reports (
            timestamp, ticker, analyst_name, firm, action, recommendation,
            target_price, sector, report_timestamp, significance_score, collected_at
        ) VALUES %s
        """

        values = [
            (
                r['timestamp'], r['ticker'], r['analyst_name'], r['firm'],
                r['action'], r['recommendation'], r['target_price'], r['sector'],
                r['report_timestamp'], r['significance_score'], r['collected_at']
            )
            for r in reports
        ]

        try:
            execute_values(cursor, insert_sql, values, template=None, page_size=100)
            self.questdb_conn.commit()

        except Exception as e:
            self.logger.error(f"Error storing reports in QuestDB: {e}")
            self.questdb_conn.rollback()
        finally:
            cursor.close()

    async def _check_alerts(self, reports: List[Dict]):
        """Check for significant reports and generate alerts"""
        if not self.config['alerts']['enabled']:
            return

        significant_reports = []

        for report in reports:
            if report['significance_score'] > 0.7:
                significant_reports.append(report)

        if significant_reports:
            self.logger.info(f"Found {len(significant_reports)} significant analyst reports")
            # TODO: Implement webhook notifications if configured

    def _is_market_hours(self, dt: datetime) -> bool:
        """Check if current time is during market hours"""
        if dt.weekday() >= 5:  # Weekend
            return False

        time_str = dt.strftime("%H:%M")
        start = self.config['collection']['market_hours']['start']
        end = self.config['collection']['market_hours']['end']

        return start <= time_str <= end

    def _is_extended_hours(self, dt: datetime) -> bool:
        """Check if current time is during extended hours"""
        if dt.weekday() >= 5:  # Weekend
            return False

        time_str = dt.strftime("%H:%M")
        start = self.config['collection']['extended_hours']['start']
        end = self.config['collection']['extended_hours']['end']

        return start <= time_str <= end

    async def _cleanup(self):
        """Cleanup connections"""
        if self.session:
            await self.session.close()

        if self.questdb_conn:
            self.questdb_conn.close()

        self.logger.info("Connections closed")


async def main():
    """Main function to run the analyst feed"""
    print("Starting Unusual Whales Analyst Feed")
    print("Collecting analyst reports every 5 minutes during market hours")
    print("Press Ctrl+C to stop")
    print("-" * 60)

    feed = UnusualWhalesAnalystFeed()
    await feed.start_collection()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nAnalyst feed stopped by user")
    except Exception as e:
        print(f"\nError: {e}")
        exit(1)