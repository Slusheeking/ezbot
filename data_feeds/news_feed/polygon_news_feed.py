#!/usr/bin/env python3
"""
Polygon News Feed Client
Fast, comprehensive news parsing from Polygon.io API with sentiment analysis
"""

import os
import aiohttp
import asyncio
import yaml
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file (look in parent directories)
load_dotenv()

def load_settings():
    """Load settings from YAML configuration file"""
    settings_path = Path(__file__).parent / "settings.yaml"
    try:
        with open(settings_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"Warning: Could not load settings.yaml: {e}")
        return None

class PolygonNewsClient:
    """Polygon.io news feed client for comprehensive financial news"""

    def __init__(self):
        # Load settings
        self.settings = load_settings()

        # Get configuration from settings or use defaults
        if self.settings and 'api' in self.settings and 'polygon' in self.settings['api']:
            polygon_config = self.settings['api']['polygon']
            self.base_url = polygon_config.get('base_url', "https://api.polygon.io/v2/reference/news")
            self.max_retries = polygon_config.get('max_retries', 3)
            self.retry_delay = polygon_config.get('retry_delay', 2)
            api_key_env = polygon_config.get('token_env_var', "POLYGON_API_KEY")
        else:
            # Fallback to defaults if settings not available
            self.base_url = "https://api.polygon.io/v2/reference/news"
            self.max_retries = 3
            self.retry_delay = 2
            api_key_env = "POLYGON_API_KEY"

        # Get API key from environment variables
        self.api_key = os.getenv(api_key_env)

        if not self.api_key:
            raise ValueError(
                f"{api_key_env} not found in environment variables. "
                f"Please set it in your .env file: {api_key_env}=your_api_key_here"
            )

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

    async def get_latest_news(self, limit: int = 1000, order: str = "desc", sort: str = "published_utc") -> List[Dict]:
        """Get latest news with comprehensive data extraction"""
        for attempt in range(self.max_retries):
            try:
                # Get max limit from settings
                max_limit = 1000
                if self.settings and 'api' in self.settings and 'polygon' in self.settings['api']:
                    max_limit = self.settings['api']['polygon'].get('max_limit', 1000)

                params = {
                    "apikey": self.api_key,
                    "limit": min(limit, max_limit),
                    "order": order,
                    "sort": sort
                }

                # Get timeout from settings
                timeout_seconds = 30
                if self.settings and 'api' in self.settings and 'polygon' in self.settings['api']:
                    timeout_seconds = self.settings['api']['polygon'].get('timeout', 30)

                timeout = aiohttp.ClientTimeout(total=timeout_seconds)
                async with self.session.get(self.base_url, params=params, timeout=timeout) as response:
                    if response.status == 429:  # Rate limited
                        wait_time = int(response.headers.get('Retry-After', self.retry_delay * (attempt + 1)))
                        print(f"Rate limited. Waiting {wait_time} seconds...")
                        await asyncio.sleep(wait_time)
                        continue

                    if response.status != 200:
                        print(f"Error fetching Polygon news: {response.status}")
                        if attempt < self.max_retries - 1:
                            await asyncio.sleep(self.retry_delay * (attempt + 1))
                            continue
                        return []

                    data = await response.json()
                    processed_news = self._process_news_data(data.get('results', []))

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
                print(f"Error fetching Polygon news (attempt {attempt + 1}): {e}")
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

            # Create Polygon news table
            await self._create_polygon_table()

        except Exception as e:
            print(f"Failed to connect to QuestDB: {e}")
            raise

    async def _create_polygon_table(self):
        """Create QuestDB table for Polygon news data"""

        # Polygon news table
        polygon_news_sql = """
        CREATE TABLE IF NOT EXISTS polygon_news (
            timestamp TIMESTAMP,
            id STRING,
            title STRING,
            description STRING,
            content STRING,
            url STRING,
            amp_url STRING,
            image_url STRING,
            author STRING,
            published_utc TIMESTAMP,
            primary_ticker SYMBOL CAPACITY 1000 CACHE,
            tickers STRING,
            symbols STRING,
            keywords STRING,
            category SYMBOL CAPACITY 50 CACHE,
            sentiment SYMBOL CAPACITY 20 CACHE,
            insights STRING,
            publisher_name STRING,
            publisher_homepage STRING,
            publisher_logo STRING,
            publisher_favicon STRING,
            source_name STRING,
            has_content BOOLEAN,
            content_length INT,
            has_image BOOLEAN,
            has_amp BOOLEAN,
            keyword_count INT,
            ticker_count INT,
            insight_count INT,
            collected_at TIMESTAMP
        ) TIMESTAMP(timestamp) PARTITION BY DAY WAL;
        """

        cursor = self.questdb_conn.cursor()
        try:
            cursor.execute(polygon_news_sql)
            self.questdb_conn.commit()
            print("Polygon news table created successfully")
        except Exception as e:
            print(f"Error creating Polygon news table: {e}")
            self.questdb_conn.rollback()
            raise
        finally:
            cursor.close()

    async def _store_news_data(self, news_items: List[Dict]) -> bool:
        """Store Polygon news data in QuestDB"""
        if not news_items or not self.questdb_conn:
            return True

        cursor = self.questdb_conn.cursor()

        # Prepare insert SQL for Polygon news table
        insert_sql = """
        INSERT INTO polygon_news (
            timestamp, id, title, description, content, url, amp_url, image_url,
            author, published_utc, primary_ticker, tickers, symbols, keywords,
            category, sentiment, insights, publisher_name, publisher_homepage,
            publisher_logo, publisher_favicon, source_name, has_content,
            content_length, has_image, has_amp, keyword_count, ticker_count,
            insight_count, collected_at
        ) VALUES %s
        """

        # Convert news items to tuples for insertion
        values = []
        current_time = datetime.now()

        for item in news_items:
            try:
                # Parse published date
                published_utc = self._parse_datetime(item.get('published_utc'))

                # Convert lists to comma-separated strings
                tickers = ','.join(item.get('tickers', [])) if item.get('tickers') else ''
                symbols = ','.join(item.get('symbols', [])) if item.get('symbols') else ''
                keywords = ','.join(item.get('keywords', [])) if item.get('keywords') else ''
                insights = str(item.get('insights', '')) if item.get('insights') else ''

                values.append((
                    current_time,  # timestamp
                    item.get('id', ''),
                    item.get('title', ''),
                    item.get('description', ''),
                    item.get('content', ''),
                    item.get('url', ''),
                    item.get('amp_url', ''),
                    item.get('image_url', ''),
                    item.get('author', ''),
                    published_utc,
                    item.get('primary_ticker', ''),
                    tickers,
                    symbols,
                    keywords,
                    item.get('category', ''),
                    item.get('sentiment', ''),
                    insights,
                    item.get('publisher', {}).get('name', ''),
                    item.get('publisher', {}).get('homepage_url', ''),
                    item.get('publisher', {}).get('logo_url', ''),
                    item.get('publisher', {}).get('favicon_url', ''),
                    item.get('source_name', ''),
                    item.get('has_content', False),
                    item.get('content_length', 0),
                    item.get('has_image', False),
                    item.get('has_amp', False),
                    item.get('keyword_count', 0),
                    item.get('ticker_count', 0),
                    item.get('insight_count', 0),
                    current_time  # collected_at
                ))
            except Exception as e:
                print(f"Error processing Polygon news item: {e}")
                continue

        try:
            if values:
                execute_values(cursor, insert_sql, values, template=None, page_size=self.questdb_config['batch_size'])
                self.questdb_conn.commit()
                print(f"Stored {len(values)} Polygon news records in QuestDB")
            return True

        except Exception as e:
            print(f"Error storing Polygon news data in QuestDB: {e}")
            self.questdb_conn.rollback()
            return False
        finally:
            cursor.close()

    def _parse_datetime(self, date_str: str) -> Optional[datetime]:
        """Parse datetime string to datetime object"""
        if not date_str:
            return datetime.now()

        try:
            # Handle ISO format
            if 'T' in date_str:
                return datetime.fromisoformat(date_str.replace('Z', '+00:00')).replace(tzinfo=None)
            else:
                return datetime.fromisoformat(date_str)
        except Exception:
            return datetime.now()

    def _process_news_data(self, results: List[Dict]) -> List[Dict]:
        """Process and enrich news data from Polygon API"""
        processed_news = []

        for item in results:
            try:
                processed_item = self._process_single_item(item)
                if processed_item:
                    processed_news.append(processed_item)
            except Exception as e:
                print(f"Error processing news item: {e}")
                continue

        return processed_news

    def _process_single_item(self, item: Dict) -> Optional[Dict]:
        """Process a single news item with comprehensive data extraction"""
        try:
            # Basic article info
            article_id = item.get('id', '')
            title = item.get('title', '')
            description = item.get('description', '')
            article_url = item.get('article_url', '')
            amp_url = item.get('amp_url', '')
            image_url = item.get('image_url', '')
            author = item.get('author', '')
            published_utc = item.get('published_utc', '')

            # Publisher information
            publisher = item.get('publisher', {})
            publisher_name = publisher.get('name', '')
            publisher_homepage = publisher.get('homepage_url', '')
            publisher_logo = publisher.get('logo_url', '')
            publisher_favicon = publisher.get('favicon_url', '')

            # Tickers and keywords
            tickers = item.get('tickers', [])
            keywords = item.get('keywords', [])

            # Insights with sentiment analysis
            insights = item.get('insights', [])
            processed_insights = self._process_insights(insights)

            # Calculate overall sentiment from insights
            overall_sentiment = self._calculate_overall_sentiment(processed_insights)

            # Extract primary ticker (first in list or from insights)
            primary_ticker = self._extract_primary_ticker(tickers, processed_insights)

            # Categorize news
            category = self._categorize_news(title, description, keywords)

            # Parse and validate published date
            parsed_date = self._parse_published_date(published_utc)

            return {
                "source": "polygon_api",
                "id": article_id,
                "title": title.strip(),
                "description": description.strip() if description else "",
                "content": "",  # Polygon doesn't provide full content
                "url": article_url,
                "amp_url": amp_url,
                "image_url": image_url,
                "author": author,
                "published_utc": parsed_date,
                "primary_ticker": primary_ticker,
                "tickers": tickers,
                "symbols": tickers,  # For compatibility
                "keywords": keywords,
                "category": category,
                "sentiment": overall_sentiment,
                "insights": processed_insights,
                "publisher": {
                    "name": publisher_name,
                    "homepage_url": publisher_homepage,
                    "logo_url": publisher_logo,
                    "favicon_url": publisher_favicon
                },
                "source_name": "Polygon.io",
                "has_content": False,
                "content_length": 0,
                "has_image": bool(image_url),
                "has_amp": bool(amp_url),
                "keyword_count": len(keywords),
                "ticker_count": len(tickers),
                "insight_count": len(processed_insights)
            }

        except Exception as e:
            print(f"Error processing single news item: {e}")
            return None

    def _process_insights(self, insights: List[Dict]) -> List[Dict]:
        """Process insights with sentiment analysis"""
        processed = []
        for insight in insights:
            processed_insight = {
                "ticker": insight.get('ticker', ''),
                "sentiment": insight.get('sentiment', 'neutral'),
                "sentiment_reasoning": insight.get('sentiment_reasoning', ''),
                "confidence": self._calculate_sentiment_confidence(insight.get('sentiment_reasoning', ''))
            }
            processed.append(processed_insight)
        return processed

    def _calculate_sentiment_confidence(self, reasoning: str) -> str:
        """Calculate confidence level from sentiment reasoning"""
        if not reasoning:
            return "low"

        # Simple heuristics for confidence based on reasoning length and keywords
        confidence_indicators = ['strong', 'significant', 'major', 'substantial', 'clear', 'definitive']
        uncertainty_indicators = ['may', 'might', 'could', 'possible', 'potential', 'uncertain']

        reasoning_lower = reasoning.lower()
        confidence_score = sum(1 for indicator in confidence_indicators if indicator in reasoning_lower)
        uncertainty_score = sum(1 for indicator in uncertainty_indicators if indicator in reasoning_lower)

        if confidence_score > uncertainty_score and len(reasoning) > 100:
            return "high"
        elif confidence_score > 0 or len(reasoning) > 50:
            return "medium"
        else:
            return "low"

    def _calculate_overall_sentiment(self, insights: List[Dict]) -> str:
        """Calculate overall article sentiment from insights"""
        if not insights:
            return "neutral"

        sentiment_scores = {"positive": 1, "neutral": 0, "negative": -1}
        total_score = sum(sentiment_scores.get(insight['sentiment'], 0) for insight in insights)

        if total_score > 0:
            return "positive"
        elif total_score < 0:
            return "negative"
        else:
            return "neutral"

    def _extract_primary_ticker(self, tickers: List[str], insights: List[Dict]) -> str:
        """Extract primary ticker from tickers list or insights"""
        if tickers:
            return tickers[0]
        elif insights:
            for insight in insights:
                if insight.get('ticker'):
                    return insight['ticker']
        return ""

    def _categorize_news(self, title: str, description: str, keywords: List[str]) -> str:
        """Categorize news based on title, description, and keywords"""
        text = f"{title} {description} {' '.join(keywords)}".lower()

        categories = {
            'earnings': ['earnings', 'quarterly', 'revenue', 'profit', 'eps', 'financial results'],
            'acquisitions': ['acquisition', 'merger', 'buyout', 'takeover', 'acquired'],
            'fda': ['fda', 'approval', 'drug', 'clinical', 'trial', 'regulatory'],
            'ipo': ['ipo', 'initial public offering', 'goes public', 'listing', 'debut'],
            'offerings': ['offering', 'raise', 'funding', 'investment', 'capital', 'financing'],
            'dividends': ['dividend', 'payout', 'distribution', 'yield'],
            'splits': ['stock split', 'split'],
            'leadership': ['ceo', 'cfo', 'president', 'director', 'executive', 'leadership'],
            'partnerships': ['partnership', 'collaboration', 'joint venture', 'alliance'],
            'products': ['launches', 'product', 'service', 'release'],
            'legal': ['lawsuit', 'litigation', 'settlement', 'court', 'legal'],
            'analyst': ['analyst', 'rating', 'upgrade', 'downgrade', 'target price'],
            'market': ['market', 'trading', 'volume', 'volatility', 'index']
        }

        for category, keywords_list in categories.items():
            if any(keyword in text for keyword in keywords_list):
                return category

        return 'general'

    def _parse_published_date(self, published_utc: str) -> str:
        """Parse and validate published date"""
        if not published_utc:
            return datetime.now(timezone.utc).isoformat()

        try:
            # Parse ISO format date
            dt = datetime.fromisoformat(published_utc.replace('Z', '+00:00'))
            return dt.isoformat()
        except:
            try:
                # Try parsing without timezone
                dt = datetime.fromisoformat(published_utc.replace('Z', ''))
                dt = dt.replace(tzinfo=timezone.utc)
                return dt.isoformat()
            except:
                # Fallback to current time
                return datetime.now(timezone.utc).isoformat()

    async def get_breaking_news(self, hours: int = 2) -> List[Dict]:
        """Get breaking news from last N hours"""
        # Get recent news with high limit
        all_news = await self.get_latest_news(limit=1000)

        # Filter by time
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        breaking_news = []

        for item in all_news:
            try:
                pub_date = datetime.fromisoformat(item['published_utc'])
                # Ensure timezone info
                if pub_date.tzinfo is None:
                    pub_date = pub_date.replace(tzinfo=timezone.utc)

                if pub_date >= cutoff_time:
                    breaking_news.append(item)
            except Exception as e:
                # Skip items with date parsing errors
                pass

        return breaking_news

    async def get_ticker_news(self, ticker: str, hours: int = 24) -> List[Dict]:
        """Get news for specific ticker from last N hours"""
        ticker = ticker.upper()

        # First try to get ticker-specific news from API
        try:
            params = {
                "apikey": self.api_key,
                "ticker": ticker,
                "limit": 1000,
                "order": "desc",
                "sort": "published_utc"
            }

            timeout = aiohttp.ClientTimeout(total=30)
            async with self.session.get(self.base_url, params=params, timeout=timeout) as response:
                if response.status == 200:
                    data = await response.json()
                    ticker_news = self._process_news_data(data.get('results', []))

                    # Filter by time
                    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
                    filtered_news = []

                    for item in ticker_news:
                        try:
                            pub_date = datetime.fromisoformat(item['published_utc'])
                            if pub_date.tzinfo is None:
                                pub_date = pub_date.replace(tzinfo=timezone.utc)

                            if pub_date >= cutoff_time:
                                filtered_news.append(item)
                        except:
                            pass

                    return filtered_news
        except:
            pass

        # Fallback: filter from general news
        all_news = await self.get_latest_news(limit=1000)
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        filtered_news = []

        for item in all_news:
            if ticker in item.get('tickers', []) or ticker == item.get('primary_ticker', ''):
                try:
                    pub_date = datetime.fromisoformat(item['published_utc'])
                    if pub_date.tzinfo is None:
                        pub_date = pub_date.replace(tzinfo=timezone.utc)

                    if pub_date >= cutoff_time:
                        filtered_news.append(item)
                except:
                    pass

        return filtered_news

    def print_feed_summary(self, news_items: List[Dict]):
        """Print comprehensive feed summary to console"""
        if not news_items:
            return

        # Calculate statistics
        total_items = len(news_items)
        with_tickers = len([item for item in news_items if item.get('primary_ticker')])
        with_images = len([item for item in news_items if item.get('has_image')])
        with_insights = len([item for item in news_items if item.get('insights')])

        # Category distribution
        categories = {}
        for item in news_items:
            cat = item.get('category', 'general')
            categories[cat] = categories.get(cat, 0) + 1

        # Sentiment distribution
        sentiments = {}
        for item in news_items:
            sent = item.get('sentiment', 'neutral')
            sentiments[sent] = sentiments.get(sent, 0) + 1

        # Publisher distribution (top 10)
        publishers = {}
        for item in news_items:
            pub = item.get('publisher', {}).get('name', 'Unknown')
            publishers[pub] = publishers.get(pub, 0) + 1

        print("\n" + "="*80)
        print("POLYGON NEWS FEED SUMMARY")
        print("="*80)
        print(f"Total items: {total_items}")
        print(f"Items with tickers: {with_tickers} ({(with_tickers/total_items)*100:.1f}%)")
        print(f"Items with images: {with_images} ({(with_images/total_items)*100:.1f}%)")
        print(f"Items with insights: {with_insights} ({(with_insights/total_items)*100:.1f}%)")

        print(f"\nSentiment Distribution:")
        for sentiment in ['positive', 'neutral', 'negative']:
            count = sentiments.get(sentiment, 0)
            print(f"  {sentiment}: {count} ({(count/total_items)*100:.1f}%)")

        print(f"\nTop Categories:")
        for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {cat}: {count}")

        print(f"\nTop Publishers:")
        for pub, count in sorted(publishers.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {pub}: {count}")

        # Show unique tickers
        unique_tickers = set(item.get('primary_ticker') for item in news_items if item.get('primary_ticker'))
        if unique_tickers:
            print(f"\nUnique tickers found: {len(unique_tickers)}")
            print(f"Top tickers: {', '.join(sorted(list(unique_tickers))[:20])}{'...' if len(unique_tickers) > 20 else ''}")

        print("="*80)

    async def start_scheduled_collection(self):
        """Start the scheduled polygon news collection process"""
        print("Starting Polygon News Feed Collection")
        print("Press Ctrl+C to stop")
        print("-" * 60)
        
        # Track last collection time to avoid duplicates
        self.last_collection = datetime.now(timezone.utc) - timedelta(hours=1)
        
        try:
            while True:
                current_time = datetime.now()
                
                # Determine collection interval based on market hours and settings
                if self._is_market_hours(current_time):
                    interval = self.settings['collection']['poll_interval'] if self.settings else 180  # 3 minutes
                elif self._is_extended_hours(current_time):
                    interval = self.settings['collection']['after_hours_interval'] if self.settings else 600  # 10 minutes
                else:
                    # Outside trading hours, check less frequently
                    interval = self.settings['collection']['weekend_interval'] if self.settings else 1800  # 30 minutes
                
                # Collect news
                await self._collect_polygon_news()
                
                # Sleep until next collection
                print(f"Next collection in {interval} seconds ({interval//60} minutes)")
                await asyncio.sleep(interval)
                
        except KeyboardInterrupt:
            print("\nShutting down Polygon news feed")
        except Exception as e:
            print(f"Error in collection loop: {e}")
            raise
    
    async def _collect_polygon_news(self):
        """Collect polygon news and store in database"""
        try:
            # Get latest news
            news_items = await self.get_latest_news(limit=1000)
            
            if news_items:
                # Filter for new items since last collection
                new_items = []
                current_time = datetime.now(timezone.utc)
                
                for item in news_items:
                    try:
                        pub_date = datetime.fromisoformat(item['published_utc'])
                        if pub_date.tzinfo is None:
                            pub_date = pub_date.replace(tzinfo=timezone.utc)
                        
                        # Only include items newer than last collection
                        if pub_date > self.last_collection:
                            new_items.append(item)
                    except:
                        continue
                
                if new_items:
                    # Update last collection time
                    self.last_collection = current_time
                    
                    print(f"Collected {len(new_items)} new Polygon news items at {current_time.strftime('%H:%M:%S')}")
                    
                    # Show recent items
                    for item in new_items[:3]:  # Show top 3
                        print(f"   • {item['title'][:80]}..." if len(item['title']) > 80 else f"   • {item['title']}")
                        if item.get('primary_ticker'):
                            print(f"     [{item['primary_ticker']}] {item['sentiment']} sentiment")
                else:
                    print(f"No new items since last collection at {current_time.strftime('%H:%M:%S')}")
            else:
                print(f"No news items found at {current_time.strftime('%H:%M:%S')}")
                
        except Exception as e:
            print(f"Error collecting Polygon news: {e}")
    
    def _is_market_hours(self, dt: datetime) -> bool:
        """Check if current time is during market hours (9:30 AM - 4:00 PM EST)"""
        if dt.weekday() >= 5:  # Weekend
            return False
        
        # Convert to EST (approximate)
        time_str = dt.strftime("%H:%M")
        return "09:30" <= time_str <= "16:00"
    
    def _is_extended_hours(self, dt: datetime) -> bool:
        """Check if current time is during extended hours (4:00 AM - 8:00 PM EST)"""
        if dt.weekday() >= 5:  # Weekend
            return False
        
        # Convert to EST (approximate)
        time_str = dt.strftime("%H:%M")
        return "04:00" <= time_str <= "20:00"

async def main():
    """Run Polygon news feed - scheduled collection or one-time display"""
    import sys
    
    # Check if we want scheduled collection (for systemd service)
    if len(sys.argv) > 1 and sys.argv[1] == "--scheduled":
        # Run scheduled collection for systemd service
        async with PolygonNewsClient() as client:
            await client.start_scheduled_collection()
    else:
        # One-time display for manual runs (show last 2 hours)
        async with PolygonNewsClient() as client:
            print("\n" + "="*80)
            print(" POLYGON NEWS FEED - LAST 2 HOURS")
            print("="*80)
            print(f" API Endpoint: {client.base_url}")
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
                print(f"    Primary Ticker: {item.get('primary_ticker', 'N/A')}")
                print(f"    All Tickers: {', '.join(item.get('tickers', [])) if item.get('tickers') else 'N/A'}")
                print(f"    Category: {item['category']}")
                print(f"    Sentiment: {item['sentiment']}")
                print(f"    Publisher: {item.get('publisher', {}).get('name', 'N/A')}")
                print(f"    Author: {item.get('author', 'N/A')}")
                print(f"    URL: {item['url']}")

                if item.get('insights'):
                    print(f"    Insights: {len(item['insights'])} sentiment analysis(es)")
                    for insight in item['insights'][:2]:  # Show first 2 insights
                        print(f"      - {insight['ticker']}: {insight['sentiment']} ({insight.get('confidence', 'N/A')})")

                if item.get('keywords'):
                    keywords_str = ', '.join(item['keywords'][:5])
                    if len(item['keywords']) > 5:
                        keywords_str += f" + {len(item['keywords']) - 5} more"
                    print(f"    Keywords: {keywords_str}")

                if item['description']:
                    desc = item['description'][:200] + "..." if len(item['description']) > 200 else item['description']
                    print(f"    Description: {desc}")

                print("-"*80)

            # Print summary statistics
            client.print_feed_summary(all_news)

            # Show update timestamp
            print(f"\nLast updated: {datetime.now().isoformat()}")
            print(f"API Endpoint: {client.base_url}")

if __name__ == "__main__":
    asyncio.run(main())