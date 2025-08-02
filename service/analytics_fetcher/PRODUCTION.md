# Production Deployment Guide

This guide covers deploying the Analytics Fetcher Service to production with monitoring, health checks, and proper resource management.

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose installed
- LinkedIn API credentials
- PostgreSQL database (or use the included one)

### 1. Environment Setup

```bash
# Copy environment template
cp env.example .env

# Edit .env with your production values
nano .env
```

Required environment variables:
```env
# Database Configuration
DB_PASS=your_secure_database_password

# LinkedIn API Configuration
LINKEDIN_API_KEY=your_linkedin_api_key
LINKEDIN_API_SECRET=your_linkedin_api_secret
LINKEDIN_PERSON_URN=urn:li:person:your_person_id

# Optional: Grafana password
GRAFANA_PASSWORD=your_grafana_password
```

### 2. Deploy to Production

```bash
# Run the deployment script
./deploy.sh

# Or manually deploy
docker-compose -f docker-compose.prod.yml up -d --build
```

## 📊 Monitoring & Health Checks

### Health Endpoints

- **Health Check**: `http://localhost:8000/health`
- **Detailed Health**: `http://localhost:8000/health/detailed`
- **Metrics**: `http://localhost:8000/metrics`

### Monitoring Stack

- **Prometheus**: `http://localhost:9090` - Metrics collection
- **Grafana**: `http://localhost:3000` - Visualization dashboard

### Example Health Response

```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z",
  "service": "analytics_fetcher",
  "version": "1.0.0",
  "uptime_seconds": 3600.0,
  "last_fetch_time": "2024-01-01T11:30:00Z",
  "fetch_count": 24,
  "error_count": 0
}
```

## 🔧 Production Configuration

### Resource Limits

The service is configured with resource limits:
- Memory: 256M-512M
- CPU: 0.25-0.5 cores

### Logging

- JSON structured logging
- Log rotation (10MB max, 3 files)
- Logs available via Docker Compose

### Security

- Non-root user execution
- Minimal base image
- Environment variable validation
- Connection pooling with limits

## 📈 Metrics & Monitoring

### Available Metrics

- `analytics_fetcher_uptime_seconds` - Service uptime
- `analytics_fetcher_fetch_total` - Total fetch operations
- `analytics_fetcher_errors_total` - Total errors
- `analytics_fetcher_health_status` - Health status (1=healthy, 0=unhealthy)

### Grafana Dashboard

Import the provided dashboard configuration:
```bash
# Copy dashboard configuration
cp grafana/dashboard.json grafana/provisioning/dashboards/
```

## 🚨 Troubleshooting

### Common Issues

1. **Service not starting**
   ```bash
   # Check logs
   docker-compose -f docker-compose.prod.yml logs analytics-fetcher
   
   # Check environment variables
   docker-compose -f docker-compose.prod.yml config
   ```

2. **Health check failing**
   ```bash
   # Check if health server is running
   curl http://localhost:8000/health
   
   # Check container status
   docker-compose -f docker-compose.prod.yml ps
   ```

3. **Database connection issues**
   ```bash
   # Check database logs
   docker-compose -f docker-compose.prod.yml logs db
   
   # Test database connection
   docker-compose -f docker-compose.prod.yml exec db psql -U n8n_user -d n8n_db
   ```

### Log Analysis

```bash
# View real-time logs
docker-compose -f docker-compose.prod.yml logs -f analytics-fetcher

# View logs with timestamps
docker-compose -f docker-compose.prod.yml logs -t analytics-fetcher

# View last 100 lines
docker-compose -f docker-compose.prod.yml logs --tail=100 analytics-fetcher
```

## 🔄 Maintenance

### Updates

```bash
# Pull latest changes
git pull

# Rebuild and restart
docker-compose -f docker-compose.prod.yml up -d --build

# Verify health
curl http://localhost:8000/health
```

### Backup

```bash
# Backup database
docker-compose -f docker-compose.prod.yml exec db pg_dump -U n8n_user n8n_db > backup.sql

# Backup logs
tar -czf logs_backup.tar.gz logs/
```

### Scaling

For high availability, consider:
- Multiple service instances behind a load balancer
- Database clustering
- Redis for caching
- Message queues for job processing

## 🔒 Security Best Practices

1. **Environment Variables**
   - Use strong, unique passwords
   - Rotate API keys regularly
   - Use secrets management in production

2. **Network Security**
   - Restrict container network access
   - Use internal networks for service communication
   - Implement proper firewall rules

3. **Monitoring**
   - Set up alerts for service failures
   - Monitor resource usage
   - Track API rate limits

4. **Backup Strategy**
   - Regular database backups
   - Configuration backups
   - Disaster recovery plan

## 📋 Production Checklist

- [ ] Environment variables configured
- [ ] Database credentials set
- [ ] LinkedIn API credentials configured
- [ ] Health checks passing
- [ ] Monitoring stack deployed
- [ ] Logs being collected
- [ ] Backup strategy implemented
- [ ] Security measures in place
- [ ] Resource limits configured
- [ ] Error handling tested

## 🆘 Support

For production issues:

1. Check the logs first
2. Verify health endpoints
3. Check resource usage
4. Review monitoring dashboards
5. Test connectivity to external services

## 📚 Additional Resources

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Prometheus Monitoring](https://prometheus.io/docs/)
- [Grafana Dashboards](https://grafana.com/docs/)
- [PostgreSQL Administration](https://www.postgresql.org/docs/) 