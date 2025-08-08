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
    ],
}
