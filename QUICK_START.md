# Quick Start Guide

Get up and running with the Rundeck MCP Server in 5 minutes.

## 🚀 Quick Installation

### Option 1: Using pip (Recommended)
```bash
pip install rundeck-mcp-server
```

### Option 2: From Source
```bash
git clone https://github.com/your-username/rundeck-mcp-server.git
cd rundeck-mcp-server
pip install -e .
```

## 🔧 Quick Configuration

### 1. Set Environment Variables
```bash
export RUNDECK_URL="https://your-rundeck-server.com"
export RUNDECK_API_TOKEN="your-api-token"
```

### 2. Test Connection
```bash
rundeck-mcp validate
```

### 3. Generate Configuration
```bash
python tests/get_claude_config.py
```

## 📱 Claude Desktop Setup

### 1. Install Configuration
Copy the configuration to your Claude Desktop config file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
**Linux**: `~/.config/claude/claude_desktop_config.json`

### 2. Development Mode (Read-only)
```json
{
  "mcpServers": {
    "rundeck-mcp": {
      "command": "uvx",
      "args": ["rundeck-mcp-server", "serve"],
      "env": {
        "RUNDECK_URL": "https://your-rundeck-server.com",
        "RUNDECK_API_TOKEN": "your-api-token"
      }
    }
  }
}
```

### 3. Production Mode (Read-write)
```json
{
  "mcpServers": {
    "rundeck-mcp": {
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

### 4. Restart Claude Desktop
Quit and restart Claude Desktop to load the new configuration.

## 🔍 VS Code Setup

### 1. Install MCP Extension
1. Open VS Code
2. Go to Extensions (Ctrl+Shift+X)
3. Search for "MCP" and install

### 2. Configure Workspace
Create `.vscode/settings.json`:
```json
{
  "mcp.servers": {
    "rundeck-mcp": {
      "type": "stdio",
      "command": "uvx",
      "args": ["rundeck-mcp-server", "serve"],
      "env": {
        "RUNDECK_URL": "https://your-rundeck-server.com",
        "RUNDECK_API_TOKEN": "your-api-token"
      }
    }
  }
}
```

## ✅ Quick Test

Try these commands in Claude Desktop:

```
Can you list all Rundeck projects?
```

```
Show me the jobs in the 'production' project
```

```
What's the health status of all configured servers?
```

## 🛠️ Development Commands

```bash
# Start development server
make serve

# Run tests
make test

# Generate configurations
make configure-claude

# Run quality checks
make check
```

## 🔐 Security Notes

- **Read-only by default**: Write operations require `--enable-write-tools`
- **Environment variables**: Never commit API tokens to version control
- **Separate environments**: Use different tokens for dev/staging/production

## 📚 Next Steps

- Read the [Deployment Guide](DEPLOYMENT_GUIDE.md) for detailed setup
- Check [CLAUDE.md](CLAUDE.md) for development guidance
- Review [SECURITY.md](SECURITY.md) for security best practices
- See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines

## 🆘 Need Help?

- **Issues**: https://github.com/your-username/rundeck-mcp-server/issues
- **Security**: security@your-domain.com
- **Documentation**: All guides are in the repository root

## 🎯 Common Use Cases

### Monitor Job Executions
```
Show me recent job executions in the production project
```

### Analyze Job Risk
```
Can you analyze the risk level of job ID 'deploy-prod-123'?
```

### Infrastructure Overview
```
Give me a summary of all nodes in the production environment
```

### System Health Check
```
What's the current system status across all Rundeck servers?
```

That's it! You're ready to automate Rundeck operations through AI assistants. 🎉