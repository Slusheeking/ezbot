"""
Enhanced Feed Base Classes

Improved base classes for data feeds with integrated QuestDB management,
telemetry collection, data validation, and standardized error handling.
"""

from .enhanced_feed_base import EnhancedFeedBase
from .feed_decorators import feed_metrics, feed_retry, feed_validate
from .feed_mixins import DatabaseMixin, TelemetryMixin, ValidationMixin

__version__ = "1.0.0"

__all__ = [
    'EnhancedFeedBase',
    'feed_metrics',
    'feed_retry',
    'feed_validate',
    'DatabaseMixin',
    'TelemetryMixin',
    'ValidationMixin'
]