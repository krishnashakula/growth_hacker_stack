# 📁 Project Structure

This document outlines the complete structure of the Growth Hacker LinkedIn Automation Stack.

## 🏗️ Root Structure

```
growth_hacker_stack/
├── 📄 README.md                    # Main project documentation
├── 📄 PROJECT_STRUCTURE.md         # This file - project structure guide
├── 📄 env.example                  # Environment variables template
├── 📄 .gitignore                   # Git ignore patterns
├── 📄 docker-compose.yml           # Main Docker Compose configuration
├── 📄 .yamllint.yml               # YAML linting configuration
├── 📄 alembic.ini                 # Database migration configuration
├── 📁 .venv/                      # Python virtual environment
├── 📁 .git/                       # Git repository data
├── 📁 custom/                     # Custom n8n nodes and extensions
├── 📁 migrations/                 # Database migration files
├── 📁 workflows/                  # n8n workflow definitions
├── 📁 sql/                        # SQL scripts and database setup
└── 📁 service/                    # Microservices directory
```

## 🔧 Service Directory Structure

### 📁 `service/` - Microservices

```
service/
├── 📁 analytics_fetcher/          # LinkedIn Analytics Service
│   ├── 📄 fetch.py                # Main analytics fetcher logic
│   ├── 📄 health_server.py        # Health check server
│   ├── 📄 security.py             # Enterprise security module
│   ├── 📄 ha_scalability.py       # High availability & clustering
│   ├── 📄 monitoring.py           # Monitoring & alerting system
│   ├── 📄 enterprise_config.py    # Enterprise configuration
│   ├── 📄 requirements.txt        # Python dependencies
│   ├── 📄 Dockerfile              # Container configuration
│   ├── 📄 docker-compose.prod.yml # Production Docker Compose
│   ├── 📄 deploy.sh               # Deployment script
│   ├── 📄 prometheus.yml          # Prometheus configuration
│   ├── 📄 env.example             # Environment variables
│   ├── 📄 README.md               # Service documentation
│   ├── 📄 PRODUCTION.md           # Production deployment guide
│   ├── 📄 ENTERPRISE_DEPLOYMENT.md # Enterprise deployment guide
│   ├── 📁 tests/                  # Test suite
│   │   └── 📄 test_fetch.py       # Analytics fetcher tests
│   └── 📁 logs/                   # Log files (created at runtime)
│
└── 📁 trending_service/           # Trending Keywords Service
    ├── 📄 main.py                 # FastAPI application
    ├── 📄 requirements.txt        # Python dependencies
    ├── 📄 Dockerfile              # Container configuration
    └── 📁 __pycache__/            # Python cache (generated)
```

## 🐳 Docker Configuration

### Main Docker Compose (`docker-compose.yml`)

**Services:**
- **traefik**: Reverse proxy with SSL termination
- **db**: PostgreSQL database
- **n8n**: Workflow automation platform
- **trending_service**: FastAPI keyword service
- **analytics_fetcher**: LinkedIn analytics service
- **metabase**: Business intelligence dashboard

**Networks:**
- `backend`: Internal service communication
- `public`: External access

**Volumes:**
- `db_data`: PostgreSQL data persistence
- `n8n_data`: n8n workflow persistence
- `traefik_letsencrypt`: SSL certificates

## 🔐 Security Configuration

### Environment Variables Structure

```
# Database Configuration
POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD

# LinkedIn API Configuration
LINKEDIN_API_KEY, LINKEDIN_API_SECRET, LINKEDIN_PERSON_URN

# Analytics Fetcher Configuration
FETCH_INTERVAL_SECONDS, ANALYTICS_FETCHER_RUN_MODE, LOG_LEVEL
HTTP_TIMEOUT, MAX_RETRIES, RETRY_DELAY
ENABLE_HEALTH_SERVER, HEALTH_PORT

# Enterprise Security Configuration
SECURITY_ENCRYPTION_KEY, SECURITY_JWT_SECRET, SECURITY_BCRYPT_ROUNDS
SECURITY_SESSION_TIMEOUT, SECURITY_MAX_LOGIN_ATTEMPTS
SECURITY_LOCKOUT_DURATION, SECURITY_AUDIT_LOG_ENABLED
SECURITY_RATE_LIMIT_REQUESTS, SECURITY_RATE_LIMIT_WINDOW

# Cluster Configuration
CLUSTER_ENABLED, CLUSTER_ID, CLUSTER_NODE_ID
CLUSTER_HEARTBEAT_INTERVAL, CLUSTER_FAILURE_TIMEOUT
CLUSTER_RECOVERY_TIMEOUT, CLUSTER_MAX_NODES
CLUSTER_LOAD_BALANCING_STRATEGY, CLUSTER_AUTO_FAILOVER
CLUSTER_QUORUM_SIZE

# Redis Configuration
REDIS_HOST, REDIS_PORT, REDIS_PASSWORD, REDIS_DB

# Monitoring Configuration
MONITORING_ENABLED, MONITORING_PROMETHEUS_ENABLED
MONITORING_ALERTING_ENABLED, MONITORING_DASHBOARDS_ENABLED
MONITORING_PERFORMANCE_ENABLED, MONITORING_NOTIFICATIONS_ENABLED

# Scalability Configuration
SCALABILITY_MAX_CONCURRENT_REQUESTS, SCALABILITY_CONNECTION_POOL_SIZE
SCALABILITY_CIRCUIT_BREAKER_ENABLED, SCALABILITY_AUTO_SCALING_ENABLED

# Resource Limits
RESOURCE_MEMORY_LIMIT_MB, RESOURCE_CPU_LIMIT_CORES
RESOURCE_MEMORY_RESERVATION_MB, RESOURCE_CPU_RESERVATION_CORES

# Logging Configuration
LOGGING_LEVEL, LOGGING_FORMAT, LOGGING_ROTATION_MAX_SIZE_MB
LOGGING_ROTATION_BACKUP_COUNT, LOGGING_AUDIT_ENABLED

# Backup Configuration
BACKUP_ENABLED, BACKUP_INTERVAL_HOURS, BACKUP_RETENTION_DAYS
BACKUP_ENCRYPTION_ENABLED

# Metabase Configuration
MB_ENCRYPTION_SECRET_KEY, MB_ADMIN_EMAIL, MB_ADMIN_PASSWORD

# Service Configuration
SERVICE_NAME, ENVIRONMENT, SERVICE_VERSION

# Development Configuration
DEBUG, DEV_MODE
```

## 📊 Monitoring & Observability

### Analytics Fetcher Monitoring

**Health Endpoints:**
- `/health` - Basic health check
- `/health/detailed` - Detailed service status
- `/metrics` - Prometheus metrics

**Metrics Collected:**
- Request rate and error rate
- Fetch duration and performance
- Memory and CPU usage
- Active connections and queue size
- Custom business metrics

**Alerting Channels:**
- Email notifications
- Slack integration
- PagerDuty escalation

## 🔄 Deployment Options

### 1. Development Deployment
```bash
# Quick start for development
cp env.example .env
docker-compose up -d
```

### 2. Production Deployment
```bash
# Production deployment with analytics fetcher
cp env.example .env
# Edit .env with production values
docker-compose up -d
```

### 3. Enterprise Deployment
```bash
# Enterprise deployment with full monitoring
cd service/analytics_fetcher
./deploy.sh
```

### 4. Kubernetes Deployment
```bash
# Kubernetes deployment
kubectl apply -f k8s/
```

## 🧪 Testing Structure

### Analytics Fetcher Tests
```
service/analytics_fetcher/tests/
└── test_fetch.py                   # Comprehensive test suite
    ├── TestAnalyticsSettings       # Configuration tests
    ├── TestLinkedInPostData        # Data structure tests
    ├── TestLoggerManager           # Logging tests
    ├── TestDatabaseManager         # Database tests
    ├── TestLinkedInAPIClient      # API client tests
    └── TestAnalyticsFetcherService # Main service tests
```

## 📝 Documentation Structure

### Analytics Fetcher Documentation
- `README.md` - Service overview and usage
- `PRODUCTION.md` - Production deployment guide
- `ENTERPRISE_DEPLOYMENT.md` - Enterprise deployment guide

### Main Project Documentation
- `README.md` - Project overview and quickstart
- `PROJECT_STRUCTURE.md` - This file

## 🔧 Configuration Files

### Docker Configuration
- `docker-compose.yml` - Main orchestration
- `service/analytics_fetcher/Dockerfile` - Analytics service container
- `service/trending_service/Dockerfile` - Trending service container

### Database Configuration
- `alembic.ini` - Migration configuration
- `sql/` - Database initialization scripts

### Monitoring Configuration
- `service/analytics_fetcher/prometheus.yml` - Prometheus config
- `service/analytics_fetcher/docker-compose.prod.yml` - Production monitoring

## 🚀 Service Communication

### Internal Communication
```
n8n ←→ trending_service (keywords)
n8n ←→ analytics_fetcher (analytics)
metabase ←→ db (reports)
```

### External APIs
```
trending_service → Twitter API
analytics_fetcher → LinkedIn API
```

### Health Checks
```
traefik → n8n (/healthz)
traefik → trending_service (/health)
traefik → analytics_fetcher (/health)
traefik → metabase (/api/health)
```

## 🔒 Security Architecture

### Network Security
- **Traefik**: SSL termination and routing
- **Network Policies**: Service-to-service communication
- **Firewall Rules**: External access control

### Application Security
- **Encryption**: AES-256 for sensitive data
- **Authentication**: JWT with bcrypt hashing
- **Rate Limiting**: Request throttling
- **Input Validation**: XSS and injection prevention
- **Audit Logging**: Security event tracking

### Container Security
- **Non-root Users**: Security best practices
- **Resource Limits**: CPU and memory constraints
- **Image Scanning**: Vulnerability detection
- **Secrets Management**: Secure credential storage

## 📈 Scalability Features

### Horizontal Scaling
- **Auto-scaling**: Based on CPU/memory usage
- **Load Balancing**: Multiple strategies available
- **Circuit Breakers**: Fault tolerance
- **Connection Pooling**: Resource optimization

### High Availability
- **Clustering**: Multi-node deployment
- **Failover**: Automatic service recovery
- **Health Checks**: Continuous monitoring
- **Graceful Shutdown**: Proper resource cleanup

## 🔍 Monitoring & Alerting

### Metrics Collection
- **Prometheus**: Time-series metrics
- **Grafana**: Visualization dashboards
- **Custom Metrics**: Business-specific KPIs

### Alerting System
- **Multi-channel**: Email, Slack, PagerDuty
- **Severity Levels**: Info, Warning, Error, Critical
- **Escalation**: Automatic alert escalation
- **Retention**: Configurable alert history

## 📋 Deployment Checklist

### Pre-deployment
- [ ] Environment variables configured
- [ ] Database initialized
- [ ] SSL certificates ready
- [ ] Monitoring stack deployed
- [ ] Backup strategy implemented

### Post-deployment
- [ ] Health checks passing
- [ ] Metrics collection active
- [ ] Alerting configured
- [ ] Performance monitoring
- [ ] Security audit completed

## 🆘 Troubleshooting

### Common Issues
1. **Database Connection**: Check PostgreSQL health
2. **API Authentication**: Verify LinkedIn credentials
3. **Service Communication**: Check network policies
4. **Resource Limits**: Monitor CPU/memory usage
5. **SSL Issues**: Verify certificate configuration

### Debug Commands
```bash
# Check service health
docker-compose ps
docker-compose logs [service_name]

# Check analytics fetcher
curl http://localhost:8001/health
curl http://localhost:8001/metrics

# Check trending service
curl http://localhost:8000/health

# Check database
docker-compose exec db psql -U n8n_user -d n8n_db
```

## 📚 Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [n8n Documentation](https://docs.n8n.io/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/) 