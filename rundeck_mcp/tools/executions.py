"""Execution management tools."""

from datetime import datetime
from typing import Any

from ..client import get_client
from ..models.base import ListResponseModel
from ..models.rundeck import ExecutionStatus, JobExecution


def get_execution_status(execution_id: str, server: str | None = None) -> ExecutionStatus:
    """Get execution status.

    Args:
        execution_id: Execution ID
        server: Server name to query (optional)

    Returns:
        Execution status information
    """
    client = get_client(server)
    response = client._make_request("GET", f"execution/{execution_id}")

    return ExecutionStatus(
        id=response["id"],
        status=response["status"],
        start_time=datetime.fromisoformat(response["date-started"].replace("Z", "+00:00"))
        if response.get("date-started")
        else None,
        end_time=datetime.fromisoformat(response["date-ended"].replace("Z", "+00:00"))
        if response.get("date-ended")
        else None,
        duration=response.get("duration"),
    )


def get_execution_output(execution_id: str, server: str | None = None) -> dict[str, Any]:
    """Get execution output.

    Args:
        execution_id: Execution ID
        server: Server name to query (optional)

    Returns:
        Execution output data
    """
    client = get_client(server)
    return client._make_request("GET", f"execution/{execution_id}/output")


def get_executions(
    project: str,
    job_id: str | None = None,
    status: str | None = None,
    limit: int = 20,
    server: str | None = None,
) -> ListResponseModel[JobExecution]:
    """Get executions for a project.

    Args:
        project: Project name
        job_id: Job ID filter (optional)
        status: Status filter (optional)
        limit: Maximum number of results
        server: Server name to query (optional)

    Returns:
        List of executions
    """
    client = get_client(server)
    params = {"max": limit}
    if job_id:
        params["jobIdFilter"] = job_id
    if status:
        params["statusFilter"] = status

    response = client._make_request("GET", f"project/{project}/executions", params=params)

    executions = []
    for exec_data in response.get("executions", []):
        executions.append(
            JobExecution(
                id=exec_data["id"],
                job_id=exec_data.get("job", {}).get("id", ""),
                project=exec_data["project"],
                status=exec_data["status"],
                start_time=datetime.fromisoformat(exec_data["date-started"].replace("Z", "+00:00"))
                if exec_data.get("date-started")
                else None,
                end_time=datetime.fromisoformat(exec_data["date-ended"].replace("Z", "+00:00"))
                if exec_data.get("date-ended")
                else None,
                duration=exec_data.get("duration"),
                user=exec_data.get("user"),
            )
        )

    return ListResponseModel[JobExecution](response=executions, total_count=response.get("total", len(executions)))


def get_bulk_execution_status(execution_ids: list[str], server: str | None = None) -> list[ExecutionStatus]:
    """Get status for multiple executions.

    Args:
        execution_ids: List of execution IDs
        server: Server name to query (optional)

    Returns:
        List of execution statuses
    """
    statuses = []

    for exec_id in execution_ids:
        try:
            status = get_execution_status(exec_id, server)
            statuses.append(status)
        except Exception as e:
            # Log error but continue with other executions
            import logging

            logging.warning(f"Failed to get status for execution {exec_id}: {e}")

    return statuses


def abort_execution(execution_id: str, server: str | None = None) -> dict[str, Any]:
    """Abort a running execution.

    Args:
        execution_id: Execution ID to abort
        server: Server name to query (optional)

    Returns:
        Response data
    """
    client = get_client(server)
    return client._make_request("POST", f"execution/{execution_id}/abort")


def retry_execution(
    execution_id: str,
    options: dict[str, Any] | None = None,
    node_filter: str | None = None,
    server: str | None = None,
) -> dict[str, Any]:
    """Retry a failed execution.

    Args:
        execution_id: Execution ID to retry
        options: Job options to override
        node_filter: Node filter to apply
        server: Server name to query (optional)

    Returns:
        Response data
    """
    client = get_client(server)

    data = {}
    if options:
        data["options"] = options
    if node_filter:
        data["filter"] = node_filter

    return client._make_request("POST", f"execution/{execution_id}/retry", json=data)


def delete_execution(execution_id: str, server: str | None = None) -> dict[str, Any]:
    """Delete an execution record.

    Args:
        execution_id: Execution ID to delete
        server: Server name to query (optional)

    Returns:
        Response data
    """
    client = get_client(server)
    return client._make_request("DELETE", f"execution/{execution_id}")


def run_adhoc_command(
    project: str,
    command: str,
    node_filter: str = "name: localhost",
    server: str | None = None,
    follow_output: bool = True,
    as_user: str | None = None,
    validate_nodes: bool = True,
) -> dict[str, Any]:
    """Execute an ad hoc command on Rundeck nodes.

    Args:
        project: Project name
        command: Command to execute on the nodes
        node_filter: Node filter pattern (default: "name: localhost" for local execution)
        server: Server name to query (optional)
        follow_output: Whether to wait and return output details (default: True)
        as_user: User to run the command as (optional)
        validate_nodes: Whether to validate nodes exist before execution (default: True)

    Returns:
        Execution details including ID, status, and output if requested
    """
    client = get_client(server)
    
    # Validate nodes exist if requested
    if validate_nodes:
        try:
            # Check if nodes match the filter
            nodes_response = client._make_request("GET", f"project/{project}/resources", params={"filter": node_filter})
            if not nodes_response or len(nodes_response) == 0:
                return {
                    "error": f"No nodes found matching filter: '{node_filter}'",
                    "suggestion": "For local execution use 'name: localhost'. Check available nodes with get_nodes tool.",
                }
        except Exception as e:
            # If we can't validate, continue anyway (backwards compatibility)
            pass

    # Build payload for ad hoc command execution
    payload = {
        "exec": command,
        "nodefilter": node_filter,
        "project": project,
    }

    if as_user:
        payload["asUser"] = as_user

    # Execute the ad hoc command
    try:
        response = client._make_request("POST", f"project/{project}/run/command", json=payload)
    except Exception as e:
        # Check if error is related to no nodes matching
        error_str = str(e).lower()
        if "no nodes matched" in error_str or "no matching nodes" in error_str:
            return {
                "error": f"No nodes matched the filter: '{node_filter}'",
                "suggestion": "Use 'name: localhost' for local execution or check available nodes with get_nodes tool.",
            }
        raise

    # Extract execution ID
    execution_id = str(response.get("execution", {}).get("id", ""))

    if not execution_id:
        return {"error": "Failed to get execution ID", "response": response}

    result = {
        "execution_id": execution_id,
        "project": project,
        "command": command,
        "node_filter": node_filter,
    }

    if follow_output:
        # Wait briefly for execution to start
        import time

        time.sleep(1)

        # Get execution status and output
        try:
            status = get_execution_status(execution_id, server)
            output = get_execution_output(execution_id, server)

            result["status"] = status.model_dump()
            result["output"] = output
        except Exception as e:
            result["warning"] = f"Could not retrieve output: {str(e)}"

    return result


# Tool definitions
execution_tools = {
    "read": [
        get_execution_status,
        get_execution_output,
        get_executions,
        get_bulk_execution_status,
    ],
    "write": [
        abort_execution,
        retry_execution,
        delete_execution,
        run_adhoc_command,
    ],
}
