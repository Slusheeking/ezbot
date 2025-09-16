"""
QuestDB Manager Client

Centralized QuestDB connection and operation management for all data feeds.
Provides connection pooling, automatic table creation, batch operations,
and health monitoring.
"""

import asyncio
import logging
import psycopg2
import psycopg2.pool
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from contextlib import asynccontextmanager
import threading
import time

from .schema_manager import SchemaManager, TableSchema
from .connection_pool import ConnectionPool
from .health_monitor import QuestDBHealthMonitor


@dataclass
class BatchInsertResult:
    """Result of a batch insert operation"""
    success: bool
    records_inserted: int
    records_failed: int
    execution_time_ms: float
    error_message: Optional[str] = None


@dataclass
class QuestDBConfig:
    """QuestDB configuration"""
    host: str = "localhost"
    port: int = 8812
    database: str = "qdb"
    user: str = "admin"
    password: str = "quest"
    pool_size: int = 10
    pool_max_overflow: int = 5
    connection_timeout: int = 10
    query_timeout: int = 30
    retry_attempts: int = 3
    retry_delay: float = 1.0


class QuestDBManager:
    """
    Centralized QuestDB manager for all data feeds

    Features:
    - Connection pooling and management
    - Automatic table creation from schemas
    - Optimized batch operations
    - Health monitoring and alerting
    - Query optimization and retries
    - Transaction management
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize QuestDB manager with configuration"""
        self.config = QuestDBConfig(**config.get('questdb', {}))
        self.logger = logging.getLogger('questdb_manager')

        # Initialize components
        self.connection_pool = ConnectionPool(self.config)
        self.schema_manager = SchemaManager()
        self.health_monitor = QuestDBHealthMonitor(self)

        # State tracking
        self.initialized = False
        self._lock = threading.Lock()
        self._last_health_check = 0
        self._health_check_interval = 60  # seconds

        # Metrics
        self.metrics = {
            'total_queries': 0,
            'successful_queries': 0,
            'failed_queries': 0,
            'total_inserts': 0,
            'total_records_inserted': 0,
            'avg_query_time': 0.0,
            'last_error': None,
            'uptime_start': datetime.now()
        }

    async def initialize(self) -> bool:
        """Initialize the QuestDB manager and create connection pool"""
        if self.initialized:
            return True

        with self._lock:
            if self.initialized:
                return True

            try:
                self.logger.info("Initializing QuestDB Manager...")

                # Initialize connection pool
                await self.connection_pool.initialize()

                # Test connection
                if not await self.health_check():
                    raise Exception("Initial health check failed")

                # Load existing schemas
                await self.schema_manager.load_existing_schemas(self)

                self.initialized = True
                self.logger.info("QuestDB Manager initialized successfully")
                return True

            except Exception as e:
                self.logger.error(f"Failed to initialize QuestDB Manager: {e}")
                return False

    async def shutdown(self):
        """Shutdown the QuestDB manager and cleanup resources"""
        try:
            self.logger.info("Shutting down QuestDB Manager...")
            await self.connection_pool.close_all()
            self.initialized = False
            self.logger.info("QuestDB Manager shutdown complete")
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")

    @asynccontextmanager
    async def get_connection(self):
        """Get a connection from the pool with automatic cleanup"""
        connection = None
        try:
            connection = await self.connection_pool.get_connection()
            yield connection
        finally:
            if connection:
                await self.connection_pool.return_connection(connection)

    async def create_table_from_schema(self, schema: TableSchema) -> bool:
        """Create a table from a schema definition"""
        try:
            self.logger.info(f"Creating table '{schema.table_name}' from schema")

            async with self.get_connection() as conn:
                cursor = conn.cursor()

                # Generate CREATE TABLE SQL from schema
                sql = schema.to_create_sql()

                cursor.execute(sql)
                conn.commit()

                # Register schema
                self.schema_manager.register_schema(schema)

                self.logger.info(f"Table '{schema.table_name}' created successfully")
                return True

        except Exception as e:
            self.logger.error(f"Failed to create table '{schema.table_name}': {e}")
            return False

    async def execute_batch_insert(self,
                                 table_name: str,
                                 data: List[Dict[str, Any]],
                                 batch_size: int = 1000) -> BatchInsertResult:
        """Execute optimized batch insert with retries and error handling"""
        start_time = time.time()
        total_records = len(data)
        records_inserted = 0
        records_failed = 0

        if not data:
            return BatchInsertResult(
                success=True,
                records_inserted=0,
                records_failed=0,
                execution_time_ms=0
            )

        try:
            # Get table schema
            schema = self.schema_manager.get_schema(table_name)
            if not schema:
                raise ValueError(f"No schema found for table '{table_name}'")

            # Validate data against schema
            validated_data = []
            for record in data:
                try:
                    validated_record = schema.validate_record(record)
                    validated_data.append(validated_record)
                    records_inserted += 1
                except Exception as e:
                    self.logger.warning(f"Invalid record for {table_name}: {e}")
                    records_failed += 1

            if not validated_data:
                return BatchInsertResult(
                    success=False,
                    records_inserted=0,
                    records_failed=total_records,
                    execution_time_ms=(time.time() - start_time) * 1000,
                    error_message="No valid records to insert"
                )

            # Execute batch insert
            async with self.get_connection() as conn:
                cursor = conn.cursor()

                # Split into batches
                for i in range(0, len(validated_data), batch_size):
                    batch = validated_data[i:i + batch_size]

                    # Generate INSERT SQL
                    insert_sql = schema.to_insert_sql()
                    values = [schema.record_to_values(record) for record in batch]

                    # Execute with retries
                    for attempt in range(self.config.retry_attempts):
                        try:
                            psycopg2.extras.execute_values(
                                cursor,
                                insert_sql,
                                values,
                                template=None,
                                page_size=len(batch)
                            )
                            conn.commit()
                            break
                        except Exception as e:
                            if attempt == self.config.retry_attempts - 1:
                                raise
                            self.logger.warning(f"Insert attempt {attempt + 1} failed: {e}")
                            await asyncio.sleep(self.config.retry_delay)
                            conn.rollback()

            execution_time = (time.time() - start_time) * 1000

            # Update metrics
            self.metrics['total_inserts'] += 1
            self.metrics['total_records_inserted'] += records_inserted
            self.metrics['successful_queries'] += 1

            self.logger.info(f"Batch insert to {table_name}: {records_inserted} records in {execution_time:.1f}ms")

            return BatchInsertResult(
                success=True,
                records_inserted=records_inserted,
                records_failed=records_failed,
                execution_time_ms=execution_time
            )

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            error_msg = str(e)

            # Update metrics
            self.metrics['failed_queries'] += 1
            self.metrics['last_error'] = error_msg

            self.logger.error(f"Batch insert to {table_name} failed: {error_msg}")

            return BatchInsertResult(
                success=False,
                records_inserted=records_inserted,
                records_failed=records_failed,
                execution_time_ms=execution_time,
                error_message=error_msg
            )

    async def execute_query(self,
                          sql: str,
                          params: Optional[tuple] = None,
                          fetch_results: bool = True) -> Dict[str, Any]:
        """Execute a SQL query with error handling and retries"""
        start_time = time.time()

        try:
            async with self.get_connection() as conn:
                cursor = conn.cursor()

                for attempt in range(self.config.retry_attempts):
                    try:
                        if params:
                            cursor.execute(sql, params)
                        else:
                            cursor.execute(sql)

                        results = None
                        if fetch_results:
                            results = cursor.fetchall()
                            columns = [desc[0] for desc in cursor.description] if cursor.description else []

                        conn.commit()

                        execution_time = (time.time() - start_time) * 1000

                        # Update metrics
                        self.metrics['total_queries'] += 1
                        self.metrics['successful_queries'] += 1

                        return {
                            'success': True,
                            'results': results,
                            'columns': columns if fetch_results else [],
                            'execution_time_ms': execution_time,
                            'rows_affected': cursor.rowcount
                        }

                    except Exception as e:
                        if attempt == self.config.retry_attempts - 1:
                            raise
                        self.logger.warning(f"Query attempt {attempt + 1} failed: {e}")
                        await asyncio.sleep(self.config.retry_delay)
                        conn.rollback()

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            error_msg = str(e)

            # Update metrics
            self.metrics['total_queries'] += 1
            self.metrics['failed_queries'] += 1
            self.metrics['last_error'] = error_msg

            self.logger.error(f"Query execution failed: {error_msg}")

            return {
                'success': False,
                'error': error_msg,
                'execution_time_ms': execution_time
            }

    async def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check"""
        current_time = time.time()

        # Rate limit health checks
        if current_time - self._last_health_check < self._health_check_interval:
            return self.health_monitor.get_cached_status()

        self._last_health_check = current_time

        try:
            # Test basic connectivity
            result = await self.execute_query("SELECT 1", fetch_results=True)

            if result['success']:
                # Get database statistics
                stats_result = await self.execute_query("""
                    SELECT
                        count(*) as total_tables
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                """)

                # Calculate metrics
                uptime_seconds = (datetime.now() - self.metrics['uptime_start']).total_seconds()
                success_rate = (
                    self.metrics['successful_queries'] / max(self.metrics['total_queries'], 1) * 100
                )

                health_status = {
                    'status': 'healthy',
                    'timestamp': datetime.now().isoformat(),
                    'connection_pool_size': self.connection_pool.current_size(),
                    'total_tables': stats_result['results'][0][0] if stats_result['success'] else 0,
                    'metrics': {
                        'uptime_seconds': uptime_seconds,
                        'total_queries': self.metrics['total_queries'],
                        'success_rate_percent': success_rate,
                        'total_records_inserted': self.metrics['total_records_inserted'],
                        'avg_query_time_ms': self.metrics['avg_query_time']
                    },
                    'last_error': self.metrics['last_error']
                }

                self.health_monitor.update_status(health_status)
                return health_status
            else:
                raise Exception(f"Health check query failed: {result.get('error')}")

        except Exception as e:
            error_status = {
                'status': 'unhealthy',
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'connection_pool_size': self.connection_pool.current_size(),
                'metrics': self.metrics
            }

            self.health_monitor.update_status(error_status)
            return error_status

    def get_metrics(self) -> Dict[str, Any]:
        """Get current manager metrics"""
        return {
            **self.metrics,
            'connection_pool_size': self.connection_pool.current_size(),
            'schemas_registered': len(self.schema_manager.schemas),
            'uptime_seconds': (datetime.now() - self.metrics['uptime_start']).total_seconds()
        }

    async def optimize_table(self, table_name: str) -> bool:
        """Optimize table performance (rebuild indices, update statistics)"""
        try:
            self.logger.info(f"Optimizing table '{table_name}'")

            # QuestDB-specific optimization queries
            optimize_queries = [
                f"ALTER TABLE {table_name} ALTER COLUMN CACHE",
                f"ANALYZE TABLE {table_name}"
            ]

            for query in optimize_queries:
                try:
                    await self.execute_query(query, fetch_results=False)
                except Exception as e:
                    self.logger.warning(f"Optimization query failed: {e}")

            self.logger.info(f"Table '{table_name}' optimization completed")
            return True

        except Exception as e:
            self.logger.error(f"Failed to optimize table '{table_name}': {e}")
            return False