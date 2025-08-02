# Analytics Fetcher Service

An optimized, production-ready service for fetching LinkedIn analytics data with robust error handling, connection pooling, and graceful shutdown capabilities.

## 🚀 Key Optimizations

### Performance Improvements
- **Async/Await Support**: Full asynchronous implementation for better I/O performance
- **Connection Pooling**: HTTP client and database connection pooling for efficient resource usage
- **Retry Logic**: Exponential backoff with configurable retry attempts
- **Rate Limiting**: Built-in rate limit handling for API calls

### Reliability Enhancements
- **Graceful Shutdown**: Proper signal handling and resource cleanup
- **Error Recovery**: Comprehensive error handling with fallback mechanisms
- **Health Checks**: Built-in health monitoring capabilities
- **Resource Management**: Automatic cleanup of connections and resources

### Code Quality
- **Type Safety**: Full type hints throughout the codebase
- **Separation of Concerns**: Modular design with clear responsibilities
- **Configuration Management**: Robust settings validation with Pydantic
- **Structured Logging**: JSON logging support for better observability

## 📋 Features

- ✅ Asynchronous HTTP client with connection pooling
- ✅ Database connection management with pooling
- ✅ Configurable retry logic with exponential backoff
- ✅ Rate limit handling for API calls
- ✅ Graceful shutdown with signal handling
- ✅ Structured logging (JSON format)
- ✅ Environment-based configuration
- ✅ Type safety with full type hints
- ✅ Error recovery and fallback mechanisms
- ✅ Health monitoring capabilities

## 🛠️ Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables (create `.env` file):
```env
# Database Configuration
DB_HOST=db
DB_PORT=5432
DB_NAME=n8n_db
DB_USER=n8n_user
DB_PASS=your_secure_password

# LinkedIn API Configuration
LINKEDIN_API_KEY=your_linkedin_api_key
LINKEDIN_API_SECRET=your_linkedin_api_secret
LINKEDIN_PERSON_URN=urn:li:person:your_person_id

# Service Configuration
FETCH_INTERVAL_SECONDS=3600
ANALYTICS_FETCHER_RUN_MODE=loop
LOG_LEVEL=INFO

# HTTP Client Configuration
HTTP_TIMEOUT=30
MAX_RETRIES=3
RETRY_DELAY=5
```

## 🚀 Usage

### Development

#### Run Once
```bash
ANALYTICS_FETCHER_RUN_MODE=once python fetch.py
```

#### Run in Loop Mode
```bash
ANALYTICS_FETCHER_RUN_MODE=loop python fetch.py
```

### Production Deployment

#### Quick Deploy
```bash
# Setup environment
cp env.example .env
# Edit .env with your production values

# Deploy
./deploy.sh
```

#### Manual Docker Deployment
```bash
docker-compose -f docker-compose.prod.yml up -d --build
```

#### Health Checks
```bash
# Check service health
curl http://localhost:8000/health

# View metrics
curl http://localhost:8000/metrics
```

For detailed production deployment instructions, see [PRODUCTION.md](./PRODUCTION.md).

## 📊 Configuration Options

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `DB_HOST` | `db` | Database host |
| `DB_PORT` | `5432` | Database port |
| `DB_NAME` | `n8n_db` | Database name |
| `DB_USER` | `n8n_user` | Database user |
| `DB_PASS` | `None` | Database password (required) |
| `LINKEDIN_API_KEY` | `None` | LinkedIn API key (required) |
| `LINKEDIN_API_SECRET` | `None` | LinkedIn API secret |
| `LINKEDIN_PERSON_URN` | `None` | LinkedIn person URN |
| `FETCH_INTERVAL_SECONDS` | `3600` | Fetch interval in seconds (min: 60) |
| `ANALYTICS_FETCHER_RUN_MODE` | `loop` | Run mode: `once` or `loop` |
| `LOG_LEVEL` | `INFO` | Logging level |
| `HTTP_TIMEOUT` | `30` | HTTP request timeout in seconds |
| `MAX_RETRIES` | `3` | Maximum retry attempts |
| `RETRY_DELAY` | `5` | Base retry delay in seconds |

## 🔧 Architecture

### Service Components

1. **AnalyticsFetcherService**: Main service orchestrator
2. **LoggerManager**: Handles logging configuration
3. **DatabaseManager**: Manages database connections and operations
4. **LinkedInAPIClient**: Handles LinkedIn API interactions
5. **AnalyticsSettings**: Configuration management with validation

### Data Flow

```
Service Startup → Initialize Components → Fetch Data → Process Data → Store Data → Repeat
```

## 🧪 Testing

Run tests with pytest:
```bash
pytest tests/
```

## 📈 Monitoring

The service provides structured logging for monitoring:

```json
{
  "timestamp": "2024-01-01T12:00:00Z",
  "level": "INFO",
  "logger": "analytics_fetcher",
  "module": "fetch",
  "function": "fetch_and_process_analytics",
  "line": 123,
  "message": "Starting analytics fetch cycle..."
}
```

## 🔒 Security

- Environment variable validation
- Secret management with Pydantic SecretStr
- Connection pooling with proper cleanup
- Rate limiting to prevent API abuse

## 🚨 Error Handling

The service includes comprehensive error handling:

- **Network Errors**: Retry with exponential backoff
- **API Rate Limits**: Automatic backoff and retry
- **Database Errors**: Connection retry and fallback
- **Configuration Errors**: Validation and clear error messages

## 🔄 Graceful Shutdown

The service handles shutdown signals (SIGINT, SIGTERM) gracefully:

1. Stop accepting new requests
2. Complete current operations
3. Close database connections
4. Close HTTP client connections
5. Exit cleanly

## 📝 Development

### Code Style
- Black for code formatting
- isort for import sorting
- mypy for type checking

### Adding New Features
1. Extend `AnalyticsSettings` for new configuration
2. Add new methods to appropriate manager classes
3. Update tests and documentation
4. Follow the existing async patterns

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License. 