# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build Commands

### Development Setup
```bash
# Quick development setup (recommended)
make dev-setup

# Alternative setup with uv
make dev-install

# Alternative automated setup
./setup.sh               # Bash script for complete environment setup
```

### Testing
```bash
# Run all tests
make test

# Run specific test categories
make test-server         # Test server connection
make test-multi         # Test multi-server setup
make debug-jobs         # Debug job analysis
make test-evals         # Run competency tests
make configure-claude   # Generate Claude Desktop config

# Manual testing and debugging
python tests/test_server.py         # Direct server testing
python tests/get_claude_config.py   # Generate Claude Desktop config
```

### Code Quality
```bash
# Format code
make format             # Uses ruff

# Run linting
make lint              # Uses ruff

# Type checking
make type-check        # Uses pyright

# Run tests with coverage
make coverage          # Generate coverage report

# All quality checks
make check             # Runs format, lint, type-check, and test
```

### Build and Distribution
```bash
make build             # Build distribution packages
make clean             # Clean build artifacts
make serve             # Start server in development mode
make serve-write       # Start server with write tools enabled
```

## Architecture Overview

This is a **Model Context Protocol (MCP) server** that provides AI integration with Rundeck automation platforms. The project uses a **modular architecture** with clear separation of concerns and comprehensive security features.

### Core Components

1. **Server Implementation** (`rundeck_mcp/server.py`):
   - Uses FastMCP framework for streamlined MCP integration
   - Implements opt-in write operations with `--enable-write-tools` flag
   - Provides comprehensive tool safety annotations
   - Supports both read-only and write operations with clear distinctions

2. **Client Management** (`rundeck_mcp/client.py`):
   - Singleton pattern with caching for API clients
   - Multi-server support through environment variable patterns
   - Robust error handling with retry logic and specific error messages
   - Session management with persistent requests session

3. **Model Layer** (`rundeck_mcp/models/`):
   - **Base Models** (`base.py`): Generic response models with computed summaries
   - **Rundeck Models** (`rundeck.py`): Domain-specific models for projects, jobs, executions, nodes
   - Uses Pydantic v2 for data validation and serialization
   - Comprehensive type hints and validation rules

4. **Tool Layer** (`rundeck_mcp/tools/`):
   - **Project Tools** (`projects.py`): Project management and statistics
   - **Job Tools** (`jobs.py`): Job management, analysis, and visualization
   - **Execution Tools** (`executions.py`): Execution monitoring and control
   - **Node Tools** (`nodes.py`): Node discovery and infrastructure inventory
   - **System Tools** (`system.py`): System administration and health checks
   - **Analytics Tools** (`analytics.py`): Metrics, ROI analysis, and reporting

5. **Utilities** (`rundeck_mcp/utils.py`):
   - Tool prompt management and loading
   - Environment validation and configuration
   - Logging setup and error formatting

### MCP Tools Architecture

The server exposes 34 tools across these categories:

#### Read-Only Tools (Always Available)
- **Server Management**: `list_servers`, `health_check_servers`
- **Project Management**: `get_projects`, `get_project_stats`
- **Job Management**: `get_jobs`, `get_job_definition`, `analyze_job`, `visualize_job`
- **Execution Monitoring**: `get_execution_status`, `get_execution_output`, `get_executions`, `get_bulk_execution_status`
- **Node Management**: `get_nodes`, `get_node_details`, `get_node_summary`
- **System Health**: `get_system_info`, `get_execution_mode`
- **Analytics**: `get_execution_metrics`, `get_all_executions`, `calculate_job_roi`

#### Write Tools (Require `--enable-write-tools`)
- **Job Execution**: `run_job`, `run_job_with_monitoring`
- **Job Control**: `enable_job`, `disable_job`, `enable_job_schedule`, `disable_job_schedule`
- **Execution Control**: `abort_execution`, `retry_execution`, `delete_execution`
- **System Control**: `set_execution_mode`

### Multi-Server Support

The architecture supports multiple Rundeck environments:
- Primary server: `RUNDECK_URL`, `RUNDECK_API_TOKEN`, etc.
- Additional servers: `RUNDECK_URL_1`, `RUNDECK_API_TOKEN_1`, etc. (up to 9 additional servers)
- Each server has optional name identifier for tool targeting (`RUNDECK_NAME_N`)
- Fallback to primary server if numbered server not configured
- Health checking across all configured servers

### Security Features

1. **Opt-in Write Operations**: Write tools disabled by default, require explicit flag
2. **Tool Safety Annotations**: All tools marked with readOnlyHint, destructiveHint, idempotentHint
3. **Risk Assessment System**: Emoji-based risk indicators (🔴 HIGH, 🟡 MEDIUM, 🟢 LOW)
4. **Comprehensive Security Policy**: SECURITY.md with vulnerability reporting process
5. **Input Validation**: All inputs validated with Pydantic models
6. **Credential Protection**: API tokens never logged or exposed

### Error Handling Strategy

- Robust retry logic for connection issues (3 attempts with exponential backoff)
- Specific error messages for common issues (401, 403, 404)
- Comprehensive logging throughout the application
- Graceful degradation for optional features
- Session management with persistent requests session
- Configurable timeouts (30-second default)

## Testing Infrastructure

### Test Structure
- **Unit Tests**: `tests/test_server.py`, `tests/test_multi_server.py`
- **Integration Tests**: `tests/debug_jobs.py`, `tests/evals/run_tests.py`
- **Configuration Tools**: `tests/get_claude_config.py`
- Uses pytest with asyncio support
- Comprehensive mocking of external dependencies
- Test coverage monitoring with coverage reports

### Test Configuration
- Uses pytest with asyncio support
- Verbose output enabled (`-v --tb=short`)
- Patterns: `test_*.py`, `Test*`, `test_*`
- Coverage requirements: >80% for critical paths

## Configuration

### Environment Variables
Primary server configuration:
- `RUNDECK_URL` - Rundeck server URL
- `RUNDECK_API_TOKEN` - API authentication token
- `RUNDECK_API_VERSION` - API version (default: "47")
- `RUNDECK_NAME` - Server identifier name

### Multi-Server Pattern
For additional servers, append `_N` where N is 1,2,3...:
- `RUNDECK_URL_1`, `RUNDECK_API_TOKEN_1`, etc.

### Claude Desktop Integration
The server integrates with Claude Desktop via MCP protocol:
- Absolute paths required for Python executable and server script
- Environment variables passed through Claude Desktop config
- Single and multi-server configuration templates available
- Support for both uvx and direct Python execution

## Development Patterns

### Adding New Tools

1. **Create tool function in appropriate module**:
   ```python
   def new_tool(param1: str, server: Optional[str] = None) -> ResponseModel:
       """Tool description with clear parameters and return type."""
       client = get_client(server)
       # Implementation
   ```

2. **Add to tool categories**:
   ```python
   # In tools/__init__.py
   read_tools = [..., new_tool]  # or write_tools
   ```

3. **Add to tool_prompts.json**:
   ```json
   {
     "new_tool": {
       "description": "Clear description for AI assistants",
       "prompt": "Detailed prompt with usage examples"
     }
   }
   ```

4. **Write comprehensive tests**:
   ```python
   @patch('rundeck_mcp.tools.module.get_client')
   def test_new_tool(self, mock_get_client):
       # Test implementation
   ```

### Server vs Project Distinction

**IMPORTANT**: When executing jobs, understand the distinction between:
- **Server**: The Rundeck server alias configured in environment variables (e.g., "demo", "production")
- **Project**: The project within that server where the job resides (e.g., "global-production", "dev-apps")

Example scenario:
- You have a server configured with alias "demo" (via RUNDECK_URL and RUNDECK_API_TOKEN)
- That server contains a project called "global-production"
- To run a job in that project, use `server="demo"` (NOT "global-production")

```python
# CORRECT - Using server alias:
run_job(job_id="02fced35-9858-4ddc-902b-13044206163a", server="demo")

# INCORRECT - Using project name as server:
run_job(job_id="02fced35-9858-4ddc-902b-13044206163a", server="global-production")
```

### Job Analysis Tools

Advanced job understanding and risk assessment:

1. **`analyze_job(job_id, server?)`**:
   - Complete job definition analysis with risk scoring
   - Purpose inference from job name, description, and workflow
   - Comprehensive risk assessment (HIGH/MEDIUM/LOW)
   - Security implications analysis
   - Human-readable report with visual indicators

2. **`visualize_job(job_id, server?)`**:
   - Generate Mermaid flowchart diagrams
   - Color-coded workflow visualization
   - Text-based flow representation as fallback
   - Export-ready visualization code

### Node Management Tools

Comprehensive infrastructure inventory:

1. **`get_nodes(project, filter_query?, server?)`**: Node discovery with filtering
2. **`get_node_details(project, node_name, server?)`**: Detailed node information
3. **`get_node_summary(project, server?)`**: Statistical infrastructure overview

### Common Usage Examples

#### Running Jobs with Monitoring
```python
# Example: Running a job in the "global-production" project on the "demo" server
result = run_job_with_monitoring(
    job_id="02fced35-9858-4ddc-902b-13044206163a",
    options={
        "application": "Grafana",
        "Namespace": "mcp_rocks"
    },
    server="demo"  # Use server alias, not project name!
)
```

#### Listing Jobs in a Project
```python
# List all jobs in the "global-production" project on "demo" server
jobs = get_jobs(
    project="global-production",  # Project name
    server="demo"                 # Server alias
)
```

### Error Handling
- Use `client._make_request()` for all API calls
- Let built-in retry logic handle connection issues
- Provide specific error messages for different HTTP status codes
- Use proper logging for debugging without exposing credentials

### Code Style and Quality
- Uses Ruff for formatting and linting (120-character line length)
- Type hints required and enforced with Pyright (strict mode)
- Python 3.12+ compatibility required
- Comprehensive documentation with docstrings

### Package Structure
- **Modern Python packaging** with uv dependency management
- **Modular architecture** with clear separation of concerns
- **Console script entry point**: `rundeck-mcp`
- **Comprehensive documentation** included in package data

## Key Architectural Decisions

1. **FastMCP Framework**: Chosen for simplified MCP integration and better performance
2. **Modular Design**: Clear separation between models, tools, client management, and server
3. **Security-First**: Opt-in write operations, comprehensive security annotations
4. **Multi-Server Support**: Enterprise-ready with support for multiple Rundeck environments
5. **Comprehensive Testing**: Unit tests, integration tests, and competency evaluations
6. **Modern Python**: Python 3.12+, uv dependency management, strict type checking

This architecture provides a robust, secure, and maintainable foundation for Rundeck automation through AI assistants while maintaining high code quality standards.