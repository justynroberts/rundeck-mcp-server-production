"""Rundeck MCP tools."""

from .analytics import analytics_tools
from .executions import execution_tools
from .jobs import job_tools
from .nodes import node_tools
from .projects import project_tools
from .system import system_tools

# Separate read-only and write tools
read_tools = [
    *project_tools["read"],
    *job_tools["read"],
    *execution_tools["read"],
    *node_tools["read"],
    *system_tools["read"],
    *analytics_tools["read"],
]

write_tools = [
    *project_tools["write"],
    *job_tools["write"],
    *execution_tools["write"],
    *system_tools["write"],
]

all_tools = read_tools + write_tools

__all__ = ["read_tools", "write_tools", "all_tools"]
