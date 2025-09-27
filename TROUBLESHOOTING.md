# Troubleshooting Guide

This document provides solutions to common issues encountered when setting up and running the Rundeck MCP Server.

## Table of Contents

- [MCP Protocol Issues](#mcp-protocol-issues)
- [Claude Desktop Integration](#claude-desktop-integration)
- [Server Startup Problems](#server-startup-problems)
- [Tool Visibility Issues](#tool-visibility-issues)
- [uvx Configuration](#uvx-configuration)
- [Environment Variables](#environment-variables)

## MCP Protocol Issues

### "Invalid request parameters" Error

**Symptoms:**
- Server starts successfully but tools/list requests fail
- Error message: `{"code": -32602, "message": "Invalid request parameters"}`

**Root Cause:**
MCP library version compatibility issues with handler function signatures.

**Solution:**
Ensure handler functions use the correct signature pattern:

```python
@server.list_tools()
async def list_tools():  # NO PARAMETERS
    """List available tools"""
    return tools

@server.call_tool()
async def call_tool(name: str, arguments: dict = None):  # Standard parameters
    """Call a tool"""
    # Implementation
```

**Important Notes:**
- MCP 1.8.0 - 1.12.0: Use no parameters for `list_tools()`
- MCP 1.15.0+: Attempted to use `ListToolsRequest` parameter but had compatibility issues
- Always use `server.create_initialization_options()` for server.run()

### Handler Signature Evolution

**Historical Changes:**
1. **MCP 1.8.0**: Simple handler signatures with no parameters
2. **MCP 1.12.0**: Same pattern, stable
3. **MCP 1.15.0**: Introduced typed request objects but broke compatibility

**Working Pattern (MCP 1.8.0 - 1.12.0):**
```python
# server_working.py implementation
async def main_working(enable_write_tools: bool = False):
    server = Server("rundeck-mcp-server")

    @server.list_tools()
    async def list_tools():  # Critical: NO parameters
        # Generate tools dynamically
        return tools

    @server.call_tool()
    async def call_tool(name: str, arguments: dict = None):
        # Handle tool execution
        return results
```

## Claude Desktop Integration

### Tools Not Appearing in Claude Desktop

**Symptoms:**
- Server process starts successfully
- No Rundeck tools visible in Claude Desktop interface
- No error messages in logs

**Troubleshooting Steps:**

1. **Verify MCP Server Process:**
   ```bash
   ps aux | grep -E "(rundeck|claude)" | grep -v grep
   ```

2. **Test MCP Protocol Manually:**
   ```bash
   echo '{"jsonrpc": "2.0", "method": "tools/list", "id": 1}' | \
   uvx --from /path/to/project rundeck-mcp serve --no-validate-config
   ```

3. **Check Claude Desktop Configuration:**
   - Location: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Verify command path and arguments
   - Ensure environment variables are set

### Configuration Validation

**Working uvx Configuration:**
```json
{
  "mcpServers": {
    "rundeck-mcp": {
      "command": "uvx",
      "args": [
        "--from", "/path/to/rundeck-mcp-server-production",
        "rundeck-mcp", "serve", "--enable-write-tools"
      ],
      "env": {
        "RUNDECK_URL": "https://your-rundeck-server",
        "RUNDECK_API_TOKEN": "your-api-token",
        "RUNDECK_API_VERSION": "47",
        "RUNDECK_NAME": "server-name"
      }
    }
  }
}
```

## Server Startup Problems

### ModuleNotFoundError Issues

**Symptoms:**
```
ImportError: cannot import name 'function_name' from 'rundeck_mcp.tools'
```

**Solutions:**
1. **Verify Installation:**
   ```bash
   uvx --from /path/to/project rundeck-mcp --help
   ```

2. **Check Tool Imports:**
   ```python
   # Use organized imports from __init__.py
   from rundeck_mcp.tools import read_tools, write_tools
   ```

3. **Validate Environment:**
   ```bash
   uvx --from /path/to/project rundeck-mcp validate
   ```

### Python Version Compatibility

**Error:**
```
ERROR: Package 'rundeck-mcp-server' requires a different Python: 3.13.5 not in '<3.13,>=3.12'
```

**Solution:**
Update `pyproject.toml`:
```toml
requires-python = ">=3.12"  # Remove upper bound
```

### Missing Dependencies

**Error:**
```
ModuleNotFoundError: No module named 'typer'
```

**Solution:**
```bash
# Clean installation
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Tool Visibility Issues

### Expected vs Actual Tool Count

**Expected:** 30+ tools across categories:
- **Project Tools:** get_projects, get_project_stats
- **Job Tools:** get_jobs, get_job_definition, analyze_job, visualize_job, run_job, etc.
- **Execution Tools:** get_execution_status, get_execution_output, etc.
- **Node Tools:** get_nodes, get_node_details, get_node_summary
- **System Tools:** list_servers, health_check_servers, get_system_info
- **Analytics Tools:** get_execution_metrics, calculate_job_roi

**Diagnostic Commands:**
```bash
# Count available tools
uvx --from /path/to/project rundeck-mcp serve --no-validate-config 2>/dev/null | \
python3 -c "
import json, sys
for line in sys.stdin:
    if 'tools' in line:
        data = json.loads(line)
        if 'result' in data:
            print(f'Tools found: {len(data[\"result\"][\"tools\"])}')
            break
"
```

### Tool Categories and Organization

**Read Tools (Always Available):**
- Project management and statistics
- Job analysis and visualization
- Execution monitoring
- Node inventory
- System health checks
- Analytics and reporting

**Write Tools (Require --enable-write-tools):**
- Job execution and control
- Execution management (abort, retry, delete)
- Job state changes (enable/disable)
- System configuration changes

## uvx Configuration

### uvx vs Direct Python Execution

**uvx Advantages:**
- Automatic dependency management
- Isolated execution environment
- Version consistency
- Matches git repository patterns

**Working uvx Pattern:**
```bash
uvx --from /path/to/rundeck-mcp-server-production rundeck-mcp serve --enable-write-tools
```

**Alternative Direct Execution:**
```bash
/path/to/project/.venv/bin/python -m rundeck_mcp serve --enable-write-tools
```

### Command Line Options

```bash
# Basic server (read-only)
uvx --from /path/to/project rundeck-mcp serve

# Full server (read-write)
uvx --from /path/to/project rundeck-mcp serve --enable-write-tools

# Skip configuration validation
uvx --from /path/to/project rundeck-mcp serve --no-validate-config

# Debug mode
uvx --from /path/to/project rundeck-mcp serve --log-level DEBUG
```

## Environment Variables

### Required Variables

**Primary Server:**
- `RUNDECK_URL`: Rundeck server URL
- `RUNDECK_API_TOKEN`: API authentication token

**Optional Variables:**
- `RUNDECK_API_VERSION`: API version (default: "47")
- `RUNDECK_NAME`: Server identifier

### Multi-Server Configuration

**Pattern:** Add `_N` suffix for additional servers (N = 1,2,3...):

```bash
# Server 1
RUNDECK_URL_1=https://demo.runbook.pagerduty.cloud
RUNDECK_API_TOKEN_1=token1
RUNDECK_API_VERSION_1=47
RUNDECK_NAME_1=demo

# Server 2
RUNDECK_URL_2=http://server2:4440
RUNDECK_API_TOKEN_2=token2
RUNDECK_API_VERSION_2=47
RUNDECK_NAME_2=production
```

### Environment Validation

```bash
# Test configuration
uvx --from /path/to/project rundeck-mcp validate

# Generate configurations
python tests/get_claude_config.py
```

## Common Resolution Steps

### Complete Reset Procedure

1. **Clean Environment:**
   ```bash
   rm -rf .venv
   rm -f /tmp/test_*.py /tmp/debug_*.py /tmp/fixed_*.py
   ```

2. **Fresh Installation:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -e .
   ```

3. **Validate Setup:**
   ```bash
   uvx --from $(pwd) rundeck-mcp validate
   ```

4. **Test MCP Protocol:**
   ```bash
   echo '{"jsonrpc": "2.0", "method": "initialize", "id": 1, "params": {"protocolVersion": "2024-11-05", "capabilities": {"tools": {}}, "clientInfo": {"name": "test", "version": "1.0"}}}' | \
   uvx --from $(pwd) rundeck-mcp serve --no-validate-config
   ```

5. **Update Claude Desktop Config:**
   - Use uvx command pattern
   - Verify environment variables
   - Restart Claude Desktop

### Verification Checklist

- [ ] uvx command works: `uvx --from /path/to/project rundeck-mcp --help`
- [ ] Server starts: `uvx --from /path/to/project rundeck-mcp serve --no-validate-config`
- [ ] Tools list: Manual MCP protocol test returns tool list
- [ ] Claude Desktop config: Proper uvx configuration
- [ ] Environment: All required variables set
- [ ] Tool count: 30+ tools visible in Claude Desktop

## Getting Help

If issues persist after following this guide:

1. **Check Recent Commits:** `git log --oneline -5`
2. **Review Working Commits:** Look for "Fix" or "Working" in commit messages
3. **Test Minimal Configuration:** Start with basic uvx setup
4. **Validate Each Component:** Test uvx, server startup, MCP protocol separately

## Version History

- **v1.0.0**: Initial MCP server implementation
- **Latest**: Fixed MCP 1.15.0 compatibility issues, restored uvx configuration