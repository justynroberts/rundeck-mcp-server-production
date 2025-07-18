"""Test multi-server setup and functionality."""

import unittest
from unittest.mock import Mock, patch
import os

from rundeck_mcp.client import ClientManager, get_client_manager
from rundeck_mcp.tools.system import list_servers, health_check_servers


class TestMultiServerSetup(unittest.TestCase):
    """Test cases for multi-server setup."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.sample_servers = {
            'RUNDECK_URL': 'https://primary.rundeck.com',
            'RUNDECK_API_TOKEN': 'primary-token',
            'RUNDECK_NAME': 'primary',
            'RUNDECK_URL_1': 'https://dev.rundeck.com',
            'RUNDECK_API_TOKEN_1': 'dev-token',
            'RUNDECK_NAME_1': 'development',
            'RUNDECK_URL_2': 'https://prod.rundeck.com',
            'RUNDECK_API_TOKEN_2': 'prod-token',
            'RUNDECK_NAME_2': 'production',
            'RUNDECK_API_VERSION_2': '48'
        }
    
    @patch.dict(os.environ, {}, clear=True)
    def test_no_servers_configured(self):
        """Test behavior when no servers are configured."""
        client_manager = ClientManager()
        
        with self.assertRaises(ValueError) as context:
            client_manager.get_client()
        
        self.assertIn("No Rundeck clients configured", str(context.exception))
    
    @patch.dict(os.environ, {
        'RUNDECK_URL': 'https://primary.rundeck.com',
        'RUNDECK_API_TOKEN': 'primary-token'
    }, clear=True)
    def test_single_server_setup(self):
        """Test single server setup."""
        client_manager = ClientManager()
        
        # Test primary client
        client = client_manager.get_client()
        self.assertEqual(client.name, "primary")
        self.assertEqual(client.base_url, "https://primary.rundeck.com")
        
        # Test server list
        servers = client_manager.list_servers()
        self.assertEqual(len(servers), 1)
        self.assertEqual(servers[0].name, "primary")
        self.assertTrue(servers[0].is_primary)
    
    def test_multi_server_setup(self):
        """Test multi-server setup."""
        with patch.dict(os.environ, self.sample_servers, clear=True):
            client_manager = ClientManager()
            
            # Test primary client
            primary_client = client_manager.get_client()
            self.assertEqual(primary_client.name, "primary")
            self.assertEqual(primary_client.base_url, "https://primary.rundeck.com")
            
            # Test additional clients
            dev_client = client_manager.get_client("development")
            self.assertEqual(dev_client.name, "development")
            self.assertEqual(dev_client.base_url, "https://dev.rundeck.com")
            
            prod_client = client_manager.get_client("production")
            self.assertEqual(prod_client.name, "production")
            self.assertEqual(prod_client.base_url, "https://prod.rundeck.com")
            self.assertEqual(prod_client.api_version, "48")  # Custom API version
            
            # Test server list
            servers = client_manager.list_servers()
            self.assertEqual(len(servers), 3)
            
            server_names = [server.name for server in servers]
            self.assertIn("primary", server_names)
            self.assertIn("development", server_names)
            self.assertIn("production", server_names)
            
            # Check primary server flag
            primary_servers = [server for server in servers if server.is_primary]
            self.assertEqual(len(primary_servers), 1)
            self.assertEqual(primary_servers[0].name, "primary")
    
    def test_incomplete_server_configuration(self):
        """Test handling of incomplete server configuration."""
        incomplete_config = {
            'RUNDECK_URL': 'https://primary.rundeck.com',
            'RUNDECK_API_TOKEN': 'primary-token',
            'RUNDECK_URL_1': 'https://dev.rundeck.com',
            # Missing RUNDECK_API_TOKEN_1
        }
        
        with patch.dict(os.environ, incomplete_config, clear=True):
            client_manager = ClientManager()
            
            # Should only have primary server
            servers = client_manager.list_servers()
            self.assertEqual(len(servers), 1)
            self.assertEqual(servers[0].name, "primary")
    
    def test_server_fallback_behavior(self):
        """Test server fallback behavior."""
        with patch.dict(os.environ, self.sample_servers, clear=True):
            client_manager = ClientManager()
            
            # Test fallback to primary when no server specified
            client = client_manager.get_client(None)
            self.assertEqual(client.name, "primary")
            
            # Test fallback to primary when invalid server specified
            with self.assertRaises(ValueError):
                client_manager.get_client("nonexistent")
    
    @patch('rundeck_mcp.client.RundeckClient.health_check')
    def test_health_check_all_servers(self, mock_health_check):
        """Test health check across all servers."""
        # Mock health check results
        mock_health_check.side_effect = [True, False, True]  # primary, dev, prod
        
        with patch.dict(os.environ, self.sample_servers, clear=True):
            client_manager = ClientManager()
            health_status = client_manager.health_check_all()
            
            self.assertEqual(len(health_status), 3)
            self.assertTrue(health_status["primary"])
            self.assertFalse(health_status["development"])
            self.assertTrue(health_status["production"])
    
    @patch('rundeck_mcp.client.get_client_manager')
    def test_list_servers_tool(self, mock_get_client_manager):
        """Test the list_servers tool."""
        # Mock client manager
        mock_client_manager = Mock()
        mock_servers = [
            Mock(name="primary", url="https://primary.rundeck.com", api_version="47", is_primary=True),
            Mock(name="development", url="https://dev.rundeck.com", api_version="47", is_primary=False),
        ]
        mock_client_manager.list_servers.return_value = mock_servers
        mock_get_client_manager.return_value = mock_client_manager
        
        result = list_servers()
        
        self.assertEqual(len(result.response), 2)
        self.assertEqual(result.response[0].name, "primary")
        self.assertEqual(result.response[1].name, "development")
    
    @patch('rundeck_mcp.client.get_client_manager')
    def test_health_check_servers_tool(self, mock_get_client_manager):
        """Test the health_check_servers tool."""
        # Mock client manager
        mock_client_manager = Mock()
        mock_client_manager.health_check_all.return_value = {
            "primary": True,
            "development": False,
            "production": True
        }
        mock_get_client_manager.return_value = mock_client_manager
        
        result = health_check_servers()
        
        self.assertEqual(len(result), 3)
        self.assertTrue(result["primary"])
        self.assertFalse(result["development"])
        self.assertTrue(result["production"])


class TestServerRouting(unittest.TestCase):
    """Test server routing and context switching."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.multi_server_config = {
            'RUNDECK_URL': 'https://primary.rundeck.com',
            'RUNDECK_API_TOKEN': 'primary-token',
            'RUNDECK_NAME': 'primary',
            'RUNDECK_URL_1': 'https://dev.rundeck.com',
            'RUNDECK_API_TOKEN_1': 'dev-token',
            'RUNDECK_NAME_1': 'development',
        }
    
    @patch('rundeck_mcp.tools.projects.get_client')
    def test_tool_server_routing(self, mock_get_client):
        """Test that tools correctly route to specified servers."""
        mock_client = Mock()
        mock_client._make_request.return_value = [{"name": "test-project"}]
        mock_get_client.return_value = mock_client
        
        # Import after patching
        from rundeck_mcp.tools.projects import get_projects
        
        # Test routing to specific server
        get_projects(server="development")
        mock_get_client.assert_called_with("development")
        
        # Test default routing (no server specified)
        get_projects()
        mock_get_client.assert_called_with(None)
    
    @patch('rundeck_mcp.client.get_client_manager')
    def test_global_client_manager_singleton(self, mock_get_client_manager):
        """Test that global client manager is singleton."""
        from rundeck_mcp.client import get_client_manager
        
        # First call should create instance
        manager1 = get_client_manager()
        
        # Second call should return same instance
        manager2 = get_client_manager()
        
        self.assertIs(manager1, manager2)


if __name__ == '__main__':
    unittest.main()