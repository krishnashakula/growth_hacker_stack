import os
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from pydantic import BaseSettings, Field, validator
from pydantic_settings import SettingsConfigDict


@dataclass
class SecuritySettings:
    """Enterprise security configuration."""
    encryption_key: Optional[str] = None
    jwt_secret: Optional[str] = None
    bcrypt_rounds: int = 12
    session_timeout_minutes: int = 60
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 15
    audit_log_enabled: bool = True
    ssl_verify: bool = True
    rate_limit_requests: int = 100
    rate_limit_window: int = 3600
    enable_encryption: bool = True
    enable_audit_logging: bool = True
    enable_rate_limiting: bool = True


@dataclass
class ClusterSettings:
    """High-availability cluster configuration."""
    cluster_id: str = "analytics-cluster"
    node_id: str = "node-1"
    heartbeat_interval: int = 30
    failure_timeout: int = 90
    recovery_timeout: int = 300
    max_nodes: int = 10
    load_balancing_strategy: str = "round_robin"
    auto_failover: bool = True
    quorum_size: int = 2
    enable_clustering: bool = True
    redis_host: str = "redis"
    redis_port: int = 6379
    redis_password: Optional[str] = None
    redis_db: int = 0


@dataclass
class MonitoringSettings:
    """Enterprise monitoring configuration."""
    enable_prometheus: bool = True
    prometheus_port: int = 9090
    enable_alerting: bool = True
    alert_check_interval: int = 60
    enable_dashboards: bool = True
    dashboard_port: int = 3000
    enable_performance_monitoring: bool = True
    metrics_retention_days: int = 30
    enable_notifications: bool = True
    notification_channels: List[str] = None
    
    def __post_init__(self):
        if self.notification_channels is None:
            self.notification_channels = ["email", "slack"]


@dataclass
class ScalabilitySettings:
    """Scalability and performance configuration."""
    max_concurrent_requests: int = 100
    connection_pool_size: int = 20
    max_retries: int = 3
    retry_delay_base: float = 1.0
    retry_delay_max: float = 60.0
    circuit_breaker_enabled: bool = True
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: int = 60
    enable_auto_scaling: bool = True
    min_instances: int = 2
    max_instances: int = 10
    scale_up_threshold: float = 0.8
    scale_down_threshold: float = 0.3


class EnterpriseAnalyticsSettings(BaseSettings):
    """Enterprise-grade configuration for the analytics fetcher service."""
    
    # Basic Service Configuration
    service_name: str = Field(default="analytics-fetcher", alias="SERVICE_NAME")
    environment: str = Field(default="production", alias="ENVIRONMENT")
    version: str = Field(default="1.0.0", alias="SERVICE_VERSION")
    
    # Database Configuration
    db_host: str = Field(default="db", alias="DB_HOST")
    db_port: int = Field(default=5432, alias="DB_PORT")
    db_name: str = Field(default="n8n_db", alias="DB_NAME")
    db_user: str = Field(default="n8n_user", alias="DB_USER")
    db_password: Optional[str] = Field(default=None, alias="DB_PASS")
    db_pool_size: int = Field(default=10, alias="DB_POOL_SIZE")
    db_max_overflow: int = Field(default=20, alias="DB_MAX_OVERFLOW")
    
    # LinkedIn API Configuration
    linkedin_api_key: Optional[str] = Field(default=None, alias="LINKEDIN_API_KEY")
    linkedin_api_secret: Optional[str] = Field(default=None, alias="LINKEDIN_API_SECRET")
    linkedin_person_urn: Optional[str] = Field(default=None, alias="LINKEDIN_PERSON_URN")
    linkedin_rate_limit: int = Field(default=100, alias="LINKEDIN_RATE_LIMIT")
    
    # Service Configuration
    fetch_interval_seconds: int = Field(default=3600, alias="FETCH_INTERVAL_SECONDS", ge=60)
    run_mode: str = Field(default="loop", alias="ANALYTICS_FETCHER_RUN_MODE")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    
    # HTTP Client Configuration
    http_timeout: int = Field(default=30, alias="HTTP_TIMEOUT")
    max_retries: int = Field(default=3, alias="MAX_RETRIES")
    retry_delay: int = Field(default=5, alias="RETRY_DELAY")
    
    # Health Server Configuration
    enable_health_server: bool = Field(default=True, alias="ENABLE_HEALTH_SERVER")
    health_port: int = Field(default=8000, alias="HEALTH_PORT")
    
    # Security Configuration
    security_encryption_key: Optional[str] = Field(default=None, alias="SECURITY_ENCRYPTION_KEY")
    security_jwt_secret: Optional[str] = Field(default=None, alias="SECURITY_JWT_SECRET")
    security_bcrypt_rounds: int = Field(default=12, alias="SECURITY_BCRYPT_ROUNDS")
    security_session_timeout: int = Field(default=60, alias="SECURITY_SESSION_TIMEOUT")
    security_max_login_attempts: int = Field(default=5, alias="SECURITY_MAX_LOGIN_ATTEMPTS")
    security_lockout_duration: int = Field(default=15, alias="SECURITY_LOCKOUT_DURATION")
    security_audit_log_enabled: bool = Field(default=True, alias="SECURITY_AUDIT_LOG_ENABLED")
    security_rate_limit_requests: int = Field(default=100, alias="SECURITY_RATE_LIMIT_REQUESTS")
    security_rate_limit_window: int = Field(default=3600, alias="SECURITY_RATE_LIMIT_WINDOW")
    
    # Cluster Configuration
    cluster_enabled: bool = Field(default=True, alias="CLUSTER_ENABLED")
    cluster_id: str = Field(default="analytics-cluster", alias="CLUSTER_ID")
    cluster_node_id: str = Field(default="node-1", alias="CLUSTER_NODE_ID")
    cluster_heartbeat_interval: int = Field(default=30, alias="CLUSTER_HEARTBEAT_INTERVAL")
    cluster_failure_timeout: int = Field(default=90, alias="CLUSTER_FAILURE_TIMEOUT")
    cluster_recovery_timeout: int = Field(default=300, alias="CLUSTER_RECOVERY_TIMEOUT")
    cluster_max_nodes: int = Field(default=10, alias="CLUSTER_MAX_NODES")
    cluster_load_balancing_strategy: str = Field(default="round_robin", alias="CLUSTER_LOAD_BALANCING_STRATEGY")
    cluster_auto_failover: bool = Field(default=True, alias="CLUSTER_AUTO_FAILOVER")
    cluster_quorum_size: int = Field(default=2, alias="CLUSTER_QUORUM_SIZE")
    
    # Redis Configuration
    redis_host: str = Field(default="redis", alias="REDIS_HOST")
    redis_port: int = Field(default=6379, alias="REDIS_PORT")
    redis_password: Optional[str] = Field(default=None, alias="REDIS_PASSWORD")
    redis_db: int = Field(default=0, alias="REDIS_DB")
    
    # Monitoring Configuration
    monitoring_enabled: bool = Field(default=True, alias="MONITORING_ENABLED")
    monitoring_prometheus_enabled: bool = Field(default=True, alias="MONITORING_PROMETHEUS_ENABLED")
    monitoring_prometheus_port: int = Field(default=9090, alias="MONITORING_PROMETHEUS_PORT")
    monitoring_alerting_enabled: bool = Field(default=True, alias="MONITORING_ALERTING_ENABLED")
    monitoring_alert_check_interval: int = Field(default=60, alias="MONITORING_ALERT_CHECK_INTERVAL")
    monitoring_dashboards_enabled: bool = Field(default=True, alias="MONITORING_DASHBOARDS_ENABLED")
    monitoring_dashboard_port: int = Field(default=3000, alias="MONITORING_DASHBOARD_PORT")
    monitoring_performance_enabled: bool = Field(default=True, alias="MONITORING_PERFORMANCE_ENABLED")
    monitoring_metrics_retention_days: int = Field(default=30, alias="MONITORING_METRICS_RETENTION_DAYS")
    monitoring_notifications_enabled: bool = Field(default=True, alias="MONITORING_NOTIFICATIONS_ENABLED")
    monitoring_notification_channels: str = Field(default="email,slack", alias="MONITORING_NOTIFICATION_CHANNELS")
    
    # Scalability Configuration
    scalability_max_concurrent_requests: int = Field(default=100, alias="SCALABILITY_MAX_CONCURRENT_REQUESTS")
    scalability_connection_pool_size: int = Field(default=20, alias="SCALABILITY_CONNECTION_POOL_SIZE")
    scalability_circuit_breaker_enabled: bool = Field(default=True, alias="SCALABILITY_CIRCUIT_BREAKER_ENABLED")
    scalability_circuit_breaker_threshold: int = Field(default=5, alias="SCALABILITY_CIRCUIT_BREAKER_THRESHOLD")
    scalability_circuit_breaker_timeout: int = Field(default=60, alias="SCALABILITY_CIRCUIT_BREAKER_TIMEOUT")
    scalability_auto_scaling_enabled: bool = Field(default=True, alias="SCALABILITY_AUTO_SCALING_ENABLED")
    scalability_min_instances: int = Field(default=2, alias="SCALABILITY_MIN_INSTANCES")
    scalability_max_instances: int = Field(default=10, alias="SCALABILITY_MAX_INSTANCES")
    scalability_scale_up_threshold: float = Field(default=0.8, alias="SCALABILITY_SCALE_UP_THRESHOLD")
    scalability_scale_down_threshold: float = Field(default=0.3, alias="SCALABILITY_SCALE_DOWN_THRESHOLD")
    
    # Resource Limits
    resource_memory_limit_mb: int = Field(default=512, alias="RESOURCE_MEMORY_LIMIT_MB")
    resource_cpu_limit_cores: float = Field(default=0.5, alias="RESOURCE_CPU_LIMIT_CORES")
    resource_memory_reservation_mb: int = Field(default=256, alias="RESOURCE_MEMORY_RESERVATION_MB")
    resource_cpu_reservation_cores: float = Field(default=0.25, alias="RESOURCE_CPU_RESERVATION_CORES")
    
    # Logging Configuration
    logging_level: str = Field(default="INFO", alias="LOGGING_LEVEL")
    logging_format: str = Field(default="json", alias="LOGGING_FORMAT")
    logging_rotation_max_size_mb: int = Field(default=100, alias="LOGGING_ROTATION_MAX_SIZE_MB")
    logging_rotation_backup_count: int = Field(default=5, alias="LOGGING_ROTATION_BACKUP_COUNT")
    logging_audit_enabled: bool = Field(default=True, alias="LOGGING_AUDIT_ENABLED")
    
    # Backup Configuration
    backup_enabled: bool = Field(default=True, alias="BACKUP_ENABLED")
    backup_interval_hours: int = Field(default=24, alias="BACKUP_INTERVAL_HOURS")
    backup_retention_days: int = Field(default=30, alias="BACKUP_RETENTION_DAYS")
    backup_encryption_enabled: bool = Field(default=True, alias="BACKUP_ENCRYPTION_ENABLED")
    
    @validator('log_level', 'logging_level')
    def validate_log_level(cls, v):
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'log_level must be one of {valid_levels}')
        return v.upper()
    
    @validator('fetch_interval_seconds')
    def validate_fetch_interval(cls, v):
        if v < 60:
            raise ValueError('fetch_interval_seconds must be at least 60 seconds')
        return v
    
    @validator('cluster_load_balancing_strategy')
    def validate_load_balancing_strategy(cls, v):
        valid_strategies = ['round_robin', 'least_loaded', 'random']
        if v not in valid_strategies:
            raise ValueError(f'load_balancing_strategy must be one of {valid_strategies}')
        return v
    
    @validator('monitoring_notification_channels')
    def validate_notification_channels(cls, v):
        valid_channels = ['email', 'slack', 'pagerduty', 'webhook']
        channels = [c.strip() for c in v.split(',')]
        for channel in channels:
            if channel not in valid_channels:
                raise ValueError(f'Invalid notification channel: {channel}')
        return channels
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding='utf-8',
        extra='ignore',
        case_sensitive=False
    )
    
    def get_security_settings(self) -> SecuritySettings:
        """Get security settings."""
        return SecuritySettings(
            encryption_key=self.security_encryption_key,
            jwt_secret=self.security_jwt_secret,
            bcrypt_rounds=self.security_bcrypt_rounds,
            session_timeout_minutes=self.security_session_timeout,
            max_login_attempts=self.security_max_login_attempts,
            lockout_duration_minutes=self.security_lockout_duration,
            audit_log_enabled=self.security_audit_log_enabled,
            rate_limit_requests=self.security_rate_limit_requests,
            rate_limit_window=self.security_rate_limit_window
        )
    
    def get_cluster_settings(self) -> ClusterSettings:
        """Get cluster settings."""
        return ClusterSettings(
            cluster_id=self.cluster_id,
            node_id=self.cluster_node_id,
            heartbeat_interval=self.cluster_heartbeat_interval,
            failure_timeout=self.cluster_failure_timeout,
            recovery_timeout=self.cluster_recovery_timeout,
            max_nodes=self.cluster_max_nodes,
            load_balancing_strategy=self.cluster_load_balancing_strategy,
            auto_failover=self.cluster_auto_failover,
            quorum_size=self.cluster_quorum_size,
            enable_clustering=self.cluster_enabled,
            redis_host=self.redis_host,
            redis_port=self.redis_port,
            redis_password=self.redis_password,
            redis_db=self.redis_db
        )
    
    def get_monitoring_settings(self) -> MonitoringSettings:
        """Get monitoring settings."""
        return MonitoringSettings(
            enable_prometheus=self.monitoring_prometheus_enabled,
            prometheus_port=self.monitoring_prometheus_port,
            enable_alerting=self.monitoring_alerting_enabled,
            alert_check_interval=self.monitoring_alert_check_interval,
            enable_dashboards=self.monitoring_dashboards_enabled,
            dashboard_port=self.monitoring_dashboard_port,
            enable_performance_monitoring=self.monitoring_performance_enabled,
            metrics_retention_days=self.monitoring_metrics_retention_days,
            enable_notifications=self.monitoring_notifications_enabled,
            notification_channels=self.monitoring_notification_channels
        )
    
    def get_scalability_settings(self) -> ScalabilitySettings:
        """Get scalability settings."""
        return ScalabilitySettings(
            max_concurrent_requests=self.scalability_max_concurrent_requests,
            connection_pool_size=self.scalability_connection_pool_size,
            max_retries=self.max_retries,
            retry_delay_base=self.retry_delay,
            retry_delay_max=60.0,
            circuit_breaker_enabled=self.scalability_circuit_breaker_enabled,
            circuit_breaker_threshold=self.scalability_circuit_breaker_threshold,
            circuit_breaker_timeout=self.scalability_circuit_breaker_timeout,
            enable_auto_scaling=self.scalability_auto_scaling_enabled,
            min_instances=self.scalability_min_instances,
            max_instances=self.scalability_max_instances,
            scale_up_threshold=self.scalability_scale_up_threshold,
            scale_down_threshold=self.scalability_scale_down_threshold
        )
    
    def validate_enterprise_config(self) -> List[str]:
        """Validate enterprise configuration and return any issues."""
        issues = []
        
        # Check required security settings
        if not self.security_encryption_key:
            issues.append("SECURITY_ENCRYPTION_KEY is required for enterprise security")
        
        if not self.security_jwt_secret:
            issues.append("SECURITY_JWT_SECRET is required for authentication")
        
        # Check required API credentials
        if not self.linkedin_api_key:
            issues.append("LINKEDIN_API_KEY is required")
        
        if not self.linkedin_api_secret:
            issues.append("LINKEDIN_API_SECRET is required")
        
        # Check database configuration
        if not self.db_password:
            issues.append("DB_PASS is required for database connection")
        
        # Check cluster configuration
        if self.cluster_enabled and not self.redis_password:
            issues.append("REDIS_PASSWORD is required for cluster security")
        
        # Check resource limits
        if self.resource_memory_limit_mb < 256:
            issues.append("RESOURCE_MEMORY_LIMIT_MB should be at least 256MB")
        
        if self.resource_cpu_limit_cores < 0.25:
            issues.append("RESOURCE_CPU_LIMIT_CORES should be at least 0.25")
        
        return issues 