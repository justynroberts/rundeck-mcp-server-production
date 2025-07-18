# VS Code Configuration Templates

This directory contains VS Code configuration templates for the Rundeck MCP Server project.

## Setup Instructions

1. **Copy template files** to create your workspace configuration:
   ```bash
   cp .vscode/settings.json.template .vscode/settings.json
   cp .vscode/launch.json.template .vscode/launch.json
   cp .vscode/tasks.json.template .vscode/tasks.json
   ```

2. **Update environment variables** in the copied files:
   - Replace `https://your-rundeck-server.com` with your actual Rundeck URL
   - Replace `your-api-token` with your actual API token
   - Update other environment variables as needed

3. **Install recommended extensions**:
   - Python
   - MCP (Model Context Protocol)
   - Pylint
   - Black Formatter

## Configuration Files

### `settings.json.template`
- MCP server configuration for VS Code
- Python development settings
- Editor formatting and linting configuration
- File exclusion patterns

### `launch.json.template`
- Debug configurations for different modes
- Development and production launch configs
- Configuration validation launcher
- Debug mode with enhanced logging

### `tasks.json.template`
- Build and test tasks
- MCP server start/stop tasks
- Code quality tasks
- Configuration generation tasks

## Available Tasks

Access these through VS Code's Command Palette (`Ctrl+Shift+P` → "Tasks: Run Task"):

- **Start MCP Server (Development)**: Start in read-only mode
- **Start MCP Server (Production)**: Start with write tools enabled
- **Run Tests**: Execute test suite
- **Run Quality Checks**: Format, lint, and type check
- **Format Code**: Auto-format with Black
- **Generate Claude Config**: Create Claude Desktop configuration
- **Validate Configuration**: Test server connectivity
- **Build Package**: Create distribution packages
- **Clean Build**: Remove build artifacts

## Debug Configurations

Available debug configurations:

- **Rundeck MCP Server (Development)**: Debug read-only mode
- **Rundeck MCP Server (Production)**: Debug with write tools
- **Rundeck MCP Server (Debug)**: Debug with verbose logging
- **Validate Configuration**: Debug configuration validation
- **Generate Claude Config**: Debug config generation

## MCP Integration

The configuration includes settings for MCP (Model Context Protocol) integration:

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

## Security Notes

- **Never commit actual configuration files** (they're in .gitignore)
- **Use environment variables** for sensitive data
- **Keep API tokens secure** and rotate them regularly
- **Use read-only mode** for development and testing

## Troubleshooting

### MCP Server Not Starting
1. Check that environment variables are set correctly
2. Verify Rundeck server connectivity
3. Check Python virtual environment is activated
4. Review debug logs in VS Code terminal

### Configuration Validation Fails
1. Test API token manually: `curl -H "X-Rundeck-Auth-Token: your-token" https://your-rundeck-server.com/api/47/system/info`
2. Check network connectivity
3. Verify Rundeck server URL and API version

### Extensions Not Working
1. Install recommended Python extensions
2. Set correct Python interpreter path
3. Reload VS Code window after configuration changes

## Development Workflow

1. **Start development server**:
   - Use "Start MCP Server (Development)" task
   - Or press F5 with "Rundeck MCP Server (Development)" config

2. **Run tests**:
   - Use "Run Tests" task
   - Or use Python test discovery in VS Code

3. **Debug issues**:
   - Use "Rundeck MCP Server (Debug)" configuration
   - Check integrated terminal for logs
   - Use breakpoints in Python code

4. **Deploy changes**:
   - Use "Run Quality Checks" task
   - Generate new configurations with "Generate Claude Config" task
   - Test with "Validate Configuration" task

## Additional Resources

- [Deployment Guide](../DEPLOYMENT_GUIDE.md) - Complete deployment instructions
- [Quick Start](../QUICK_START.md) - Fast setup guide
- [CLAUDE.md](../CLAUDE.md) - Development documentation
- [CONTRIBUTING.md](../CONTRIBUTING.md) - Contribution guidelines