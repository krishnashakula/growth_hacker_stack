import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from fetch import (
    AnalyticsSettings,
    LinkedInPostData,
    LoggerManager,
    DatabaseManager,
    LinkedInAPIClient,
    AnalyticsFetcherService,
    RunMode
)


class TestAnalyticsSettings:
    """Test configuration settings."""
    
    def test_default_settings(self):
        """Test default settings are loaded correctly."""
        settings = AnalyticsSettings()
        assert settings.db_host == "db"
        assert settings.db_port == 5432
        assert settings.fetch_interval_seconds == 3600
        assert settings.run_mode == RunMode.LOOP
    
    def test_custom_settings(self):
        """Test custom settings override defaults."""
        with patch.dict('os.environ', {
            'DB_HOST': 'custom_host',
            'FETCH_INTERVAL_SECONDS': '1800',
            'ANALYTICS_FETCHER_RUN_MODE': 'once'
        }):
            settings = AnalyticsSettings()
            assert settings.db_host == "custom_host"
            assert settings.fetch_interval_seconds == 1800
            assert settings.run_mode == RunMode.ONCE
    
    def test_invalid_log_level(self):
        """Test invalid log level raises error."""
        with patch.dict('os.environ', {'LOG_LEVEL': 'INVALID'}):
            with pytest.raises(ValueError, match="log_level must be one of"):
                AnalyticsSettings()
    
    def test_invalid_fetch_interval(self):
        """Test invalid fetch interval raises error."""
        with patch.dict('os.environ', {'FETCH_INTERVAL_SECONDS': '30'}):
            with pytest.raises(ValueError, match="fetch_interval_seconds must be at least 60 seconds"):
                AnalyticsSettings()


class TestLinkedInPostData:
    """Test LinkedIn post data structure."""
    
    def test_create_post_data(self):
        """Test creating LinkedIn post data."""
        post_data = LinkedInPostData(
            post_id="urn:li:share:123",
            impressions=1000,
            clicks=50,
            likes=20,
            shares=5,
            comments=3,
            engagement_rate=7.8
        )
        
        assert post_data.post_id == "urn:li:share:123"
        assert post_data.impressions == 1000
        assert post_data.engagement_rate == 7.8
    
    def test_default_values(self):
        """Test default values for optional fields."""
        post_data = LinkedInPostData(
            post_id="urn:li:share:123",
            impressions=1000,
            clicks=50,
            likes=20
        )
        
        assert post_data.shares == 0
        assert post_data.comments == 0
        assert post_data.engagement_rate == 0.0
        assert post_data.fetched_at is None


class TestLoggerManager:
    """Test logging manager."""
    
    def test_logger_initialization(self):
        """Test logger manager initialization."""
        settings = AnalyticsSettings()
        logger_manager = LoggerManager(settings)
        
        assert logger_manager.logger is not None
        assert logger_manager.logger.name == "analytics_fetcher"
        assert logger_manager.logger.level == settings.log_level


class TestDatabaseManager:
    """Test database manager."""
    
    @pytest.fixture
    def db_manager(self):
        """Create database manager fixture."""
        settings = AnalyticsSettings()
        logger = Mock()
        return DatabaseManager(settings, logger)
    
    @pytest.mark.asyncio
    async def test_initialize_success(self, db_manager):
        """Test successful database initialization."""
        result = await db_manager.initialize()
        assert result is True
        db_manager.logger.info.assert_called_with("Database connection initialized (placeholder)")
    
    @pytest.mark.asyncio
    async def test_store_analytics_data_empty(self, db_manager):
        """Test storing empty analytics data."""
        result = await db_manager.store_analytics_data([])
        assert result is True
    
    @pytest.mark.asyncio
    async def test_store_analytics_data_success(self, db_manager):
        """Test storing analytics data successfully."""
        data = [
            LinkedInPostData(
                post_id="urn:li:share:123",
                impressions=1000,
                clicks=50,
                likes=20
            )
        ]
        
        result = await db_manager.store_analytics_data(data)
        assert result is True
        db_manager.logger.info.assert_called_with("Stored 1 analytics records (placeholder)")


class TestLinkedInAPIClient:
    """Test LinkedIn API client."""
    
    @pytest.fixture
    def api_client(self):
        """Create API client fixture."""
        settings = AnalyticsSettings()
        logger = Mock()
        return LinkedInAPIClient(settings, logger)
    
    @pytest.mark.asyncio
    async def test_initialize_success(self, api_client):
        """Test successful API client initialization."""
        result = await api_client.initialize()
        assert result is True
        assert api_client.client is not None
    
    @pytest.mark.asyncio
    async def test_close_client(self, api_client):
        """Test closing API client."""
        await api_client.initialize()
        await api_client.close()
        # Verify client is closed (this would be tested with actual httpx client)
    
    @pytest.mark.asyncio
    async def test_fetch_post_analytics_no_api_key(self, api_client):
        """Test fetching analytics without API key."""
        await api_client.initialize()
        result = await api_client.fetch_post_analytics()
        
        assert result == []
        api_client.logger.error.assert_called_with("LinkedIn API key not configured")
    
    @pytest.mark.asyncio
    async def test_fetch_post_analytics_success(self, api_client):
        """Test successful analytics fetch."""
        # Mock API key
        api_client.settings.linkedin_api_key = Mock()
        api_client.settings.linkedin_api_key.get_secret_value.return_value = "test_key"
        
        await api_client.initialize()
        result = await api_client.fetch_post_analytics()
        
        assert len(result) == 2
        assert all(isinstance(item, LinkedInPostData) for item in result)
        api_client.logger.info.assert_called_with("Fetching LinkedIn post analytics...")


class TestAnalyticsFetcherService:
    """Test main service class."""
    
    @pytest.fixture
    def service(self):
        """Create service fixture."""
        return AnalyticsFetcherService()
    
    @pytest.mark.asyncio
    async def test_initialize_success(self, service):
        """Test successful service initialization."""
        with patch('fetch.AnalyticsSettings') as mock_settings:
            mock_settings.return_value = Mock()
            
            result = await service.initialize()
            assert result is True
            assert service.settings is not None
            assert service.logger is not None
            assert service.db_manager is not None
            assert service.api_client is not None
    
    @pytest.mark.asyncio
    async def test_fetch_and_process_analytics_success(self, service):
        """Test successful analytics fetch and process."""
        # Mock service components
        service.logger = Mock()
        service.api_client = Mock()
        service.db_manager = Mock()
        
        # Mock API response
        mock_data = [
            LinkedInPostData(
                post_id="urn:li:share:123",
                impressions=1000,
                clicks=50,
                likes=20
            )
        ]
        service.api_client.fetch_post_analytics = AsyncMock(return_value=mock_data)
        service.db_manager.store_analytics_data = AsyncMock(return_value=True)
        
        result = await service.fetch_and_process_analytics()
        
        assert result is True
        service.logger.info.assert_called_with("Analytics data processed and stored successfully")
    
    @pytest.mark.asyncio
    async def test_fetch_and_process_analytics_no_data(self, service):
        """Test analytics fetch with no data."""
        service.logger = Mock()
        service.api_client = Mock()
        service.api_client.fetch_post_analytics = AsyncMock(return_value=[])
        
        result = await service.fetch_and_process_analytics()
        
        assert result is False
        service.logger.warning.assert_called_with("No analytics data received")
    
    @pytest.mark.asyncio
    async def test_run_once_success(self, service):
        """Test successful single run."""
        service.logger = Mock()
        service.fetch_and_process_analytics = AsyncMock(return_value=True)
        
        await service.run_once()
        
        service.logger.info.assert_called_with("Single run completed successfully")
    
    @pytest.mark.asyncio
    async def test_run_once_failure(self, service):
        """Test failed single run."""
        service.logger = Mock()
        service.fetch_and_process_analytics = AsyncMock(return_value=False)
        
        with pytest.raises(SystemExit):
            await service.run_once()
        
        service.logger.error.assert_called_with("Single run failed")
    
    @pytest.mark.asyncio
    async def test_shutdown(self, service):
        """Test graceful shutdown."""
        service.logger = Mock()
        service.api_client = Mock()
        service.api_client.close = AsyncMock()
        
        await service.shutdown()
        
        service.logger.info.assert_called_with("Service shutdown complete")
        service.api_client.close.assert_called_once()


@pytest.mark.asyncio
async def test_main_function():
    """Test main function execution."""
    with patch('fetch.AnalyticsFetcherService') as mock_service_class:
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.initialize = AsyncMock(return_value=True)
        mock_service.settings.run_mode = RunMode.ONCE
        mock_service.run_once = AsyncMock()
        mock_service.shutdown = AsyncMock()
        
        from fetch import main
        await main()
        
        mock_service.initialize.assert_called_once()
        mock_service.run_once.assert_called_once()
        mock_service.shutdown.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__]) 