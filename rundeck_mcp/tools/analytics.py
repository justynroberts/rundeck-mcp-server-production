"""Analytics and reporting tools."""

import statistics
from datetime import datetime, timedelta
from typing import Any

from ..client import get_client
from ..models.rundeck import ExecutionMetrics, ROIAnalysis
from .executions import get_executions


def get_execution_metrics(project: str, days: int = 30, server: str | None = None) -> ExecutionMetrics:
    """Get execution metrics for a project.

    Args:
        project: Project name
        days: Number of days to analyze
        server: Server name to query (optional)

    Returns:
        Execution metrics
    """
    # Get executions for the specified period
    executions_response = get_executions(project, limit=1000, server=server)
    executions = executions_response.response

    # Filter executions by date range
    cutoff_date = datetime.now() - timedelta(days=days)
    recent_executions = [exec for exec in executions if exec.start_time and exec.start_time >= cutoff_date]

    total_executions = len(recent_executions)

    if total_executions == 0:
        return ExecutionMetrics(
            total_executions=0,
            success_rate=0.0,
            average_duration=0.0,
            failure_rate=0.0,
            most_active_users=[],
            execution_trends={},
        )

    # Calculate success/failure rates
    successful = len([exec for exec in recent_executions if exec.status == "succeeded"])
    failed = len([exec for exec in recent_executions if exec.status == "failed"])

    success_rate = (successful / total_executions) * 100
    failure_rate = (failed / total_executions) * 100

    # Calculate average duration
    durations = [exec.duration for exec in recent_executions if exec.duration]
    average_duration = statistics.mean(durations) / 1000 if durations else 0  # Convert to seconds

    # Find most active users
    user_counts = {}
    for exec in recent_executions:
        if exec.user:
            user_counts[exec.user] = user_counts.get(exec.user, 0) + 1

    most_active_users = sorted(user_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    most_active_users = [user for user, count in most_active_users]

    # Calculate execution trends (by day)
    daily_counts = {}
    for exec in recent_executions:
        if exec.start_time:
            day_key = exec.start_time.strftime("%Y-%m-%d")
            daily_counts[day_key] = daily_counts.get(day_key, 0) + 1

    execution_trends = {
        "daily_counts": daily_counts,
        "peak_day": max(daily_counts.items(), key=lambda x: x[1])[0] if daily_counts else None,
        "average_per_day": total_executions / days if days > 0 else 0,
    }

    return ExecutionMetrics(
        total_executions=total_executions,
        success_rate=success_rate,
        average_duration=average_duration,
        failure_rate=failure_rate,
        most_active_users=most_active_users,
        execution_trends=execution_trends,
    )


def calculate_job_roi(
    job_id: str,
    manual_time_hours: float,
    frequency_per_month: int,
    hourly_rate: float = 50.0,
    server: str | None = None,
) -> ROIAnalysis:
    """Calculate ROI for job automation.

    Args:
        job_id: Job ID to analyze
        manual_time_hours: Time in hours for manual execution
        frequency_per_month: How often the job runs per month
        hourly_rate: Hourly rate for manual work
        server: Server name to query (optional)

    Returns:
        ROI analysis
    """
    # Get job execution data to estimate automation time
    try:
        # Get recent executions for this job
        from .jobs import get_job_definition

        job_def = get_job_definition(job_id, server)
        project = job_def.project

        executions_response = get_executions(project, job_id=job_id, limit=20, server=server)
        executions = executions_response.response

        # Calculate average automation time
        durations = [exec.duration for exec in executions if exec.duration and exec.status == "succeeded"]
        if durations:
            avg_duration_ms = statistics.mean(durations)
            automation_time_hours = avg_duration_ms / (1000 * 60 * 60)  # Convert to hours
        else:
            automation_time_hours = 0.1  # Default assumption: 6 minutes
    except Exception:
        automation_time_hours = 0.1  # Default assumption: 6 minutes

    # Calculate savings
    monthly_manual_cost = manual_time_hours * frequency_per_month * hourly_rate
    monthly_automation_cost = automation_time_hours * frequency_per_month * hourly_rate
    monthly_savings = monthly_manual_cost - monthly_automation_cost
    annual_savings = monthly_savings * 12

    # Calculate ROI percentage
    roi_percentage = monthly_savings / monthly_manual_cost * 100 if monthly_manual_cost > 0 else 0

    return ROIAnalysis(
        job_id=job_id,
        manual_time_hours=manual_time_hours,
        automation_time_hours=automation_time_hours,
        frequency_per_month=frequency_per_month,
        hourly_rate=hourly_rate,
        monthly_savings=monthly_savings,
        annual_savings=annual_savings,
        roi_percentage=roi_percentage,
    )


def get_all_executions(project: str, limit: int = 100, server: str | None = None) -> list[dict[str, Any]]:
    """Get all executions with detailed information.

    Args:
        project: Project name
        limit: Maximum number of executions to retrieve
        server: Server name to query (optional)

    Returns:
        List of execution details
    """
    client = get_client(server)
    response = client._make_request("GET", f"project/{project}/executions", params={"max": limit})

    return response.get("executions", [])


# Tool definitions
analytics_tools = {
    "read": [
        get_execution_metrics,
        calculate_job_roi,
        get_all_executions,
    ],
    "write": [],
}
