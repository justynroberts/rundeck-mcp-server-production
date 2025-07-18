"""Test server connectivity and basic functionality."""

import unittest
from unittest.mock import Mock, patch, MagicMock
import os
import asyncio

from rundeck_mcp.client import RundeckClient, ClientManager
from rundeck_mcp.server import RundeckMCPServer


class TestRundeckClient(unittest.TestCase):
    """Test cases for RundeckClient."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.client = RundeckClient(
            base_url="https://test.rundeck.com",
            api_token="test-token",
            name="test-server"
        )
    
    def test_client_initialization(self):
        """Test client initialization."""
        self.assertEqual(self.client.base_url, "https://test.rundeck.com")
        self.assertEqual(self.client.api_token, "test-token")
        self.assertEqual(self.client.name, "test-server")
        self.assertEqual(self.client.api_version, "47")
    
    @patch('rundeck_mcp.client.requests.Session')
    def test_make_request_success(self, mock_session):
        """Test successful API request."""
        mock_response = Mock()
        mock_response.json.return_value = {"test": "data"}
        mock_response.content = b'{"test": "data"}'
        mock_session.return_value.request.return_value = mock_response
        
        result = self.client._make_request('GET', 'test-endpoint')
        self.assertEqual(result, {"test": "data"})
    
    @patch('rundeck_mcp.client.requests.Session')
    def test_make_request_empty_response(self, mock_session):
        """Test handling of empty response."""
        mock_response = Mock()
        mock_response.content = b''
        mock_session.return_value.request.return_value = mock_response
        
        result = self.client._make_request('GET', 'test-endpoint')
        self.assertEqual(result, {})
    
    @patch('rundeck_mcp.client.requests.Session')
    def test_health_check_success(self, mock_session):
        """Test successful health check."""
        mock_response = Mock()
        mock_response.json.return_value = {"system": {"rundeck": {"version": "4.0.0"}}}
        mock_response.content = b'{"system": {"rundeck": {"version": "4.0.0"}}}'
        mock_session.return_value.request.return_value = mock_response
        
        result = self.client.health_check()
        self.assertTrue(result)
    
    @patch('rundeck_mcp.client.requests.Session')
    def test_health_check_failure(self, mock_session):
        """Test failed health check."""
        mock_session.return_value.request.side_effect = Exception("Connection failed")
        
        result = self.client.health_check()
        self.assertFalse(result)


class TestClientManager(unittest.TestCase):
    """Test cases for ClientManager."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock environment variables
        self.env_patcher = patch.dict(os.environ, {
            'RUNDECK_URL': 'https://primary.rundeck.com',
            'RUNDECK_API_TOKEN': 'primary-token',
            'RUNDECK_NAME': 'primary-server',
            'RUNDECK_URL_1': 'https://secondary.rundeck.com',
            'RUNDECK_API_TOKEN_1': 'secondary-token',
            'RUNDECK_NAME_1': 'secondary-server'
        })
        self.env_patcher.start()
        
        self.client_manager = ClientManager()
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.env_patcher.stop()
    
    def test_load_primary_client(self):
        """Test loading primary client."""
        client = self.client_manager.get_client()
        self.assertEqual(client.name, "primary-server")
        self.assertEqual(client.base_url, "https://primary.rundeck.com")
    
    def test_load_additional_client(self):
        """Test loading additional client."""
        client = self.client_manager.get_client("secondary-server")
        self.assertEqual(client.name, "secondary-server")
        self.assertEqual(client.base_url, "https://secondary.rundeck.com")
    
    def test_get_nonexistent_client(self):
        """Test getting nonexistent client."""
        with self.assertRaises(ValueError):
            self.client_manager.get_client("nonexistent-server")
    
    def test_list_servers(self):
        """Test listing servers."""
        servers = self.client_manager.list_servers()
        self.assertEqual(len(servers), 2)
        
        server_names = [server.name for server in servers]
        self.assertIn("primary-server", server_names)
        self.assertIn("secondary-server", server_names)


class TestRundeckMCPServer(unittest.TestCase):
    """Test cases for RundeckMCPServer."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.server = RundeckMCPServer(enable_write_tools=False)
    
    def test_server_initialization(self):
        """Test server initialization."""
        self.assertFalse(self.server.enable_write_tools)
        self.assertIsNotNone(self.server.server)
        self.assertIsNotNone(self.server.tool_prompts)
    
    def test_server_initialization_with_write_tools(self):
        """Test server initialization with write tools enabled."""
        server = RundeckMCPServer(enable_write_tools=True)
        self.assertTrue(server.enable_write_tools)
    
    @patch('rundeck_mcp.server.get_client_manager')
    async def test_list_tools_read_only(self, mock_get_client_manager):
        """Test listing tools in read-only mode."""
        mock_request = Mock()
        tools = await self.server._list_tools(mock_request)
        
        # Should only include read tools
        tool_names = [tool.name for tool in tools]
        self.assertIn("get_projects", tool_names)
        self.assertIn("get_jobs", tool_names)
        self.assertNotIn("run_job", tool_names)  # Write tool should not be included
    
    @patch('rundeck_mcp.server.get_client_manager')
    async def test_list_tools_with_write_tools(self, mock_get_client_manager):
        """Test listing tools with write tools enabled."""
        server = RundeckMCPServer(enable_write_tools=True)
        mock_request = Mock()
        tools = await server._list_tools(mock_request)
        
        # Should include both read and write tools
        tool_names = [tool.name for tool in tools]
        self.assertIn("get_projects", tool_names)
        self.assertIn("get_jobs", tool_names)
        self.assertIn("run_job", tool_names)  # Write tool should be included
    
    @patch('rundeck_mcp.tools.projects.get_client')
    async def test_call_tool_success(self, mock_get_client):
        """Test successful tool call."""
        # Mock the client and response
        mock_client = Mock()
        mock_client._make_request.return_value = [{"name": "test-project"}]
        mock_get_client.return_value = mock_client
        
        # Create mock request
        mock_request = Mock()
        mock_request.params.name = "get_projects"
        mock_request.params.arguments = {}
        
        result = await self.server._call_tool(mock_request)
        self.assertFalse(result.isError)
        self.assertEqual(len(result.content), 1)
    
    async def test_call_tool_unknown_tool(self):
        """Test calling unknown tool."""
        mock_request = Mock()
        mock_request.params.name = "unknown_tool"
        mock_request.params.arguments = {}
        
        result = await self.server._call_tool(mock_request)
        self.assertTrue(result.isError)
        self.assertIn("Unknown tool", result.content[0].text)
    
    async def test_call_tool_write_tool_disabled(self):
        """Test calling write tool when disabled."""
        mock_request = Mock()
        mock_request.params.name = "run_job"
        mock_request.params.arguments = {}
        
        result = await self.server._call_tool(mock_request)
        self.assertTrue(result.isError)
        self.assertIn("Write tool", result.content[0].text)
        self.assertIn("disabled", result.content[0].text)


if __name__ == '__main__':
    unittest.main()