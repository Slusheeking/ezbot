"""
QuestDB Manager Package

Centralized QuestDB connection management, schema handling, and operations.
Provides connection pooling, automatic table creation, health monitoring,
and optimized batch operations for all data feeds.
"""

from .client import QuestDBManager
from .schema_manager import SchemaManager, TableSchema
from .connection_pool import ConnectionPool
from .health_monitor import QuestDBHealthMonitor

__version__ = "1.0.0"

__all__ = [
    'QuestDBManager',
    'SchemaManager',
    'TableSchema',
    'ConnectionPool',
    'QuestDBHealthMonitor'
]

# Global instance for easy access
_questdb_manager = None

def get_questdb_manager(config: dict = None) -> QuestDBManager:
    """Get or create the global QuestDB manager instance"""
    global _questdb_manager
    if _questdb_manager is None:
        if config is None:
            raise ValueError("QuestDB manager not initialized. Provide config on first call.")
        _questdb_manager = QuestDBManager(config)
    return _questdb_manager

def initialize_questdb_manager(config: dict) -> QuestDBManager:
    """Initialize the global QuestDB manager with configuration"""
    global _questdb_manager
    _questdb_manager = QuestDBManager(config)
    return _questdb_manager