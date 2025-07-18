"""Job management tools."""

from typing import Any

from ..client import get_client
from ..models.base import ListResponseModel
from ..models.rundeck import Job, JobAnalysis, JobDefinition, JobVisualization


def get_jobs(project: str, group: str | None = None, server: str | None = None) -> ListResponseModel[Job]:
    """Get jobs from a project.

    Args:
        project: Project name
        group: Job group filter (optional)
        server: Server name to query (optional)

    Returns:
        List of jobs
    """
    client = get_client(server)
    params = {}
    if group:
        params["groupPath"] = group

    response = client._make_request("GET", f"project/{project}/jobs", params=params)

    jobs = []
    for job_data in response:
        jobs.append(
            Job(
                id=job_data["id"],
                name=job_data["name"],
                group=job_data.get("group"),
                project=job_data["project"],
                description=job_data.get("description"),
                enabled=job_data.get("enabled", True),
                scheduled=job_data.get("scheduled", False),
                schedule_enabled=job_data.get("scheduleEnabled", False),
            )
        )

    return ListResponseModel[Job](response=jobs, total_count=len(jobs))


def get_job_definition(job_id: str, server: str | None = None) -> JobDefinition:
    """Get complete job definition.

    Args:
        job_id: Job ID
        server: Server name to query (optional)

    Returns:
        Complete job definition
    """
    client = get_client(server)
    response = client._make_request("GET", f"job/{job_id}")

    return JobDefinition(
        id=response["id"],
        name=response["name"],
        group=response.get("group"),
        project=response["project"],
        description=response.get("description"),
        enabled=response.get("enabled", True),
        scheduled=response.get("scheduled", False),
        schedule_enabled=response.get("scheduleEnabled", False),
        workflow=response.get("workflow", {}).get("steps", []),
        options=response.get("options", {}),
        node_filter=response.get("nodefilters"),
        schedule=response.get("schedule"),
    )


def analyze_job(job_id: str, server: str | None = None) -> JobAnalysis:
    """Analyze a job for purpose, risk, and recommendations.

    Args:
        job_id: Job ID
        server: Server name to query (optional)

    Returns:
        Job analysis with risk assessment
    """
    client = get_client(server)
    job_def = get_job_definition(job_id, server)

    # Analyze job purpose
    purpose_keywords = {
        "deploy": ["deploy", "release", "install", "update"],
        "backup": ["backup", "archive", "export"],
        "maintenance": ["clean", "restart", "maintenance", "repair"],
        "monitoring": ["check", "monitor", "health", "status"],
        "security": ["security", "patch", "vulnerability", "audit"],
    }

    job_text = f"{job_def.name} {job_def.description or ''}".lower()
    inferred_purpose = "General automation"

    for category, keywords in purpose_keywords.items():
        if any(keyword in job_text for keyword in keywords):
            inferred_purpose = f"{category.title()} automation"
            break

    # Risk assessment
    risk_factors = []
    risk_score = 0

    # Check for destructive operations
    destructive_keywords = ["delete", "remove", "drop", "destroy", "kill", "terminate"]
    for step in job_def.workflow:
        step_text = str(step).lower()
        if any(keyword in step_text for keyword in destructive_keywords):
            risk_factors.append("Contains potentially destructive operations")
            risk_score += 3

    # Check for system-level operations
    system_keywords = ["sudo", "root", "admin", "system", "kernel"]
    for step in job_def.workflow:
        step_text = str(step).lower()
        if any(keyword in step_text for keyword in system_keywords):
            risk_factors.append("Performs system-level operations")
            risk_score += 2

    # Check for network operations
    network_keywords = ["curl", "wget", "ssh", "scp", "ftp", "rsync"]
    for step in job_def.workflow:
        step_text = str(step).lower()
        if any(keyword in step_text for keyword in network_keywords):
            risk_factors.append("Performs network operations")
            risk_score += 1

    # Check for production indicators
    if job_def.node_filter:
        node_filter_text = str(job_def.node_filter).lower()
        if any(keyword in node_filter_text for keyword in ["prod", "production", "live"]):
            risk_factors.append("Targets production environment")
            risk_score += 2

    # Determine risk level
    if risk_score >= 5:
        risk_level = "HIGH"
    elif risk_score >= 2:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    # Generate workflow summary
    workflow_summary = f"Job contains {len(job_def.workflow)} workflow steps"
    if job_def.workflow:
        step_types = {}
        for step in job_def.workflow:
            step_type = step.get("type", "unknown")
            step_types[step_type] = step_types.get(step_type, 0) + 1
        workflow_summary += f": {', '.join(f'{count} {type}' for type, count in step_types.items())}"

    # Generate node targeting summary
    node_targeting = "No specific node targeting"
    if job_def.node_filter:
        node_targeting = f"Targets nodes with filter: {job_def.node_filter}"

    # Generate options summary
    options_summary = f"Job has {len(job_def.options)} options"
    if job_def.options:
        required_options = [opt for opt in job_def.options if opt.get("required", False)]
        options_summary += f" ({len(required_options)} required)"

    # Generate schedule summary
    schedule_summary = None
    if job_def.schedule:
        schedule_summary = f"Scheduled job with cron: {job_def.schedule.get('crontab', 'unknown')}"

    # Generate recommendations
    recommendations = []
    if risk_score >= 3:
        recommendations.append("Consider implementing approval workflow for this job")
    if not job_def.description:
        recommendations.append("Add detailed description explaining job purpose")
    if job_def.schedule and not job_def.schedule_enabled:
        recommendations.append("Schedule is configured but disabled - verify if this is intentional")

    return JobAnalysis(
        job_id=job_id,
        job_name=job_def.name,
        purpose=inferred_purpose,
        risk_level=risk_level,
        risk_factors=risk_factors,
        workflow_summary=workflow_summary,
        node_targeting=node_targeting,
        options_summary=options_summary,
        schedule_summary=schedule_summary,
        recommendations=recommendations,
    )


def visualize_job(job_id: str, server: str | None = None) -> JobVisualization:
    """Generate visual representation of job workflow.

    Args:
        job_id: Job ID
        server: Server name to query (optional)

    Returns:
        Job visualization data
    """
    client = get_client(server)
    job_def = get_job_definition(job_id, server)

    # Generate Mermaid diagram
    mermaid_lines = ["graph TD", f"    A[Start: {job_def.name}] --> B[Job Configuration]"]

    # Add options
    if job_def.options:
        mermaid_lines.append("    B --> C[Options Validation]")
        previous_node = "C"
    else:
        previous_node = "B"

    # Add node filtering
    if job_def.node_filter:
        node_id = chr(ord(previous_node) + 1)
        mermaid_lines.append(f"    {previous_node} --> {node_id}[Node Selection]")
        previous_node = node_id

    # Add workflow steps
    for i, step in enumerate(job_def.workflow):
        step_id = chr(ord(previous_node) + 1 + i)
        step_name = step.get("description", f"Step {i + 1}")
        step_type = step.get("type", "command")

        if step_type == "command":
            shape = f"[{step_name}]"
        elif step_type == "script":
            shape = f"({step_name})"
        else:
            shape = f"{{{step_name}}}"

        mermaid_lines.append(f"    {previous_node} --> {step_id}{shape}")
        previous_node = step_id

    # Add end node
    end_id = chr(ord(previous_node) + 1)
    mermaid_lines.append(f"    {previous_node} --> {end_id}[End]")

    mermaid_diagram = "\\n".join(mermaid_lines)

    # Generate text flow
    text_flow = f"Job Flow: {job_def.name}\\n"
    text_flow += "=" * (len(job_def.name) + 11) + "\\n\\n"

    if job_def.options:
        text_flow += f"1. Options: {len(job_def.options)} parameters\\n"

    if job_def.node_filter:
        text_flow += f"2. Node Selection: {job_def.node_filter}\\n"

    text_flow += "3. Workflow Steps:\\n"
    for i, step in enumerate(job_def.workflow):
        step_name = step.get("description", f"Step {i + 1}")
        text_flow += f"   {i + 1}. {step_name}\\n"

    # Generate summary
    summary = f"Visualization for job '{job_def.name}' with {len(job_def.workflow)} steps"
    if job_def.options:
        summary += f" and {len(job_def.options)} options"

    return JobVisualization(
        job_id=job_id, job_name=job_def.name, mermaid_diagram=mermaid_diagram, text_flow=text_flow, summary=summary
    )


def run_job(
    job_id: str,
    options: dict[str, Any] | None = None,
    node_filter: str | None = None,
    server: str | None = None,
) -> dict[str, Any]:
    """Run a job with optional parameters.

    Args:
        job_id: Job ID to run
        options: Job options to pass (e.g., {"application": "Grafana", "Namespace": "mcp_rocks"})
        node_filter: Node filter to apply
        server: Server name/alias to use (e.g., "demo"), not the project name

    Returns:
        Execution response with execution ID and status

    Example:
        # To run job 02fced35-9858-4ddc-902b-13044206163a in project "global-production" on server "demo":
        run_job(
            job_id="02fced35-9858-4ddc-902b-13044206163a",
            options={"application": "Grafana", "Namespace": "mcp_rocks"},
            server="demo"  # Server alias, not project name
        )
    """
    client = get_client(server)

    data = {}
    if options:
        data["options"] = options
    if node_filter:
        data["filter"] = node_filter

    response = client._make_request("POST", f"job/{job_id}/run", json=data)
    return response


def run_job_with_monitoring(
    job_id: str,
    options: dict[str, Any] | None = None,
    node_filter: str | None = None,
    server: str | None = None,
    poll_interval: int = 5,
    timeout: int = 300,
) -> dict[str, Any]:
    """Run a job and monitor its execution until completion.

    Args:
        job_id: Job ID to run
        options: Job options to pass (e.g., {"application": "Grafana", "Namespace": "mcp_rocks"})
        node_filter: Node filter to apply
        server: Server name/alias to use (e.g., "demo"), not the project name
        poll_interval: Seconds between status checks (default: 5)
        timeout: Maximum seconds to wait for completion (default: 300)

    Returns:
        Final execution result with complete status and output

    Example:
        # To run and monitor job in project "global-production" on server "demo":
        result = run_job_with_monitoring(
            job_id="02fced35-9858-4ddc-902b-13044206163a",
            options={"application": "Grafana", "Namespace": "mcp_rocks"},
            server="demo"  # Server alias, not project name
        )
    """
    import time

    from ..tools.executions import get_execution_output, get_execution_status

    # Start the job execution
    run_response = run_job(job_id, options, node_filter, server)
    execution_id = run_response.get("id")

    if not execution_id:
        return {"error": "Failed to start job execution", "response": run_response}

    # Monitor the execution
    start_time = time.time()
    final_status = None

    while time.time() - start_time < timeout:
        try:
            status = get_execution_status(execution_id, server)
            final_status = status.status

            # Check if execution is complete
            if final_status in ["succeeded", "failed", "aborted"]:
                # Get the final output
                try:
                    output = get_execution_output(execution_id, server)
                except Exception as e:
                    output = {"error": f"Failed to retrieve output: {str(e)}"}

                return {
                    "execution_id": execution_id,
                    "status": final_status,
                    "start_time": status.start_time.isoformat() if status.start_time else None,
                    "end_time": status.end_time.isoformat() if status.end_time else None,
                    "duration": status.duration,
                    "output": output,
                }

            # Wait before next check
            time.sleep(poll_interval)

        except Exception as e:
            return {
                "execution_id": execution_id,
                "error": f"Error monitoring execution: {str(e)}",
                "last_status": final_status,
            }

    # Timeout reached
    return {
        "execution_id": execution_id,
        "error": f"Execution monitoring timed out after {timeout} seconds",
        "last_status": final_status,
    }


def enable_job(job_id: str, server: str | None = None) -> dict[str, Any]:
    """Enable a job.

    Args:
        job_id: Job ID to enable
        server: Server name to query (optional)

    Returns:
        Response data
    """
    client = get_client(server)
    return client._make_request("POST", f"job/{job_id}/enable")


def disable_job(job_id: str, server: str | None = None) -> dict[str, Any]:
    """Disable a job.

    Args:
        job_id: Job ID to disable
        server: Server name to query (optional)

    Returns:
        Response data
    """
    client = get_client(server)
    return client._make_request("POST", f"job/{job_id}/disable")


def enable_job_schedule(job_id: str, server: str | None = None) -> dict[str, Any]:
    """Enable job schedule.

    Args:
        job_id: Job ID to enable schedule for
        server: Server name to query (optional)

    Returns:
        Response data
    """
    client = get_client(server)
    return client._make_request("POST", f"job/{job_id}/schedule/enable")


def disable_job_schedule(job_id: str, server: str | None = None) -> dict[str, Any]:
    """Disable job schedule.

    Args:
        job_id: Job ID to disable schedule for
        server: Server name to query (optional)

    Returns:
        Response data
    """
    client = get_client(server)
    return client._make_request("POST", f"job/{job_id}/schedule/disable")


# Tool definitions
job_tools = {
    "read": [
        get_jobs,
        get_job_definition,
        analyze_job,
        visualize_job,
    ],
    "write": [
        run_job,
        run_job_with_monitoring,
        enable_job,
        disable_job,
        enable_job_schedule,
        disable_job_schedule,
    ],
}
