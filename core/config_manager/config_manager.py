"""
Configuration Manager

Centralized configuration management system that loads and manages
configurations from YAML files with environment overrides.
"""

import os
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional


class ConfigManager:
    """Centralized configuration management"""

    def __init__(self, config: Dict[str, Any]):
        self.config_root = Path(config.get('config_root', '/home/ezb0t/ezbot/new_config'))
        self.environment = os.getenv('EZBOT_ENV', 'production')
        self.logger = logging.getLogger('config_manager')

        self.global_config: Dict[str, Any] = {}
        self.feed_configs: Dict[str, Dict[str, Any]] = {}
        self.initialized = False

    async def initialize(self) -> bool:
        """Initialize configuration manager"""
        try:
            self.logger.info("Initializing Configuration Manager...")

            # Load global configuration
            await self._load_global_config()

            # Load default feed configuration
            await self._load_default_feed_config()

            self.initialized = True
            self.logger.info("Configuration Manager initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize Configuration Manager: {e}")
            return False

    async def _load_global_config(self):
        """Load global system configuration"""
        global_config_file = self.config_root / 'global' / 'system.yaml'

        if global_config_file.exists():
            with open(global_config_file, 'r') as f:
                self.global_config = yaml.safe_load(f) or {}

            # Apply environment overrides
            env_overrides = self.global_config.get('environments', {}).get(self.environment, {})
            self._apply_overrides(self.global_config, env_overrides)
        else:
            self.logger.warning(f"Global config file not found: {global_config_file}")
            self.global_config = {}

    async def _load_default_feed_config(self):
        """Load default feed configuration"""
        default_config_file = self.config_root / 'feeds' / 'feed_defaults.yaml'

        if default_config_file.exists():
            with open(default_config_file, 'r') as f:
                self.default_feed_config = yaml.safe_load(f) or {}
        else:
            self.logger.warning(f"Default feed config not found: {default_config_file}")
            self.default_feed_config = {}

    def _apply_overrides(self, base_config: Dict[str, Any], overrides: Dict[str, Any]):
        """Apply configuration overrides recursively"""
        for key, value in overrides.items():
            if isinstance(value, dict) and key in base_config and isinstance(base_config[key], dict):
                self._apply_overrides(base_config[key], value)
            else:
                base_config[key] = value

    async def get_global_config(self) -> Dict[str, Any]:
        """Get global configuration"""
        return self.global_config

    async def get_questdb_config(self) -> Dict[str, Any]:
        """Get QuestDB configuration"""
        return self.global_config.get('questdb', {})

    async def get_feed_config(self, feed_name: str) -> Dict[str, Any]:
        """Get configuration for a specific feed"""
        if feed_name not in self.feed_configs:
            await self._load_feed_config(feed_name)
        return self.feed_configs.get(feed_name, self.default_feed_config)

    async def load_feed_config(self, feed_name: str, config_path: str) -> Dict[str, Any]:
        """Load feed configuration from specific path"""
        try:
            with open(config_path, 'r') as f:
                feed_config = yaml.safe_load(f) or {}

            # Merge with defaults
            merged_config = self.default_feed_config.copy()
            self._apply_overrides(merged_config, feed_config)

            self.feed_configs[feed_name] = merged_config
            return merged_config

        except Exception as e:
            self.logger.error(f"Failed to load feed config '{config_path}': {e}")
            return self.default_feed_config

    async def _load_feed_config(self, feed_name: str):
        """Load feed configuration from standard location"""
        feed_config_file = self.config_root / 'feeds' / f'{feed_name}.yaml'

        if feed_config_file.exists():
            await self.load_feed_config(feed_name, str(feed_config_file))
        else:
            self.feed_configs[feed_name] = self.default_feed_config