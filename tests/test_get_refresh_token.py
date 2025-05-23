import unittest
from unittest.mock import patch, MagicMock
import os
import sys
import importlib.util

class TestGetRefreshToken(unittest.TestCase):
    
    @patch('os.getenv')
    @patch('praw.Reddit')
    def test_reddit_initialization(self, mock_reddit, mock_getenv):
        # Setup environment variable mocks
        mock_getenv.side_effect = lambda key: {
            'REDDIT_CLIENT_ID': 'test_client_id',
            'REDDIT_CLIENT_SECRET': 'test_client_secret',
            'REDDIT_USER_AGENT': 'test_user_agent'
        }.get(key)
        
        # Setup Reddit mock
        mock_reddit_instance = MagicMock()
        mock_reddit.return_value = mock_reddit_instance
        mock_auth = MagicMock()
        mock_reddit_instance.auth = mock_auth
        mock_auth.url.return_value = "https://reddit.com/auth/url"
        
        # Import the module dynamically to avoid executing the main code
        spec = importlib.util.spec_from_file_location(
            "get_refresh_token", 
            "/workspace/growth_hacker_stack/get_refresh_token.py"
        )
        module = importlib.util.module_from_spec(spec)
        
        # Patch input and webbrowser.open to prevent interactive behavior
        with patch.object(sys, 'modules', {'__main__': module}):
            with patch('builtins.input', return_value="test_code"):
                with patch('webbrowser.open'):
                    with patch('webbrowser.register'):
                        with patch('os.path.exists', return_value=False):
                            with patch('builtins.print'):
                                # Execute only the initialization part
                                spec.loader.exec_module(module)
        
        # Verify Reddit was initialized with correct parameters
        mock_reddit.assert_called_once_with(
            client_id='test_client_id',
            client_secret='test_client_secret',
            redirect_uri='http://localhost:65010/authorize_callback',
            user_agent='test_user_agent'
        )
        
        # Verify auth URL was generated with correct parameters
        mock_auth.url.assert_called_once_with(['read', 'submit'], 'random_state_string', 'permanent')
        
        # Verify authorize was called with the input code
        mock_auth.authorize.assert_called_once_with('test_code')