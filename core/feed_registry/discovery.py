"""
Feed Discovery System

Automatically discovers and registers data feeds from the filesystem.
Scans directories for feed implementations and registers them with the registry.
"""

import os
import sys
import importlib
import importlib.util
import logging
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import inspect


class FeedDiscovery:
    """
    Automatic feed discovery system

    Features:
    - Filesystem scanning for feed implementations
    - Dynamic module loading and validation
    - Automatic registration with feed registry
    - Configuration loading and validation
    - Error handling and reporting
    """

    def __init__(self, registry, config: Dict[str, Any]):
        """Initialize feed discovery system"""
        self.registry = registry
        self.config = config
        self.logger = logging.getLogger('feed_discovery')

        # Discovery configuration
        self.scan_paths = config.get('discovery', {}).get('scan_paths', [])
        self.exclude_patterns = config.get('discovery', {}).get('exclude_patterns', [])
        self.require_config = config.get('discovery', {}).get('require_config', True)

        # Discovered feeds tracking
        self.discovered_feeds: Dict[str, Dict[str, Any]] = {}
        self.discovery_errors: List[str] = []

    async def discover_all_feeds(self) -> Dict[str, Any]:
        """Discover all feeds in configured paths"""
        self.logger.info("Starting feed discovery process...")

        discovery_results = {
            'discovered': [],
            'registered': [],
            'errors': [],
            'skipped': []
        }

        # Clear previous state
        self.discovered_feeds.clear()
        self.discovery_errors.clear()

        # Scan each configured path
        for scan_path in self.scan_paths:
            try:
                path_results = await self._scan_path(scan_path)

                discovery_results['discovered'].extend(path_results['discovered'])
                discovery_results['errors'].extend(path_results['errors'])
                discovery_results['skipped'].extend(path_results['skipped'])

            except Exception as e:
                error_msg = f"Error scanning path '{scan_path}': {e}"
                self.logger.error(error_msg)
                discovery_results['errors'].append(error_msg)

        # Register discovered feeds
        for feed_info in discovery_results['discovered']:
            try:
                success = await self._register_discovered_feed(feed_info)
                if success:
                    discovery_results['registered'].append(feed_info['name'])
                else:
                    discovery_results['errors'].append(f"Failed to register feed: {feed_info['name']}")

            except Exception as e:
                error_msg = f"Error registering feed '{feed_info['name']}': {e}"
                self.logger.error(error_msg)
                discovery_results['errors'].append(error_msg)

        self.logger.info(
            f"Feed discovery complete: "
            f"{len(discovery_results['registered'])} registered, "
            f"{len(discovery_results['errors'])} errors, "
            f"{len(discovery_results['skipped'])} skipped"
        )

        return discovery_results

    async def _scan_path(self, scan_path: str) -> Dict[str, List[Any]]:
        """Scan a specific path for feed implementations"""
        results = {
            'discovered': [],
            'errors': [],
            'skipped': []
        }

        try:
            base_path = Path(scan_path)
            if not base_path.exists():
                results['errors'].append(f"Scan path does not exist: {scan_path}")
                return results

            self.logger.info(f"Scanning path: {scan_path}")

            # Look for feed directories
            for item_path in base_path.iterdir():
                if not item_path.is_dir():
                    continue

                # Skip excluded patterns
                if self._should_exclude(item_path.name):
                    results['skipped'].append(f"Excluded directory: {item_path.name}")
                    continue

                # Check if this looks like a feed directory
                feed_info = await self._analyze_feed_directory(item_path)
                if feed_info:
                    results['discovered'].append(feed_info)
                else:
                    results['skipped'].append(f"Not a feed directory: {item_path.name}")

        except Exception as e:
            results['errors'].append(f"Error scanning path '{scan_path}': {e}")

        return results

    async def _analyze_feed_directory(self, feed_path: Path) -> Optional[Dict[str, Any]]:
        """Analyze a directory to determine if it contains a valid feed"""
        try:
            # Check for required files
            init_file = feed_path / "__init__.py"
            if not init_file.exists():
                return None

            # Look for main feed file (various naming patterns)
            feed_files = []
            for pattern in ["*_feed.py", "*feed.py", "feed.py", "main.py"]:
                feed_files.extend(feed_path.glob(pattern))

            if not feed_files:
                return None

            main_feed_file = feed_files[0]  # Use first match

            # Check for settings file
            settings_file = feed_path / "settings.yaml"
            if self.require_config and not settings_file.exists():
                self.logger.warning(f"Feed directory '{feed_path.name}' missing settings.yaml")
                return None

            # Load and validate the feed module
            feed_module_info = await self._load_feed_module(main_feed_file, feed_path.name)
            if not feed_module_info:
                return None

            # Load configuration if available
            config = None
            if settings_file.exists():
                config = await self._load_feed_config(settings_file)

            return {
                'name': feed_path.name,
                'path': str(feed_path),
                'main_file': str(main_feed_file),
                'settings_file': str(settings_file) if settings_file.exists() else None,
                'module_info': feed_module_info,
                'config': config
            }

        except Exception as e:
            self.logger.error(f"Error analyzing feed directory '{feed_path}': {e}")
            return None

    async def _load_feed_module(self, module_file: Path, feed_name: str) -> Optional[Dict[str, Any]]:
        """Load and validate a feed module"""
        try:
            # Import the module
            spec = importlib.util.spec_from_file_location(f"{feed_name}_module", module_file)
            if not spec or not spec.loader:
                return None

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Find feed classes that inherit from ScheduledFeedBase
            feed_classes = []
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if hasattr(obj, 'feed_name') and hasattr(obj, 'collect_data'):
                    # Check if it looks like a feed class
                    if self._is_valid_feed_class(obj):
                        feed_classes.append({
                            'name': name,
                            'class': obj,
                            'module': module
                        })

            if not feed_classes:
                self.logger.warning(f"No valid feed classes found in {module_file}")
                return None

            # Use the first valid feed class
            feed_class_info = feed_classes[0]

            return {
                'module': module,
                'feed_class': feed_class_info['class'],
                'class_name': feed_class_info['name'],
                'file_path': str(module_file)
            }

        except Exception as e:
            self.logger.error(f"Error loading feed module '{module_file}': {e}")
            return None

    def _is_valid_feed_class(self, cls) -> bool:
        """Check if a class is a valid feed implementation"""
        try:
            # Check for required methods
            required_methods = ['collect_data']
            for method_name in required_methods:
                if not hasattr(cls, method_name):
                    return False

            # Check if it's async
            if not inspect.iscoroutinefunction(cls.collect_data):
                self.logger.warning(f"Feed class {cls.__name__} collect_data is not async")

            # Check for required attributes (might be set in __init__)
            # We'll validate these when instantiating
            return True

        except Exception as e:
            self.logger.error(f"Error validating feed class {cls.__name__}: {e}")
            return False

    async def _load_feed_config(self, config_file: Path) -> Optional[Dict[str, Any]]:
        """Load feed configuration from YAML file"""
        try:
            import yaml
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
            return config

        except Exception as e:
            self.logger.error(f"Error loading config from '{config_file}': {e}")
            return None

    async def _register_discovered_feed(self, feed_info: Dict[str, Any]) -> bool:
        """Register a discovered feed with the registry"""
        try:
            feed_name = feed_info['name']
            module_info = feed_info['module_info']
            feed_class = module_info['feed_class']

            self.logger.info(f"Registering discovered feed: {feed_name}")

            # Instantiate the feed class
            # Pass config file path if available
            if feed_info.get('settings_file'):
                feed_instance = feed_class(config_path=feed_info['settings_file'])
            else:
                feed_instance = feed_class()

            # Validate feed instance
            if not self._validate_feed_instance(feed_instance):
                self.logger.error(f"Feed instance validation failed for '{feed_name}'")
                return False

            # Register with the registry
            success = self.registry.register_feed(feed_instance)
            if success:
                self.discovered_feeds[feed_name] = feed_info
                self.logger.info(f"Successfully registered feed: {feed_name}")
            else:
                self.logger.error(f"Failed to register feed with registry: {feed_name}")

            return success

        except Exception as e:
            self.logger.error(f"Error registering discovered feed '{feed_info['name']}': {e}")
            return False

    def _validate_feed_instance(self, feed_instance) -> bool:
        """Validate a feed instance has required attributes and methods"""
        try:
            # Check required attributes
            required_attrs = ['feed_name', 'feed_category']
            for attr in required_attrs:
                if not hasattr(feed_instance, attr):
                    self.logger.error(f"Feed instance missing required attribute: {attr}")
                    return False

                value = getattr(feed_instance, attr)
                if not value:
                    self.logger.error(f"Feed instance has empty required attribute: {attr}")
                    return False

            # Check required methods
            if not hasattr(feed_instance, 'collect_data'):
                self.logger.error("Feed instance missing collect_data method")
                return False

            if not callable(getattr(feed_instance, 'collect_data')):
                self.logger.error("Feed instance collect_data is not callable")
                return False

            return True

        except Exception as e:
            self.logger.error(f"Error validating feed instance: {e}")
            return False

    def _should_exclude(self, directory_name: str) -> bool:
        """Check if a directory should be excluded from scanning"""
        for pattern in self.exclude_patterns:
            if pattern in directory_name:
                return True

        # Built-in exclusions
        builtin_exclusions = ['__pycache__', '.git', '.pytest_cache', 'node_modules', '.venv', 'venv']
        return directory_name in builtin_exclusions

    async def rediscover_feed(self, feed_name: str) -> bool:
        """Rediscover and re-register a specific feed"""
        try:
            self.logger.info(f"Rediscovering feed: {feed_name}")

            # Unregister existing feed
            self.registry.unregister_feed(feed_name)

            # Find the feed directory
            feed_path = None
            for scan_path in self.scan_paths:
                potential_path = Path(scan_path) / feed_name
                if potential_path.exists() and potential_path.is_dir():
                    feed_path = potential_path
                    break

            if not feed_path:
                self.logger.error(f"Feed directory not found for: {feed_name}")
                return False

            # Analyze and register
            feed_info = await self._analyze_feed_directory(feed_path)
            if not feed_info:
                self.logger.error(f"Failed to analyze feed directory: {feed_name}")
                return False

            return await self._register_discovered_feed(feed_info)

        except Exception as e:
            self.logger.error(f"Error rediscovering feed '{feed_name}': {e}")
            return False

    def get_discovery_report(self) -> Dict[str, Any]:
        """Get a detailed discovery report"""
        return {
            'timestamp': str(datetime.now()),
            'total_discovered': len(self.discovered_feeds),
            'scan_paths': self.scan_paths,
            'exclude_patterns': self.exclude_patterns,
            'discovered_feeds': {
                name: {
                    'path': info['path'],
                    'main_file': info['main_file'],
                    'has_config': info['settings_file'] is not None,
                    'class_name': info['module_info']['class_name']
                }
                for name, info in self.discovered_feeds.items()
            },
            'errors': self.discovery_errors,
            'config': {
                'require_config': self.require_config
            }
        }

    async def validate_all_discovered_feeds(self) -> Dict[str, Any]:
        """Validate all discovered feeds without registering them"""
        validation_results = {
            'valid': [],
            'invalid': [],
            'errors': []
        }

        discovery_results = await self.discover_all_feeds()

        for feed_info in discovery_results['discovered']:
            try:
                feed_name = feed_info['name']
                module_info = feed_info['module_info']
                feed_class = module_info['feed_class']

                # Try to instantiate
                if feed_info.get('settings_file'):
                    feed_instance = feed_class(config_path=feed_info['settings_file'])
                else:
                    feed_instance = feed_class()

                # Validate
                if self._validate_feed_instance(feed_instance):
                    validation_results['valid'].append({
                        'name': feed_name,
                        'class': module_info['class_name'],
                        'path': feed_info['path']
                    })
                else:
                    validation_results['invalid'].append({
                        'name': feed_name,
                        'class': module_info['class_name'],
                        'path': feed_info['path'],
                        'reason': 'Validation failed'
                    })

            except Exception as e:
                validation_results['errors'].append({
                    'name': feed_info.get('name', 'unknown'),
                    'error': str(e)
                })

        return validation_results