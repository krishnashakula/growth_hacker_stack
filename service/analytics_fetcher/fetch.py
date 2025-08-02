import os
import sys
import time
import asyncio
import logging
import signal
import threading
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from contextlib import asynccontextmanager
from enum import Enum
from datetime import datetime

# Database imports (uncomment when needed)
# from sqlalchemy import create_engine, text
# from sqlalchemy.orm import sessionmaker
# from sqlalchemy.exc import SQLAlchemyError
# from sqlalchemy.pool import QueuePool

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr, Field, validator
import httpx


class RunMode(str, Enum):
    """Supported run modes for the analytics fetcher."""
    ONCE = "once"
    LOOP = "loop"


class AnalyticsSettings(BaseSettings):
    """Configuration settings for the analytics fetcher service."""
    
    # Database Configuration
    db_host: str = Field(default="db", alias="DB_HOST")
    db_port: int = Field(default=5432, alias="DB_PORT")
    db_name: str = Field(default="n8n_db", alias="DB_NAME")
    db_user: str = Field(default="n8n_user", alias="DB_USER")
    db_password: Optional[SecretStr] = Field(default=None, alias="DB_PASS")
    
    # LinkedIn API Configuration
    linkedin_api_key: Optional[SecretStr] = Field(default=None, alias="LINKEDIN_API_KEY")
    linkedin_api_secret: Optional[SecretStr] = Field(default=None, alias="LINKEDIN_API_SECRET")
    linkedin_person_urn: Optional[str] = Field(default=None, alias="LINKEDIN_PERSON_URN")
    
    # Service Configuration
    fetch_interval_seconds: int = Field(default=3600, alias="FETCH_INTERVAL_SECONDS", ge=60)
    run_mode: RunMode = Field(default=RunMode.LOOP, alias="ANALYTICS_FETCHER_RUN_MODE")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    
    # HTTP Client Configuration
    http_timeout: int = Field(default=30, alias="HTTP_TIMEOUT")
    max_retries: int = Field(default=3, alias="MAX_RETRIES")
    retry_delay: int = Field(default=5, alias="RETRY_DELAY")
    
    # Health Server Configuration
    enable_health_server: bool = Field(default=True, alias="ENABLE_HEALTH_SERVER")
    health_port: int = Field(default=8000, alias="HEALTH_PORT")
    
    @validator('log_level')
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

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding='utf-8',
        extra='ignore',
        case_sensitive=False
    )


@dataclass
class LinkedInPostData:
    """Data structure for LinkedIn post analytics."""
    post_id: str
    impressions: int
    clicks: int
    likes: int
    shares: int = 0
    comments: int = 0
    engagement_rate: float = 0.0
    fetched_at: Optional[str] = None


class LoggerManager:
    """Manages logging configuration and setup."""
    
    def __init__(self, settings: AnalyticsSettings):
        self.settings = settings
        self.logger = None
        self._setup_logging()
    
    def _setup_logging(self):
        """Configure logging with structured output."""
        # Clear existing handlers
        logging.getLogger().handlers.clear()
        
        # Create logger
        self.logger = logging.getLogger("analytics_fetcher")
        self.logger.setLevel(self.settings.log_level)
        
        # Create handler
        handler = logging.StreamHandler()
        
        # Try to use JSON formatter if available
        try:
            from pythonjsonlogger.jsonlogger import JsonFormatter
            formatter = JsonFormatter(
                fmt="%(asctime)s %(levelname)s %(name)s %(module)s %(funcName)s %(lineno)d %(message)s"
            )
        except ImportError:
            formatter = logging.Formatter(
                fmt="%(asctime)s - %(levelname)s - %(name)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s"
            )
        
        handler.setFormatter(formatter)
        
        if not self.logger.handlers:
            self.logger.addHandler(handler)


class DatabaseManager:
    """Manages database connections and operations."""
    
    def __init__(self, settings: AnalyticsSettings, logger: logging.Logger):
        self.settings = settings
        self.logger = logger
        self.engine = None
        self.session_factory = None
        self._connection_pool = None
    
    async def initialize(self) -> bool:
        """Initialize database connection with connection pooling."""
        try:
            # Uncomment when SQLAlchemy is available
            # from sqlalchemy import create_engine
            # from sqlalchemy.orm import sessionmaker
            # from sqlalchemy.pool import QueuePool
            # 
            # if not self.settings.db_password:
            #     self.logger.error("Database password not configured")
            #     return False
            # 
            # db_url = f"postgresql://{self.settings.db_user}:{self.settings.db_password.get_secret_value()}@{self.settings.db_host}:{self.settings.db_port}/{self.settings.db_name}"
            # 
            # self.engine = create_engine(
            #     db_url,
            #     poolclass=QueuePool,
            #     pool_size=5,
            #     max_overflow=10,
            #     pool_pre_ping=True,
            #     pool_recycle=3600,
            #     connect_args={"connect_timeout": 10}
            # )
            # 
            # self.session_factory = sessionmaker(
            #     autocommit=False,
            #     autoflush=False,
            #     bind=self.engine
            # )
            # 
            # # Test connection
            # with self.engine.connect() as conn:
            #     self.logger.info(f"Successfully connected to database: {self.settings.db_host}/{self.settings.db_name}")
            
            self.logger.info("Database connection initialized (placeholder)")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize database connection: {e}")
            return False
    
    async def store_analytics_data(self, data: List[LinkedInPostData]) -> bool:
        """Store analytics data in the database."""
        if not data:
            return True
        
        try:
            # Uncomment when SQLAlchemy is available
            # if not self.session_factory:
            #     self.logger.error("Database session factory not available")
            #     return False
            # 
            # with self.session_factory() as session:
            #     for post_data in data:
            #         # Implement your database storage logic here
            #         # Example: upsert operation
            #         pass
            #     session.commit()
            
            self.logger.info(f"Stored {len(data)} analytics records (placeholder)")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to store analytics data: {e}")
            return False


class LinkedInAPIClient:
    """Handles LinkedIn API interactions with retry logic and rate limiting."""
    
    def __init__(self, settings: AnalyticsSettings, logger: logging.Logger):
        self.settings = settings
        self.logger = logger
        self.client = None
        self._rate_limit_remaining = 100
        self._rate_limit_reset = None
    
    async def initialize(self) -> bool:
        """Initialize HTTP client with connection pooling."""
        try:
            limits = httpx.Limits(max_keepalive_connections=5, max_connections=10)
            self.client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.settings.http_timeout),
                limits=limits
            )
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize HTTP client: {e}")
            return False
    
    async def close(self):
        """Close HTTP client."""
        if self.client:
            await self.client.aclose()
    
    async def _make_request(self, method: str, url: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Make HTTP request with retry logic."""
        for attempt in range(self.settings.max_retries):
            try:
                response = await self.client.request(method, url, **kwargs)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:  # Rate limited
                    retry_after = int(e.response.headers.get('Retry-After', self.settings.retry_delay))
                    self.logger.warning(f"Rate limited, waiting {retry_after} seconds")
                    await asyncio.sleep(retry_after)
                elif e.response.status_code >= 500:  # Server error
                    if attempt < self.settings.max_retries - 1:
                        wait_time = self.settings.retry_delay * (2 ** attempt)
                        self.logger.warning(f"Server error, retrying in {wait_time} seconds")
                        await asyncio.sleep(wait_time)
                    else:
                        raise
                else:
                    raise
            except Exception as e:
                if attempt < self.settings.max_retries - 1:
                    wait_time = self.settings.retry_delay * (2 ** attempt)
                    self.logger.warning(f"Request failed, retrying in {wait_time} seconds: {e}")
                    await asyncio.sleep(wait_time)
                else:
                    raise
        
        return None
    
    async def fetch_post_analytics(self) -> List[LinkedInPostData]:
        """Fetch LinkedIn post analytics data."""
        if not self.settings.linkedin_api_key:
            self.logger.error("LinkedIn API key not configured")
            return []
        
        try:
            # Implement actual LinkedIn API calls here
            # This is a placeholder implementation
            self.logger.info("Fetching LinkedIn post analytics...")
            
            # Simulate API call
            await asyncio.sleep(1)
            
            # Return mock data
            return [
                LinkedInPostData(
                    post_id="urn:li:share:123",
                    impressions=1000,
                    clicks=50,
                    likes=20,
                    shares=5,
                    comments=3,
                    engagement_rate=7.8
                ),
                LinkedInPostData(
                    post_id="urn:li:share:456",
                    impressions=2500,
                    clicks=120,
                    likes=45,
                    shares=12,
                    comments=8,
                    engagement_rate=7.4
                )
            ]
            
        except Exception as e:
            self.logger.error(f"Failed to fetch LinkedIn analytics: {e}")
            return []


class AnalyticsFetcherService:
    """Main service class for fetching and processing analytics data."""
    
    def __init__(self):
        self.settings = None
        self.logger_manager = None
        self.logger = None
        self.db_manager = None
        self.api_client = None
        self._shutdown_event = asyncio.Event()
        self._health_server = None
        self._health_thread = None
        self._fetch_count = 0
        self._error_count = 0
        self._last_fetch_time = None
    
    async def initialize(self) -> bool:
        """Initialize all service components."""
        try:
            # Load settings
            self.settings = AnalyticsSettings()
            
            # Setup logging
            self.logger_manager = LoggerManager(self.settings)
            self.logger = self.logger_manager.logger
            
            self.logger.info("Initializing Analytics Fetcher Service...")
            
            # Initialize database manager
            self.db_manager = DatabaseManager(self.settings, self.logger)
            if not await self.db_manager.initialize():
                self.logger.error("Failed to initialize database manager")
                return False
            
            # Initialize API client
            self.api_client = LinkedInAPIClient(self.settings, self.logger)
            if not await self.api_client.initialize():
                self.logger.error("Failed to initialize API client")
                return False
            
            # Setup signal handlers for graceful shutdown
            self._setup_signal_handlers()
            
            # Initialize health server if enabled
            if self.settings.enable_health_server:
                await self._setup_health_server()
            
            self.logger.info("Analytics Fetcher Service initialized successfully")
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to initialize service: {e}")
            else:
                print(f"Failed to initialize service: {e}")
            return False
    
    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            self.logger.info(f"Received signal {signum}, initiating graceful shutdown...")
            self._shutdown_event.set()
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def _setup_health_server(self):
        """Setup health server in a separate thread."""
        try:
            from health_server import HealthServer
            
            self._health_server = HealthServer(port=self.settings.health_port)
            
            # Start health server in a separate thread
            def run_health_server():
                self._health_server.run()
            
            self._health_thread = threading.Thread(target=run_health_server, daemon=True)
            self._health_thread.start()
            
            self.logger.info(f"Health server started on port {self.settings.health_port}")
            
        except ImportError:
            self.logger.warning("Health server dependencies not available. Skipping health server setup.")
        except Exception as e:
            self.logger.error(f"Failed to setup health server: {e}")
    
    async def _update_health_status(self, **kwargs):
        """Update health server status."""
        if self._health_server:
            try:
                self._health_server.update_status(**kwargs)
            except Exception as e:
                self.logger.error(f"Failed to update health status: {e}")
    
    async def fetch_and_process_analytics(self) -> bool:
        """Main method to fetch and process analytics data."""
        try:
            self.logger.info("Starting analytics fetch cycle...")
            
            # Fetch data from LinkedIn API
            analytics_data = await self.api_client.fetch_post_analytics()
            
            if not analytics_data:
                self.logger.warning("No analytics data received")
                return False
            
            self.logger.info(f"Fetched {len(analytics_data)} analytics records")
            
            # Process and store data
            if await self.db_manager.store_analytics_data(analytics_data):
                self.logger.info("Analytics data processed and stored successfully")
                
                # Update health metrics
                self._fetch_count += 1
                self._last_fetch_time = datetime.utcnow().isoformat()
                await self._update_health_status(
                    fetch_count=self._fetch_count,
                    last_fetch_time=self._last_fetch_time
                )
                
                return True
            else:
                self.logger.error("Failed to store analytics data")
                self._error_count += 1
                await self._update_health_status(error_count=self._error_count)
                return False
                
        except Exception as e:
            self.logger.error(f"Error during analytics fetch cycle: {e}", exc_info=True)
            self._error_count += 1
            await self._update_health_status(error_count=self._error_count)
            return False
    
    async def run_once(self):
        """Run the service once."""
        self.logger.info("Running in 'once' mode")
        success = await self.fetch_and_process_analytics()
        if success:
            self.logger.info("Single run completed successfully")
        else:
            self.logger.error("Single run failed")
            sys.exit(1)
    
    async def run_loop(self):
        """Run the service in a continuous loop."""
        self.logger.info(f"Starting polling loop with interval: {self.settings.fetch_interval_seconds} seconds")
        
        while not self._shutdown_event.is_set():
            try:
                await self.fetch_and_process_analytics()
                
                # Wait for next cycle or shutdown signal
                try:
                    await asyncio.wait_for(
                        self._shutdown_event.wait(),
                        timeout=self.settings.fetch_interval_seconds
                    )
                    break  # Shutdown signal received
                except asyncio.TimeoutError:
                    continue  # Continue to next cycle
                    
            except Exception as e:
                self.logger.error(f"Unexpected error in polling loop: {e}", exc_info=True)
                # Wait before retrying
                await asyncio.sleep(min(60, self.settings.fetch_interval_seconds))
    
    async def shutdown(self):
        """Gracefully shutdown the service."""
        self.logger.info("Shutting down Analytics Fetcher Service...")
        
        # Update health status to indicate shutdown
        await self._update_health_status(status="shutting_down")
        
        if self.api_client:
            await self.api_client.close()
        
        self.logger.info("Service shutdown complete")


async def main():
    """Main entry point for the analytics fetcher service."""
    service = AnalyticsFetcherService()
    
    try:
        if not await service.initialize():
            sys.exit(1)
        
        if service.settings.run_mode == RunMode.ONCE:
            await service.run_once()
        elif service.settings.run_mode == RunMode.LOOP:
            await service.run_loop()
        else:
            service.logger.error(f"Invalid run mode: {service.settings.run_mode}")
            sys.exit(1)
            
    except KeyboardInterrupt:
        service.logger.info("Received keyboard interrupt")
    except Exception as e:
        service.logger.critical(f"Critical error in main: {e}", exc_info=True)
        sys.exit(1)
    finally:
        await service.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
