"""Rundeck-specific models."""

from datetime import datetime
from typing import Any

from pydantic import Field, computed_field

from .base import BaseModel


class Server(BaseModel):
    """Rundeck server configuration."""

    name: str = Field(description="Server identifier name")
    url: str = Field(description="Server URL")
    api_version: str = Field(default="47", description="API version")
    is_primary: bool = Field(default=False, description="Whether this is the primary server")


class Project(BaseModel):
    """Rundeck project model."""

    name: str = Field(description="Project name")
    description: str | None = Field(None, description="Project description")
    url: str | None = Field(None, description="Project URL")
    config: dict[str, Any] | None = Field(None, description="Project configuration")

    @computed_field
    @property
    def summary(self) -> str:
        """Human-readable project summary."""
        desc = f": {self.description}" if self.description else ""
        return f"Project {self.name}{desc}"


class Job(BaseModel):
    """Rundeck job model."""

    id: str = Field(description="Job ID")
    name: str = Field(description="Job name")
    group: str | None = Field(None, description="Job group")
    project: str = Field(description="Project name")
    description: str | None = Field(None, description="Job description")
    enabled: bool = Field(default=True, description="Whether job is enabled")
    scheduled: bool = Field(default=False, description="Whether job is scheduled")
    schedule_enabled: bool = Field(default=False, description="Whether schedule is enabled")

    @computed_field
    @property
    def full_name(self) -> str:
        """Full job name including group."""
        if self.group:
            return f"{self.group}/{self.name}"
        return self.name

    @computed_field
    @property
    def summary(self) -> str:
        """Human-readable job summary."""
        status = "enabled" if self.enabled else "disabled"
        sched = " (scheduled)" if self.scheduled and self.schedule_enabled else ""
        return f"Job {self.full_name} ({status}){sched}"


class JobDefinition(BaseModel):
    """Complete job definition."""

    id: str = Field(description="Job ID")
    name: str = Field(description="Job name")
    group: str | None = Field(None, description="Job group")
    project: str = Field(description="Project name")
    description: str | None = Field(None, description="Job description")
    enabled: bool = Field(default=True, description="Whether job is enabled")
    scheduled: bool = Field(default=False, description="Whether job is scheduled")
    schedule_enabled: bool = Field(default=False, description="Whether schedule is enabled")
    workflow: list[dict[str, Any]] = Field(default_factory=list, description="Job workflow steps")
    options: list[dict[str, Any]] = Field(default_factory=list, description="Job options")
    node_filter: dict[str, Any] | None = Field(None, description="Node filter configuration")
    schedule: dict[str, Any] | None = Field(None, description="Schedule configuration")

    @computed_field
    @property
    def step_count(self) -> int:
        """Number of workflow steps."""
        return len(self.workflow)

    @computed_field
    @property
    def option_count(self) -> int:
        """Number of job options."""
        return len(self.options)


class JobExecution(BaseModel):
    """Job execution model."""

    id: str = Field(description="Execution ID")
    job_id: str = Field(description="Job ID")
    project: str = Field(description="Project name")
    status: str = Field(description="Execution status")
    start_time: datetime | None = Field(None, description="Execution start time")
    end_time: datetime | None = Field(None, description="Execution end time")
    duration: int | None = Field(None, description="Execution duration in milliseconds")
    user: str | None = Field(None, description="User who started the execution")

    @computed_field
    @property
    def is_running(self) -> bool:
        """Whether the execution is currently running."""
        return self.status.lower() in ["running", "started"]

    @computed_field
    @property
    def is_completed(self) -> bool:
        """Whether the execution has completed."""
        return self.status.lower() in ["succeeded", "failed", "aborted"]

    @computed_field
    @property
    def summary(self) -> str:
        """Human-readable execution summary."""
        return f"Execution {self.id} ({self.status})"


class JobAnalysis(BaseModel):
    """Job analysis result."""

    job_id: str = Field(description="Job ID")
    job_name: str = Field(description="Job name")
    purpose: str = Field(description="Inferred job purpose")
    risk_level: str = Field(description="Risk level (HIGH/MEDIUM/LOW)")
    risk_factors: list[str] = Field(default_factory=list, description="Risk factors identified")
    workflow_summary: str = Field(description="Workflow summary")
    node_targeting: str = Field(description="Node targeting configuration")
    options_summary: str = Field(description="Options summary")
    schedule_summary: str | None = Field(None, description="Schedule summary")
    recommendations: list[str] = Field(default_factory=list, description="Recommendations")

    @computed_field
    @property
    def risk_emoji(self) -> str:
        """Risk level emoji indicator."""
        return {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}.get(self.risk_level, "⚪")


class JobVisualization(BaseModel):
    """Job visualization data."""

    job_id: str = Field(description="Job ID")
    job_name: str = Field(description="Job name")
    mermaid_diagram: str = Field(description="Mermaid diagram code")
    text_flow: str = Field(description="Text-based flow representation")
    summary: str = Field(description="Visualization summary")


class Node(BaseModel):
    """Rundeck node model."""

    name: str = Field(description="Node name")
    hostname: str = Field(description="Node hostname")
    os_name: str | None = Field(None, description="Operating system name")
    os_version: str | None = Field(None, description="Operating system version")
    os_arch: str | None = Field(None, description="Operating system architecture")
    tags: list[str] = Field(default_factory=list, description="Node tags")
    attributes: dict[str, Any] = Field(default_factory=dict, description="Node attributes")

    @computed_field
    @property
    def os_summary(self) -> str:
        """Operating system summary."""
        parts = [self.os_name, self.os_version, self.os_arch]
        return " ".join(filter(None, parts)) or "Unknown"

    @computed_field
    @property
    def summary(self) -> str:
        """Human-readable node summary."""
        return f"Node {self.name} ({self.hostname}) - {self.os_summary}"


class NodeDetails(BaseModel):
    """Detailed node information."""

    name: str = Field(description="Node name")
    hostname: str = Field(description="Node hostname")
    os_name: str | None = Field(None, description="Operating system name")
    os_version: str | None = Field(None, description="Operating system version")
    os_arch: str | None = Field(None, description="Operating system architecture")
    description: str | None = Field(None, description="Node description")
    tags: list[str] = Field(default_factory=list, description="Node tags")
    attributes: dict[str, Any] = Field(default_factory=dict, description="Node attributes")
    status: str | None = Field(None, description="Node status")

    @computed_field
    @property
    def capabilities(self) -> list[str]:
        """Node capabilities extracted from attributes."""
        capabilities = []
        if self.attributes.get("ssh-key-storage-path"):
            capabilities.append("SSH Key Authentication")
        if self.attributes.get("ssh-password-storage-path"):
            capabilities.append("SSH Password Authentication")
        if self.attributes.get("winrm-protocol"):
            capabilities.append("WinRM Protocol")
        return capabilities


class NodeSummary(BaseModel):
    """Statistical summary of nodes."""

    total_nodes: int = Field(description="Total number of nodes")
    os_distribution: dict[str, int] = Field(default_factory=dict, description="OS distribution")
    status_breakdown: dict[str, int] = Field(default_factory=dict, description="Status breakdown")
    common_tags: list[str] = Field(default_factory=list, description="Most common tags")

    @computed_field
    @property
    def summary(self) -> str:
        """Human-readable summary."""
        return f"Infrastructure: {self.total_nodes} nodes across {len(self.os_distribution)} OS types"


class ExecutionStatus(BaseModel):
    """Execution status information."""

    id: str = Field(description="Execution ID")
    status: str = Field(description="Current status")
    start_time: datetime | None = Field(None, description="Start time")
    end_time: datetime | None = Field(None, description="End time")
    duration: int | None = Field(None, description="Duration in milliseconds")
    progress: float | None = Field(None, description="Progress percentage")

    @computed_field
    @property
    def is_final(self) -> bool:
        """Whether the status is final."""
        return self.status.lower() in ["succeeded", "failed", "aborted"]


class ExecutionMetrics(BaseModel):
    """Execution metrics and analytics."""

    total_executions: int = Field(description="Total number of executions")
    success_rate: float = Field(description="Success rate percentage")
    average_duration: float = Field(description="Average duration in seconds")
    failure_rate: float = Field(description="Failure rate percentage")
    most_active_users: list[str] = Field(default_factory=list, description="Most active users")
    execution_trends: dict[str, Any] = Field(default_factory=dict, description="Execution trends")

    @computed_field
    @property
    def summary(self) -> str:
        """Human-readable metrics summary."""
        return f"Metrics: {self.total_executions} executions, {self.success_rate:.1f}% success rate"


class SystemInfo(BaseModel):
    """System information."""

    rundeck_version: str = Field(description="Rundeck version")
    api_version: str = Field(description="API version")
    server_name: str = Field(description="Server name")
    server_uuid: str = Field(description="Server UUID")
    build_info: str | dict[str, Any] | None = Field(None, description="Build information")
    system_stats: dict[str, Any] | None = Field(None, description="System statistics")

    @computed_field
    @property
    def summary(self) -> str:
        """Human-readable system summary."""
        build_str = ""
        if isinstance(self.build_info, str):
            build_str = f" (build: {self.build_info})"
        elif isinstance(self.build_info, dict) and self.build_info:
            build_str = f" (build: {self.build_info.get('version', 'unknown')})"
        return f"Rundeck {self.rundeck_version} (API v{self.api_version}){build_str}"


class ProjectStats(BaseModel):
    """Project statistics."""

    project_name: str = Field(description="Project name")
    job_count: int = Field(description="Number of jobs")
    execution_count: int = Field(description="Number of executions")
    node_count: int = Field(description="Number of nodes")
    active_executions: int = Field(description="Number of active executions")

    @computed_field
    @property
    def summary(self) -> str:
        """Human-readable project summary."""
        return f"Project {self.project_name}: {self.job_count} jobs, {self.node_count} nodes"


class ROIAnalysis(BaseModel):
    """ROI analysis for job automation."""

    job_id: str = Field(description="Job ID")
    manual_time_hours: float = Field(description="Manual execution time in hours")
    automation_time_hours: float = Field(description="Automated execution time in hours")
    frequency_per_month: int = Field(description="Execution frequency per month")
    hourly_rate: float = Field(description="Hourly rate for manual work")
    monthly_savings: float = Field(description="Monthly savings in currency")
    annual_savings: float = Field(description="Annual savings in currency")
    roi_percentage: float = Field(description="ROI percentage")

    @computed_field
    @property
    def summary(self) -> str:
        """Human-readable ROI summary."""
        return f"ROI Analysis: {self.roi_percentage:.1f}% ROI, ${self.annual_savings:.2f} annual savings"


class ExecutionMode(BaseModel):
    """System execution mode."""

    mode: str = Field(description="Execution mode (active/passive)")
    is_active: bool = Field(description="Whether executions are active")
    message: str | None = Field(None, description="Mode message")

    @computed_field
    @property
    def summary(self) -> str:
        """Human-readable mode summary."""
        status = "active" if self.is_active else "passive"
        return f"Execution mode: {status}"
