import asyncio
import logging
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import aiohttp
from prometheus_client import Counter, Gauge, Histogram, Summary, generate_latest
import redis.asyncio as redis


class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class Alert:
    """Alert definition."""
    id: str
    name: str
    description: str
    severity: AlertSeverity
    condition: Callable
    threshold: float
    duration: int = 300  # seconds
    enabled: bool = True
    notification_channels: List[str] = field(default_factory=list)


@dataclass
class Metric:
    """Metric definition."""
    name: str
    value: float
    timestamp: datetime
    labels: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class MetricsCollector:
    """Enterprise metrics collector with Prometheus integration."""
    
    def __init__(self):
        self.logger = logging.getLogger("metrics_collector")
        
        # Prometheus metrics
        self.request_counter = Counter('analytics_fetcher_requests_total', 'Total requests', ['endpoint', 'status'])
        self.error_counter = Counter('analytics_fetcher_errors_total', 'Total errors', ['type'])
        self.fetch_duration = Histogram('analytics_fetcher_fetch_duration_seconds', 'Fetch duration', ['source'])
        self.active_connections = Gauge('analytics_fetcher_active_connections', 'Active connections')
        self.memory_usage = Gauge('analytics_fetcher_memory_bytes', 'Memory usage in bytes')
        self.cpu_usage = Gauge('analytics_fetcher_cpu_percent', 'CPU usage percentage')
        self.queue_size = Gauge('analytics_fetcher_queue_size', 'Queue size')
        
        # Custom metrics
        self._custom_metrics: Dict[str, Any] = {}
    
    def record_request(self, endpoint: str, status: str):
        """Record a request."""
        self.request_counter.labels(endpoint=endpoint, status=status).inc()
    
    def record_error(self, error_type: str):
        """Record an error."""
        self.error_counter.labels(type=error_type).inc()
    
    def record_fetch_duration(self, source: str, duration: float):
        """Record fetch duration."""
        self.fetch_duration.labels(source=source).observe(duration)
    
    def set_active_connections(self, count: int):
        """Set active connections count."""
        self.active_connections.set(count)
    
    def set_memory_usage(self, bytes_used: int):
        """Set memory usage."""
        self.memory_usage.set(bytes_used)
    
    def set_cpu_usage(self, percent: float):
        """Set CPU usage."""
        self.cpu_usage.set(percent)
    
    def set_queue_size(self, size: int):
        """Set queue size."""
        self.queue_size.set(size)
    
    def add_custom_metric(self, name: str, value: float, labels: Dict[str, str] = None):
        """Add a custom metric."""
        if name not in self._custom_metrics:
            self._custom_metrics[name] = Gauge(f'analytics_fetcher_{name}', f'Custom metric: {name}')
        
        if labels:
            self._custom_metrics[name].labels(**labels).set(value)
        else:
            self._custom_metrics[name].set(value)
    
    def get_prometheus_metrics(self) -> str:
        """Get Prometheus metrics in text format."""
        return generate_latest().decode('utf-8')


class AlertManager:
    """Enterprise alert manager with multiple notification channels."""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.logger = logging.getLogger("alert_manager")
        self.alerts: Dict[str, Alert] = {}
        self.alert_history: List[Dict[str, Any]] = []
        self._notification_handlers: Dict[str, Callable] = {}
        
        # Setup default alerts
        self._setup_default_alerts()
    
    def _setup_default_alerts(self):
        """Setup default system alerts."""
        # High error rate alert
        self.add_alert(Alert(
            id="high_error_rate",
            name="High Error Rate",
            description="Error rate exceeds threshold",
            severity=AlertSeverity.ERROR,
            condition=lambda metrics: metrics.get('error_rate', 0) > 0.1,
            threshold=0.1,
            notification_channels=["email", "slack"]
        ))
        
        # High memory usage alert
        self.add_alert(Alert(
            id="high_memory_usage",
            name="High Memory Usage",
            description="Memory usage exceeds 80%",
            severity=AlertSeverity.WARNING,
            condition=lambda metrics: metrics.get('memory_usage_percent', 0) > 80,
            threshold=80,
            notification_channels=["email"]
        ))
        
        # Service unavailable alert
        self.add_alert(Alert(
            id="service_unavailable",
            name="Service Unavailable",
            description="Service health check failed",
            severity=AlertSeverity.CRITICAL,
            condition=lambda metrics: not metrics.get('service_healthy', True),
            threshold=0,
            notification_channels=["email", "slack", "pagerduty"]
        ))
    
    def add_alert(self, alert: Alert):
        """Add an alert definition."""
        self.alerts[alert.id] = alert
        self.logger.info(f"Added alert: {alert.name}")
    
    def register_notification_handler(self, channel: str, handler: Callable):
        """Register a notification handler."""
        self._notification_handlers[channel] = handler
        self.logger.info(f"Registered notification handler for channel: {channel}")
    
    async def check_alerts(self, metrics: Dict[str, Any]):
        """Check all alerts against current metrics."""
        for alert_id, alert in self.alerts.items():
            if not alert.enabled:
                continue
            
            try:
                if alert.condition(metrics):
                    await self._trigger_alert(alert, metrics)
                else:
                    await self._clear_alert(alert_id)
            except Exception as e:
                self.logger.error(f"Error checking alert {alert_id}: {e}")
    
    async def _trigger_alert(self, alert: Alert, metrics: Dict[str, Any]):
        """Trigger an alert."""
        alert_key = f"alert:{alert.id}"
        
        # Check if alert is already active
        is_active = await self.redis.get(alert_key)
        if is_active:
            return  # Alert already active
        
        # Store alert state
        alert_data = {
            'alert_id': alert.id,
            'name': alert.name,
            'description': alert.description,
            'severity': alert.severity.value,
            'triggered_at': datetime.utcnow().isoformat(),
            'metrics': metrics
        }
        
        await self.redis.setex(alert_key, alert.duration, json.dumps(alert_data))
        
        # Send notifications
        await self._send_notifications(alert, alert_data)
        
        # Log alert
        self.logger.warning(f"Alert triggered: {alert.name} - {alert.description}")
        
        # Store in history
        self.alert_history.append(alert_data)
        if len(self.alert_history) > 1000:  # Keep last 1000 alerts
            self.alert_history = self.alert_history[-1000:]
    
    async def _clear_alert(self, alert_id: str):
        """Clear an alert."""
        alert_key = f"alert:{alert_id}"
        if await self.redis.exists(alert_key):
            await self.redis.delete(alert_key)
            self.logger.info(f"Alert cleared: {alert_id}")
    
    async def _send_notifications(self, alert: Alert, alert_data: Dict[str, Any]):
        """Send notifications for an alert."""
        for channel in alert.notification_channels:
            if channel in self._notification_handlers:
                try:
                    await self._notification_handlers[channel](alert, alert_data)
                except Exception as e:
                    self.logger.error(f"Failed to send notification to {channel}: {e}")
    
    async def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get currently active alerts."""
        active_alerts = []
        async for key in self.redis.scan_iter(match="alert:*"):
            alert_data = await self.redis.get(key)
            if alert_data:
                active_alerts.append(json.loads(alert_data))
        
        return active_alerts
    
    def get_alert_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get alert history."""
        return self.alert_history[-limit:]


class DashboardManager:
    """Dashboard manager for metrics visualization."""
    
    def __init__(self, metrics_collector: MetricsCollector, alert_manager: AlertManager):
        self.metrics_collector = metrics_collector
        self.alert_manager = alert_manager
        self.logger = logging.getLogger("dashboard_manager")
        self.dashboards: Dict[str, Dict[str, Any]] = {}
        
        # Setup default dashboards
        self._setup_default_dashboards()
    
    def _setup_default_dashboards(self):
        """Setup default dashboards."""
        # System Overview Dashboard
        self.dashboards["system_overview"] = {
            "name": "System Overview",
            "description": "High-level system metrics",
            "panels": [
                {
                    "title": "Request Rate",
                    "type": "line",
                    "metric": "analytics_fetcher_requests_total",
                    "time_range": "1h"
                },
                {
                    "title": "Error Rate",
                    "type": "line",
                    "metric": "analytics_fetcher_errors_total",
                    "time_range": "1h"
                },
                {
                    "title": "Memory Usage",
                    "type": "gauge",
                    "metric": "analytics_fetcher_memory_bytes",
                    "time_range": "5m"
                },
                {
                    "title": "CPU Usage",
                    "type": "gauge",
                    "metric": "analytics_fetcher_cpu_percent",
                    "time_range": "5m"
                }
            ]
        }
        
        # Performance Dashboard
        self.dashboards["performance"] = {
            "name": "Performance Metrics",
            "description": "Detailed performance metrics",
            "panels": [
                {
                    "title": "Fetch Duration",
                    "type": "histogram",
                    "metric": "analytics_fetcher_fetch_duration_seconds",
                    "time_range": "1h"
                },
                {
                    "title": "Active Connections",
                    "type": "gauge",
                    "metric": "analytics_fetcher_active_connections",
                    "time_range": "5m"
                },
                {
                    "title": "Queue Size",
                    "type": "gauge",
                    "metric": "analytics_fetcher_queue_size",
                    "time_range": "5m"
                }
            ]
        }
    
    def get_dashboard_data(self, dashboard_id: str) -> Dict[str, Any]:
        """Get dashboard data."""
        if dashboard_id not in self.dashboards:
            return {"error": "Dashboard not found"}
        
        dashboard = self.dashboards[dashboard_id]
        
        # Get active alerts
        active_alerts = asyncio.run(self.alert_manager.get_active_alerts())
        
        return {
            "dashboard": dashboard,
            "active_alerts": active_alerts,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def add_dashboard(self, dashboard_id: str, dashboard_config: Dict[str, Any]):
        """Add a custom dashboard."""
        self.dashboards[dashboard_id] = dashboard_config
        self.logger.info(f"Added dashboard: {dashboard_config.get('name', dashboard_id)}")
    
    def get_available_dashboards(self) -> List[Dict[str, str]]:
        """Get list of available dashboards."""
        return [
            {"id": k, "name": v.get("name", k), "description": v.get("description", "")}
            for k, v in self.dashboards.items()
        ]


class NotificationManager:
    """Notification manager for multiple channels."""
    
    def __init__(self):
        self.logger = logging.getLogger("notification_manager")
        self._handlers: Dict[str, Callable] = {}
    
    def register_handler(self, channel: str, handler: Callable):
        """Register a notification handler."""
        self._handlers[channel] = handler
        self.logger.info(f"Registered notification handler for {channel}")
    
    async def send_notification(self, channel: str, message: str, **kwargs):
        """Send a notification to a specific channel."""
        if channel in self._handlers:
            try:
                await self._handlers[channel](message, **kwargs)
            except Exception as e:
                self.logger.error(f"Failed to send notification to {channel}: {e}")
        else:
            self.logger.warning(f"No handler registered for channel: {channel}")
    
    async def send_email_alert(self, alert: Alert, alert_data: Dict[str, Any]):
        """Send email alert."""
        subject = f"[{alert.severity.value.upper()}] {alert.name}"
        body = f"""
Alert: {alert.name}
Description: {alert.description}
Severity: {alert.severity.value}
Triggered at: {alert_data['triggered_at']}
Metrics: {json.dumps(alert_data['metrics'], indent=2)}
        """
        
        await self.send_notification("email", body, subject=subject)
    
    async def send_slack_alert(self, alert: Alert, alert_data: Dict[str, Any]):
        """Send Slack alert."""
        color_map = {
            AlertSeverity.INFO: "#36a64f",
            AlertSeverity.WARNING: "#ffa500",
            AlertSeverity.ERROR: "#ff0000",
            AlertSeverity.CRITICAL: "#8b0000"
        }
        
        message = {
            "attachments": [{
                "color": color_map.get(alert.severity, "#000000"),
                "title": alert.name,
                "text": alert.description,
                "fields": [
                    {"title": "Severity", "value": alert.severity.value, "short": True},
                    {"title": "Triggered At", "value": alert_data['triggered_at'], "short": True}
                ]
            }]
        }
        
        await self.send_notification("slack", json.dumps(message))
    
    async def send_pagerduty_alert(self, alert: Alert, alert_data: Dict[str, Any]):
        """Send PagerDuty alert."""
        payload = {
            "routing_key": "your-pagerduty-key",
            "event_action": "trigger",
            "dedup_key": alert.id,
            "payload": {
                "summary": alert.name,
                "severity": alert.severity.value,
                "source": "analytics-fetcher",
                "custom_details": alert_data
            }
        }
        
        await self.send_notification("pagerduty", json.dumps(payload))


class PerformanceMonitor:
    """Performance monitoring and profiling."""
    
    def __init__(self):
        self.logger = logging.getLogger("performance_monitor")
        self.metrics_collector = MetricsCollector()
        self._start_time = time.time()
        self._operation_times: Dict[str, List[float]] = {}
    
    def start_operation(self, operation_name: str):
        """Start timing an operation."""
        return time.time()
    
    def end_operation(self, operation_name: str, start_time: float):
        """End timing an operation and record metrics."""
        duration = time.time() - start_time
        
        if operation_name not in self._operation_times:
            self._operation_times[operation_name] = []
        
        self._operation_times[operation_name].append(duration)
        
        # Keep only last 1000 measurements
        if len(self._operation_times[operation_name]) > 1000:
            self._operation_times[operation_name] = self._operation_times[operation_name][-1000:]
        
        # Record in Prometheus metrics
        self.metrics_collector.record_fetch_duration(operation_name, duration)
        
        return duration
    
    def get_operation_stats(self, operation_name: str) -> Dict[str, float]:
        """Get statistics for an operation."""
        if operation_name not in self._operation_times:
            return {}
        
        times = self._operation_times[operation_name]
        if not times:
            return {}
        
        return {
            "count": len(times),
            "min": min(times),
            "max": max(times),
            "avg": sum(times) / len(times),
            "p95": sorted(times)[int(len(times) * 0.95)],
            "p99": sorted(times)[int(len(times) * 0.99)]
        }
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get current system metrics."""
        import psutil
        
        process = psutil.Process()
        memory_info = process.memory_info()
        
        return {
            "memory_usage_bytes": memory_info.rss,
            "memory_usage_percent": process.memory_percent(),
            "cpu_percent": process.cpu_percent(),
            "uptime_seconds": time.time() - self._start_time,
            "thread_count": process.num_threads(),
            "open_files": len(process.open_files()),
            "connections": len(process.connections())
        } 