# Deployment Guide: Claude Code & Visual Studio Code

This guide covers deploying the Rundeck MCP Server in both Claude Code and Visual Studio Code environments.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Claude Code Deployment](#claude-code-deployment)
3. [Visual Studio Code Deployment](#visual-studio-code-deployment)
4. [Configuration Management](#configuration-management)
5. [Troubleshooting](#troubleshooting)
6. [Best Practices](#best-practices)

## Prerequisites

### System Requirements
- Python 3.12 or higher
- Internet connection for package installation
- Access to Rundeck server(s)
- Valid Rundeck API token(s)

### Required Information
- **Rundeck Server URL**: `https://your-rundeck-server.com`
- **API Token**: Generate from Rundeck → User Profile → API Tokens
- **API Version**: Usually `47` (latest) or your server's supported version

## Claude Code Deployment

Claude Code uses the Model Context Protocol (MCP) for server integration.

### Method 1: Using uvx (Recommended)

#### Step 1: Install the Package
```bash
# Install via pip first
pip install rundeck-mcp-server

# Or install from source
git clone https://github.com/your-username/rundeck-mcp-server.git
cd rundeck-mcp-server
pip install -e .
```

#### Step 2: Generate Configuration
```bash
# Generate Claude Desktop configurations
python tests/get_claude_config.py
```

This creates configuration files in `config_examples/`:
- `claude_desktop_development.json` (read-only)
- `claude_desktop_production.json` (read-write)

#### Step 3: Configure Claude Desktop

**Location of config file:**
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/claude/claude_desktop_config.json`

**Development Configuration (Read-only):**
```json
{
  "mcpServers": {
    "rundeck-mcp": {
      "command": "uvx",
      "args": ["rundeck-mcp-server", "serve"],
      "env": {
        "RUNDECK_URL": "https://your-rundeck-server.com",
        "RUNDECK_API_TOKEN": "your-api-token",
        "RUNDECK_API_VERSION": "47",
        "RUNDECK_NAME": "production"
      }
    }
  }
}
```

**Production Configuration (Read-write):**
```json
{
  "mcpServers": {
    "rundeck-mcp": {
      "command": "uvx",
      "args": ["rundeck-mcp-server", "serve", "--enable-write-tools"],
      "env": {
        "RUNDECK_URL": "https://your-rundeck-server.com",
        "RUNDECK_API_TOKEN": "your-api-token",
        "RUNDECK_API_VERSION": "47",
        "RUNDECK_NAME": "production"
      }
    }
  }
}
```

#### Step 4: Multi-Server Configuration

For multiple Rundeck environments:

```json
{
  "mcpServers": {
    "rundeck-mcp": {
      "command": "uvx",
      "args": ["rundeck-mcp-server", "serve", "--enable-write-tools"],
      "env": {
        "RUNDECK_URL": "https://prod.rundeck.com",
        "RUNDECK_API_TOKEN": "prod-token",
        "RUNDECK_NAME": "production",
        "RUNDECK_URL_1": "https://dev.rundeck.com",
        "RUNDECK_API_TOKEN_1": "dev-token",
        "RUNDECK_NAME_1": "development",
        "RUNDECK_URL_2": "https://staging.rundeck.com",
        "RUNDECK_API_TOKEN_2": "staging-token",
        "RUNDECK_NAME_2": "staging"
      }
    }
  }
}
```

### Method 2: Direct Python Execution

If you prefer direct Python execution:

```json
{
  "mcpServers": {
    "rundeck-mcp": {
      "command": "/usr/local/bin/python3",
      "args": ["-m", "rundeck_mcp", "serve"],
      "env": {
        "RUNDECK_URL": "https://your-rundeck-server.com",
        "RUNDECK_API_TOKEN": "your-api-token"
      }
    }
  }
}
```

### Step 5: Restart Claude Desktop

After updating the configuration:
1. Quit Claude Desktop completely
2. Restart Claude Desktop
3. The MCP server should connect automatically

### Step 6: Verify Connection

In Claude Desktop, try these commands:
```
Can you list the available Rundeck servers?
```

```
Show me all projects in Rundeck
```

```
What tools are available for Rundeck management?
```

## Visual Studio Code Deployment

VS Code uses MCP through extensions and workspace configuration.

### Method 1: MCP Extension (Recommended)

#### Step 1: Install MCP Extension
1. Open VS Code
2. Go to Extensions (Ctrl+Shift+X)
3. Search for "MCP" or "Model Context Protocol"
4. Install the MCP extension

#### Step 2: Configure Workspace

Create `.vscode/settings.json` in your workspace:

```json
{
  "mcp.servers": {
    "rundeck-mcp": {
      "type": "stdio",
      "command": "uvx",
      "args": ["rundeck-mcp-server", "serve"],
      "env": {
        "RUNDECK_URL": "https://your-rundeck-server.com",
        "RUNDECK_API_TOKEN": "your-api-token",
        "RUNDECK_API_VERSION": "47"
      }
    }
  }
}
```

#### Step 3: Enable Write Operations (Optional)

For write operations, add the flag:

```json
{
  "mcp.servers": {
    "rundeck-mcp": {
      "type": "stdio",
      "command": "uvx",
      "args": ["rundeck-mcp-server", "serve", "--enable-write-tools"],
      "env": {
        "RUNDECK_URL": "https://your-rundeck-server.com",
        "RUNDECK_API_TOKEN": "your-api-token"
      }
    }
  }
}
```

### Method 2: Manual Integration

#### Step 1: Create Integration Script

Create `scripts/vscode-mcp-integration.py`:

```python
#!/usr/bin/env python3
"""VS Code MCP integration script."""

import subprocess
import sys
import os

def main():
    """Start MCP server for VS Code."""
    # Set environment variables
    os.environ['RUNDECK_URL'] = 'https://your-rundeck-server.com'
    os.environ['RUNDECK_API_TOKEN'] = 'your-api-token'
    
    # Start the server
    cmd = [sys.executable, '-m', 'rundeck_mcp', 'serve']
    subprocess.run(cmd)

if __name__ == '__main__':
    main()
```

#### Step 2: Configure VS Code Task

Add to `.vscode/tasks.json`:

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Start Rundeck MCP Server",
      "type": "shell",
      "command": "python",
      "args": ["scripts/vscode-mcp-integration.py"],
      "group": "build",
      "presentation": {
        "echo": true,
        "reveal": "always",
        "focus": false,
        "panel": "shared"
      },
      "problemMatcher": []
    }
  ]
}
```

#### Step 3: Create Launch Configuration

Add to `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Rundeck MCP Server",
      "type": "python",
      "request": "launch",
      "module": "rundeck_mcp",
      "args": ["serve", "--enable-write-tools"],
      "env": {
        "RUNDECK_URL": "https://your-rundeck-server.com",
        "RUNDECK_API_TOKEN": "your-api-token"
      },
      "console": "integratedTerminal"
    }
  ]
}
```

## Configuration Management

### Environment Variables

Create `.env` file in your project (never commit this):

```bash
# Primary Rundeck server
RUNDECK_URL=https://your-rundeck-server.com
RUNDECK_API_TOKEN=your-api-token
RUNDECK_API_VERSION=47
RUNDECK_NAME=production

# Additional servers (optional)
RUNDECK_URL_1=https://dev.rundeck.com
RUNDECK_API_TOKEN_1=dev-token
RUNDECK_NAME_1=development

RUNDECK_URL_2=https://staging.rundeck.com
RUNDECK_API_TOKEN_2=staging-token
RUNDECK_NAME_2=staging
```

### Configuration Templates

Use the configuration generator:

```bash
# Generate all configuration templates
python tests/get_claude_config.py

# This creates:
# - config_examples/claude_desktop_development.json
# - config_examples/claude_desktop_production.json
# - config_examples/vs_code_development.json
# - config_examples/vs_code_production.json
# - config_examples/uvx_development.json
# - config_examples/uvx_production.json
```

### Validation

Always validate your configuration:

```bash
# Validate configuration
rundeck-mcp validate

# Test server connectivity
rundeck-mcp info
```

## Troubleshooting

### Common Issues

#### 1. Server Not Starting

**Symptoms**: MCP server fails to start
**Solutions**:
```bash
# Check Python version
python --version  # Should be 3.12+

# Check installation
pip show rundeck-mcp-server

# Test manual start
rundeck-mcp serve --log-level DEBUG
```

#### 2. Authentication Errors

**Symptoms**: "Authentication failed" errors
**Solutions**:
```bash
# Test API token
curl -H "X-Rundeck-Auth-Token: your-token" https://your-rundeck-server.com/api/47/system/info

# Check token permissions in Rundeck
# User Profile → API Tokens → Permissions
```

#### 3. Connection Timeouts

**Symptoms**: Connection timeout errors
**Solutions**:
```bash
# Test network connectivity
ping your-rundeck-server.com

# Check firewall/proxy settings
# Verify HTTPS certificate
```

#### 4. Tools Not Available

**Symptoms**: "Tool not found" errors
**Solutions**:
```bash
# Check tool listing
rundeck-mcp info

# Verify write tools are enabled
rundeck-mcp serve --enable-write-tools
```

#### 5. Configuration Not Loading

**Symptoms**: Server starts but configuration ignored
**Solutions**:
```bash
# Check config file location
# macOS: ~/Library/Application Support/Claude/claude_desktop_config.json
# Windows: %APPDATA%\Claude\claude_desktop_config.json
# Linux: ~/.config/claude/claude_desktop_config.json

# Validate JSON syntax
python -m json.tool claude_desktop_config.json
```

### Debug Mode

Enable debug logging:

```bash
# Start with debug logging
rundeck-mcp serve --log-level DEBUG

# Or set environment variable
export LOG_LEVEL=DEBUG
rundeck-mcp serve
```

### Health Checks

Monitor server health:

```bash
# Check all servers
rundeck-mcp validate

# Get system info
rundeck-mcp info

# Test specific server
python -c "
from rundeck_mcp.client import get_client
client = get_client('production')
print(client.health_check())
"
```

## Best Practices

### Security

1. **Use Read-Only Mode by Default**
   ```json
   "args": ["rundeck-mcp-server", "serve"]
   ```

2. **Enable Write Operations Only When Needed**
   ```json
   "args": ["rundeck-mcp-server", "serve", "--enable-write-tools"]
   ```

3. **Use Environment Variables for Secrets**
   ```json
   "env": {
     "RUNDECK_API_TOKEN": "${RUNDECK_API_TOKEN}"
   }
   ```

4. **Separate Development and Production Configs**
   - Use different API tokens
   - Use different server names
   - Limit production access

### Performance

1. **Connection Pooling**
   - Server automatically pools connections
   - Reuses sessions for better performance

2. **Caching**
   - Server caches client instances
   - Reduces connection overhead

3. **Timeout Configuration**
   - Default 30-second timeout
   - Adjust based on network conditions

### Monitoring

1. **Log Monitoring**
   ```bash
   # Monitor server logs
   tail -f ~/.local/share/claude/logs/mcp-server.log
   ```

2. **Health Checks**
   ```bash
   # Regular health checks
   rundeck-mcp validate
   ```

3. **Performance Metrics**
   - Monitor API response times
   - Track error rates
   - Monitor resource usage

### Development Workflow

1. **Local Development**
   ```bash
   # Start development server
   make serve
   
   # Run tests
   make test
   
   # Generate configurations
   make configure-claude
   ```

2. **Testing**
   ```bash
   # Test server connection
   make test-server
   
   # Test multi-server setup
   make test-multi
   
   # Run competency tests
   make test-evals
   ```

3. **Code Quality**
   ```bash
   # Run all quality checks
   make check
   
   # Format code
   make format
   
   # Run linting
   make lint
   ```

## Advanced Configuration

### Custom Tool Prompts

Modify `tool_prompts.json` to customize tool descriptions:

```json
{
  "get_projects": {
    "description": "Custom description for project listing",
    "prompt": "Enhanced prompt for AI assistants"
  }
}
```

### Multi-Environment Setup

Use different configurations for different environments:

```bash
# Development
RUNDECK_ENV=development rundeck-mcp serve

# Production
RUNDECK_ENV=production rundeck-mcp serve --enable-write-tools
```

### Custom Error Handling

Configure custom error handling:

```python
# In your configuration
import logging
logging.getLogger('rundeck_mcp').setLevel(logging.DEBUG)
```

## Support

For additional support:

- **Documentation**: Check CLAUDE.md and CONTRIBUTING.md
- **Issues**: Report at https://github.com/your-username/rundeck-mcp-server/issues
- **Security**: Email security@your-domain.com for security issues
- **Community**: Join discussions on GitHub

## Changelog

### Version 1.0.0
- Initial deployment guide
- Claude Code integration
- Visual Studio Code integration
- Multi-server support
- Comprehensive troubleshooting