import unittest
from unittest.mock import patch, Mock, MagicMock
from datetime import datetime, UTC
from service.analytics_fetcher.fetch import fetch_and_store

class TestAnalyticsFetcher(unittest.TestCase):
    
    @patch('service.analytics_fetcher.fetch.psycopg2.connect')
    @patch('service.analytics_fetcher.fetch.requests.get')
    @patch('service.analytics_fetcher.fetch.datetime')
    def test_fetch_and_store(self, mock_datetime, mock_get, mock_connect):
        # Setup datetime mock
        mock_now = datetime(2025, 5, 23, 12, 0, 0)
        mock_datetime.now.return_value = mock_now
        
        # Setup database mock
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # Mock cursor fetchall to return some post IDs
        mock_cursor.fetchall.return_value = [('post1',), ('post2',)]
        
        # Setup API response mock
        mock_response = MagicMock()
        mock_response.json.side_effect = [
            {'likeCount': 42, 'commentCount': 7},  # First post
            {'likeCount': 15, 'commentCount': 3}   # Second post
        ]
        mock_get.return_value = mock_response
        
        # Call the function
        fetch_and_store()
        
        # Verify database connection was established
        mock_connect.assert_called_once()
        
        # Verify SQL query to get post IDs was executed
        mock_cursor.execute.assert_any_call("SELECT post_id FROM posts;")
        
        # Verify API calls were made for each post
        self.assertEqual(mock_get.call_count, 2)
        
        # Verify data was inserted for each post
        expected_insert_calls = [
            unittest.mock.call(
                "INSERT INTO post_stats (post_id, like_count, comment_count, fetched_at) VALUES (%s,%s,%s,%s) ON CONFLICT DO NOTHING",
                ('post1', 42, 7, mock_now)
            ),
            unittest.mock.call(
                "INSERT INTO post_stats (post_id, like_count, comment_count, fetched_at) VALUES (%s,%s,%s,%s) ON CONFLICT DO NOTHING",
                ('post2', 15, 3, mock_now)
            )
        ]
        mock_cursor.execute.assert_has_calls(expected_insert_calls, any_order=False)
        
        # Verify connection was committed and closed
        mock_conn.commit.assert_called_once()
        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()
    
    @patch('service.analytics_fetcher.fetch.psycopg2.connect')
    @patch('service.analytics_fetcher.fetch.requests.get')
    @patch('service.analytics_fetcher.fetch.datetime')
    def test_fetch_and_store_empty_response(self, mock_datetime, mock_get, mock_connect):
        # Setup datetime mock
        mock_now = datetime(2025, 5, 23, 12, 0, 0)
        mock_datetime.now.return_value = mock_now
        # Setup database mock
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # Mock cursor fetchall to return some post IDs
        mock_cursor.fetchall.return_value = [('post1',)]
        
        # Setup API response mock with missing data
        mock_response = MagicMock()
        mock_response.json.return_value = {}  # Empty response
        mock_get.return_value = mock_response
        
        # Call the function
        fetch_and_store()
        
        # Verify default values (0) are used when data is missing
        mock_cursor.execute.assert_any_call(
            "INSERT INTO post_stats (post_id, like_count, comment_count, fetched_at) VALUES (%s,%s,%s,%s) ON CONFLICT DO NOTHING",
            ('post1', 0, 0, mock_now)
        )