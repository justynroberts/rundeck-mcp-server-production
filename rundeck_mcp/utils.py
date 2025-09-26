"""Utility functions for Rundeck MCP Server."""

import inspect
import json
import logging
import os
from pathlib import Path
from typing import Any, get_origin, get_args

logger = logging.getLogger(__name__)


def load_tool_prompts() -> dict[str, dict[str, str]]:
    """Load tool prompts from JSON file.

    Returns:
        Dictionary of tool prompts
    """
    try:
        # Look for tool_prompts.json in the current directory first
        prompts_file = Path("tool_prompts.json")
        if not prompts_file.exists():
            # Fall back to package directory
            package_dir = Path(__file__).parent.parent
            prompts_file = package_dir / "tool_prompts.json"

        if prompts_file.exists():
            with open(prompts_file) as f:
                return json.load(f)
        else:
            logger.warning("tool_prompts.json not found, using default descriptions")
            return {}

    except Exception as e:
        logger.error(f"Error loading tool prompts: {e}")
        return {}


def get_tool_description(tool_name: str, tool_prompts: dict[str, dict[str, str]]) -> str:
    """Get description for a tool.

    Args:
        tool_name: Name of the tool
        tool_prompts: Tool prompts dictionary

    Returns:
        Tool description
    """
    if tool_name in tool_prompts:
        return tool_prompts[tool_name].get("description", f"Tool: {tool_name}")

    # Fallback descriptions
    fallback_descriptions = {
        # Project tools
        "get_projects": "Get all projects from Rundeck server",
        "get_project_stats": "Get statistics for a specific project",
        # Job tools
        "get_jobs": "Get jobs from a project with optional filtering",
        "get_job_definition": "Get complete job definition with workflow and options",
        "analyze_job": "Analyze a job for purpose, risk assessment, and recommendations",
        "visualize_job": "Generate visual representation of job workflow",
        "run_job": "🟡 Run a job with optional parameters",
        "enable_job": "🟡 Enable a job for execution",
        "disable_job": "🟡 Disable a job from execution",
        "enable_job_schedule": "🟡 Enable job scheduling",
        "disable_job_schedule": "🟡 Disable job scheduling",
        # Execution tools
        "get_execution_status": "Get execution status and details",
        "get_execution_output": "Get execution output and logs",
        "get_executions": "Get executions for a project with filtering",
        "get_bulk_execution_status": "Get status for multiple executions",
        "abort_execution": "🔴 Abort a running execution",
        "retry_execution": "🟡 Retry a failed execution",
        "delete_execution": "🔴 Delete an execution record",
        # Node tools
        "get_nodes": "Get nodes from a project with optional filtering",
        "get_node_details": "Get detailed information about a specific node",
        "get_node_summary": "Get statistical summary of nodes in a project",
        # System tools
        "list_servers": "List all configured Rundeck servers",
        "get_system_info": "Get system information from Rundeck server",
        "get_execution_mode": "Get current execution mode",
        "set_execution_mode": "🔴 Set execution mode (active/passive)",
        "health_check_servers": "Check health of all configured servers",
        # Analytics tools
        "get_execution_metrics": "Get execution metrics and analytics",
        "calculate_job_roi": "Calculate ROI for job automation",
        "get_all_executions": "Get all executions with detailed information",
    }

    return fallback_descriptions.get(tool_name, f"Tool: {tool_name}")


def format_error(error: Exception) -> str:
    """Format an error message for display.

    Args:
        error: Exception to format

    Returns:
        Formatted error message
    """
    error_type = type(error).__name__
    error_message = str(error)

    # Clean up common error messages
    if "Connection error" in error_message:
        return f"Connection Error: {error_message}"
    elif "Authentication failed" in error_message:
        return f"Authentication Error: {error_message}"
    elif "Access denied" in error_message:
        return f"Authorization Error: {error_message}"
    elif "Resource not found" in error_message:
        return f"Not Found Error: {error_message}"
    else:
        return f"{error_type}: {error_message}"


def validate_environment() -> dict[str, Any]:
    """Validate environment configuration.

    Returns:
        Dictionary with validation results
    """
    validation_results = {"valid": True, "errors": [], "warnings": [], "servers": {}}

    # Check primary server
    primary_url = os.getenv("RUNDECK_URL")
    primary_token = os.getenv("RUNDECK_API_TOKEN")

    # Check additional servers first
    additional_servers_found = False
    for i in range(1, 10):
        url = os.getenv(f"RUNDECK_URL_{i}")
        token = os.getenv(f"RUNDECK_API_TOKEN_{i}")

        if url and token:
            validation_results["servers"][f"server_{i}"] = {
                "url": url,
                "name": os.getenv(f"RUNDECK_NAME_{i}", f"server_{i}"),
                "api_version": os.getenv(f"RUNDECK_API_VERSION_{i}", "47"),
            }
            additional_servers_found = True
        elif url or token:
            validation_results["warnings"].append(
                f"Incomplete configuration for server {i}: {'missing token' if url else 'missing URL'}"
            )

    # Only require primary server if no numbered servers are configured
    if primary_url and primary_token:
        validation_results["servers"]["primary"] = {
            "url": primary_url,
            "name": os.getenv("RUNDECK_NAME", "primary"),
            "api_version": os.getenv("RUNDECK_API_VERSION", "47"),
        }
    elif not additional_servers_found:
        # Only error if no numbered servers were found
        if not primary_url:
            validation_results["errors"].append("RUNDECK_URL environment variable is not set and no numbered servers configured")
            validation_results["valid"] = False

        if not primary_token:
            validation_results["errors"].append("RUNDECK_API_TOKEN environment variable is not set and no numbered servers configured")
            validation_results["valid"] = False

    # Ensure at least one server is configured
    if not validation_results["servers"]:
        validation_results["errors"].append("No Rundeck servers configured - set either RUNDECK_URL/RUNDECK_API_TOKEN or numbered variants")
        validation_results["valid"] = False

    return validation_results


def setup_logging(level: str = "INFO"):
    """Setup logging configuration.

    Args:
        level: Logging level
    """
    import sys

    log_level = getattr(logging, level.upper(), logging.INFO)

    # Always use stderr for logging to avoid interfering with MCP stdout
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stderr)],
    )

    # Set specific loggers
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


def generate_input_schema(func: Any) -> dict[str, Any]:
    """Generate JSON schema for function parameters.

    Args:
        func: Function to analyze

    Returns:
        JSON schema dictionary for the function parameters
    """
    signature = inspect.signature(func)
    properties = {}
    required = []

    for param_name, param in signature.parameters.items():
        # Skip *args and **kwargs
        if param.kind in (param.VAR_POSITIONAL, param.VAR_KEYWORD):
            continue

        # Get type annotation
        param_type = param.annotation

        # Determine JSON schema type
        json_type = "string"  # Default
        json_format = None

        if param_type is str or param_type == "str":
            json_type = "string"
        elif param_type is int or param_type == "int":
            json_type = "integer"
        elif param_type is float or param_type == "float":
            json_type = "number"
        elif param_type is bool or param_type == "bool":
            json_type = "boolean"
        elif param_type is list or (hasattr(param_type, "__origin__") and param_type.__origin__ is list):
            json_type = "array"
        elif param_type is dict or (hasattr(param_type, "__origin__") and param_type.__origin__ is dict):
            json_type = "object"
        elif hasattr(param_type, "__origin__"):
            # Handle Union types (like str | None)
            origin = get_origin(param_type)
            args = get_args(param_type)

            if origin is type(None) and len(args) >= 2:  # Union[X, None] or X | None
                # Find the non-None type
                non_none_types = [arg for arg in args if arg is not type(None)]
                if non_none_types:
                    first_type = non_none_types[0]
                    if first_type is str:
                        json_type = "string"
                    elif first_type is int:
                        json_type = "integer"
                    elif first_type is float:
                        json_type = "number"
                    elif first_type is bool:
                        json_type = "boolean"

        # Create property schema
        prop_schema = {"type": json_type}
        if json_format:
            prop_schema["format"] = json_format

        # Add description based on parameter name
        descriptions = {
            "project": "Project name",
            "server": "Server name to query (optional)",
            "job_id": "Job ID",
            "execution_id": "Execution ID",
            "node_name": "Node name",
            "group": "Job group filter (optional)",
            "filter_query": "Node filter query (optional)",
            "tags": "Tags filter (optional)",
            "limit": "Maximum number of results",
            "status": "Status filter (optional)",
            "search_term": "Search term (optional)",
            "command": "Command to execute",
            "node_filter": "Node filter pattern (required for adhoc commands)",
            "options": "Job options (optional)",
            "content": "Content to import",
            "format": "Import format (yaml or json)",
            "operation": "Operation to perform",
            "confirmed": "Confirmation flag for destructive operations"
        }

        if param_name in descriptions:
            prop_schema["description"] = descriptions[param_name]

        properties[param_name] = prop_schema

        # Determine if parameter is required (no default value)
        if param.default == param.empty:
            required.append(param_name)

    return {
        "type": "object",
        "properties": properties,
        "required": required
    }
