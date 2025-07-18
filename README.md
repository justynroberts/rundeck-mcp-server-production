# Rundeck MCP Server

Rundeck's local MCP (Model Context Protocol) server which provides tools to interact with your Rundeck automation platform, allowing you to manage projects, jobs, executions, nodes, and more directly from your MCP-enabled client.

## Prerequisites

- Python 3.12 or higher installed
- `uv` installed globally
- A Rundeck API Token

To obtain a Rundeck API Token, follow these steps:

1. Navigate to your Rundeck server and log in
2. Click on your user profile icon, then select **User Profile**
3. In your user profile, locate the **API Tokens** section
4. Click the **Generate API Token** button and follow the prompts to create a new token
5. Copy the generated token and store it securely. You will need this token to configure the MCP server

## Using with MCP Clients

### VS Code Integration

You can configure this MCP server directly within Visual Studio Code's settings.json file, allowing VS Code to manage the server lifecycle.

1. Open VS Code settings (File > Preferences > Settings, or `Cmd+,` on Mac, or `Ctrl+,` on Windows/Linux)
2. Search for "mcp" and ensure "Mcp: Enabled" is checked under Features > Chat
3. Click "Edit in settings.json" under "Mcp > Discovery: Servers"
4. Add the following configuration:

```json
{
    "mcp": {
        "inputs": [
            {
                "type": "promptString",
                "id": "rundeck-api-token",
                "description": "Rundeck API Token",
                "password": true
            }
        ],
        "servers": {
            "rundeck-mcp": { 
                "type": "stdio",
                "command": "uvx",
                "args": [
                    "rundeck-mcp-server",
                    "serve",
                    "--enable-write-tools"
                    // This flag enables write operations on the MCP Server enabling you to run jobs, manage executions and much more
                ],
                "env": {
                    "RUNDECK_URL": "https://your-rundeck-server.com",
                    "RUNDECK_API_TOKEN": "${input:rundeck-api-token}",
                    "RUNDECK_API_VERSION": "47"
                    // Update to your server's API version if different
                }
            }
        }
    }
}
```

#### Trying it in VS Code Chat (Agent)

1. Ensure MCP is enabled in VS Code settings (Features > Chat > "Mcp: Enabled")
2. Configure the server as described above
3. Open the Chat view in VS Code (View > Chat)
4. Make sure Agent mode is selected. In the Chat view, you can enable or disable specific tools by clicking the 🛠️ icon
5. Enter a command such as "Show me all projects" to interact with your Rundeck server through the MCP server

You can start, stop, and manage your MCP servers using the command palette (`Cmd+Shift+P`/`Ctrl+Shift+P`) and searching for "MCP: List Servers". Ensure the server is running before sending commands. You can also try to restart the server if you encounter any issues.

### Claude Desktop Integration

You can configure this MCP server to work with Claude Desktop by adding it to Claude's configuration file.

1. Locate your Claude Desktop configuration file:
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
   - **Linux**: `~/.config/claude/claude_desktop_config.json`

2. Create or edit the configuration file and add the following configuration:

```json
{
  "mcpServers": {
    "rundeck-mcp": {
      "command": "uvx",
      "args": [
        "rundeck-mcp-server",
        "serve",
        "--enable-write-tools"
      ],
      "env": {
        "RUNDECK_URL": "https://your-rundeck-server.com",
        "RUNDECK_API_TOKEN": "your-rundeck-api-token-here",
        "RUNDECK_API_VERSION": "47"
      }
    }
  }
}
```

3. Replace the placeholder values:
   - Replace `https://your-rundeck-server.com` with your actual Rundeck server URL
   - Replace `your-rundeck-api-token-here` with your actual Rundeck API Token
   - Update `RUNDECK_API_VERSION` if your server uses a different API version

4. Restart Claude Desktop completely for the changes to take effect

5. Test the integration by starting a conversation with Claude and asking something like "Show me all my Rundeck projects" to verify the MCP server is working

**Security Note**: Unlike VS Code's secure input prompts, Claude Desktop requires you to store your API token directly in the configuration file. Ensure this file has appropriate permissions (readable only by your user account) and consider the security implications of storing credentials in plain text.

### Multi-Server Configuration

For multiple Rundeck environments, you can configure additional servers:

```json
{
  "mcpServers": {
    "rundeck-mcp": {
      "command": "uvx",
      "args": [
        "rundeck-mcp-server",
        "serve",
        "--enable-write-tools"
      ],
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

## Set up locally

### Clone the repository

```bash
git clone https://github.com/your-username/rundeck-mcp-server.git
cd rundeck-mcp-server
```

### Install dependencies

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install with development dependencies
pip install -e ".[dev]"
```

### Configure environment

```bash
# Copy example environment file
cp .env.example .env

# Edit with your Rundeck server details
nano .env
```

### Ensure uv is available globally

The MCP server can be run from different places so you need `uv` to be available globally. To do so, follow the [official documentation](https://docs.astral.sh/uv/getting-started/installation/).

**Tip**: You may need to restart your terminal and/or VS Code for the changes to take effect.

## Run it locally

To run your cloned Rundeck MCP Server you need to update your configuration to use `uv` instead of `uvx`.

```json
{
    "mcp": {
        "servers": {
            "rundeck-mcp": { 
                "type": "stdio",
                "command": "uv",
                "args": [
                    "run",
                    "--directory",
                    "/path/to/your/mcp-server-directory",
                    // Replace with the full path to the directory where you cloned the MCP server, e.g. "/Users/yourname/code/rundeck-mcp-server"     
                    "python",
                    "-m",
                    "rundeck_mcp",
                    "serve",
                    "--enable-write-tools"
                    // This flag enables write operations on the MCP Server enabling you to run jobs, manage executions and much more
                ],
                "env": {
                    "RUNDECK_URL": "https://your-rundeck-server.com",
                    "RUNDECK_API_TOKEN": "${input:rundeck-api-token}",
                    "RUNDECK_API_VERSION": "47"
                    // Update to your server's API version if different
                }
            }
        }
    }
}
```

## Available Tools and Resources

This section describes the tools provided by the Rundeck MCP server. They are categorized based on whether they only read data or can modify data in your Rundeck environment.

**Important**: By default, the MCP server only exposes read-only tools. To enable tools that can modify your Rundeck environment (write-mode tools), you must explicitly start the server with the `--enable-write-tools` flag. This helps prevent accidental changes to your Rundeck data.

| Tool | Area | Description | Read-only |
|------|------|-------------|-----------|
| `list_servers` | Server Management | Lists all configured Rundeck servers | ✅ |
| `get_projects` | Project Management | Lists all projects | ✅ |
| `get_project_stats` | Project Management | Gets statistics for a specific project | ✅ |
| `get_jobs` | Job Management | Lists jobs in a project with filtering | ✅ |
| `get_job_definition` | Job Management | Gets complete job definition | ✅ |
| `analyze_job` | Job Management | Analyzes job for risk assessment | ✅ |
| `visualize_job` | Job Management | Generates visual workflow diagrams | ✅ |
| `run_job` | Job Execution | Executes a job with parameters | ❌ |
| `enable_job` | Job Control | Enables a job for execution | ❌ |
| `disable_job` | Job Control | Disables a job from execution | ❌ |
| `enable_job_schedule` | Job Control | Enables job scheduling | ❌ |
| `disable_job_schedule` | Job Control | Disables job scheduling | ❌ |
| `get_execution_status` | Execution Monitoring | Gets execution status and details | ✅ |
| `get_execution_output` | Execution Monitoring | Gets execution output logs | ✅ |
| `get_executions` | Execution Monitoring | Lists executions with filtering | ✅ |
| `get_bulk_execution_status` | Execution Monitoring | Gets status for multiple executions | ✅ |
| `abort_execution` | Execution Control | Aborts a running execution | ❌ |
| `retry_execution` | Execution Control | Retries a failed execution | ❌ |
| `delete_execution` | Execution Control | Deletes an execution record | ❌ |
| `get_nodes` | Node Management | Lists nodes with filtering | ✅ |
| `get_node_details` | Node Management | Gets detailed node information | ✅ |
| `get_node_summary` | Node Management | Gets statistical node summary | ✅ |
| `get_system_info` | System Management | Gets system information | ✅ |
| `get_execution_mode` | System Management | Gets current execution mode | ✅ |
| `set_execution_mode` | System Management | Sets execution mode (active/passive) | ❌ |
| `health_check_servers` | System Management | Checks health of all servers | ✅ |
| `get_execution_metrics` | Analytics | Gets execution metrics and trends | ✅ |
| `calculate_job_roi` | Analytics | Calculates ROI for job automation | ✅ |
| `get_all_executions` | Analytics | Gets all executions with details | ✅ |

### Risk Assessment

Tools include visual risk indicators:
- 🔴 **High Risk**: Destructive operations (delete, abort, system control)
- 🟡 **Medium Risk**: Execution and state changes (run, enable/disable)
- 🟢 **Low Risk**: Read-only operations (get, list, analyze)

## Support

Rundeck's MCP server is an open-source project, and as such, we offer only community-based support. If assistance is required, please open an issue in GitHub.

## Contributing

If you are interested in contributing to this project, please refer to our [Contributing Guidelines](CONTRIBUTING.md).

## Development Commands

```bash
# Install development dependencies
make dev-install

# Run tests
make test

# Format code
make format

# Run linting
make lint

# Type checking
make type-check

# Run all quality checks
make check

# Generate Claude Desktop configuration
make configure-claude

# Start development server
make serve

# Start server with write tools enabled
make serve-write
```

## Security

- Store API tokens securely using environment variables
- Never commit API tokens to version control
- Use HTTPS connections to Rundeck servers
- Limit API token permissions to required operations only
- Enable write tools only when necessary

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.