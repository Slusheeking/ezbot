"""
Feed Registry and Discovery System

Centralized registration, discovery, and management of all data feeds.
Provides automatic feed discovery, health aggregation, coordinated startup,
and comprehensive monitoring across the entire feed ecosystem.
"""

from .registry import FeedRegistry
from .discovery import FeedDiscovery
from .coordinator import FeedCoordinator
from .health_aggregator import HealthAggregator

__version__ = "1.0.0"

__all__ = [
    'FeedRegistry',
    'FeedDiscovery',
    'FeedCoordinator',
    'HealthAggregator'
]

# Global registry instance
_feed_registry = None

def get_feed_registry(config: dict = None) -> FeedRegistry:
    """Get or create the global feed registry instance"""
    global _feed_registry
    if _feed_registry is None:
        if config is None:
            raise ValueError("Feed registry not initialized. Provide config on first call.")
        _feed_registry = FeedRegistry(config)
    return _feed_registry

def initialize_feed_registry(config: dict) -> FeedRegistry:
    """Initialize the global feed registry with configuration"""
    global _feed_registry
    _feed_registry = FeedRegistry(config)
    return _feed_registry