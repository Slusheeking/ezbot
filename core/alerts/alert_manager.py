"""
Alert Manager

Centralized alert management with multiple notification channels,
severity-based routing, and alert correlation capabilities.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class Alert:
    """Alert data structure"""
    feed_name: str
    severity: str
    message: str
    timestamp: datetime
    context: Dict[str, Any]
    alert_id: str = None
    resolved: bool = False
    resolved_at: Optional[datetime] = None


class AlertManager:
    """Centralized alert management system"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config.get('alerts', {})
        self.logger = logging.getLogger('alert_manager')

        # Alert storage and state
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.cooldown_periods: Dict[str, datetime] = {}

        # Configuration
        self.enabled = self.config.get('enabled', True)
        self.channels = self.config.get('channels', {})
        self.rules = self.config.get('rules', {})

        self.initialized = False

    async def initialize(self) -> bool:
        """Initialize alert manager"""
        try:
            self.logger.info("Initializing Alert Manager...")
            self.initialized = True
            self.logger.info("Alert Manager initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize Alert Manager: {e}")
            return False

    async def send_alert(self,
                        feed_name: str,
                        severity: str,
                        message: str,
                        context: Dict[str, Any] = None) -> bool:
        """Send an alert through appropriate channels"""
        if not self.enabled:
            return True

        if context is None:
            context = {}

        # Check cooldown
        cooldown_key = f"{feed_name}:{severity}:{message}"
        if self._is_in_cooldown(cooldown_key, severity):
            return True

        # Create alert
        alert = Alert(
            feed_name=feed_name,
            severity=severity,
            message=message,
            timestamp=datetime.now(),
            context=context,
            alert_id=f"{feed_name}_{int(datetime.now().timestamp())}"
        )

        # Store alert
        self.active_alerts[alert.alert_id] = alert
        self.alert_history.append(alert)

        # Set cooldown
        self._set_cooldown(cooldown_key, severity)

        # Route to channels
        channels = self._get_channels_for_severity(severity)
        success = True

        for channel in channels:
            try:
                await self._send_to_channel(channel, alert)
            except Exception as e:
                self.logger.error(f"Failed to send alert to {channel}: {e}")
                success = False

        return success

    def _is_in_cooldown(self, key: str, severity: str) -> bool:
        """Check if alert is in cooldown period"""
        if key not in self.cooldown_periods:
            return False

        cooldown_minutes = self.rules.get('cooldown_minutes', {}).get(severity, 0)
        if cooldown_minutes == 0:
            return False

        cooldown_until = self.cooldown_periods[key] + timedelta(minutes=cooldown_minutes)
        return datetime.now() < cooldown_until

    def _set_cooldown(self, key: str, severity: str):
        """Set cooldown period for alert"""
        self.cooldown_periods[key] = datetime.now()

    def _get_channels_for_severity(self, severity: str) -> List[str]:
        """Get notification channels for severity level"""
        return self.rules.get('severity_routing', {}).get(severity, ['console'])

    async def _send_to_channel(self, channel: str, alert: Alert):
        """Send alert to specific channel"""
        if channel == 'console':
            await self._send_to_console(alert)
        elif channel == 'webhook':
            await self._send_to_webhook(alert)
        elif channel == 'database':
            await self._send_to_database(alert)

    async def _send_to_console(self, alert: Alert):
        """Send alert to console/logs"""
        log_level = getattr(logging, alert.severity.upper(), logging.INFO)
        self.logger.log(log_level, f"[{alert.feed_name}] {alert.message}")

    async def _send_to_webhook(self, alert: Alert):
        """Send alert to webhook"""
        # Placeholder for webhook implementation
        pass

    async def _send_to_database(self, alert: Alert):
        """Send alert to database"""
        # Placeholder for database storage
        pass