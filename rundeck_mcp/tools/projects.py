"""Project management tools."""

from ..client import get_client
from ..models.base import ListResponseModel
from ..models.rundeck import Project, ProjectStats


def get_projects(server: str | None = None) -> ListResponseModel[Project]:
    """Get all projects from Rundeck server.

    Args:
        server: Server name to query (optional)

    Returns:
        List of projects
    """
    client = get_client(server)
    response = client._make_request("GET", "projects")

    projects = []
    for project_data in response:
        projects.append(
            Project(
                name=project_data["name"],
                description=project_data.get("description"),
                url=project_data.get("url"),
                config=project_data.get("config", {}),
            )
        )

    return ListResponseModel[Project](response=projects, total_count=len(projects))


def get_project_stats(project: str, server: str | None = None) -> ProjectStats:
    """Get statistics for a specific project.

    Args:
        project: Project name
        server: Server name to query (optional)

    Returns:
        Project statistics
    """
    client = get_client(server)

    # Get project info (for validation)
    client._make_request("GET", f"project/{project}")

    # Get jobs count
    jobs_response = client._make_request("GET", f"project/{project}/jobs")
    job_count = len(jobs_response)

    # Get executions count (last 30 days)
    executions_response = client._make_request("GET", f"project/{project}/executions")
    execution_count = len(executions_response.get("executions", []))

    # Get nodes count
    nodes_response = client._make_request("GET", f"project/{project}/resources")
    node_count = len(nodes_response)

    # Get active executions
    active_executions = client._make_request("GET", f"project/{project}/executions", params={"statusFilter": "running"})
    active_count = len(active_executions.get("executions", []))

    return ProjectStats(
        project_name=project,
        job_count=job_count,
        execution_count=execution_count,
        node_count=node_count,
        active_executions=active_count,
    )


# Tool definitions
project_tools = {
    "read": [
        get_projects,
        get_project_stats,
    ],
    "write": [],
}
