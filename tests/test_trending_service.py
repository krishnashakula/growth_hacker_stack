import unittest
from unittest.mock import patch, Mock
import xml.etree.ElementTree as ET
from service.trending_service.main import fetch_trends_rss, app
from fastapi.testclient import TestClient

client = TestClient(app)

class TestTrendingService(unittest.TestCase):
    
    @patch('service.trending_service.main.requests.get')
    def test_fetch_trends_rss(self, mock_get):
        # Create a mock response with sample XML data
        mock_response = Mock()
        mock_response.content = '''<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
            <channel>
                <title>Google Trends</title>
                <item>
                    <title>Trending Topic 1</title>
                </item>
                <item>
                    <title>Trending Topic 2</title>
                </item>
                <item>
                    <title>Trending Topic 3</title>
                </item>
            </channel>
        </rss>'''
        mock_get.return_value = mock_response
        
        # Test with default parameters
        result = fetch_trends_rss()
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0], "Trending Topic 1")
        self.assertEqual(result[1], "Trending Topic 2")
        self.assertEqual(result[2], "Trending Topic 3")
        
        # Test with custom limit
        result = fetch_trends_rss(limit=2)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], "Trending Topic 1")
        self.assertEqual(result[1], "Trending Topic 2")
        
        # Test with custom geo
        fetch_trends_rss(geo="CA")
        # Verify the URL contains the geo parameter
        called_url = mock_get.call_args[0][0]
        self.assertIn("CA", called_url)
    
    @patch('service.trending_service.main.fetch_trends_rss')
    def test_keywords_endpoint(self, mock_fetch):
        # Setup mock return value
        mock_fetch.return_value = ["Topic 1", "Topic 2"]
        
        # Test the endpoint
        response = client.get("/keywords")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"keywords": ["Topic 1", "Topic 2"]})
        
        # Test with parameters
        response = client.get("/keywords?geo=ca&limit=5")
        self.assertEqual(response.status_code, 200)
        # Verify the function was called with correct parameters
        mock_fetch.assert_called_with(geo="CA", limit=5)