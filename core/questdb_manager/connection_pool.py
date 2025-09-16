"""
QuestDB Connection Pool

Manages a pool of database connections for efficient resource utilization
and improved performance across all data feeds.
"""

import asyncio
import logging
import psycopg2
import psycopg2.pool
from typing import Optional, Dict, Any
import threading
import time
from contextlib import contextmanager


class ConnectionPool:
    """
    Thread-safe connection pool for QuestDB connections

    Features:
    - Connection pooling with configurable min/max sizes
    - Connection health monitoring
    - Automatic connection recovery
    - Connection usage tracking
    - Graceful shutdown
    """

    def __init__(self, config):
        """Initialize connection pool with configuration"""
        self.config = config
        self.logger = logging.getLogger('connection_pool')

        # Pool state
        self.pool = None
        self.initialized = False
        self._lock = threading.Lock()

        # Connection tracking
        self.active_connections = 0
        self.total_connections_created = 0
        self.total_connections_closed = 0
        self.connection_errors = 0
        self.last_health_check = 0

        # Performance metrics
        self.metrics = {
            'pool_size': 0,
            'active_connections': 0,
            'available_connections': 0,
            'total_gets': 0,
            'total_puts': 0,
            'wait_time_total': 0.0,
            'avg_wait_time': 0.0
        }

    async def initialize(self) -> bool:
        """Initialize the connection pool"""
        if self.initialized:
            return True

        with self._lock:
            if self.initialized:
                return True

            try:
                self.logger.info("Initializing QuestDB connection pool...")

                # Create connection pool
                self.pool = psycopg2.pool.ThreadedConnectionPool(
                    minconn=1,
                    maxconn=self.config.pool_size,
                    host=self.config.host,
                    port=self.config.port,
                    database=self.config.database,
                    user=self.config.user,
                    password=self.config.password,
                    connect_timeout=self.config.connection_timeout
                )

                # Test initial connection
                test_conn = self.pool.getconn()
                if test_conn:
                    # Test the connection
                    cursor = test_conn.cursor()
                    cursor.execute("SELECT 1")
                    cursor.close()
                    self.pool.putconn(test_conn)

                    self.initialized = True
                    self.logger.info(f"Connection pool initialized with {self.config.pool_size} max connections")
                    return True
                else:
                    raise Exception("Failed to get test connection from pool")

            except Exception as e:
                self.logger.error(f"Failed to initialize connection pool: {e}")
                self.pool = None
                return False

    async def get_connection(self):
        """Get a connection from the pool"""
        if not self.initialized:
            raise Exception("Connection pool not initialized")

        start_time = time.time()

        try:
            # Get connection from pool
            connection = self.pool.getconn()
            if not connection:
                raise Exception("Failed to get connection from pool")

            # Test connection health
            if not self._test_connection(connection):
                # Return bad connection and try again
                self.pool.putconn(connection, close=True)
                connection = self.pool.getconn()
                if not connection or not self._test_connection(connection):
                    raise Exception("Unable to get healthy connection from pool")

            # Update metrics
            wait_time = time.time() - start_time
            self.metrics['total_gets'] += 1
            self.metrics['wait_time_total'] += wait_time
            self.metrics['avg_wait_time'] = self.metrics['wait_time_total'] / self.metrics['total_gets']
            self.active_connections += 1
            self.metrics['active_connections'] = self.active_connections

            self.logger.debug(f"Connection acquired in {wait_time:.3f}s")
            return connection

        except Exception as e:
            self.connection_errors += 1
            self.logger.error(f"Failed to get connection from pool: {e}")
            raise

    async def return_connection(self, connection, close: bool = False):
        """Return a connection to the pool"""
        if not connection:
            return

        try:
            if close or not self._test_connection(connection):
                # Close bad connection
                self.pool.putconn(connection, close=True)
                self.total_connections_closed += 1
            else:
                # Return healthy connection to pool
                self.pool.putconn(connection)

            # Update metrics
            self.metrics['total_puts'] += 1
            self.active_connections = max(0, self.active_connections - 1)
            self.metrics['active_connections'] = self.active_connections

        except Exception as e:
            self.logger.warning(f"Error returning connection to pool: {e}")
            try:
                connection.close()
            except:
                pass

    def _test_connection(self, connection) -> bool:
        """Test if a connection is healthy"""
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            return True
        except Exception:
            return False

    def current_size(self) -> int:
        """Get current pool size"""
        if not self.pool:
            return 0

        # psycopg2 doesn't provide direct access to pool size
        # Return configured size as approximation
        return self.config.pool_size

    def available_connections(self) -> int:
        """Get number of available connections"""
        if not self.pool:
            return 0

        return max(0, self.config.pool_size - self.active_connections)

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on the connection pool"""
        current_time = time.time()

        # Rate limit health checks to every 60 seconds
        if current_time - self.last_health_check < 60:
            return self._get_cached_health_status()

        self.last_health_check = current_time

        try:
            if not self.initialized:
                return {
                    'status': 'unhealthy',
                    'error': 'Connection pool not initialized',
                    'metrics': self.metrics
                }

            # Test getting a connection
            test_start = time.time()
            test_conn = await self.get_connection()
            connection_time = time.time() - test_start

            if test_conn:
                await self.return_connection(test_conn)

                # Update metrics
                self.metrics.update({
                    'pool_size': self.current_size(),
                    'available_connections': self.available_connections(),
                    'connection_test_time_ms': connection_time * 1000
                })

                status = {
                    'status': 'healthy',
                    'timestamp': current_time,
                    'connection_test_time_ms': connection_time * 1000,
                    'metrics': self.metrics,
                    'pool_stats': {
                        'max_connections': self.config.pool_size,
                        'active_connections': self.active_connections,
                        'available_connections': self.available_connections(),
                        'total_created': self.total_connections_created,
                        'total_closed': self.total_connections_closed,
                        'total_errors': self.connection_errors
                    }
                }

                self._cached_health_status = status
                return status
            else:
                raise Exception("Failed to get test connection")

        except Exception as e:
            error_status = {
                'status': 'unhealthy',
                'timestamp': current_time,
                'error': str(e),
                'metrics': self.metrics
            }
            self._cached_health_status = error_status
            return error_status

    def _get_cached_health_status(self) -> Dict[str, Any]:
        """Get cached health status"""
        return getattr(self, '_cached_health_status', {
            'status': 'unknown',
            'error': 'No health check performed yet'
        })

    async def close_all(self):
        """Close all connections in the pool"""
        if not self.pool:
            return

        try:
            self.logger.info("Closing all connections in pool...")
            self.pool.closeall()
            self.initialized = False
            self.active_connections = 0
            self.logger.info("All connections closed")
        except Exception as e:
            self.logger.error(f"Error closing connection pool: {e}")

    def get_pool_stats(self) -> Dict[str, Any]:
        """Get detailed pool statistics"""
        return {
            'initialized': self.initialized,
            'max_connections': self.config.pool_size,
            'active_connections': self.active_connections,
            'available_connections': self.available_connections(),
            'total_connections_created': self.total_connections_created,
            'total_connections_closed': self.total_connections_closed,
            'connection_errors': self.connection_errors,
            'metrics': self.metrics,
            'config': {
                'host': self.config.host,
                'port': self.config.port,
                'database': self.config.database,
                'pool_size': self.config.pool_size,
                'connection_timeout': self.config.connection_timeout
            }
        }

    @contextmanager
    def get_connection_sync(self):
        """Synchronous context manager for getting connections"""
        connection = None
        try:
            # Synchronous version for non-async contexts
            start_time = time.time()
            connection = self.pool.getconn()

            if not connection:
                raise Exception("Failed to get connection from pool")

            if not self._test_connection(connection):
                self.pool.putconn(connection, close=True)
                connection = self.pool.getconn()
                if not connection or not self._test_connection(connection):
                    raise Exception("Unable to get healthy connection from pool")

            # Update metrics
            wait_time = time.time() - start_time
            self.metrics['total_gets'] += 1
            self.metrics['wait_time_total'] += wait_time
            self.metrics['avg_wait_time'] = self.metrics['wait_time_total'] / self.metrics['total_gets']
            self.active_connections += 1

            yield connection

        finally:
            if connection:
                try:
                    self.pool.putconn(connection)
                    self.active_connections = max(0, self.active_connections - 1)
                    self.metrics['total_puts'] += 1
                except Exception as e:
                    self.logger.warning(f"Error returning connection: {e}")
                    try:
                        connection.close()
                    except:
                        pass