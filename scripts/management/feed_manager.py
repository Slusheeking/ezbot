#!/usr/bin/env python3
"""
Feed Manager Script

Central management script for all data feeds in the EzBot system.
Provides commands for starting, stopping, monitoring, and managing feeds.
"""

import asyncio
import argparse
import json
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path
sys.path.append('/home/ezb0t/ezbot')

from core.feed_registry import FeedRegistry, FeedDiscovery, initialize_feed_registry
from core.questdb_manager import initialize_questdb_manager
from core.config_manager import ConfigManager, initialize_config_manager
from core.alerts import initialize_alert_manager


class FeedManager:
    """Central feed management system"""

    def __init__(self):
        self.config_manager = None
        self.feed_registry = None
        self.feed_discovery = None
        self.logger = self._setup_logging()

    def _setup_logging(self) -> logging.Logger:
        """Setup logging for the feed manager"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler('/home/ezb0t/ezbot/logs/feed_manager.log')
            ]
        )
        return logging.getLogger('feed_manager')

    async def initialize(self):
        """Initialize all system components"""
        try:
            self.logger.info("Initializing Feed Manager...")

            # Initialize configuration manager
            self.config_manager = initialize_config_manager({
                'config_root': '/home/ezb0t/ezbot/config'
            })
            await self.config_manager.initialize()

            # Get global config
            global_config = await self.config_manager.get_global_config()

            # Initialize QuestDB manager
            questdb_manager = initialize_questdb_manager(global_config)
            await questdb_manager.initialize()

            # Initialize alert manager
            alert_manager = initialize_alert_manager(global_config)
            await alert_manager.initialize()

            # Initialize feed registry
            self.feed_registry = initialize_feed_registry(global_config)
            await self.feed_registry.initialize()

            # Initialize feed discovery
            self.feed_discovery = FeedDiscovery(self.feed_registry, global_config)

            self.logger.info("Feed Manager initialized successfully")

        except Exception as e:
            self.logger.error(f"Failed to initialize Feed Manager: {e}")
            raise

    async def discover_feeds(self) -> Dict[str, Any]:
        """Discover and register all feeds"""
        self.logger.info("Discovering feeds...")
        return await self.feed_discovery.discover_all_feeds()

    async def list_feeds(self, category: str = None, status: str = None) -> List[Dict[str, Any]]:
        """List all registered feeds"""
        feeds = self.feed_registry.list_feeds(category=category)
        return [
            {
                'name': feed.name,
                'category': feed.category,
                'market_type': feed.market_type,
                'priority': feed.priority,
                'status': feed.status.value,
                'last_heartbeat': feed.last_heartbeat.isoformat(),
                'error_count': feed.error_count,
                'health_score': feed.health_score
            }
            for feed in feeds
        ]

    async def start_feed(self, feed_name: str) -> bool:
        """Start a specific feed"""
        self.logger.info(f"Starting feed: {feed_name}")
        return await self.feed_registry.start_feed(feed_name)

    async def stop_feed(self, feed_name: str) -> bool:
        """Stop a specific feed"""
        self.logger.info(f"Stopping feed: {feed_name}")
        return await self.feed_registry.stop_feed(feed_name)

    async def restart_feed(self, feed_name: str) -> bool:
        """Restart a specific feed"""
        self.logger.info(f"Restarting feed: {feed_name}")
        return await self.feed_registry.restart_feed(feed_name)

    async def start_all_feeds(self, stagger_delay: float = 10.0) -> Dict[str, bool]:
        """Start all feeds with staggering"""
        self.logger.info("Starting all feeds...")
        return await self.feed_registry.start_all_feeds(stagger_delay)

    async def stop_all_feeds(self) -> Dict[str, bool]:
        """Stop all feeds"""
        self.logger.info("Stopping all feeds...")
        return await self.feed_registry.stop_all_feeds()

    async def start_category(self, category: str, stagger_delay: float = 5.0) -> Dict[str, bool]:
        """Start all feeds in a category"""
        self.logger.info(f"Starting feeds in category: {category}")
        return await self.feed_registry.start_feeds_by_category(category, stagger_delay)

    async def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health"""
        return self.feed_registry.get_system_health()

    async def get_feed_status(self, feed_name: str) -> Dict[str, Any]:
        """Get detailed status for a specific feed"""
        feed_info = self.feed_registry.get_feed_info(feed_name)
        if not feed_info:
            return {'error': f'Feed not found: {feed_name}'}

        return {
            'name': feed_info.name,
            'category': feed_info.category,
            'market_type': feed_info.market_type,
            'priority': feed_info.priority,
            'status': feed_info.status.value,
            'last_heartbeat': feed_info.last_heartbeat.isoformat(),
            'start_time': feed_info.start_time.isoformat() if feed_info.start_time else None,
            'error_count': feed_info.error_count,
            'last_error': feed_info.last_error,
            'health_score': feed_info.health_score,
            'consecutive_failures': feed_info.consecutive_failures,
            'total_runs': feed_info.total_runs,
            'successful_runs': feed_info.successful_runs,
            'metrics': feed_info.metrics
        }


async def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(description='EzBot Feed Manager')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Discover command
    discover_parser = subparsers.add_parser('discover', help='Discover and register feeds')

    # List command
    list_parser = subparsers.add_parser('list', help='List feeds')
    list_parser.add_argument('--category', help='Filter by category')
    list_parser.add_argument('--status', help='Filter by status')

    # Start commands
    start_parser = subparsers.add_parser('start', help='Start feeds')
    start_parser.add_argument('target', nargs='?', help='Feed name, category, or "all"')
    start_parser.add_argument('--stagger', type=float, default=10.0, help='Stagger delay in seconds')

    # Stop commands
    stop_parser = subparsers.add_parser('stop', help='Stop feeds')
    stop_parser.add_argument('target', nargs='?', help='Feed name or "all"')

    # Restart command
    restart_parser = subparsers.add_parser('restart', help='Restart a feed')
    restart_parser.add_argument('feed_name', help='Name of the feed to restart')

    # Status commands
    status_parser = subparsers.add_parser('status', help='Get feed or system status')
    status_parser.add_argument('target', nargs='?', default='system', help='Feed name or "system"')

    # Health command
    health_parser = subparsers.add_parser('health', help='Get system health')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Initialize feed manager
    manager = FeedManager()
    await manager.initialize()

    try:
        if args.command == 'discover':
            result = await manager.discover_feeds()
            print(json.dumps(result, indent=2))

        elif args.command == 'list':
            feeds = await manager.list_feeds(category=args.category, status=args.status)
            print(json.dumps(feeds, indent=2))

        elif args.command == 'start':
            if not args.target or args.target == 'all':
                result = await manager.start_all_feeds(args.stagger)
            elif args.target in ['market_data', 'social_sentiment', 'news_monitoring', 'account_monitoring']:
                result = await manager.start_category(args.target, args.stagger)
            else:
                result = await manager.start_feed(args.target)
            print(json.dumps(result, indent=2))

        elif args.command == 'stop':
            if not args.target or args.target == 'all':
                result = await manager.stop_all_feeds()
            else:
                result = await manager.stop_feed(args.target)
            print(json.dumps(result, indent=2))

        elif args.command == 'restart':
            result = await manager.restart_feed(args.feed_name)
            print(json.dumps({'success': result}, indent=2))

        elif args.command == 'status':
            if args.target == 'system':
                result = await manager.get_system_health()
            else:
                result = await manager.get_feed_status(args.target)
            print(json.dumps(result, indent=2))

        elif args.command == 'health':
            result = await manager.get_system_health()
            print(json.dumps(result, indent=2))

    except Exception as e:
        print(f"Error executing command: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())