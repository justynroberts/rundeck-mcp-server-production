# Rundeck MCP Server

A production-ready MCP (Model Context Protocol) server for Rundeck automation platform. Manage projects, jobs, executions, and infrastructure directly from Claude Desktop or any MCP-enabled client.

## 🚀 Quick Start

### 1. Install uvx

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or using Homebrew
brew install uv

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2. Get Your Rundeck API Token

1. Log into your Rundeck server
2. Click your username → **Profile**
3. Navigate to **User API Tokens**
4. Click **Generate New Token**
5. Copy and save the token securely

### 3. Configure Claude Desktop

Edit `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "rundeck-mcp": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/yourusername/rundeck-mcp-server",
        "rundeck-mcp",
        "serve",
        "--enable-write-tools"
      ],
      "env": {
        "RUNDECK_URL": "https://your-rundeck.com",
        "RUNDECK_API_TOKEN": "your-token-here"
      }
    }
  }
}
```

### 4. Restart Claude Desktop

That's it! You can now manage Rundeck from Claude Desktop.

## 💡 Features

- **30+ Tools** for complete Rundeck automation
- **Multi-Server Support** - Connect to multiple Rundeck instances
- **Read-Only Mode** - Safe exploration without modifications
- **Write Operations** - Create jobs, run executions, manage projects
- **Intelligent Job Creation** - Automatic variable extraction and step splitting
- **Job Analysis** - Risk assessment and workflow visualization

## 🔧 Advanced Configuration

### Multiple Rundeck Servers

```json
{
  "mcpServers": {
    "rundeck-mcp": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/yourusername/rundeck-mcp-server", "rundeck-mcp", "serve", "--enable-write-tools"],
      "env": {
        "RUNDECK_URL": "https://prod.rundeck.com",
        "RUNDECK_API_TOKEN": "prod-token",
        "RUNDECK_NAME": "production",
        "RUNDECK_URL_1": "https://dev.rundeck.com",
        "RUNDECK_API_TOKEN_1": "dev-token",
        "RUNDECK_NAME_1": "development"
      }
    }
  }
}
```

### API Version Configuration

If your Rundeck server uses a different API version:

```json
"env": {
  "RUNDECK_URL": "https://your-rundeck.com",
  "RUNDECK_API_TOKEN": "your-token",
  "RUNDECK_API_VERSION": "55"
}
```

### Development from Local Clone

```bash
# Clone repository
git clone https://github.com/yourusername/rundeck-mcp-server.git
cd rundeck-mcp-server

# Install dependencies
uvx --from . rundeck-mcp validate
```

Update Claude Desktop config to use local path:

```json
"args": ["--from", "/absolute/path/to/rundeck-mcp-server", "rundeck-mcp", "serve", "--enable-write-tools"]
```

## 🛠️ Available Tools

### Read-Only Tools (Always Available)
- `list_servers` - List configured Rundeck servers
- `get_projects` - List all projects
- `get_jobs` - List jobs in a project
- `get_job_definition` - Get complete job configuration
- `analyze_job` - Analyze job risk and recommendations
- `visualize_job` - Generate workflow diagrams
- `get_executions` - List execution history
- `get_execution_status` - Get execution details
- `get_execution_output` - View execution logs
- `get_nodes` - List infrastructure nodes
- `get_node_summary` - Infrastructure statistics
- `get_execution_metrics` - Analytics and trends
- `calculate_job_roi` - ROI analysis

### Write Tools (Require --enable-write-tools)
- `run_job` - Execute a job
- `run_job_with_monitoring` - Execute and monitor job
- `create_job` - Create new job
- `job_import` - Import jobs from YAML/JSON
- `modify_job` - Modify existing job
- `delete_job` - Delete a job
- `job_control` - Enable/disable jobs and schedules
- `create_project` - Create new project
- `abort_execution` - Stop running execution
- `retry_execution` - Retry failed execution

## 📝 Usage Examples

### From Claude Desktop

```
"List all projects on the production server"

"Show me jobs in the DevOps project"

"Create a new job that backs up the database daily"

"Run the deployment job with version 1.2.3"

"Show execution logs for execution 12345"
```

### Command Line Testing

```bash
# Validate configuration
uvx --from . rundeck-mcp validate

# Test connection
curl -H "X-Rundeck-Auth-Token: $RUNDECK_API_TOKEN" \
  $RUNDECK_URL/api/47/system/info
```

## 🔍 Troubleshooting

### Connection Issues

**Token not authorized:**
- Verify token has API access permissions
- Check token hasn't expired
- Ensure user has required ACLs

**Wrong API version:**
- Check server version: `curl $RUNDECK_URL/api/47/system/info`
- Update `RUNDECK_API_VERSION` environment variable

**Cannot connect:**
- Verify URL is accessible
- Check firewall/network settings
- Ensure HTTPS for cloud instances

### Debug Mode

```bash
# Run with debug logging
uvx --from . rundeck-mcp serve --log-level DEBUG --no-validate-config
```

### Common Fixes

```bash
# Refresh installation
uvx --from git+https://github.com/yourusername/rundeck-mcp-server --force rundeck-mcp validate

# Clear uvx cache
rm -rf ~/.local/share/uv/cache
```

## 📚 Documentation

- [Job Creation Rules](VARIABLE_RULES.md) - Variable substitution and step types
- [Troubleshooting Guide](TROUBLESHOOTING.md) - Detailed troubleshooting
- [Architecture Guide](CLAUDE.md) - Technical documentation

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `make check`
5. Submit a pull request

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🔗 Links

- [Rundeck Documentation](https://docs.rundeck.com)
- [MCP Protocol](https://modelcontextprotocol.io)
- [uvx Documentation](https://docs.astral.sh/uv)

---

Built with ❤️ for the Rundeck community
