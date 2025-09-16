"""
Feed Registry

Central registry for managing all data feeds in the system.
Provides registration, health tracking, and coordination services.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import threading


class FeedStatus(Enum):
    """Feed status states"""
    UNKNOWN = "unknown"
    REGISTERED = "registered"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class FeedInfo:
    """Information about a registered feed"""
    name: str
    category: str
    market_type: str
    priority: str
    feed_instance: Any
    status: FeedStatus = FeedStatus.REGISTERED
    last_heartbeat: datetime = field(default_factory=datetime.now)
    start_time: Optional[datetime] = None
    error_count: int = 0
    last_error: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    health_score: float = 100.0
    consecutive_failures: int = 0
    total_runs: int = 0
    successful_runs: int = 0


@dataclass
class RegistryMetrics:
    """Registry-wide metrics"""
    total_feeds: int = 0
    running_feeds: int = 0
    healthy_feeds: int = 0
    degraded_feeds: int = 0
    unhealthy_feeds: int = 0
    error_feeds: int = 0
    avg_health_score: float = 100.0
    last_updated: datetime = field(default_factory=datetime.now)


class FeedRegistry:
    """
    Central registry for all data feeds

    Features:
    - Feed registration and discovery
    - Health status aggregation
    - Coordinated startup and shutdown
    - Performance monitoring
    - Error tracking and alerting
    - Feed dependency management
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize feed registry"""
        self.config = config
        self.logger = logging.getLogger('feed_registry')

        # Feed tracking
        self.feeds: Dict[str, FeedInfo] = {}
        self.feed_categories: Dict[str, List[str]] = {}
        self.feed_priorities: Dict[str, List[str]] = {
            'critical': [],
            'high': [],
            'medium': [],
            'low': []
        }

        # State management
        self.registry_lock = threading.Lock()
        self.is_running = False
        self.startup_order: List[str] = []
        self.shutdown_order: List[str] = []

        # Metrics and monitoring
        self.metrics = RegistryMetrics()
        self.health_check_interval = config.get('health_check_interval', 60)
        self.heartbeat_timeout = config.get('heartbeat_timeout', 300)  # 5 minutes

        # Background tasks
        self._health_check_task = None
        self._cleanup_task = None

    async def initialize(self) -> bool:
        """Initialize the feed registry"""
        try:
            self.logger.info("Initializing Feed Registry...")

            # Start background monitoring tasks
            await self._start_background_tasks()

            self.is_running = True
            self.logger.info("Feed Registry initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize Feed Registry: {e}")
            return False

    async def shutdown(self):
        """Shutdown the feed registry"""
        try:
            self.logger.info("Shutting down Feed Registry...")
            self.is_running = False

            # Stop all feeds
            await self.stop_all_feeds()

            # Cancel background tasks
            if self._health_check_task:
                self._health_check_task.cancel()
            if self._cleanup_task:
                self._cleanup_task.cancel()

            self.logger.info("Feed Registry shutdown complete")

        except Exception as e:
            self.logger.error(f"Error during registry shutdown: {e}")

    def register_feed(self, feed_instance) -> bool:
        """Register a feed with the registry"""
        try:
            with self.registry_lock:
                feed_name = feed_instance.feed_name
                feed_category = feed_instance.feed_category
                market_type = feed_instance.market_type or "stock_market"
                priority = feed_instance.priority or "medium"

                if feed_name in self.feeds:
                    self.logger.warning(f"Feed '{feed_name}' already registered, updating...")

                # Create feed info
                feed_info = FeedInfo(
                    name=feed_name,
                    category=feed_category,
                    market_type=market_type,
                    priority=priority,
                    feed_instance=feed_instance
                )

                # Register feed
                self.feeds[feed_name] = feed_info

                # Update categorization
                if feed_category not in self.feed_categories:
                    self.feed_categories[feed_category] = []
                if feed_name not in self.feed_categories[feed_category]:
                    self.feed_categories[feed_category].append(feed_name)

                # Update priority lists
                if feed_name not in self.feed_priorities[priority]:
                    self.feed_priorities[priority].append(feed_name)

                # Update startup order based on priority
                self._update_startup_order()

                # Update metrics
                self._update_registry_metrics()

                self.logger.info(
                    f"Registered feed '{feed_name}' "
                    f"(category: {feed_category}, priority: {priority})"
                )

                return True

        except Exception as e:
            self.logger.error(f"Failed to register feed '{feed_name}': {e}")
            return False

    def unregister_feed(self, feed_name: str) -> bool:
        """Unregister a feed from the registry"""
        try:
            with self.registry_lock:
                if feed_name not in self.feeds:
                    self.logger.warning(f"Feed '{feed_name}' not found for unregistration")
                    return False

                feed_info = self.feeds[feed_name]

                # Remove from categorization
                if feed_info.category in self.feed_categories:
                    if feed_name in self.feed_categories[feed_info.category]:
                        self.feed_categories[feed_info.category].remove(feed_name)

                # Remove from priority lists
                if feed_name in self.feed_priorities[feed_info.priority]:
                    self.feed_priorities[feed_info.priority].remove(feed_name)

                # Remove from registry
                del self.feeds[feed_name]

                # Update startup order
                self._update_startup_order()

                # Update metrics
                self._update_registry_metrics()

                self.logger.info(f"Unregistered feed '{feed_name}'")
                return True

        except Exception as e:
            self.logger.error(f"Failed to unregister feed '{feed_name}': {e}")
            return False

    def get_feed_info(self, feed_name: str) -> Optional[FeedInfo]:
        """Get information about a specific feed"""
        return self.feeds.get(feed_name)

    def list_feeds(self, category: Optional[str] = None, status: Optional[FeedStatus] = None) -> List[FeedInfo]:
        """List feeds with optional filtering"""
        feeds = list(self.feeds.values())

        if category:
            feeds = [feed for feed in feeds if feed.category == category]

        if status:
            feeds = [feed for feed in feeds if feed.status == status]

        return feeds

    def get_feeds_by_category(self, category: str) -> List[FeedInfo]:
        """Get all feeds in a specific category"""
        feed_names = self.feed_categories.get(category, [])
        return [self.feeds[name] for name in feed_names if name in self.feeds]

    def get_feeds_by_priority(self, priority: str) -> List[FeedInfo]:
        """Get all feeds with a specific priority"""
        feed_names = self.feed_priorities.get(priority, [])
        return [self.feeds[name] for name in feed_names if name in self.feeds]

    async def start_feed(self, feed_name: str) -> bool:
        """Start a specific feed"""
        try:
            feed_info = self.feeds.get(feed_name)
            if not feed_info:
                self.logger.error(f"Feed '{feed_name}' not found")
                return False

            if feed_info.status == FeedStatus.RUNNING:
                self.logger.info(f"Feed '{feed_name}' already running")
                return True

            self.logger.info(f"Starting feed '{feed_name}'...")
            feed_info.status = FeedStatus.STARTING

            # Start the feed
            await feed_info.feed_instance.start_standalone()

            feed_info.status = FeedStatus.RUNNING
            feed_info.start_time = datetime.now()

            self.logger.info(f"Feed '{feed_name}' started successfully")
            return True

        except Exception as e:
            if feed_name in self.feeds:
                self.feeds[feed_name].status = FeedStatus.ERROR
                self.feeds[feed_name].last_error = str(e)
                self.feeds[feed_name].error_count += 1

            self.logger.error(f"Failed to start feed '{feed_name}': {e}")
            return False

    async def stop_feed(self, feed_name: str) -> bool:
        """Stop a specific feed"""
        try:
            feed_info = self.feeds.get(feed_name)
            if not feed_info:
                self.logger.error(f"Feed '{feed_name}' not found")
                return False

            if feed_info.status == FeedStatus.STOPPED:
                self.logger.info(f"Feed '{feed_name}' already stopped")
                return True

            self.logger.info(f"Stopping feed '{feed_name}'...")
            feed_info.status = FeedStatus.STOPPING

            # Stop the feed if it has a stop method
            if hasattr(feed_info.feed_instance, 'stop'):
                await feed_info.feed_instance.stop()

            feed_info.status = FeedStatus.STOPPED

            self.logger.info(f"Feed '{feed_name}' stopped successfully")
            return True

        except Exception as e:
            if feed_name in self.feeds:
                self.feeds[feed_name].status = FeedStatus.ERROR
                self.feeds[feed_name].last_error = str(e)

            self.logger.error(f"Failed to stop feed '{feed_name}': {e}")
            return False

    async def start_feeds_by_category(self, category: str, stagger_delay: float = 5.0) -> Dict[str, bool]:
        """Start all feeds in a category with staggering"""
        feeds = self.get_feeds_by_category(category)
        results = {}

        self.logger.info(f"Starting {len(feeds)} feeds in category '{category}'")

        for i, feed_info in enumerate(feeds):
            if i > 0:
                await asyncio.sleep(stagger_delay)

            results[feed_info.name] = await self.start_feed(feed_info.name)

        return results

    async def start_all_feeds(self, stagger_delay: float = 10.0) -> Dict[str, bool]:
        """Start all feeds in priority order with staggering"""
        results = {}

        # Start feeds in priority order
        for feed_name in self.startup_order:
            results[feed_name] = await self.start_feed(feed_name)
            await asyncio.sleep(stagger_delay)

        self.logger.info(f"Started {sum(results.values())} of {len(results)} feeds")
        return results

    async def stop_all_feeds(self) -> Dict[str, bool]:
        """Stop all feeds in reverse priority order"""
        results = {}

        # Stop feeds in reverse order
        for feed_name in reversed(self.shutdown_order):
            results[feed_name] = await self.stop_feed(feed_name)

        self.logger.info(f"Stopped {sum(results.values())} of {len(results)} feeds")
        return results

    async def restart_feed(self, feed_name: str) -> bool:
        """Restart a specific feed"""
        self.logger.info(f"Restarting feed '{feed_name}'...")

        # Stop first
        stop_result = await self.stop_feed(feed_name)
        if not stop_result:
            return False

        # Wait a moment
        await asyncio.sleep(2.0)

        # Start again
        return await self.start_feed(feed_name)

    def update_feed_status(self, feed_name: str, status: FeedStatus, metrics: Optional[Dict[str, Any]] = None):
        """Update feed status and metrics"""
        if feed_name not in self.feeds:
            return

        feed_info = self.feeds[feed_name]
        feed_info.status = status
        feed_info.last_heartbeat = datetime.now()

        if metrics:
            feed_info.metrics = metrics

            # Update health score based on metrics
            feed_info.health_score = self._calculate_health_score(metrics)

            # Update run statistics
            if 'success' in metrics:
                feed_info.total_runs += 1
                if metrics['success']:
                    feed_info.successful_runs += 1
                    feed_info.consecutive_failures = 0
                else:
                    feed_info.consecutive_failures += 1

        # Update registry metrics
        self._update_registry_metrics()

    def record_feed_error(self, feed_name: str, error: str):
        """Record an error for a feed"""
        if feed_name not in self.feeds:
            return

        feed_info = self.feeds[feed_name]
        feed_info.error_count += 1
        feed_info.last_error = error
        feed_info.last_heartbeat = datetime.now()
        feed_info.consecutive_failures += 1

        # Update status based on error frequency
        if feed_info.consecutive_failures >= 5:
            feed_info.status = FeedStatus.UNHEALTHY
        elif feed_info.consecutive_failures >= 3:
            feed_info.status = FeedStatus.DEGRADED

        self.logger.warning(f"Feed '{feed_name}' error: {error}")

    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health summary"""
        self._update_registry_metrics()

        feed_statuses = {}
        for feed_name, feed_info in self.feeds.items():
            feed_statuses[feed_name] = {
                'status': feed_info.status.value,
                'health_score': feed_info.health_score,
                'last_heartbeat': feed_info.last_heartbeat.isoformat(),
                'error_count': feed_info.error_count,
                'consecutive_failures': feed_info.consecutive_failures
            }

        return {
            'timestamp': datetime.now().isoformat(),
            'registry_metrics': {
                'total_feeds': self.metrics.total_feeds,
                'running_feeds': self.metrics.running_feeds,
                'healthy_feeds': self.metrics.healthy_feeds,
                'degraded_feeds': self.metrics.degraded_feeds,
                'unhealthy_feeds': self.metrics.unhealthy_feeds,
                'error_feeds': self.metrics.error_feeds,
                'avg_health_score': self.metrics.avg_health_score
            },
            'feeds': feed_statuses,
            'categories': {
                category: len(feeds) for category, feeds in self.feed_categories.items()
            },
            'startup_order': self.startup_order
        }

    def _update_startup_order(self):
        """Update the startup order based on priorities"""
        self.startup_order = []

        # Add feeds in priority order
        for priority in ['critical', 'high', 'medium', 'low']:
            self.startup_order.extend(self.feed_priorities[priority])

        # Shutdown order is reverse
        self.shutdown_order = list(reversed(self.startup_order))

    def _update_registry_metrics(self):
        """Update registry-wide metrics"""
        total_feeds = len(self.feeds)
        running_feeds = sum(1 for f in self.feeds.values() if f.status == FeedStatus.RUNNING)
        healthy_feeds = sum(1 for f in self.feeds.values() if f.status == FeedStatus.HEALTHY)
        degraded_feeds = sum(1 for f in self.feeds.values() if f.status == FeedStatus.DEGRADED)
        unhealthy_feeds = sum(1 for f in self.feeds.values() if f.status == FeedStatus.UNHEALTHY)
        error_feeds = sum(1 for f in self.feeds.values() if f.status == FeedStatus.ERROR)

        avg_health_score = (
            sum(f.health_score for f in self.feeds.values()) / total_feeds
            if total_feeds > 0 else 100.0
        )

        self.metrics = RegistryMetrics(
            total_feeds=total_feeds,
            running_feeds=running_feeds,
            healthy_feeds=healthy_feeds,
            degraded_feeds=degraded_feeds,
            unhealthy_feeds=unhealthy_feeds,
            error_feeds=error_feeds,
            avg_health_score=avg_health_score,
            last_updated=datetime.now()
        )

    def _calculate_health_score(self, metrics: Dict[str, Any]) -> float:
        """Calculate health score based on feed metrics"""
        score = 100.0

        # Deduct points for various issues
        success_rate = metrics.get('success_rate', 100.0)
        score -= (100.0 - success_rate) * 0.5  # Success rate impact

        execution_time = metrics.get('execution_time_ms', 0)
        if execution_time > 10000:  # Over 10 seconds
            score -= 20
        elif execution_time > 5000:  # Over 5 seconds
            score -= 10

        error_count = metrics.get('error_count', 0)
        score -= min(error_count * 5, 30)  # Cap at 30 points

        # Ensure score is within bounds
        return max(0.0, min(100.0, score))

    async def _start_background_tasks(self):
        """Start background monitoring tasks"""
        self._health_check_task = asyncio.create_task(self._health_check_loop())
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def _health_check_loop(self):
        """Background task for periodic health checks"""
        while self.is_running:
            try:
                await self._perform_health_checks()
                await asyncio.sleep(self.health_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in health check loop: {e}")
                await asyncio.sleep(self.health_check_interval)

    async def _perform_health_checks(self):
        """Perform health checks on all feeds"""
        current_time = datetime.now()
        timeout_threshold = current_time - timedelta(seconds=self.heartbeat_timeout)

        for feed_name, feed_info in self.feeds.items():
            # Check for heartbeat timeout
            if feed_info.last_heartbeat < timeout_threshold:
                if feed_info.status in [FeedStatus.RUNNING, FeedStatus.HEALTHY]:
                    self.logger.warning(f"Feed '{feed_name}' heartbeat timeout")
                    feed_info.status = FeedStatus.UNHEALTHY
                    feed_info.consecutive_failures += 1

        # Update metrics after health checks
        self._update_registry_metrics()

    async def _cleanup_loop(self):
        """Background task for periodic cleanup"""
        while self.is_running:
            try:
                await self._perform_cleanup()
                await asyncio.sleep(3600)  # Run every hour
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in cleanup loop: {e}")
                await asyncio.sleep(3600)

    async def _perform_cleanup(self):
        """Perform periodic cleanup tasks"""
        # Clear old metrics, logs, etc.
        # This can be expanded as needed
        pass