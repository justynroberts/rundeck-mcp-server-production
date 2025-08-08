"""System management tools."""

from ..client import get_client, get_client_manager
from ..models.base import ListResponseModel
from ..models.rundeck import ExecutionMode, Server, SystemInfo


def list_servers() -> ListResponseModel[Server]:
    """List all configured Rundeck servers.

    Returns:
        List of configured servers
    """
    client_manager = get_client_manager()
    servers = client_manager.list_servers()

    return ListResponseModel[Server](response=servers, total_count=len(servers))


def get_system_info(server: str | None = None) -> SystemInfo:
    """Get system information from Rundeck server.

    Args:
        server: Server name to query (optional)

    Returns:
        System information
    """
    client = get_client(server)
    response = client._make_request("GET", "system/info")

    return SystemInfo(
        rundeck_version=response.get("system", {}).get("rundeck", {}).get("version", "Unknown"),
        api_version=response.get("system", {}).get("rundeck", {}).get("apiversion", "Unknown"),
        server_name=response.get("system", {}).get("rundeck", {}).get("node", "Unknown"),
        server_uuid=response.get("system", {}).get("rundeck", {}).get("serverUUID", "Unknown"),
        build_info=response.get("system", {}).get("rundeck", {}).get("build", {}),
        system_stats=response.get("system", {}).get("stats", {}),
    )


def get_execution_mode(server: str | None = None) -> ExecutionMode:
    """Get current execution mode.

    Args:
        server: Server name to query (optional)

    Returns:
        Current execution mode
    """
    client = get_client(server)
    response = client._make_request("GET", "system/executions/status")

    return ExecutionMode(
        mode=response.get("executionMode", "unknown"),
        is_active=response.get("executionMode") == "active",
        message=response.get("message"),
    )


def set_execution_mode(mode: str, server: str | None = None) -> ExecutionMode:
    """Set execution mode.

    Args:
        mode: Execution mode ('active' or 'passive')
        server: Server name to query (optional)

    Returns:
        Updated execution mode
    """
    if mode not in ["active", "passive"]:
        raise ValueError("Mode must be 'active' or 'passive'")

    client = get_client(server)
    response = client._make_request("POST", f"system/executions/{mode}")

    return ExecutionMode(
        mode=response.get("executionMode", mode),
        is_active=response.get("executionMode") == "active",
        message=response.get("message"),
    )


def health_check_servers() -> dict[str, bool]:
    """Check health of all configured servers.

    Returns:
        Dictionary mapping server names to health status
    """
    client_manager = get_client_manager()
    return client_manager.health_check_all()


# Tool definitions
system_tools = {
    "read": [
        list_servers,
        get_system_info,
        get_execution_mode,
        health_check_servers,
    ],
    "write": [
        set_execution_mode,
    ],
}
