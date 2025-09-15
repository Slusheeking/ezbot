#!/usr/bin/env python3
"""
Reddit Feed Parser
Financial discussion monitoring from Reddit subreddits
"""

import os
import sys
import asyncio
import praw
import yaml
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dotenv import load_dotenv
from pathlib import Path
import re

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

class RedditFeedClient:
    """Reddit feed parser for financial discussions"""

    def __init__(self):
        # Load settings
        self.settings = load_settings()

        # Reddit API credentials from environment
        self.client_id = os.getenv('CLIENT_ID')
        self.client_secret = os.getenv('CLIENT_SECRET')
        self.username = os.getenv('USERNAME')
        self.password = os.getenv('PASSWORD')
        self.user_agent = os.getenv('USER_AGENT', 'reddit-feed-bot/1.0')

        # Initialize Reddit client
        print(f"Initializing Reddit client with user: {self.username}")
        self.reddit = praw.Reddit(
            client_id=self.client_id,
            client_secret=self.client_secret,
            username=self.username,
            password=self.password,
            user_agent=self.user_agent
        )
        print("Reddit client initialized successfully")

        # QuestDB connection
        self.questdb_conn = None
        self.questdb_config = self.settings.get('questdb') if self.settings else None

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

    async def get_financial_posts(self, subreddits: List[str] = None, limit: int = None) -> List[Dict]:
        """Get financial posts from specified subreddits"""
        if subreddits is None:
            subreddits = [
                # Core financial subreddits
                'wallstreetbets', 'stocks', 'investing', 'SecurityAnalysis', 'ValueInvesting',

                # High priority for trading strategies
                '10xPennyStocks', 'Daytrading', 'pennystocks', 'StockMarket', 'options',

                # Medium priority momentum/swing
                'RobinhoodPennystocks', 'SwingTrading', 'SPY', 'smallstreetbets',

                # Specialized channels
                'biotech_stocks', 'MillennialBets', 'UnusualWhales', 'Superstonk',

                # Crypto subreddits
                'cryptocurrency', 'Bitcoin', 'ethereum', 'CryptoCurrency', 'btc', 'ethtrader',
                'CryptoMarkets', 'altcoin', 'bitcoinmarkets', 'CryptoCurrencyTrading'
            ]

        if limit is None:
            limit = 100
            if self.settings and 'collection' in self.settings:
                limit = self.settings['collection'].get('max_posts_per_subreddit', 100)

        print(f"Fetching posts from {len(subreddits)} subreddits with limit {limit}")
        all_posts = []

        for subreddit_name in subreddits:
            try:
                print(f"Fetching from r/{subreddit_name}...")
                subreddit = self.reddit.subreddit(subreddit_name)

                # Use crypto-specific limit if it's a crypto subreddit
                current_limit = limit
                if self.settings and 'collection' in self.settings:
                    crypto_limit = self.settings['collection'].get('crypto_post_limit', limit)
                    crypto_subreddits = []
                    if 'filters' in self.settings and 'crypto_subreddit_priority' in self.settings['filters']:
                        priorities = self.settings['filters']['crypto_subreddit_priority']
                        crypto_subreddits = priorities.get('high', []) + priorities.get('medium', []) + priorities.get('low', [])

                    if subreddit_name in crypto_subreddits:
                        current_limit = crypto_limit

                posts = subreddit.hot(limit=current_limit)

                post_count = 0
                for post in posts:
                    processed_post = self._process_post(post, subreddit_name)
                    if processed_post:
                        all_posts.append(processed_post)
                        post_count += 1

                print(f"  Found {post_count} posts from r/{subreddit_name}")

            except Exception as e:
                print(f"Error fetching from r/{subreddit_name}: {e}")
                continue

        print(f"Total posts collected: {len(all_posts)}")

        # Store in QuestDB if available
        if self.questdb_conn and all_posts:
            print("Storing posts in QuestDB...")
            await self._store_reddit_data(all_posts)
        elif not self.questdb_conn:
            print("QuestDB connection not available - skipping storage")

        return all_posts

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

            # Create Reddit posts table
            await self._create_reddit_table()

            # Create crypto-specific indices
            await self._create_indices()

        except Exception as e:
            print(f"Failed to connect to QuestDB: {e}")
            raise

    async def _create_reddit_table(self):
        """Create QuestDB table for Reddit data"""

        reddit_posts_sql = """
        CREATE TABLE IF NOT EXISTS reddit_posts (
            timestamp TIMESTAMP,
            id STRING,
            title STRING,
            content STRING,
            author STRING,
            subreddit SYMBOL CAPACITY 100 CACHE,
            score INT,
            upvote_ratio DOUBLE,
            num_comments INT,
            sentiment SYMBOL CAPACITY 30 CACHE,
            symbols STRING,
            created_at TIMESTAMP,
            collected_at TIMESTAMP
        ) TIMESTAMP(timestamp) PARTITION BY DAY WAL;
        """

        cursor = self.questdb_conn.cursor()
        try:
            cursor.execute(reddit_posts_sql)
            self.questdb_conn.commit()
            print("Reddit posts table created successfully")
        except Exception as e:
            print(f"Error creating Reddit posts table: {e}")
            self.questdb_conn.rollback()
            raise
        finally:
            cursor.close()

    async def _create_indices(self):
        """Create indices for better query performance"""

        indices_sql = [
            "ALTER TABLE reddit_posts ALTER COLUMN sentiment ADD INDEX;"
        ]

        cursor = self.questdb_conn.cursor()
        try:
            for index_sql in indices_sql:
                try:
                    cursor.execute(index_sql)
                    self.questdb_conn.commit()
                except Exception as e:
                    print(f"Index may already exist: {e}")
                    self.questdb_conn.rollback()
            print("Indices created/verified successfully")
        except Exception as e:
            print(f"Error creating indices: {e}")
            self.questdb_conn.rollback()
        finally:
            cursor.close()

    async def _store_reddit_data(self, posts: List[Dict]) -> bool:
        """Store Reddit data in QuestDB"""
        if not posts or not self.questdb_conn:
            return True

        cursor = self.questdb_conn.cursor()

        insert_sql = """
        INSERT INTO reddit_posts (
            timestamp, id, title, content, author, subreddit, score, upvote_ratio,
            num_comments, sentiment, symbols, created_at, collected_at
        ) VALUES %s
        """

        values = []
        current_time = datetime.now()

        for post in posts:
            try:
                # Parse Reddit post creation time
                created_utc = datetime.fromtimestamp(post.get('created_utc', 0))

                # Extract symbols using our improved extraction method
                extracted_tickers = post.get('tickers', [])

                # Clean and deduplicate symbols
                if extracted_tickers:
                    # Remove empty strings and None values
                    clean_tickers = [ticker.strip() for ticker in extracted_tickers if ticker and str(ticker).strip()]
                    # Remove duplicates while preserving order
                    unique_tickers = []
                    seen = set()
                    for ticker in clean_tickers:
                        ticker_upper = ticker.upper()
                        if ticker_upper not in seen:
                            seen.add(ticker_upper)
                            unique_tickers.append(ticker_upper)

                    symbols = ','.join(unique_tickers) if unique_tickers else ''
                else:
                    symbols = ''

                # Debug print for symbol extraction issues
                if post.get('title', '').upper().find('$') != -1 and not symbols:
                    print(f"DEBUG: Missing symbols for title: {post.get('title', '')}")
                    print(f"DEBUG: Extracted tickers: {extracted_tickers}")

                values.append((
                    current_time,          # timestamp - when we collected it
                    post.get('id', ''),
                    post.get('title', ''),
                    post.get('content', ''),
                    post.get('author', ''),
                    post.get('subreddit', ''),
                    post.get('score', 0),
                    post.get('upvote_ratio', 0.0),
                    post.get('num_comments', 0),
                    post.get('sentiment', 'neutral'),
                    symbols,
                    created_utc,           # created_at - original Reddit post time
                    current_time           # collected_at - when we collected it
                ))
            except Exception as e:
                print(f"Error processing Reddit post: {e}")
                continue

        try:
            if values:
                batch_size = self.questdb_config.get('batch_size', 100)
                execute_values(cursor, insert_sql, values, template=None, page_size=batch_size)
                self.questdb_conn.commit()
                print(f"Stored {len(values)} Reddit posts in QuestDB")
            return True

        except Exception as e:
            print(f"Error storing Reddit data in QuestDB: {e}")
            self.questdb_conn.rollback()
            return False
        finally:
            cursor.close()

    def _process_post(self, post, subreddit_name: str) -> Optional[Dict]:
        """Process individual Reddit post"""
        try:
            # Extract tickers from title and content
            tickers = self._extract_tickers(post.title, getattr(post, 'selftext', ''))

            # Determine post type
            post_type = self._categorize_post(post.title, getattr(post, 'selftext', ''))

            # Basic sentiment (could be enhanced with ML)
            sentiment = self._basic_sentiment(post.title, getattr(post, 'selftext', ''))

            return {
                "id": post.id,
                "title": post.title,
                "content": getattr(post, 'selftext', ''),
                "url": post.url,
                "author": str(post.author) if post.author else "[deleted]",
                "created_utc": post.created_utc,
                "subreddit": subreddit_name,
                "score": post.score,
                "upvote_ratio": post.upvote_ratio,
                "num_comments": post.num_comments,
                "ticker": tickers[0] if tickers else '',
                "tickers": tickers,
                "sentiment": sentiment,
                "post_type": post_type,
                "is_self": post.is_self,
                "is_video": post.is_video,
                "over_18": post.over_18,
                "spoiler": post.spoiler,
                "locked": post.locked,
                "permalink": post.permalink
            }

        except Exception as e:
            print(f"Error processing Reddit post: {e}")
            return None

    def _extract_tickers(self, title: str, content: str) -> List[str]:
        """Extract ticker symbols and crypto symbols from post title and content"""
        if not title:
            title = ""
        if not content:
            content = ""

        text = f"{title} {content}".upper()
        if not text.strip():
            return []

        # All patterns to extract tickers
        all_patterns = [
            # Dollar sign patterns - highest priority
            r'\$([A-Z]{1,5})\b',

            # Context-based patterns
            r'\b([A-Z]{2,5})\s+(?:calls?|puts?|options?)\b',
            r'\b([A-Z]{2,5})\s+(?:shares?|stock|position|holdings?)\b',
            r'\b([A-Z]{2,5})\s+(?:buy|sell|long|short|bullish|bearish)\b',
            r'\b([A-Z]{2,5})\s+(?:earnings|ER|report|guidance)\b',
            r'\b([A-Z]{2,5})\s+(?:DD|due\s+diligence)\b',
            r'\b([A-Z]{2,5})\s+(?:yolo|all\s+in)\b',
            r'\b([A-Z]{2,5})\s+(?:moon|rocket|pump|dump)\b',
            r'\b([A-Z]{2,5})\s+(?:up|down|gain|loss|drop|rally|crash)\b',

            # Action patterns
            r'(?:bought?|sold?|holding|owns?)\s+([A-Z]{2,5})\b',
            r'(?:long|short)\s+([A-Z]{2,5})\b',

            # Options patterns
            r'\b([A-Z]{2,5})\s+\d+[CP]\s*(?:\d+/\d+)?\b',
            r'\b([A-Z]{2,5})\s+\d+\.\d+[CP]\b',

            # Price patterns
            r'\b([A-Z]{2,5})\s+(?:at|@)\s*\$?\d+',
            r'\b([A-Z]{2,5})\s+\$\d+',
            r'\b([A-Z]{2,5})\s+\d+\%',

            # Standalone tickers in financial context (be more selective)
            r'\b([A-Z]{2,5})\s+(?:to\s+the\s+moon|diamond\s+hands?|paper\s+hands?)\b',
        ]

        # Crypto patterns
        crypto_patterns = [
            r'\b(BTC|BITCOIN)\b',
            r'\b(ETH|ETHEREUM)\b',
            r'\b(ADA|CARDANO)\b',
            r'\b(SOL|SOLANA)\b',
            r'\b(DOGE|DOGECOIN)\b',
            r'\b(XRP|RIPPLE)\b',
            r'\b(DOT|POLKADOT)\b',
            r'\b(MATIC|POLYGON)\b',
            r'\b(AVAX|AVALANCHE)\b',
            r'\b(LINK|CHAINLINK)\b',
        ]

        # Extensive blacklist of common false positives
        blacklist = {
            'THE', 'AND', 'FOR', 'ARE', 'BUT', 'NOT', 'YOU', 'ALL', 'CAN', 'WAS', 'HAS', 'HAD',
            'GET', 'GOT', 'NEW', 'NOW', 'ONE', 'TWO', 'SEE', 'SAY', 'WHO', 'OIL', 'GAS', 'CAR',
            'BAD', 'OLD', 'BIG', 'TOP', 'LOW', 'RUN', 'WIN', 'RED', 'HOT', 'CUT', 'SET', 'PUT',
            'ADD', 'USE', 'WAY', 'END', 'LOL', 'WTF', 'FML', 'SMH', 'TBH', 'IMO', 'FYI', 'DIY',
            'CEO', 'CFO', 'CTO', 'IPO', 'SEC', 'FDA', 'FBI', 'CIA', 'IRS', 'GDP', 'CPI', 'QE',
            'USA', 'USD', 'EUR', 'GBP', 'JPY', 'CAD', 'AUD', 'CHF', 'CNY', 'INR', 'ATH', 'AMA',
            'TIL', 'ELI', 'PSA', 'AMA', 'TBD', 'FUD', 'DD', 'TA', 'WSB', 'GME', 'AMC', 'APE',
            'HOLD', 'YOLO', 'MOON', 'HODL', 'FOMO', 'FUD', 'BTFD', 'ATH', 'DIP', 'RIP',
            'THIS', 'THAT', 'THEY', 'THEM', 'WHEN', 'WHERE', 'WHAT', 'WHICH', 'WHY', 'HOW',
            'HAVE', 'BEEN', 'WILL', 'WITH', 'FROM', 'JUST', 'ONLY', 'EVEN', 'ALSO', 'EACH',
            'SOME', 'MANY', 'MUCH', 'MORE', 'MOST', 'LESS', 'THAN', 'OVER', 'UNDER', 'ABOVE',
            'BELOW', 'AFTER', 'SINCE', 'UNTIL', 'WHILE', 'DURING', 'BEFORE', 'AGAIN', 'ONCE',
            'HERE', 'THERE', 'THEN', 'STILL', 'VERY', 'TOO', 'QUITE', 'RATHER', 'ENOUGH',
            'HELP', 'MAKE', 'TAKE', 'GIVE', 'COME', 'LOOK', 'THINK', 'KNOW', 'FEEL', 'WANT',
            'NEED', 'SEEM', 'FIND', 'KEEP', 'CALL', 'WORK', 'PLAY', 'MOVE', 'LIVE', 'SHOW',
            'TELL', 'TALK', 'TURN', 'WALK', 'STOP', 'WAIT', 'HEAR', 'READ', 'WRITE', 'LEARN',
            'CHANGE', 'HAPPEN', 'BECOME', 'LEAVE', 'START', 'CLOSE', 'OPEN', 'FOLLOW', 'MEET',
            'BRING', 'SEND', 'BUILD', 'STAY', 'FALL', 'RISE', 'GROW', 'LOST', 'GONE', 'DONE'
        }

        found_tickers = set()

        # Extract from all patterns
        for pattern in all_patterns + crypto_patterns:
            try:
                matches = re.findall(pattern, text)
                for match in matches:
                    match = match.strip()
                    if (2 <= len(match) <= 5 and
                        match not in blacklist and
                        not match.isdigit() and
                        not all(c in '0123456789.-' for c in match)):
                        found_tickers.add(match)
            except Exception as e:
                print(f"Pattern error: {pattern}, {e}")
                continue

        # Convert to list and sort for consistent ordering
        return sorted(list(found_tickers))

    def _categorize_post(self, title: str, content: str) -> str:
        """Categorize post based on content with crypto support"""
        text = f"{title} {content}".lower()

        categories = {
            'dd': ['dd', 'due diligence', 'research', 'analysis', 'technical analysis'],
            'yolo': ['yolo', 'all in', 'life savings', 'mortgage', 'leveraged'],
            'gain': ['gain', 'profit', 'tendies', 'moon', 'diamond hands', 'lambo', 'gains'],
            'loss': ['loss', 'red', 'bag holder', 'rip', 'paper hands', 'rekt', 'losses'],
            'news': ['news', 'breaking', 'announcement', 'earnings', 'adoption', 'regulation'],
            'meme': ['meme', 'joke', 'funny', 'wife', 'boyfriend', 'doge', 'shib'],
            'question': ['?', 'help', 'question', 'eli5', 'explain', 'how to'],
            'crypto': ['bitcoin', 'ethereum', 'crypto', 'hodl', 'defi', 'nft', 'web3', 'blockchain']
        }

        for category, keywords in categories.items():
            if any(keyword in text for keyword in keywords):
                return category

        return 'discussion'

    def _basic_sentiment(self, title: str, content: str) -> str:
        """Basic sentiment analysis with crypto support"""
        text = f"{title} {content}".lower()

        positive_words = ['bullish', 'moon', 'rocket', 'diamond', 'buy', 'calls', 'green', 'up', 'bull', 'long', 'hodl', 'pump', 'lambo', 'ath']
        negative_words = ['bearish', 'crash', 'red', 'down', 'puts', 'sell', 'bear', 'rip', 'dead', 'short', 'dump', 'rekt', 'correction']

        pos_count = sum(1 for word in positive_words if word in text)
        neg_count = sum(1 for word in negative_words if word in text)

        if pos_count > neg_count:
            return 'bullish'
        elif neg_count > pos_count:
            return 'bearish'
        else:
            return 'neutral'

    async def start_scheduled_collection(self):
        """Start scheduled collection service with market-aware intervals"""
        print("Reddit feed scheduled collection started")
        print(f"Starting at: {datetime.now().isoformat()}")

        while True:
            try:
                # Get market status and appropriate interval
                status = market_time.get_market_status()
                sleep_seconds = market_time.get_collection_interval(
                    market_interval=900,      # 15 minutes during market hours
                    extended_interval=1800,   # 30 minutes during extended hours
                    off_hours_interval=3600   # 60 minutes during off hours/weekends
                )

                interval_minutes = sleep_seconds // 60

                print(f"\n[{datetime.now().isoformat()}] {status} - Collecting Reddit posts...")

                posts = await self.get_financial_posts()

                if posts:
                    print(f"Collected {len(posts)} Reddit posts")
                else:
                    print("No new Reddit posts found")

                # Wait for next collection
                print(f"Next collection in {interval_minutes} minutes ({status})...")
                await asyncio.sleep(sleep_seconds)

            except Exception as e:
                print(f"Error in Reddit scheduled collection: {e}")
                print("Retrying in 5 minutes...")
                await asyncio.sleep(300)

async def main():
    """Run Reddit feed - scheduled collection or one-time display"""
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--scheduled":
        # Run scheduled collection for systemd service
        async with RedditFeedClient() as client:
            await client.start_scheduled_collection()
    else:
        # Display Reddit posts (manual mode)
        async with RedditFeedClient() as client:
            print("\n" + "="*80)
            print(" REDDIT FINANCIAL FEED")
            print("="*80)
            print(f" Timestamp: {datetime.now().isoformat()}")
            print("="*80)

            posts = await client.get_financial_posts(limit=50)

            if not posts:
                print("\nNo posts found.")
                return

            print(f"\nTotal posts: {len(posts)}\n")
            print("-"*80)

            for idx, post in enumerate(posts[:20], 1):
                print(f"\n[{idx}] r/{post['subreddit']} - {post['title']}")
                print(f"    Author: {post['author']} | Score: {post['score']} | Comments: {post['num_comments']}")
                if post['tickers']:
                    print(f"    Tickers: {', '.join(post['tickers'])}")
                print(f"    Type: {post['post_type']} | Sentiment: {post['sentiment']}")
                print(f"    URL: https://reddit.com{post['permalink']}")
                print("-"*80)

if __name__ == "__main__":
    asyncio.run(main())