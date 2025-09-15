#!/usr/bin/env python3
"""
Stock Titan RSS Feed Parser
Fast, lightweight news parsing from Stock Titan RSS feed
"""

import os
import aiohttp
import asyncio
import xml.etree.ElementTree as ET
import yaml
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dotenv import load_dotenv
from pathlib import Path
import re

# Load environment variables
load_dotenv()

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

class StockTitanRSSClient:
    """Stock Titan RSS feed parser for fast news updates"""

    def __init__(self):
        # Load settings
        self.settings = load_settings()

        # Get configuration from settings or use defaults
        if self.settings and 'api' in self.settings and 'stock_titan' in self.settings['api']:
            stock_titan_config = self.settings['api']['stock_titan']
            self.rss_url = stock_titan_config.get('rss_url', "https://www.stocktitan.net/rss")
            self.max_retries = stock_titan_config.get('max_retries', 3)
            self.retry_delay = stock_titan_config.get('retry_delay', 2)
        else:
            # Fallback to defaults if settings not available
            self.rss_url = "https://www.stocktitan.net/rss"
            self.max_retries = 3
            self.retry_delay = 2

        self.session: Optional[aiohttp.ClientSession] = None

        # QuestDB connection
        self.questdb_conn = None
        self.questdb_config = self.settings.get('questdb') if self.settings else None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
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

    async def get_latest_news(self, limit: int = None) -> List[Dict]:
        """Get latest news from RSS feed with retry logic"""
        # Get limit from settings if not provided
        if limit is None:
            limit = 50
            if self.settings and 'api' in self.settings and 'stock_titan' in self.settings['api']:
                limit = self.settings['api']['stock_titan'].get('max_limit', 50)

        for attempt in range(self.max_retries):
            try:
                # Get timeout from settings
                timeout_seconds = 30
                if self.settings and 'api' in self.settings and 'stock_titan' in self.settings['api']:
                    timeout_seconds = self.settings['api']['stock_titan'].get('timeout', 30)

                timeout = aiohttp.ClientTimeout(total=timeout_seconds)
                async with self.session.get(self.rss_url, timeout=timeout) as response:
                    if response.status == 429:  # Rate limited
                        wait_time = int(response.headers.get('Retry-After', self.retry_delay * (attempt + 1)))
                        print(f"Rate limited. Waiting {wait_time} seconds...")
                        await asyncio.sleep(wait_time)
                        continue

                    if response.status != 200:
                        print(f"Error fetching RSS: {response.status}")
                        if attempt < self.max_retries - 1:
                            await asyncio.sleep(self.retry_delay * (attempt + 1))
                            continue
                        return []

                    xml_content = await response.text()
                    processed_news = self._parse_rss_feed(xml_content, limit)

                    # Store in QuestDB if available
                    if self.questdb_conn and processed_news:
                        await self._store_news_data(processed_news)

                    return processed_news

            except asyncio.TimeoutError:
                print(f"Timeout on attempt {attempt + 1}/{self.max_retries}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                    continue
                return []
            except Exception as e:
                print(f"Error fetching Stock Titan RSS (attempt {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                    continue
                return []

        return []

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

            # Create Stock Titan news table
            await self._create_stock_titan_table()

        except Exception as e:
            print(f"Failed to connect to QuestDB: {e}")
            raise

    async def _create_stock_titan_table(self):
        """Create QuestDB table for Stock Titan news data"""

        stock_titan_news_sql = """
        CREATE TABLE IF NOT EXISTS stock_titan_news (
            timestamp TIMESTAMP,
            id STRING,
            title STRING,
            description STRING,
            content STRING,
            url STRING,
            author STRING,
            published_utc TIMESTAMP,
            ticker SYMBOL CAPACITY 1000 CACHE,
            symbols STRING,
            category SYMBOL CAPACITY 50 CACHE,
            rss_category STRING,
            sentiment SYMBOL CAPACITY 20 CACHE,
            source_name STRING,
            has_content BOOLEAN,
            content_length INT,
            enclosure_url STRING,
            guid_permalink STRING,
            collected_at TIMESTAMP
        ) TIMESTAMP(timestamp) PARTITION BY DAY WAL;
        """

        cursor = self.questdb_conn.cursor()
        try:
            cursor.execute(stock_titan_news_sql)
            self.questdb_conn.commit()
            print("Stock Titan news table created successfully")
        except Exception as e:
            print(f"Error creating Stock Titan news table: {e}")
            self.questdb_conn.rollback()
            raise
        finally:
            cursor.close()

    async def _store_news_data(self, news_items: List[Dict]) -> bool:
        """Store Stock Titan news data in QuestDB"""
        if not news_items or not self.questdb_conn:
            return True

        cursor = self.questdb_conn.cursor()

        insert_sql = """
        INSERT INTO stock_titan_news (
            timestamp, id, title, description, content, url, author, published_utc,
            ticker, symbols, category, rss_category, sentiment, source_name,
            has_content, content_length, enclosure_url, guid_permalink, collected_at
        ) VALUES %s
        """

        values = []
        current_time = datetime.now()

        for item in news_items:
            try:
                # Parse published date
                published_utc = self._parse_datetime(item.get('published_utc'))

                # Convert lists to comma-separated strings
                symbols = ','.join(item.get('symbols', [])) if item.get('symbols') else ''

                values.append((
                    current_time,
                    item.get('id', ''),
                    item.get('title', ''),
                    item.get('description', ''),
                    item.get('content', ''),
                    item.get('url', ''),
                    item.get('author', ''),
                    published_utc,
                    item.get('ticker', ''),
                    symbols,
                    item.get('category', ''),
                    item.get('rss_category', ''),
                    item.get('sentiment', ''),
                    item.get('source_name', ''),
                    item.get('has_content', False),
                    item.get('content_length', 0),
                    item.get('enclosure_url', ''),
                    item.get('guid_permalink', ''),
                    current_time
                ))
            except Exception as e:
                print(f"Error processing Stock Titan news item: {e}")
                continue

        try:
            if values:
                execute_values(cursor, insert_sql, values, template=None, page_size=self.questdb_config['batch_size'])
                self.questdb_conn.commit()
                print(f"Stored {len(values)} Stock Titan news records in QuestDB")
            return True

        except Exception as e:
            print(f"Error storing Stock Titan news data in QuestDB: {e}")
            self.questdb_conn.rollback()
            return False
        finally:
            cursor.close()

    def _parse_datetime(self, date_str: str) -> Optional[datetime]:
        """Parse datetime string to datetime object"""
        if not date_str:
            return datetime.now()

        try:
            if 'T' in date_str:
                return datetime.fromisoformat(date_str.replace('Z', '+00:00')).replace(tzinfo=None)
            else:
                return datetime.fromisoformat(date_str)
        except Exception:
            return datetime.now()

    def _parse_rss_feed(self, xml_content: str, limit: int) -> List[Dict]:
        """Parse RSS XML content into news items"""
        try:
            root = ET.fromstring(xml_content)
            channel = root.find('channel')

            if channel is None:
                return []

            news_items = []
            items = channel.findall('item')

            for item in items[:limit]:
                news_item = self._parse_rss_item(item)
                if news_item:
                    news_items.append(news_item)

            return news_items

        except Exception as e:
            print(f"Error parsing RSS feed: {e}")
            return []

    def _parse_rss_item(self, item) -> Optional[Dict]:
        """Parse individual RSS item"""
        try:
            title = self._get_element_text(item, 'title')
            link = self._get_element_text(item, 'link')
            description = self._get_element_text(item, 'description')
            pub_date = self._get_element_text(item, 'pubDate')
            guid = self._get_element_text(item, 'guid')

            # Additional RSS elements that might be present
            author = self._get_element_text(item, 'author')
            category_element = self._get_element_text(item, 'category')
            enclosure = item.find('enclosure')
            enclosure_url = enclosure.get('url') if enclosure is not None else None

            if not title:
                return None

            # Extract ticker symbol from title or link
            ticker = self._extract_ticker(title, link)

            # Clean and format description
            clean_description = self._clean_description(description)

            # Parse publication date
            parsed_date = self._parse_pub_date(pub_date)

            # Determine category/type from title and description
            category = self._categorize_news(title, clean_description)

            return {
                "source": "stock_titan_rss",
                "id": guid or link,
                "title": title.strip(),
                "description": clean_description,
                "content": "",  # RSS doesn't provide full content
                "url": link,
                "author": author or "Stock Titan",
                "published_utc": parsed_date,
                "ticker": ticker,
                "symbols": [ticker] if ticker else [],
                "category": category,
                "rss_category": category_element,
                "sentiment": "neutral",  # RSS doesn't provide sentiment
                "source_name": "Stock Titan",
                "has_content": False,
                "content_length": 0,
                "enclosure_url": enclosure_url,
                "guid_permalink": guid if guid else None
            }

        except Exception as e:
            print(f"Error parsing RSS item: {e}")
            return None

    def _get_element_text(self, element, tag: str) -> str:
        """Safely get text from XML element"""
        child = element.find(tag)
        return child.text.strip() if child is not None and child.text else ""

    def _extract_ticker(self, title: str, link: str) -> str:
        """Extract ticker symbol from title or URL"""
        # Try to extract from title (common patterns)
        title_patterns = [
            r'\b([A-Z]{1,5})\b(?:\s+Reports|\s+Announces|\s+Files|\s+Completes)',
            r'^\s*([A-Z]{1,5})\s*[:\-]',
            r'\(([A-Z]{1,5})\)',
            r'\b([A-Z]{2,5})\s+(?:Stock|Shares|Corp|Inc|Ltd)'
        ]

        for pattern in title_patterns:
            match = re.search(pattern, title)
            if match:
                ticker = match.group(1)
                if 1 <= len(ticker) <= 5:  # Valid ticker length
                    return ticker

        # Try to extract from URL
        if link and '/news/' in link:
            parts = link.split('/news/')
            if len(parts) > 1:
                url_parts = parts[1].split('/')
                if url_parts and url_parts[0].isupper() and 1 <= len(url_parts[0]) <= 5:
                    return url_parts[0]

        return ""

    def _clean_description(self, description: str) -> str:
        """Clean and format description text"""
        if not description:
            return ""

        # Remove HTML tags
        clean_text = re.sub(r'<[^>]+>', '', description)

        # Remove extra whitespace
        clean_text = ' '.join(clean_text.split())

        # Truncate if too long
        if len(clean_text) > 500:
            clean_text = clean_text[:500] + "..."

        return clean_text.strip()

    def _parse_pub_date(self, pub_date: str) -> str:
        """Parse RSS publication date to ISO format"""
        if not pub_date:
            return datetime.now().isoformat()

        try:
            # RFC 2822 format with GMT timezone
            if 'GMT' in pub_date:
                # Replace GMT with +0000 for proper parsing
                pub_date_fixed = pub_date.replace(' GMT', ' +0000')
                dt = datetime.strptime(pub_date_fixed, '%a, %d %b %Y %H:%M:%S %z')
                return dt.isoformat()

            # RFC 2822 format (typical for RSS)
            dt = datetime.strptime(pub_date, '%a, %d %b %Y %H:%M:%S %z')
            return dt.isoformat()
        except:
            try:
                # Alternative format without timezone
                dt = datetime.strptime(pub_date, '%a, %d %b %Y %H:%M:%S')
                return dt.isoformat()
            except:
                # Fallback to current time
                return datetime.now().isoformat()

    def _categorize_news(self, title: str, description: str) -> str:
        """Categorize news based on title and description"""
        text = f"{title} {description}".lower()

        categories = {
            'earnings': ['earnings', 'reports q', 'quarterly', 'revenue', 'profit', 'eps'],
            'acquisitions': ['acquires', 'acquisition', 'merger', 'buyout', 'takeover'],
            'fda': ['fda', 'approval', 'drug', 'clinical', 'trial', 'regulatory'],
            'ipo': ['ipo', 'initial public offering', 'goes public', 'listing'],
            'offerings': ['offering', 'raise', 'funding', 'investment', 'capital'],
            'dividends': ['dividend', 'payout', 'distribution'],
            'splits': ['stock split', 'split'],
            'leadership': ['ceo', 'cfo', 'president', 'director', 'executive', 'leadership'],
            'partnerships': ['partnership', 'collaboration', 'joint venture', 'alliance'],
            'products': ['launches', 'product', 'service', 'release']
        }

        for category, keywords in categories.items():
            if any(keyword in text for keyword in keywords):
                return category

        return 'general'

    async def get_ticker_news(self, ticker: str, hours: int = 24) -> List[Dict]:
        """Get news for specific ticker from last N hours"""
        ticker = ticker.upper()  # Normalize ticker to uppercase
        all_news = await self.get_latest_news(limit=100)

        # Filter by ticker and time
        from datetime import timezone
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        filtered_news = []

        for item in all_news:
            # Check if ticker matches (case-insensitive)
            if item['ticker'] and item['ticker'].upper() == ticker or ticker in [s.upper() for s in item['symbols']]:
                # Check if within time range
                try:
                    pub_date = datetime.fromisoformat(item['published_utc'])
                    # Make sure pub_date has timezone info
                    if pub_date.tzinfo is None:
                        pub_date = pub_date.replace(tzinfo=timezone.utc)

                    if pub_date >= cutoff_time:
                        filtered_news.append(item)
                except:
                    # Skip items with date parsing errors
                    pass

        return filtered_news

    async def get_breaking_news(self, hours: int = 1) -> List[Dict]:
        """Get breaking news from last N hours"""
        all_news = await self.get_latest_news(limit=100)

        # Filter by time
        from datetime import timezone
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        breaking_news = []

        for item in all_news:
            try:
                pub_date = datetime.fromisoformat(item['published_utc'])
                # Make sure pub_date has timezone info
                if pub_date.tzinfo is None:
                    pub_date = pub_date.replace(tzinfo=timezone.utc)

                if pub_date >= cutoff_time:
                    breaking_news.append(item)
            except Exception as e:
                # Skip items with date parsing errors
                pass

        return breaking_news

    def print_feed_summary(self, news_items: List[Dict]):
        """Print feed summary statistics to console"""
        # Calculate statistics
        with_tickers = len([item for item in news_items if item['ticker']])
        categories = {}
        for item in news_items:
            cat = item['category']
            categories[cat] = categories.get(cat, 0) + 1

        print("\n" + "="*80)
        print("STOCK TITAN RSS FEED SUMMARY")
        print("="*80)
        print(f"Total items: {len(news_items)}")
        print(f"Items with tickers: {with_tickers} ({round((with_tickers / len(news_items)) * 100, 1) if news_items else 0}%)")
        print(f"\nCategories:")
        for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            print(f"  {cat}: {count}")

        # Show unique tickers
        unique_tickers = set(item['ticker'] for item in news_items if item['ticker'])
        if unique_tickers:
            print(f"\nUnique tickers found: {len(unique_tickers)}")
            print(f"Tickers: {', '.join(sorted(unique_tickers)[:20])}{'...' if len(unique_tickers) > 20 else ''}")

        print("="*80)

    def _is_market_hours(self) -> bool:
        """Check if current time is during market hours (9:30 AM - 4:00 PM ET)"""
        import pytz
        et_tz = pytz.timezone('US/Eastern')
        now_et = datetime.now(et_tz)

        # Skip weekends
        if now_et.weekday() >= 5:  # Saturday = 5, Sunday = 6
            return False

        # Market hours: 9:30 AM - 4:00 PM ET
        market_open = now_et.replace(hour=9, minute=30, second=0, microsecond=0)
        market_close = now_et.replace(hour=16, minute=0, second=0, microsecond=0)

        return market_open <= now_et <= market_close

    def _is_extended_hours(self) -> bool:
        """Check if current time is during extended hours (4:00 AM - 9:30 AM ET, 4:00 PM - 8:00 PM ET)"""
        import pytz
        et_tz = pytz.timezone('US/Eastern')
        now_et = datetime.now(et_tz)

        # Skip weekends
        if now_et.weekday() >= 5:  # Saturday = 5, Sunday = 6
            return False

        # Pre-market: 4:00 AM - 9:30 AM ET
        premarket_start = now_et.replace(hour=4, minute=0, second=0, microsecond=0)
        premarket_end = now_et.replace(hour=9, minute=30, second=0, microsecond=0)

        # After-hours: 4:00 PM - 8:00 PM ET
        afterhours_start = now_et.replace(hour=16, minute=0, second=0, microsecond=0)
        afterhours_end = now_et.replace(hour=20, minute=0, second=0, microsecond=0)

        return (premarket_start <= now_et < premarket_end) or (afterhours_start < now_et <= afterhours_end)

    async def start_scheduled_collection(self):
        """Start scheduled collection service with market-aware intervals"""
        print("Stock Titan RSS scheduled collection started")
        print(f"Feed URL: {self.rss_url}")
        print(f"Starting at: {datetime.now().isoformat()}")

        while True:
            try:
                # Determine collection interval based on market status
                if self._is_market_hours():
                    interval_minutes = 3  # Every 3 minutes during market hours
                    status = "MARKET HOURS"
                elif self._is_extended_hours():
                    interval_minutes = 10  # Every 10 minutes during extended hours
                    status = "EXTENDED HOURS"
                else:
                    interval_minutes = 30  # Every 30 minutes during off-hours
                    status = "OFF HOURS"

                print(f"\n[{datetime.now().isoformat()}] {status} - Collecting Stock Titan RSS feed...")

                # Collect and store news
                news_items = await self.get_latest_news(limit=50)

                if news_items:
                    print(f"Collected {len(news_items)} RSS items")
                    # Data is automatically stored in QuestDB by get_latest_news()
                else:
                    print("No new RSS items found")

                # Wait for next collection
                sleep_seconds = interval_minutes * 60
                print(f"Next collection in {interval_minutes} minutes...")
                await asyncio.sleep(sleep_seconds)

            except Exception as e:
                print(f"Error in Stock Titan RSS scheduled collection: {e}")
                print("Retrying in 5 minutes...")
                await asyncio.sleep(300)  # Wait 5 minutes before retry

async def main():
    """Run Stock Titan RSS feed - scheduled collection or one-time display"""
    import sys

    # Check if we want scheduled collection (for systemd service)
    if len(sys.argv) > 1 and sys.argv[1] == "--scheduled":
        # Run scheduled collection for systemd service
        async with StockTitanRSSClient() as client:
            await client.start_scheduled_collection()
    else:
        # Display Stock Titan RSS feed from last 2 hours (manual mode)
        async with StockTitanRSSClient() as client:
            print("\n" + "="*80)
            print(" STOCK TITAN RSS FEED - LAST 2 HOURS")
            print("="*80)
            print(f" Feed URL: {client.rss_url}")
            print(f" Timestamp: {datetime.now().isoformat()}")
            print("="*80)

            # Get breaking news from last 2 hours
            all_news = await client.get_breaking_news(hours=2)

            if not all_news:
                print("\nNo news items found in the last 2 hours.")
                print("="*80)
                return

            print(f"\nTotal items in last 2 hours: {len(all_news)}\n")
            print("-"*80)

            # Print each news item in detail
            for idx, item in enumerate(all_news, 1):
                print(f"\n[{idx}] {item['title']}")
                print(f"    Published: {item['published_utc']}")
                print(f"    Ticker: {item['ticker'] if item['ticker'] else 'N/A'}")
                print(f"    Category: {item['category']}")
                print(f"    URL: {item['url']}")
                print(f"    GUID: {item.get('guid_permalink', 'N/A')}")
                print(f"    Author: {item.get('author', 'N/A')}")
                if item.get('rss_category'):
                    print(f"    RSS Category: {item['rss_category']}")
                if item['description']:
                    print(f"    Description: {item['description'][:200]}..." if len(item['description']) > 200 else f"    Description: {item['description']}")
                print("-"*80)

            # Print summary statistics
            client.print_feed_summary(all_news)

            # Show update timestamp
            print(f"\nLast updated: {datetime.now().isoformat()}")
            print(f"Feed URL: {client.rss_url}")

if __name__ == "__main__":
    asyncio.run(main())