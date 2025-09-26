# Rundeck MCP Server

A production-ready MCP (Model Context Protocol) server for Rundeck automation platform. Manage projects, jobs, executions, and infrastructure directly from Claude Desktop or any MCP-enabled client.

## 🚀 Quick Start

### Prerequisites

1. **Python 3.12+** installed
2. **Rundeck API Token** (see [Getting a Token](#getting-a-rundeck-api-token))
3. **uv** package manager (see [Installing uv](#installing-uv))

### Installing uv

uv is a fast, modern Python package manager. Install it using one of these methods:

#### macOS/Linux
```bash
# Using curl
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or using Homebrew
brew install uv
```

#### Windows
```powershell
# Using PowerShell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or using Scoop
scoop install uv
```

#### Verify Installation
```bash
uv --version
```

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/rundeck-mcp-server.git
cd rundeck-mcp-server

# Install with uv (creates virtual environment automatically)
uv sync

# Or install globally with uvx for direct use
uvx install rundeck-mcp-server
```

### Configuration

Set your Rundeck environment variables:

```bash
export RUNDECK_URL="https://rundeck.example.com"
export RUNDECK_API_TOKEN="your-api-token-here"
export RUNDECK_API_VERSION="47"  # Optional, defaults to 47
```

### Running the Server

```bash
# Development mode (read-only)
uv run rundeck-mcp serve

# Production mode (with write operations)
uv run rundeck-mcp serve --enable-write-tools

# Or if installed globally with uvx
uvx rundeck-mcp-server serve --enable-write-tools
```

## ✨ Recent Improvements

### MCP Protocol Compliance (Latest)
- **Fixed Parameter Validation Issue**: Resolved "job retrieval functions aren't accepting the required project parameter properly"
- **Dynamic Schema Generation**: Automatic input schema generation from function signatures using Python `inspect` module
- **Enhanced Type Safety**: Proper JSON schema types (string, integer, boolean) with required/optional parameter detection
- **Better User Experience**: Claude Desktop now shows proper parameter forms and validation errors
- **Union Type Support**: Handles `str | None` patterns for optional parameters with automatic descriptions

### Tool Consolidation
- **Simplified Interface**: Reduced from 35 to 30 tools by consolidating related functions
- **`job_import`**: Single tool supporting both YAML and JSON formats (replaces 3 separate tools)
- **`job_control`**: Unified enable/disable operations with operation parameter
- **Enhanced UUIDs**: 16-digit alphanumeric job identifiers for better tracking

### Variable Substitution
- **Consistent Format**: All job scripts now use `@option.VARIABLENAME@` format regardless of script type
- **Intelligent Extraction**: Automatic variable detection from scripts with type inference
- **Secure Defaults**: Password options automatically get placeholder defaults

## 📦 Deployment

### Production Deployment

1. **Environment Setup**
   ```bash
   # Create production environment file
   cat > .env.production << EOF
   RUNDECK_URL=https://your-rundeck.com
   RUNDECK_API_TOKEN=your-production-token
   RUNDECK_API_VERSION=47
   EOF
   ```

2. **Install Dependencies**
   ```bash
   # Install in production mode
   uv sync --no-dev
   ```

3. **Run Server**
   ```bash
   # Start with production settings
   source .env.production
   uv run rundeck-mcp serve --enable-write-tools
   ```

### Docker Deployment

```dockerfile
FROM python:3.12-slim

# Install uv
RUN pip install uv

# Copy application
WORKDIR /app
COPY . .

# Install dependencies
RUN uv sync --no-dev

# Run server
CMD ["uv", "run", "rundeck-mcp", "serve", "--enable-write-tools"]
```

### Systemd Service (Linux)

Create `/etc/systemd/system/rundeck-mcp.service`:

```ini
[Unit]
Description=Rundeck MCP Server
After=network.target

[Service]
Type=simple
User=rundeck-mcp
WorkingDirectory=/opt/rundeck-mcp-server
Environment="RUNDECK_URL=https://your-rundeck.com"
Environment="RUNDECK_API_TOKEN=your-token"
ExecStart=/usr/local/bin/uv run rundeck-mcp serve --enable-write-tools
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable rundeck-mcp
sudo systemctl start rundeck-mcp
```

## 🔧 Claude Desktop Integration

### Automatic Configuration

```bash
# Generate Claude Desktop configuration
uv run python tests/get_claude_config.py --write-tools

# Config will be saved to ~/Library/Application Support/Claude/claude_desktop_config.json
```

### Manual Configuration

Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "rundeck": {
      "command": "uvx",
      "args": ["rundeck-mcp-server", "serve", "--enable-write-tools"],
      "env": {
        "RUNDECK_URL": "https://your-rundeck.com",
        "RUNDECK_API_TOKEN": "your-token-here"
      }
    }
  }
}
```

## 🔐 Getting a Rundeck API Token

1. **Log into Rundeck** - Navigate to your Rundeck server
2. **Access Profile** - Click your username → "Profile"
3. **API Tokens Section** - Find the "User API Tokens" section
4. **Generate Token** - Click "Generate New Token"
5. **Set Expiration** - Choose expiration (or never)
6. **Copy & Save** - Store the token securely

## 🛠️ Available Tools

### Complete Tool Reference

The server provides **36 tools** organized by category and access level:

| Tool Name | Type | Category | Description |
|-----------|------|----------|-------------|
| **SYSTEM TOOLS** ||||
| `list_servers` | 🔍 Read | System | List all configured Rundeck servers |
| `health_check_servers` | 🔍 Read | System | Check health status of all servers |
| `get_system_info` | 🔍 Read | System | Get Rundeck system information and version |
| `get_execution_mode` | 🔍 Read | System | Get current execution mode (active/passive) |
| `set_execution_mode` | ✏️ Write | System | Set execution mode for maintenance |
| **PROJECT TOOLS** ||||
| `get_projects` | 🔍 Read | Projects | List all projects in Rundeck |
| `get_project_stats` | 🔍 Read | Projects | Get project statistics and metrics |
| `create_project` | ✏️ Write | Projects | Create new Rundeck project |
| **JOB TOOLS** ||||
| `get_jobs` | 🔍 Read | Jobs | List jobs in a project with filtering |
| `get_job_definition` | 🔍 Read | Jobs | Get complete job definition and configuration |
| `analyze_job` | 🔍 Read | Jobs | Analyze job for risk and recommendations |
| `visualize_job` | 🔍 Read | Jobs | Generate job workflow visualization |
| `run_job` | ✏️ Write | Jobs | Execute a job with parameters |
| `run_job_with_monitoring` | ✏️ Write | Jobs | Execute job and monitor until completion |
| `create_job` | ✏️ Write | Jobs | Create new job programmatically |
| `create_job_from_yaml` | ✏️ Write | Jobs | Import job from YAML definition |
| `create_multiple_jobs_from_yaml` | ✏️ Write | Jobs | Bulk import multiple jobs from YAML |
| `enable_job` | ✏️ Write | Jobs | Enable a disabled job |
| `disable_job` | ✏️ Write | Jobs | Disable an enabled job |
| `enable_job_schedule` | ✏️ Write | Jobs | Enable job scheduling |
| `disable_job_schedule` | ✏️ Write | Jobs | Disable job scheduling |
| **EXECUTION TOOLS** ||||
| `get_executions` | 🔍 Read | Executions | List executions with filtering |
| `get_execution_status` | 🔍 Read | Executions | Get execution status and details |
| `get_execution_output` | 🔍 Read | Executions | Get execution output logs |
| `get_bulk_execution_status` | 🔍 Read | Executions | Get status for multiple executions |
| `abort_execution` | ✏️ Write | Executions | Abort a running execution |
| `retry_execution` | ✏️ Write | Executions | Retry a failed execution |
| `delete_execution` | ✏️ Write | Executions | Delete execution history |
| `run_adhoc_command` | ✏️ Write | Executions | Execute ad hoc commands on nodes |
| **NODE TOOLS** ||||
| `get_nodes` | 🔍 Read | Nodes | List nodes with filtering |
| `get_node_details` | 🔍 Read | Nodes | Get detailed node information |
| `get_node_summary` | 🔍 Read | Nodes | Get node statistics summary |
| **ANALYTICS TOOLS** ||||
| `get_execution_metrics` | 🔍 Read | Analytics | Get execution metrics and trends |
| `calculate_job_roi` | 🔍 Read | Analytics | Calculate ROI for job automation |
| `get_all_executions` | 🔍 Read | Analytics | Get all executions with pagination |

### Tool Categories Summary

| Category | Read Tools | Write Tools | Total |
|----------|------------|-------------|-------|
| System | 4 | 1 | 5 |
| Projects | 2 | 1 | 3 |
| Jobs | 4 | 10 | 14 |
| Executions | 4 | 4 | 8 |
| Nodes | 3 | 0 | 3 |
| Analytics | 3 | 0 | 3 |
| **Total** | **20** | **16** | **36** |

### Access Control

- **🔍 Read Tools (20)**: Always available, safe for production use
- **✏️ Write Tools (16)**: Require `--enable-write-tools` flag, can modify Rundeck state

## 📝 Usage Examples

### Basic Commands

```bash
# Check server status
uv run rundeck-mcp check

# List available tools
uv run rundeck-mcp serve --help

# Run with debug logging
LOG_LEVEL=DEBUG uv run rundeck-mcp serve
```

### Multi-Server Setup

Configure multiple Rundeck instances:

```bash
# Primary server
export RUNDECK_URL="https://prod.rundeck.com"
export RUNDECK_API_TOKEN="prod-token"
export RUNDECK_NAME="production"

# Secondary server
export RUNDECK_URL_1="https://dev.rundeck.com"
export RUNDECK_API_TOKEN_1="dev-token"
export RUNDECK_NAME_1="development"
```

## 🧪 Testing

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov

# Test server connection
uv run python tests/test_server.py

# Debug job operations
uv run python tests/debug_jobs.py
```

## 🔍 Troubleshooting

### Common Issues

**Connection Refused**
```bash
# Check URL and network
curl -I $RUNDECK_URL/api/47/system/info

# Verify token
echo $RUNDECK_API_TOKEN
```

**Permission Denied**
- Ensure API token has required permissions
- Check if write tools are enabled for write operations

**Module Not Found**
```bash
# Reinstall dependencies
uv sync --refresh
```

### Debug Mode

```bash
# Enable debug logging
LOG_LEVEL=DEBUG uv run rundeck-mcp serve

# Test specific tool
uv run python -c "from rundeck_mcp.tools.jobs import get_jobs; print(get_jobs('my-project'))"
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting:
   ```bash
   make check  # Runs format, lint, type-check, and test
   ```
5. Submit a pull request

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🔗 Links

- [Rundeck Documentation](https://docs.rundeck.com)
- [MCP Protocol Specification](https://modelcontextprotocol.io)
- [uv Documentation](https://github.com/astral-sh/uv)

## 💡 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/rundeck-mcp-server/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/rundeck-mcp-server/discussions)
- **Security**: See [SECURITY.md](SECURITY.md) for reporting vulnerabilities

---

Built with ❤️ for the Rundeck community. Ready for production use!