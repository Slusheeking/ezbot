"""
Enhanced Feed Base Class

Improved base class for all data feeds with integrated QuestDB management,
telemetry collection, data validation, and standardized patterns.
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass

# Import from existing base
import sys
sys.path.append('/home/ezb0t/ezbot')
from utils.market_schedule import ScheduledFeedBase

# Import new core systems
from core.questdb_manager import QuestDBManager, get_questdb_manager
from core.questdb_manager.schema_manager import TableSchema
from core.config_manager import ConfigManager, get_config_manager
from core.alerts import AlertManager, get_alert_manager
from core.data_validation import DataValidator
from utils.telemetry import TelemetryCollector, TelemetryStorage


@dataclass
class FeedExecutionResult:
    """Result of feed execution with metrics and data"""
    success: bool
    records_processed: int = 0
    records_failed: int = 0
    execution_time_ms: float = 0.0
    data_quality_score: float = 100.0
    error_message: Optional[str] = None
    warnings: List[str] = None
    data_summary: Dict[str, Any] = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []
        if self.data_summary is None:
            self.data_summary = {}


class EnhancedFeedBase(ScheduledFeedBase):
    """
    Enhanced base class for all data feeds

    Features:
    - Integrated QuestDB management with automatic table creation
    - Built-in telemetry collection and health monitoring
    - Standardized data validation framework
    - Alert management and notification
    - Configuration management with environment overrides
    - Standardized error handling and retry logic
    - Data quality monitoring and reporting
    """

    def __init__(self,
                 feed_name: str,
                 feed_category: str,
                 market_type: Optional[str] = None,
                 custom_intervals: Optional[Dict] = None,
                 priority: str = "medium",
                 config_path: Optional[str] = None):
        """Initialize enhanced feed base"""

        # Initialize parent class
        super().__init__(
            feed_name=feed_name,
            feed_category=feed_category,
            market_type=market_type,
            custom_intervals=custom_intervals,
            priority=priority
        )

        # Enhanced components
        self.logger = logging.getLogger(f'feed.{feed_name}')

        # Core managers (will be initialized in setup)
        self.config_manager: Optional[ConfigManager] = None
        self.questdb_manager: Optional[QuestDBManager] = None
        self.alert_manager: Optional[AlertManager] = None

        # Feed-specific components
        self.data_validator: Optional[DataValidator] = None
        self.telemetry_collector: Optional[TelemetryCollector] = None
        self.telemetry_storage: Optional[TelemetryStorage] = None

        # Configuration
        self.config_path = config_path
        self.feed_config: Dict[str, Any] = {}

        # Schema and validation
        self.table_schema: Optional[TableSchema] = None
        self.validation_rules: Dict[str, Any] = {}

        # State tracking
        self.initialized = False
        self.execution_count = 0
        self.last_execution_time: Optional[datetime] = None
        self.last_execution_result: Optional[FeedExecutionResult] = None

    async def initialize(self) -> bool:
        """Initialize all enhanced feed components"""
        if self.initialized:
            return True

        try:
            self.logger.info(f"Initializing enhanced feed: {self.feed_name}")

            # Initialize configuration
            await self._initialize_config()

            # Initialize core managers
            await self._initialize_managers()

            # Initialize feed-specific components
            await self._initialize_feed_components()

            # Create database schema
            await self._initialize_database_schema()

            # Setup telemetry
            await self._initialize_telemetry()

            self.initialized = True
            self.logger.info(f"Enhanced feed '{self.feed_name}' initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize enhanced feed '{self.feed_name}': {e}")
            return False

    async def _initialize_config(self):
        """Initialize configuration management"""
        self.config_manager = get_config_manager()

        # Load feed-specific configuration
        if self.config_path:
            self.feed_config = await self.config_manager.load_feed_config(
                self.feed_name, self.config_path
            )
        else:
            self.feed_config = await self.config_manager.get_feed_config(self.feed_name)

        self.logger.debug(f"Loaded configuration for feed '{self.feed_name}'")

    async def _initialize_managers(self):
        """Initialize core system managers"""
        # Get global manager instances
        global_config = await self.config_manager.get_global_config()

        self.questdb_manager = get_questdb_manager(global_config)
        if not self.questdb_manager.initialized:
            await self.questdb_manager.initialize()

        self.alert_manager = get_alert_manager(global_config)
        if not self.alert_manager.initialized:
            await self.alert_manager.initialize()

    async def _initialize_feed_components(self):
        """Initialize feed-specific components"""
        # Data validator
        self.data_validator = DataValidator(
            rules=self.feed_config.get('validation', {}),
            feed_name=self.feed_name
        )

        # Validation rules from config
        self.validation_rules = self.feed_config.get('validation', {})

    async def _initialize_database_schema(self):
        """Initialize database schema and tables"""
        # Get schema definition from feed implementation
        schema_def = await self.define_schema()
        if schema_def:
            self.table_schema = TableSchema.from_dict(schema_def)

            # Create table in QuestDB
            success = await self.questdb_manager.create_table_from_schema(self.table_schema)
            if success:
                self.logger.info(f"Database table '{self.table_schema.table_name}' ready")
            else:
                self.logger.warning(f"Failed to create table '{self.table_schema.table_name}'")

    async def _initialize_telemetry(self):
        """Initialize telemetry collection and storage"""
        telemetry_config = self.feed_config.get('telemetry', {})

        if telemetry_config.get('enabled', True):
            self.telemetry_collector = TelemetryCollector(self.feed_name)

            # Initialize telemetry storage
            questdb_config = await self.config_manager.get_questdb_config()
            self.telemetry_storage = TelemetryStorage(
                host=questdb_config.get('host', 'localhost'),
                port=questdb_config.get('port', 8812),
                database=questdb_config.get('database', 'qdb')
            )

    @abstractmethod
    async def define_schema(self) -> Optional[Dict[str, Any]]:
        """
        Define the database schema for this feed's data

        Returns:
            Dictionary representing the table schema, or None if no database storage needed
        """
        pass

    @abstractmethod
    async def fetch_data(self) -> List[Dict[str, Any]]:
        """
        Fetch raw data from the data source

        Returns:
            List of raw data records
        """
        pass

    async def process_data(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process and transform raw data

        Args:
            raw_data: Raw data from fetch_data()

        Returns:
            Processed data ready for storage

        Note: This method can be overridden for custom processing
        """
        # Default implementation: basic timestamp addition
        processed_data = []
        current_time = datetime.now(timezone.utc)

        for record in raw_data:
            processed_record = record.copy()
            if 'timestamp' not in processed_record:
                processed_record['timestamp'] = current_time
            if 'collected_at' not in processed_record:
                processed_record['collected_at'] = current_time
            processed_data.append(processed_record)

        return processed_data

    async def validate_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Validate processed data against schema and rules

        Args:
            data: Processed data to validate

        Returns:
            Validated data (may have some records filtered out)
        """
        if not self.data_validator:
            return data

        validated_data = []
        for record in data:
            try:
                # Validate against schema if available
                if self.table_schema:
                    validated_record = self.table_schema.validate_record(record)
                else:
                    validated_record = record

                # Apply custom validation rules
                if await self.data_validator.validate_record(validated_record):
                    validated_data.append(validated_record)

            except Exception as e:
                self.logger.warning(f"Data validation failed for record: {e}")

        return validated_data

    async def store_data(self, data: List[Dict[str, Any]]) -> bool:
        """
        Store validated data in QuestDB

        Args:
            data: Validated data to store

        Returns:
            True if storage was successful
        """
        if not data or not self.table_schema:
            return True

        try:
            result = await self.questdb_manager.execute_batch_insert(
                table_name=self.table_schema.table_name,
                data=data,
                batch_size=self.feed_config.get('database', {}).get('batch_size', 1000)
            )

            if result.success:
                self.logger.debug(f"Stored {result.records_inserted} records in database")
                return True
            else:
                self.logger.error(f"Database storage failed: {result.error_message}")
                return False

        except Exception as e:
            self.logger.error(f"Error storing data: {e}")
            return False

    async def collect_data(self) -> Dict[str, Any]:
        """
        Enhanced implementation of the main data collection method

        This method orchestrates the entire data collection pipeline:
        1. Fetch raw data
        2. Process and transform data
        3. Validate data
        4. Store data
        5. Collect telemetry and metrics
        6. Handle errors and alerts
        """
        start_time = time.time()
        execution_result = FeedExecutionResult(success=False)

        try:
            # Ensure initialization
            if not self.initialized:
                await self.initialize()

            # Start telemetry collection
            telemetry_start = None
            if self.telemetry_collector:
                telemetry_start = self.telemetry_collector.start_collection()

            # Step 1: Fetch raw data
            self.logger.debug("Fetching raw data...")
            raw_data = await self.fetch_data()
            self.logger.debug(f"Fetched {len(raw_data)} raw records")

            # Step 2: Process data
            self.logger.debug("Processing data...")
            processed_data = await self.process_data(raw_data)
            self.logger.debug(f"Processed {len(processed_data)} records")

            # Step 3: Validate data
            self.logger.debug("Validating data...")
            validated_data = await self.validate_data(processed_data)
            self.logger.debug(f"Validated {len(validated_data)} records")

            # Calculate metrics
            records_processed = len(validated_data)
            records_failed = len(raw_data) - records_processed
            execution_time_ms = (time.time() - start_time) * 1000

            # Step 4: Store data
            storage_success = True
            if validated_data and self.table_schema:
                self.logger.debug("Storing data...")
                storage_success = await self.store_data(validated_data)

            # Step 5: Calculate data quality score
            data_quality_score = await self._calculate_data_quality_score(
                raw_data, validated_data
            )

            # Step 6: Update execution result
            execution_result = FeedExecutionResult(
                success=storage_success,
                records_processed=records_processed,
                records_failed=records_failed,
                execution_time_ms=execution_time_ms,
                data_quality_score=data_quality_score,
                data_summary=await self._generate_data_summary(validated_data)
            )

            # Step 7: Store telemetry
            if self.telemetry_collector and telemetry_start:
                metrics = self.telemetry_collector.end_collection(
                    start_time=telemetry_start,
                    records_processed=records_processed,
                    records_failed=records_failed,
                    error=None
                )

                if self.telemetry_storage:
                    await self.telemetry_storage.store_metrics(metrics)

            # Step 8: Check for alerts
            await self._check_execution_alerts(execution_result)

            # Update state
            self.execution_count += 1
            self.last_execution_time = datetime.now()
            self.last_execution_result = execution_result

            # Log success
            self.logger.info(
                f"Data collection successful: {records_processed} records, "
                f"{execution_time_ms:.1f}ms, quality: {data_quality_score:.1f}%"
            )

            # Return summary for base class
            return {
                'success': execution_result.success,
                'records_processed': execution_result.records_processed,
                'records_failed': execution_result.records_failed,
                'execution_time_ms': execution_result.execution_time_ms,
                'data_quality_score': execution_result.data_quality_score,
                'timestamp': datetime.now().isoformat(),
                'data_summary': execution_result.data_summary
            }

        except Exception as e:
            # Handle errors
            execution_time_ms = (time.time() - start_time) * 1000
            error_message = str(e)

            execution_result = FeedExecutionResult(
                success=False,
                execution_time_ms=execution_time_ms,
                error_message=error_message
            )

            # Store error telemetry
            if self.telemetry_collector and telemetry_start:
                metrics = self.telemetry_collector.end_collection(
                    start_time=telemetry_start,
                    records_processed=0,
                    records_failed=0,
                    error=error_message
                )

                if self.telemetry_storage:
                    await self.telemetry_storage.store_metrics(metrics)

            # Send error alert
            if self.alert_manager:
                await self.alert_manager.send_alert(
                    feed_name=self.feed_name,
                    severity="error",
                    message=f"Feed execution failed: {error_message}",
                    context={'execution_time_ms': execution_time_ms}
                )

            self.logger.error(f"Data collection failed: {error_message}")

            # Update state
            self.last_execution_result = execution_result

            # Re-raise for parent class handling
            raise

    async def _calculate_data_quality_score(self,
                                          raw_data: List[Dict[str, Any]],
                                          validated_data: List[Dict[str, Any]]) -> float:
        """Calculate data quality score based on various metrics"""
        if not raw_data:
            return 100.0

        # Base score
        score = 100.0

        # Completeness score (how much data passed validation)
        completeness = len(validated_data) / len(raw_data) if raw_data else 1.0
        score *= completeness

        # Additional quality checks can be added here
        # - Null value percentage
        # - Duplicate detection
        # - Value range validation
        # - Freshness checks

        return min(100.0, max(0.0, score))

    async def _generate_data_summary(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a summary of the collected data"""
        if not data:
            return {'record_count': 0}

        summary = {
            'record_count': len(data),
            'first_record_time': None,
            'last_record_time': None,
            'unique_symbols': set(),
            'data_types': {}
        }

        # Analyze data
        for record in data:
            # Time analysis
            if 'timestamp' in record:
                timestamp = record['timestamp']
                if isinstance(timestamp, datetime):
                    timestamp_str = timestamp.isoformat()
                else:
                    timestamp_str = str(timestamp)

                if summary['first_record_time'] is None:
                    summary['first_record_time'] = timestamp_str
                summary['last_record_time'] = timestamp_str

            # Symbol tracking
            if 'symbol' in record:
                summary['unique_symbols'].add(record['symbol'])

            # Data type analysis
            for key, value in record.items():
                if key not in summary['data_types']:
                    summary['data_types'][key] = type(value).__name__

        # Convert sets to lists for JSON serialization
        summary['unique_symbols'] = list(summary['unique_symbols'])
        summary['unique_symbol_count'] = len(summary['unique_symbols'])

        return summary

    async def _check_execution_alerts(self, result: FeedExecutionResult):
        """Check execution result for alert conditions"""
        if not self.alert_manager:
            return

        alert_config = self.feed_config.get('alerts', {})
        if not alert_config.get('enabled', True):
            return

        alerts = []

        # Performance alerts
        if result.execution_time_ms > alert_config.get('max_execution_time_ms', 30000):
            alerts.append({
                'severity': 'warning',
                'message': f"Slow execution: {result.execution_time_ms:.1f}ms",
                'metric': 'execution_time_ms',
                'value': result.execution_time_ms
            })

        # Data quality alerts
        if result.data_quality_score < alert_config.get('min_data_quality_score', 90.0):
            alerts.append({
                'severity': 'warning',
                'message': f"Low data quality: {result.data_quality_score:.1f}%",
                'metric': 'data_quality_score',
                'value': result.data_quality_score
            })

        # Record count alerts
        min_records = alert_config.get('min_records_per_execution', 0)
        if result.records_processed < min_records:
            alerts.append({
                'severity': 'warning',
                'message': f"Low record count: {result.records_processed} (min: {min_records})",
                'metric': 'records_processed',
                'value': result.records_processed
            })

        # Send alerts
        for alert in alerts:
            await self.alert_manager.send_alert(
                feed_name=self.feed_name,
                severity=alert['severity'],
                message=alert['message'],
                context={
                    'metric': alert['metric'],
                    'value': alert['value'],
                    'execution_result': result.__dict__
                }
            )

    async def get_feed_status(self) -> Dict[str, Any]:
        """Get comprehensive feed status and metrics"""
        status = {
            'feed_name': self.feed_name,
            'feed_category': self.feed_category,
            'market_type': self.market_type,
            'priority': self.priority,
            'initialized': self.initialized,
            'execution_count': self.execution_count,
            'last_execution_time': self.last_execution_time.isoformat() if self.last_execution_time else None,
        }

        # Add last execution result
        if self.last_execution_result:
            status['last_execution'] = {
                'success': self.last_execution_result.success,
                'records_processed': self.last_execution_result.records_processed,
                'records_failed': self.last_execution_result.records_failed,
                'execution_time_ms': self.last_execution_result.execution_time_ms,
                'data_quality_score': self.last_execution_result.data_quality_score,
                'error_message': self.last_execution_result.error_message
            }

        # Add component status
        status['components'] = {
            'config_manager': self.config_manager is not None,
            'questdb_manager': self.questdb_manager is not None and self.questdb_manager.initialized,
            'alert_manager': self.alert_manager is not None,
            'data_validator': self.data_validator is not None,
            'telemetry_collector': self.telemetry_collector is not None,
            'table_schema': self.table_schema is not None
        }

        return status

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on the feed"""
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'checks': {}
        }

        # Check initialization
        health_status['checks']['initialized'] = {
            'status': 'pass' if self.initialized else 'fail',
            'message': 'Feed properly initialized' if self.initialized else 'Feed not initialized'
        }

        # Check QuestDB connection
        if self.questdb_manager:
            db_health = await self.questdb_manager.health_check()
            health_status['checks']['database'] = {
                'status': 'pass' if db_health['status'] == 'healthy' else 'fail',
                'message': f"Database {db_health['status']}"
            }
        else:
            health_status['checks']['database'] = {
                'status': 'warn',
                'message': 'No database manager configured'
            }

        # Check recent execution
        if self.last_execution_result:
            execution_age = (datetime.now() - self.last_execution_time).total_seconds()
            max_age = self.feed_config.get('health_check', {}).get('max_execution_age_seconds', 3600)

            if execution_age > max_age:
                health_status['checks']['recent_execution'] = {
                    'status': 'warn',
                    'message': f"Last execution was {execution_age:.0f}s ago"
                }
            elif not self.last_execution_result.success:
                health_status['checks']['recent_execution'] = {
                    'status': 'fail',
                    'message': f"Last execution failed: {self.last_execution_result.error_message}"
                }
            else:
                health_status['checks']['recent_execution'] = {
                    'status': 'pass',
                    'message': 'Recent execution successful'
                }

        # Determine overall status
        check_statuses = [check['status'] for check in health_status['checks'].values()]
        if 'fail' in check_statuses:
            health_status['status'] = 'unhealthy'
        elif 'warn' in check_statuses:
            health_status['status'] = 'degraded'

        return health_status