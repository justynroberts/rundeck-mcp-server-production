"""Run competency tests against the MCP server."""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List
from unittest.mock import Mock, patch

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from rundeck_mcp.server import RundeckMCPServer
from rundeck_mcp.client import get_client_manager
from rundeck_mcp.tools import all_tools


class MCPServerEvaluator:
    """Evaluator for MCP server competency tests."""
    
    def __init__(self):
        """Initialize evaluator."""
        self.server = RundeckMCPServer(enable_write_tools=True)
        self.test_results = []
        self.mock_data = self._load_mock_data()
    
    def _load_mock_data(self) -> Dict[str, Any]:
        """Load mock data for testing."""
        return {
            "projects": [
                {"name": "webapp", "description": "Web application project"},
                {"name": "api", "description": "API service project"}
            ],
            "jobs": [
                {
                    "id": "job-123",
                    "name": "Deploy Application",
                    "project": "webapp",
                    "description": "Deploy web application",
                    "enabled": True,
                    "scheduled": True,
                    "workflow": [
                        {"type": "command", "description": "Stop service", "command": "sudo systemctl stop webapp"},
                        {"type": "script", "description": "Deploy code", "script": "deploy.sh"},
                        {"type": "command", "description": "Start service", "command": "sudo systemctl start webapp"}
                    ],
                    "options": [
                        {"name": "version", "required": True, "description": "Version to deploy"}
                    ],
                    "nodefilters": {"filter": "tags: production"}
                }
            ],
            "nodes": [
                {
                    "nodename": "web-01",
                    "hostname": "web-01.company.com",
                    "osName": "Linux",
                    "osVersion": "Ubuntu 20.04",
                    "tags": "production,webapp"
                },
                {
                    "nodename": "web-02",
                    "hostname": "web-02.company.com",
                    "osName": "Linux",
                    "osVersion": "Ubuntu 20.04",
                    "tags": "production,webapp"
                }
            ],
            "executions": [
                {
                    "id": "exec-456",
                    "job": {"id": "job-123"},
                    "project": "webapp",
                    "status": "succeeded",
                    "date-started": "2024-01-15T10:00:00Z",
                    "date-ended": "2024-01-15T10:05:00Z",
                    "duration": 300000,
                    "user": "admin"
                }
            ],
            "system_info": {
                "system": {
                    "rundeck": {
                        "version": "4.17.0",
                        "apiversion": "47",
                        "node": "rundeck-server",
                        "serverUUID": "12345678-1234-1234-1234-123456789012"
                    }
                }
            }
        }
    
    async def run_competency_tests(self) -> Dict[str, Any]:
        """Run comprehensive competency tests."""
        print("=== Running MCP Server Competency Tests ===")
        print()
        
        # Test categories
        test_categories = [
            ("Project Management", self._test_project_tools),
            ("Job Management", self._test_job_tools),
            ("Job Analysis", self._test_job_analysis),
            ("Node Management", self._test_node_tools),
            ("Execution Management", self._test_execution_tools),
            ("System Management", self._test_system_tools),
            ("Error Handling", self._test_error_handling),
            ("Tool Descriptions", self._test_tool_descriptions),
            ("Security Features", self._test_security_features),
        ]
        
        overall_results = {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "categories": {}
        }
        
        for category_name, test_func in test_categories:
            print(f"Testing {category_name}...")
            category_results = await test_func()
            overall_results["categories"][category_name] = category_results
            overall_results["total_tests"] += category_results["total"]
            overall_results["passed_tests"] += category_results["passed"]
            overall_results["failed_tests"] += category_results["failed"]
            
            status = "✅ PASS" if category_results["failed"] == 0 else "❌ FAIL"
            print(f"  {status} ({category_results['passed']}/{category_results['total']})")
        
        print()
        print("=== Test Summary ===")
        print(f"Total tests: {overall_results['total_tests']}")
        print(f"Passed: {overall_results['passed_tests']}")
        print(f"Failed: {overall_results['failed_tests']}")
        print(f"Success rate: {overall_results['passed_tests']/overall_results['total_tests']*100:.1f}%")
        
        return overall_results
    
    async def _test_project_tools(self) -> Dict[str, Any]:
        """Test project management tools."""
        results = {"total": 0, "passed": 0, "failed": 0, "details": []}
        
        with patch('rundeck_mcp.tools.projects.get_client') as mock_get_client:
            mock_client = Mock()
            mock_client._make_request.return_value = self.mock_data["projects"]
            mock_get_client.return_value = mock_client
            
            # Test get_projects
            try:
                from rundeck_mcp.tools.projects import get_projects
                result = get_projects()
                
                results["total"] += 1
                if len(result.response) == 2 and result.response[0].name == "webapp":
                    results["passed"] += 1
                    results["details"].append("✅ get_projects returns correct data")
                else:
                    results["failed"] += 1
                    results["details"].append("❌ get_projects returns incorrect data")
                    
            except Exception as e:
                results["total"] += 1
                results["failed"] += 1
                results["details"].append(f"❌ get_projects failed: {e}")
        
        return results
    
    async def _test_job_tools(self) -> Dict[str, Any]:
        """Test job management tools."""
        results = {"total": 0, "passed": 0, "failed": 0, "details": []}
        
        with patch('rundeck_mcp.tools.jobs.get_client') as mock_get_client:
            mock_client = Mock()
            mock_client._make_request.return_value = self.mock_data["jobs"]
            mock_get_client.return_value = mock_client
            
            # Test get_jobs
            try:
                from rundeck_mcp.tools.jobs import get_jobs
                result = get_jobs("webapp")
                
                results["total"] += 1
                if len(result.response) == 1 and result.response[0].name == "Deploy Application":
                    results["passed"] += 1
                    results["details"].append("✅ get_jobs returns correct data")
                else:
                    results["failed"] += 1
                    results["details"].append("❌ get_jobs returns incorrect data")
                    
            except Exception as e:
                results["total"] += 1
                results["failed"] += 1
                results["details"].append(f"❌ get_jobs failed: {e}")
        
        return results
    
    async def _test_job_analysis(self) -> Dict[str, Any]:
        """Test job analysis capabilities."""
        results = {"total": 0, "passed": 0, "failed": 0, "details": []}
        
        with patch('rundeck_mcp.tools.jobs.get_job_definition') as mock_get_job_def:
            from rundeck_mcp.models.rundeck import JobDefinition
            job_def = JobDefinition(**self.mock_data["jobs"][0])
            mock_get_job_def.return_value = job_def
            
            # Test analyze_job
            try:
                from rundeck_mcp.tools.jobs import analyze_job
                result = analyze_job("job-123")
                
                results["total"] += 1
                if result.job_id == "job-123" and result.risk_level in ["LOW", "MEDIUM", "HIGH"]:
                    results["passed"] += 1
                    results["details"].append("✅ analyze_job returns valid analysis")
                else:
                    results["failed"] += 1
                    results["details"].append("❌ analyze_job returns invalid analysis")
                    
            except Exception as e:
                results["total"] += 1
                results["failed"] += 1
                results["details"].append(f"❌ analyze_job failed: {e}")
            
            # Test visualize_job
            try:
                from rundeck_mcp.tools.jobs import visualize_job
                result = visualize_job("job-123")
                
                results["total"] += 1
                if result.job_id == "job-123" and "graph TD" in result.mermaid_diagram:
                    results["passed"] += 1
                    results["details"].append("✅ visualize_job returns valid visualization")
                else:
                    results["failed"] += 1
                    results["details"].append("❌ visualize_job returns invalid visualization")
                    
            except Exception as e:
                results["total"] += 1
                results["failed"] += 1
                results["details"].append(f"❌ visualize_job failed: {e}")
        
        return results
    
    async def _test_node_tools(self) -> Dict[str, Any]:
        """Test node management tools."""
        results = {"total": 0, "passed": 0, "failed": 0, "details": []}
        
        with patch('rundeck_mcp.tools.nodes.get_client') as mock_get_client:
            mock_client = Mock()
            mock_client._make_request.return_value = self.mock_data["nodes"]
            mock_get_client.return_value = mock_client
            
            # Test get_nodes
            try:
                from rundeck_mcp.tools.nodes import get_nodes
                result = get_nodes("webapp")
                
                results["total"] += 1
                if len(result.response) == 2 and result.response[0].name == "web-01":
                    results["passed"] += 1
                    results["details"].append("✅ get_nodes returns correct data")
                else:
                    results["failed"] += 1
                    results["details"].append("❌ get_nodes returns incorrect data")
                    
            except Exception as e:
                results["total"] += 1
                results["failed"] += 1
                results["details"].append(f"❌ get_nodes failed: {e}")
        
        return results
    
    async def _test_execution_tools(self) -> Dict[str, Any]:
        """Test execution management tools."""
        results = {"total": 0, "passed": 0, "failed": 0, "details": []}
        
        with patch('rundeck_mcp.tools.executions.get_client') as mock_get_client:
            mock_client = Mock()
            mock_client._make_request.return_value = {"executions": self.mock_data["executions"]}
            mock_get_client.return_value = mock_client
            
            # Test get_executions
            try:
                from rundeck_mcp.tools.executions import get_executions
                result = get_executions("webapp")
                
                results["total"] += 1
                if len(result.response) == 1 and result.response[0].id == "exec-456":
                    results["passed"] += 1
                    results["details"].append("✅ get_executions returns correct data")
                else:
                    results["failed"] += 1
                    results["details"].append("❌ get_executions returns incorrect data")
                    
            except Exception as e:
                results["total"] += 1
                results["failed"] += 1
                results["details"].append(f"❌ get_executions failed: {e}")
        
        return results
    
    async def _test_system_tools(self) -> Dict[str, Any]:
        """Test system management tools."""
        results = {"total": 0, "passed": 0, "failed": 0, "details": []}
        
        with patch('rundeck_mcp.tools.system.get_client') as mock_get_client:
            mock_client = Mock()
            mock_client._make_request.return_value = self.mock_data["system_info"]
            mock_get_client.return_value = mock_client
            
            # Test get_system_info
            try:
                from rundeck_mcp.tools.system import get_system_info
                result = get_system_info()
                
                results["total"] += 1
                if result.rundeck_version == "4.17.0" and result.api_version == "47":
                    results["passed"] += 1
                    results["details"].append("✅ get_system_info returns correct data")
                else:
                    results["failed"] += 1
                    results["details"].append("❌ get_system_info returns incorrect data")
                    
            except Exception as e:
                results["total"] += 1
                results["failed"] += 1
                results["details"].append(f"❌ get_system_info failed: {e}")
        
        return results
    
    async def _test_error_handling(self) -> Dict[str, Any]:
        """Test error handling capabilities."""
        results = {"total": 0, "passed": 0, "failed": 0, "details": []}
        
        with patch('rundeck_mcp.tools.projects.get_client') as mock_get_client:
            mock_client = Mock()
            mock_client._make_request.side_effect = Exception("Connection failed")
            mock_get_client.return_value = mock_client
            
            # Test error handling
            try:
                from rundeck_mcp.tools.projects import get_projects
                get_projects()
                
                results["total"] += 1
                results["failed"] += 1
                results["details"].append("❌ Error handling failed - no exception raised")
                
            except Exception as e:
                results["total"] += 1
                results["passed"] += 1
                results["details"].append("✅ Error handling works correctly")
        
        return results
    
    async def _test_tool_descriptions(self) -> Dict[str, Any]:
        """Test tool descriptions are clear and helpful."""
        results = {"total": 0, "passed": 0, "failed": 0, "details": []}
        
        from mcp.types import ListToolsRequest
        
        # Test tool listing
        try:
            mock_request = Mock(spec=ListToolsRequest)
            tools = await self.server._list_tools(mock_request)
            
            results["total"] += 1
            if len(tools) > 0:
                results["passed"] += 1
                results["details"].append(f"✅ Listed {len(tools)} tools")
            else:
                results["failed"] += 1
                results["details"].append("❌ No tools listed")
            
            # Check tool descriptions
            for tool in tools[:5]:  # Check first 5 tools
                results["total"] += 1
                if tool.description and len(tool.description) > 10:
                    results["passed"] += 1
                    results["details"].append(f"✅ Tool {tool.name} has good description")
                else:
                    results["failed"] += 1
                    results["details"].append(f"❌ Tool {tool.name} has poor description")
                    
        except Exception as e:
            results["total"] += 1
            results["failed"] += 1
            results["details"].append(f"❌ Tool listing failed: {e}")
        
        return results
    
    async def _test_security_features(self) -> Dict[str, Any]:
        """Test security features."""
        results = {"total": 0, "passed": 0, "failed": 0, "details": []}
        
        # Test write tools are disabled by default
        server_readonly = RundeckMCPServer(enable_write_tools=False)
        
        try:
            from mcp.types import ListToolsRequest
            mock_request = Mock(spec=ListToolsRequest)
            tools = await server_readonly._list_tools(mock_request)
            
            write_tools = [tool for tool in tools if not tool.annotations.readOnlyHint]
            
            results["total"] += 1
            if len(write_tools) == 0:
                results["passed"] += 1
                results["details"].append("✅ Write tools disabled by default")
            else:
                results["failed"] += 1
                results["details"].append(f"❌ {len(write_tools)} write tools enabled by default")
                
        except Exception as e:
            results["total"] += 1
            results["failed"] += 1
            results["details"].append(f"❌ Security test failed: {e}")
        
        # Test write tools are enabled when requested
        try:
            from mcp.types import ListToolsRequest
            mock_request = Mock(spec=ListToolsRequest)
            tools = await self.server._list_tools(mock_request)
            
            write_tools = [tool for tool in tools if not tool.annotations.readOnlyHint]
            
            results["total"] += 1
            if len(write_tools) > 0:
                results["passed"] += 1
                results["details"].append(f"✅ {len(write_tools)} write tools enabled when requested")
            else:
                results["failed"] += 1
                results["details"].append("❌ No write tools enabled when requested")
                
        except Exception as e:
            results["total"] += 1
            results["failed"] += 1
            results["details"].append(f"❌ Write tools test failed: {e}")
        
        return results


async def main():
    """Main function to run evaluations."""
    # Set up environment for testing
    os.environ['RUNDECK_URL'] = 'https://test.rundeck.com'
    os.environ['RUNDECK_API_TOKEN'] = 'test-token'
    
    evaluator = MCPServerEvaluator()
    results = await evaluator.run_competency_tests()
    
    # Save results
    results_file = Path("test_results.json")
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\\nResults saved to: {results_file}")
    
    # Return exit code based on results
    if results["failed_tests"] > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    asyncio.run(main())