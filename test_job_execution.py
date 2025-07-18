#!/usr/bin/env python3
"""Test script demonstrating server vs project distinction for job execution."""

import os
import sys

# Add parent directory to path for local imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rundeck_mcp.tools.jobs import run_job, get_job_definition
from rundeck_mcp.tools.projects import get_projects
from rundeck_mcp.tools.system import list_servers


def demonstrate_server_project_distinction():
    """Demonstrate how to properly use server vs project parameters."""
    
    print("=== Rundeck MCP Server - Job Execution Demo ===\n")
    
    # List all configured servers
    print("1. Available Servers:")
    try:
        servers = list_servers()
        for server in servers.response:
            print(f"   - {server.name}: {server.url}")
    except Exception as e:
        print(f"   Error listing servers: {e}")
    
    print("\n2. Projects on each server:")
    # For each server, list its projects
    for server in servers.response:
        try:
            projects = get_projects(server=server.name)
            print(f"   Server '{server.name}' has {len(projects.response)} projects:")
            for project in projects.response[:3]:  # Show first 3
                print(f"      - {project.name}")
        except Exception as e:
            print(f"   Error getting projects for {server.name}: {e}")
    
    print("\n3. Example: Running a job")
    print("   To run job '02fced35-9858-4ddc-902b-13044206163a' in project 'global-production' on server 'demo':")
    print('   run_job(')
    print('       job_id="02fced35-9858-4ddc-902b-13044206163a",')
    print('       options={"application": "Grafana", "Namespace": "mcp_rocks"},')
    print('       server="demo"  # Use server alias, NOT project name!')
    print('   )')
    
    print("\n4. Key Points:")
    print("   ✓ Server parameter = configured server alias (e.g., 'demo', 'production')")
    print("   ✓ Project is determined by the job itself - jobs belong to projects")
    print("   ✓ Never use project name as the server parameter")
    print("   ✓ Use list_servers() to see available server aliases")
    
    print("\n5. Common Mistakes:")
    print('   ✗ run_job(job_id="...", server="global-production")  # Wrong! This is a project name')
    print('   ✓ run_job(job_id="...", server="demo")              # Correct! This is a server alias')


if __name__ == "__main__":
    # Check if environment is configured
    if not os.getenv("RUNDECK_URL"):
        print("ERROR: Please set RUNDECK_URL and RUNDECK_API_TOKEN environment variables")
        sys.exit(1)
    
    demonstrate_server_project_distinction()