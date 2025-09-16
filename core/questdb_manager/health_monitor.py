"""
QuestDB Health Monitor

Monitors QuestDB health, performance, and availability.
Provides alerting and status tracking for the database system.
"""

import logging
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum


class HealthStatus(Enum):
    """Health status levels"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class HealthThreshold:
    """Health monitoring threshold configuration"""
    warning_level: float
    critical_level: float
    description: str = ""


@dataclass
class HealthAlert:
    """Health alert information"""
    timestamp: datetime
    alert_type: str
    severity: str
    message: str
    value: Optional[float] = None
    threshold: Optional[float] = None
    resolved: bool = False
    resolved_at: Optional[datetime] = None


@dataclass
class HealthMetrics:
    """QuestDB health metrics"""
    timestamp: datetime = field(default_factory=datetime.now)
    status: HealthStatus = HealthStatus.UNKNOWN
    response_time_ms: float = 0.0
    connection_pool_usage: float = 0.0
    active_connections: int = 0
    total_queries: int = 0
    failed_queries: int = 0
    success_rate: float = 100.0
    avg_query_time_ms: float = 0.0
    total_tables: int = 0
    disk_usage_percent: Optional[float] = None
    memory_usage_percent: Optional[float] = None
    uptime_seconds: float = 0.0
    last_error: Optional[str] = None
    alerts: List[HealthAlert] = field(default_factory=list)


class QuestDBHealthMonitor:
    """
    Health monitor for QuestDB instance

    Features:
    - Real-time health status tracking
    - Configurable alert thresholds
    - Historical health data
    - Alert management and notification
    - Performance trend analysis
    """

    def __init__(self, questdb_manager):
        """Initialize health monitor"""
        self.questdb_manager = questdb_manager
        self.logger = logging.getLogger('questdb_health_monitor')

        # Health tracking
        self.current_status: HealthMetrics = HealthMetrics()
        self.status_history: List[HealthMetrics] = []
        self.active_alerts: Dict[str, HealthAlert] = {}

        # Configuration
        self.thresholds = self._get_default_thresholds()
        self.max_history_size = 1000
        self.alert_cooldown_minutes = 5

        # State tracking
        self.last_health_check = 0
        self.consecutive_failures = 0
        self.last_successful_check = datetime.now()

    def _get_default_thresholds(self) -> Dict[str, HealthThreshold]:
        """Get default health monitoring thresholds"""
        return {
            'response_time_ms': HealthThreshold(
                warning_level=1000.0,
                critical_level=5000.0,
                description="Database response time in milliseconds"
            ),
            'connection_pool_usage': HealthThreshold(
                warning_level=70.0,
                critical_level=90.0,
                description="Connection pool usage percentage"
            ),
            'success_rate': HealthThreshold(
                warning_level=95.0,
                critical_level=90.0,
                description="Query success rate percentage (reversed - lower is worse)"
            ),
            'consecutive_failures': HealthThreshold(
                warning_level=3.0,
                critical_level=5.0,
                description="Number of consecutive health check failures"
            ),
            'disk_usage_percent': HealthThreshold(
                warning_level=80.0,
                critical_level=90.0,
                description="Disk usage percentage"
            ),
            'memory_usage_percent': HealthThreshold(
                warning_level=80.0,
                critical_level=90.0,
                description="Memory usage percentage"
            )
        }

    def update_thresholds(self, thresholds: Dict[str, Dict[str, float]]):
        """Update health monitoring thresholds"""
        for metric, threshold_config in thresholds.items():
            if metric in self.thresholds:
                self.thresholds[metric].warning_level = threshold_config.get(
                    'warning_level', self.thresholds[metric].warning_level
                )
                self.thresholds[metric].critical_level = threshold_config.get(
                    'critical_level', self.thresholds[metric].critical_level
                )

    def update_status(self, status_data: Dict[str, Any]):
        """Update current health status from QuestDB manager"""
        try:
            # Parse status data
            timestamp = datetime.now()
            status = HealthStatus(status_data.get('status', 'unknown'))

            # Extract metrics
            metrics_data = status_data.get('metrics', {})

            current_metrics = HealthMetrics(
                timestamp=timestamp,
                status=status,
                response_time_ms=status_data.get('connection_test_time_ms', 0.0),
                connection_pool_usage=self._calculate_pool_usage(status_data),
                active_connections=status_data.get('connection_pool_size', 0),
                total_queries=metrics_data.get('total_queries', 0),
                failed_queries=metrics_data.get('failed_queries', 0),
                success_rate=self._calculate_success_rate(metrics_data),
                avg_query_time_ms=metrics_data.get('avg_query_time', 0.0),
                total_tables=status_data.get('total_tables', 0),
                uptime_seconds=metrics_data.get('uptime_seconds', 0.0),
                last_error=status_data.get('error') or metrics_data.get('last_error')
            )

            # Update consecutive failures
            if status == HealthStatus.HEALTHY:
                self.consecutive_failures = 0
                self.last_successful_check = timestamp
            else:
                self.consecutive_failures += 1

            # Check for alerts
            new_alerts = self._check_alert_conditions(current_metrics)
            current_metrics.alerts = new_alerts

            # Update current status
            self.current_status = current_metrics

            # Add to history
            self._add_to_history(current_metrics)

            # Log status change
            if hasattr(self, '_last_logged_status') and self._last_logged_status != status:
                self.logger.info(f"Health status changed: {self._last_logged_status.value} -> {status.value}")
            self._last_logged_status = status

        except Exception as e:
            self.logger.error(f"Error updating health status: {e}")

    def _calculate_pool_usage(self, status_data: Dict[str, Any]) -> float:
        """Calculate connection pool usage percentage"""
        pool_stats = status_data.get('pool_stats', {})
        max_connections = pool_stats.get('max_connections', 1)
        active_connections = pool_stats.get('active_connections', 0)

        return (active_connections / max_connections) * 100 if max_connections > 0 else 0.0

    def _calculate_success_rate(self, metrics_data: Dict[str, Any]) -> float:
        """Calculate query success rate percentage"""
        total_queries = metrics_data.get('total_queries', 0)
        successful_queries = metrics_data.get('successful_queries', 0)

        if total_queries == 0:
            return 100.0

        return (successful_queries / total_queries) * 100

    def _check_alert_conditions(self, metrics: HealthMetrics) -> List[HealthAlert]:
        """Check for alert conditions and generate alerts"""
        alerts = []
        current_time = datetime.now()

        # Check each threshold
        checks = [
            ('response_time_ms', metrics.response_time_ms, False),
            ('connection_pool_usage', metrics.connection_pool_usage, False),
            ('success_rate', metrics.success_rate, True),  # Reversed - lower is worse
            ('consecutive_failures', self.consecutive_failures, False),
        ]

        for metric_name, value, reversed_logic in checks:
            if metric_name not in self.thresholds:
                continue

            threshold = self.thresholds[metric_name]
            alert_key = f"{metric_name}"

            # Skip if in cooldown period
            if alert_key in self.active_alerts:
                last_alert = self.active_alerts[alert_key]
                if (current_time - last_alert.timestamp).total_seconds() < (self.alert_cooldown_minutes * 60):
                    continue

            severity = None
            if reversed_logic:
                # For metrics where lower values are worse (like success_rate)
                if value <= threshold.critical_level:
                    severity = "critical"
                elif value <= threshold.warning_level:
                    severity = "warning"
            else:
                # For metrics where higher values are worse
                if value >= threshold.critical_level:
                    severity = "critical"
                elif value >= threshold.warning_level:
                    severity = "warning"

            if severity:
                alert = HealthAlert(
                    timestamp=current_time,
                    alert_type=metric_name,
                    severity=severity,
                    message=f"{threshold.description}: {value:.2f}",
                    value=value,
                    threshold=threshold.warning_level if severity == "warning" else threshold.critical_level
                )

                alerts.append(alert)
                self.active_alerts[alert_key] = alert

                self.logger.warning(
                    f"QuestDB Health Alert [{severity.upper()}]: {alert.message}"
                )

        # Check for resolved alerts
        self._check_resolved_alerts(metrics)

        return alerts

    def _check_resolved_alerts(self, metrics: HealthMetrics):
        """Check if any active alerts have been resolved"""
        current_time = datetime.now()
        resolved_alerts = []

        for alert_key, alert in list(self.active_alerts.items()):
            if alert.resolved:
                continue

            metric_name = alert.alert_type
            if metric_name not in self.thresholds:
                continue

            threshold = self.thresholds[metric_name]
            current_value = getattr(metrics, metric_name, None)

            if current_value is None:
                continue

            # Check if condition is resolved
            resolved = False
            if metric_name == 'success_rate':
                # Reversed logic
                resolved = current_value > threshold.warning_level
            else:
                resolved = current_value < threshold.warning_level

            if resolved:
                alert.resolved = True
                alert.resolved_at = current_time
                resolved_alerts.append(alert_key)

                self.logger.info(
                    f"QuestDB Health Alert Resolved: {alert.alert_type} - {current_value:.2f}"
                )

        # Remove resolved alerts
        for alert_key in resolved_alerts:
            del self.active_alerts[alert_key]

    def _add_to_history(self, metrics: HealthMetrics):
        """Add metrics to history and maintain size limit"""
        self.status_history.append(metrics)

        # Trim history if too large
        if len(self.status_history) > self.max_history_size:
            # Keep most recent entries
            self.status_history = self.status_history[-self.max_history_size:]

    def get_current_status(self) -> HealthMetrics:
        """Get current health status"""
        return self.current_status

    def get_cached_status(self) -> Dict[str, Any]:
        """Get cached status as dictionary"""
        return {
            'status': self.current_status.status.value,
            'timestamp': self.current_status.timestamp.isoformat(),
            'response_time_ms': self.current_status.response_time_ms,
            'connection_pool_usage': self.current_status.connection_pool_usage,
            'success_rate': self.current_status.success_rate,
            'consecutive_failures': self.consecutive_failures,
            'last_successful_check': self.last_successful_check.isoformat(),
            'active_alerts': len(self.active_alerts),
            'uptime_seconds': self.current_status.uptime_seconds,
            'last_error': self.current_status.last_error
        }

    def get_status_history(self, hours: int = 24) -> List[HealthMetrics]:
        """Get status history for the specified number of hours"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [
            metrics for metrics in self.status_history
            if metrics.timestamp >= cutoff_time
        ]

    def get_active_alerts(self) -> List[HealthAlert]:
        """Get list of active alerts"""
        return list(self.active_alerts.values())

    def get_health_summary(self) -> Dict[str, Any]:
        """Get comprehensive health summary"""
        recent_history = self.get_status_history(1)  # Last hour

        # Calculate trends
        avg_response_time = sum(m.response_time_ms for m in recent_history) / len(recent_history) if recent_history else 0
        avg_success_rate = sum(m.success_rate for m in recent_history) / len(recent_history) if recent_history else 100

        return {
            'current_status': self.current_status.status.value,
            'timestamp': self.current_status.timestamp.isoformat(),
            'metrics': {
                'response_time_ms': self.current_status.response_time_ms,
                'avg_response_time_1h': avg_response_time,
                'connection_pool_usage': self.current_status.connection_pool_usage,
                'success_rate': self.current_status.success_rate,
                'avg_success_rate_1h': avg_success_rate,
                'total_queries': self.current_status.total_queries,
                'failed_queries': self.current_status.failed_queries,
                'uptime_seconds': self.current_status.uptime_seconds,
                'consecutive_failures': self.consecutive_failures
            },
            'alerts': {
                'active_count': len(self.active_alerts),
                'active_alerts': [
                    {
                        'type': alert.alert_type,
                        'severity': alert.severity,
                        'message': alert.message,
                        'timestamp': alert.timestamp.isoformat(),
                        'value': alert.value
                    }
                    for alert in self.active_alerts.values()
                ]
            },
            'thresholds': {
                name: {
                    'warning': threshold.warning_level,
                    'critical': threshold.critical_level,
                    'description': threshold.description
                }
                for name, threshold in self.thresholds.items()
            },
            'last_successful_check': self.last_successful_check.isoformat(),
            'last_error': self.current_status.last_error
        }

    def reset_alerts(self):
        """Reset all active alerts (for testing or manual intervention)"""
        self.logger.info("Resetting all active alerts")
        self.active_alerts.clear()
        self.consecutive_failures = 0