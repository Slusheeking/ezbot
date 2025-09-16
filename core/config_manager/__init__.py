"""
Configuration Manager Package

Centralized configuration management with environment overrides,
validation, and hot-reloading capabilities.
"""

from .config_manager import ConfigManager

__version__ = "1.0.0"
__all__ = ["ConfigManager"]

# Global instance
_config_manager = None

def get_config_manager(config: dict = None) -> ConfigManager:
    """Get or create the global config manager instance"""
    global _config_manager
    if _config_manager is None:
        if config is None:
            raise ValueError("Config manager not initialized. Provide config on first call.")
        _config_manager = ConfigManager(config)
    return _config_manager

def initialize_config_manager(config: dict) -> ConfigManager:
    """Initialize the global config manager with configuration"""
    global _config_manager
    _config_manager = ConfigManager(config)
    return _config_manager