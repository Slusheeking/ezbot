"""
Alert Management Package

Centralized alert management with multiple notification channels,
severity routing, and alert correlation.
"""

from .alert_manager import AlertManager

__version__ = "1.0.0"
__all__ = ["AlertManager"]

# Global instance
_alert_manager = None

def get_alert_manager(config: dict = None) -> AlertManager:
    """Get or create the global alert manager instance"""
    global _alert_manager
    if _alert_manager is None:
        if config is None:
            raise ValueError("Alert manager not initialized. Provide config on first call.")
        _alert_manager = AlertManager(config)
    return _alert_manager

def initialize_alert_manager(config: dict) -> AlertManager:
    """Initialize the global alert manager with configuration"""
    global _alert_manager
    _alert_manager = AlertManager(config)
    return _alert_manager