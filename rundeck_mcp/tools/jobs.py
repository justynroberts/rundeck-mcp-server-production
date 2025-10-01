"""Job management tools."""

import json
import random
import re
import string
from typing import Any

import yaml

from ..client import get_client
from ..models.base import ListResponseModel
from ..models.rundeck import Job, JobAnalysis, JobDefinition, JobVisualization


def _generate_job_uuid() -> str:
    """Generate a proper UUID (RFC 4122) for job creation.

    Returns:
        UUID string in standard format (e.g., '123e4567-e89b-12d3-a456-426614174000')
    """
    import uuid
    return str(uuid.uuid4())


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


def job_control(
    job_id: str,
    operation: str,
    server: str | None = None,
) -> dict[str, Any]:
    """Control job execution and scheduling state.

    🟡 MEDIUM RISK: This operation can disable jobs and affect scheduled execution.

    Consolidates job enable/disable operations for both execution and scheduling.

    Args:
        job_id: Job ID to control
        operation: Control operation to perform:
                  - "enable": Enable job execution and scheduling
                  - "disable": Disable job execution and scheduling
                  - "enable_schedule": Enable only job scheduling (manual execution still works)
                  - "disable_schedule": Disable only job scheduling (manual execution still works)
        server: Server name to query (optional)

    Returns:
        Response data confirming the operation

    Raises:
        ValueError: If operation is not one of the supported values
    """
    valid_operations = ["enable", "disable", "enable_schedule", "disable_schedule"]
    if operation not in valid_operations:
        raise ValueError(f"Invalid operation '{operation}'. Must be one of: {', '.join(valid_operations)}")

    client = get_client(server)

    # Map operations to API endpoints
    endpoint_map = {
        "enable": f"job/{job_id}/enable",
        "disable": f"job/{job_id}/disable",
        "enable_schedule": f"job/{job_id}/schedule/enable",
        "disable_schedule": f"job/{job_id}/schedule/disable",
    }

    endpoint = endpoint_map[operation]
    response = client._make_request("POST", endpoint)

    # Add operation info to response for clarity
    if isinstance(response, dict):
        response["operation_performed"] = operation
        response["job_id"] = job_id

    return response


def delete_job(job_id: str, confirmed: bool = False, server: str | None = None) -> dict[str, Any]:
    """Delete a job permanently.

    🔴 HIGH RISK: This operation permanently deletes the job and cannot be undone.

    IMPORTANT: This is a DESTRUCTIVE operation that requires explicit user confirmation.
    The job will be permanently removed from Rundeck, including all its configuration,
    history, and scheduled runs. This action cannot be reversed.

    Args:
        job_id: Job ID to delete
        confirmed: Must be True to confirm deletion (required safety check)
        server: Server name to query (optional)

    Returns:
        Response data confirming deletion

    Raises:
        ValueError: If confirmed is not True
    """
    if not confirmed:
        # Get job details for user confirmation
        try:
            job_def = get_job_definition(job_id, server)
            job_info = f"Job '{job_def.name}' (ID: {job_id}) in project '{job_def.project}'"
            if job_def.description:
                job_info += f"\nDescription: {job_def.description}"
        except Exception:
            job_info = f"Job ID: {job_id}"

        raise ValueError(
            f"🚨 DELETION CONFIRMATION REQUIRED 🚨\n\n"
            f"You are about to PERMANENTLY DELETE:\n{job_info}\n\n"
            f"⚠️  This action CANNOT be undone!\n"
            f"⚠️  All job configuration, history, and schedules will be lost!\n\n"
            f"To proceed with deletion, you must call this function again with confirmed=True:\n"
            f"delete_job(job_id='{job_id}', confirmed=True{', server=\"' + server + '\"' if server else ''})"
        )

    client = get_client(server)

    # Get job details before deletion for confirmation message
    try:
        job_def = get_job_definition(job_id, server)
        job_name = job_def.name
        project = job_def.project
    except Exception:
        job_name = "Unknown"
        project = "Unknown"

    # Perform the deletion
    response = client._make_request("DELETE", f"job/{job_id}")

    return {
        "success": True,
        "message": f"✅ Job '{job_name}' (ID: {job_id}) has been permanently deleted from project '{project}'",
        "job_id": job_id,
        "job_name": job_name,
        "project": project,
        "deleted_at": response.get("timestamp", "Unknown"),
        "warning": "This action cannot be undone. The job and all its data have been permanently removed."
    }


def _extract_variables_from_command(command: str) -> list[str]:
    """Extract variable names from shell commands.

    Looks for patterns like $VAR, ${VAR}, or VAR= at the start of lines.
    """
    variables = set()

    # Pattern 1: $VAR or ${VAR} usage
    var_usage_pattern = r"\$\{?([A-Z_][A-Z0-9_]*)\}?"
    variables.update(re.findall(var_usage_pattern, command, re.IGNORECASE))

    # Pattern 2: VAR=value assignments (extract VAR)
    var_assignment_pattern = r"^([A-Z_][A-Z0-9_]*)\s*="
    for line in command.split("\n"):
        line = line.strip()
        match = re.match(var_assignment_pattern, line, re.IGNORECASE)
        if match:
            variables.add(match.group(1).upper())

    return sorted(list(variables))


def _break_command_into_steps(command: str, name: str) -> list[dict[str, Any]]:
    """Break a command into logical steps for better organization.

    Creates multiple steps when appropriate:
    - Detects logical boundaries (comments, echo separators, key operations)
    - Groups related commands together
    - Uses 'exec' for single commands, 'script' for multi-line blocks

    Returns:
        List of step dictionaries with 'exec'/'script' and 'description' fields
    """
    lines = [line.strip() for line in command.split("\n") if line.strip()]

    # Single line command - return as exec step
    if len(lines) == 1 and not command.strip().startswith("#!"):
        return [{"exec": command.strip(), "description": name}]

    # Script with shebang - keep as single script step
    if command.strip().startswith("#!"):
        return [{"script": command, "description": name}]

    steps = []
    current_step_lines = []
    step_counter = 1

    # Keywords that indicate a new logical step
    step_keywords = [
        "check", "verify", "validate", "test",
        "install", "download", "fetch", "clone",
        "setup", "configure", "initialize", "prepare",
        "start", "stop", "restart", "reload",
        "deploy", "build", "compile", "package",
        "backup", "restore", "archive", "snapshot",
        "cleanup", "clean", "remove", "delete",
        "update", "upgrade", "patch", "migrate",
        "monitor", "health", "status", "diagnostic"
    ]

    for line in lines:
        # Detect step boundaries
        is_new_step = False

        if current_step_lines:  # Only split if we have accumulated lines
            # Comment-based separation
            if line.startswith("#") and not line.startswith("#!/"):
                is_new_step = True
            # Echo separators
            elif line.startswith('echo "=') or line.startswith("echo '="):
                is_new_step = True
            # Keyword-based detection
            elif any(keyword in line.lower() for keyword in step_keywords):
                is_new_step = True

        if is_new_step:
            # Save current step
            step_command = "\n".join(current_step_lines)
            step_field = "script" if len(current_step_lines) > 1 else "exec"
            steps.append({
                step_field: step_command,
                "description": _infer_step_description(current_step_lines[0])
            })
            step_counter += 1
            current_step_lines = []

        current_step_lines.append(line)

    # Add final step
    if current_step_lines:
        step_command = "\n".join(current_step_lines)
        step_field = "script" if len(current_step_lines) > 1 else "exec"
        steps.append({
            step_field: step_command,
            "description": _infer_step_description(current_step_lines[0])
        })

    return steps if steps else [{"script": command, "description": name}]


def _infer_step_description(line: str) -> str:
    """Infer a human-readable description from a command line."""
    line = line.strip()

    # Remove comment markers
    if line.startswith("#"):
        return line[1:].strip()

    # Common command patterns
    if line.startswith("apt-get install") or line.startswith("yum install"):
        return "Install packages"
    elif line.startswith("wget") or line.startswith("curl"):
        return "Download files"
    elif line.startswith("tar") or line.startswith("unzip"):
        return "Extract archive"
    elif line.startswith("systemctl start") or line.startswith("service") and "start" in line:
        return "Start service"
    elif line.startswith("systemctl stop") or line.startswith("service") and "stop" in line:
        return "Stop service"
    elif line.startswith("cp") or line.startswith("mv"):
        return "Move/copy files"
    elif line.startswith("mkdir"):
        return "Create directories"
    elif line.startswith("chmod") or line.startswith("chown"):
        return "Set permissions"
    elif "deploy" in line.lower():
        return "Deploy application"
    elif "backup" in line.lower():
        return "Backup data"
    elif "clean" in line.lower():
        return "Cleanup"
    else:
        return "Execute command"


def _create_job_options_from_variables(variables: list[str]) -> dict[str, Any]:
    """Create Rundeck job options from extracted variables."""
    options = {}

    for var in variables:
        # Infer option properties based on variable name
        option_config = {"required": True, "description": f"Value for {var}"}

        # Add specific configurations for common variable patterns
        var_lower = var.lower()
        if "password" in var_lower or "secret" in var_lower or "token" in var_lower:
            option_config["secure"] = True
            option_config["description"] = f"Secure value for {var}"
        elif "port" in var_lower:
            option_config["description"] = f"Port number for {var}"
            option_config["defaultValue"] = "8080"
        elif "host" in var_lower or "server" in var_lower:
            option_config["description"] = f"Hostname or IP for {var}"
        elif "path" in var_lower or "dir" in var_lower:
            option_config["description"] = f"File path for {var}"
        elif "env" in var_lower or "environment" in var_lower:
            option_config["values"] = ["dev", "staging", "production"]
            option_config["description"] = f"Environment for {var}"
        elif "version" in var_lower:
            option_config["description"] = f"Version number for {var}"
            option_config["defaultValue"] = "latest"

        options[var] = option_config

    return options


def _substitute_variables_in_command(command: str, variables: list[str], is_script: bool = False) -> str:
    """Replace variable references with Rundeck option syntax.

    Critical Rules:
    - Script steps (script field): MUST use @option.variablename@ format
    - Exec steps (exec field): Use ${option.variablename} format

    Args:
        command: Command or script text
        variables: List of variable names to substitute
        is_script: True if this is a script step, False for exec step

    Returns:
        Command with variables substituted in correct format
    """
    modified_command = command

    if is_script:
        # Script steps: Use @option.VAR@ format
        for var in variables:
            if var.lower() == "option":
                continue
            # Convert ${VAR} or $VAR to @option.VAR@
            modified_command = re.sub(rf"\${{{var}}}", f"@option.{var}@", modified_command, flags=re.IGNORECASE)
            modified_command = re.sub(rf"\${var}(?![A-Za-z0-9_])", f"@option.{var}@", modified_command, flags=re.IGNORECASE)
            # Also handle if already in ${option.VAR} format
            modified_command = re.sub(rf"\${{option\.{var}}}", f"@option.{var}@", modified_command, flags=re.IGNORECASE)
    else:
        # Exec steps: Use ${option.VAR} format
        for var in variables:
            if var.lower() == "option":
                continue
            # Convert ${VAR} or $VAR to ${option.VAR}
            modified_command = re.sub(rf"\${{{var}}}", f"${{option.{var}}}", modified_command, flags=re.IGNORECASE)
            modified_command = re.sub(rf"\${var}(?![A-Za-z0-9_])", f"${{option.{var}}}", modified_command, flags=re.IGNORECASE)

    return modified_command


def _generate_markdown_documentation(name: str, description: str, variables: list[str], steps: list[dict]) -> str:
    """Generate markdown documentation for the job."""
    doc = f"# {name}\n\n"

    if description:
        doc += f"{description}\n\n"

    if variables:
        doc += "## Variables\n\n"
        doc += "This job uses the following variables (configured as job options):\n\n"
        for var in variables:
            doc += f"- `{var}`: Variable for job execution\n"
        doc += "\n"

    if len(steps) > 1:
        doc += "## Execution Steps\n\n"
        for i, step in enumerate(steps, 1):
            doc += f"{i}. **{step['description']}**\n"
            doc += "   ```bash\n"
            # Handle both exec and script fields
            command_text = step.get('exec') or step.get('script', '')
            doc += f"   {command_text}\n"
            doc += "   ```\n\n"
    else:
        doc += "## Execution\n\n"
        # Handle both exec and script fields
        command_text = steps[0].get('exec') or steps[0].get('script', '')
        doc += f"```bash\n{command_text}\n```\n\n"

    doc += "## Notes\n\n"
    doc += "- Job runs locally if no target nodes specified\n"
    doc += "- Variables are automatically extracted and created as job options\n"
    doc += "- Variable substitution rules:\n"
    doc += "  - Single-line commands: `${option.VARIABLENAME}` format\n"
    doc += "  - Multi-line scripts: `@option.VARIABLENAME@` format\n"

    return doc


def build_job(
    project: str,
    name: str,
    command: str,
    description: str = "",
    group: str | None = None,
    extract_variables: bool = True,
    break_into_steps: bool = True,
    node_filter: dict[str, Any] | str | None = None,
    schedule: dict[str, Any] | None = None,
    timeout: str | None = None,
    retry_count: int | None = None,
    execution_enabled: bool = True,
    schedule_enabled: bool = True,
    multiple_executions: bool = False,
    log_level: str = "INFO",
    dupe_option: str = "create",
    server: str | None = None,
) -> dict[str, Any]:
    """Build a Rundeck job from a command/script with intelligent processing.

    Use this for: Shell scripts, bash commands, simple automation
    Creates: exec/script steps only (not plugin steps)

    Features:
    - Automatic variable extraction from commands
    - Breaking complex scripts into logical exec/script steps
    - Proper variable substitution based on step type
    - Auto-generation of job options

    Variable Substitution Rules (Critical):
    - Script steps (script field): Use @option.variablename@ format
    - Exec steps (exec field): Use ${option.variablename} format

    For jobs with plugin steps (SQL, Ansible, HTTP, job refs, etc.):
    - Use create_job() with pre-defined workflow parameter
    - Use job_import() with complete YAML/JSON definition

    Step Types Created:
    - exec: Single simple commands ONLY (e.g., "df -h", "echo test", "ls -la")
    - script: ANYTHING complex - multi-line, heredocs, if/loops, functions, shebangs

    CRITICAL: Use script (not exec) for:
    - Multi-line scripts
    - Heredocs (<<EOF)
    - Complex logic (if/for/while)
    - Variable assignments
    - Command substitution

    Args:
        project: Project name
        name: Job name
        command: Command or script to process
        description: Job description
        group: Job group
        extract_variables: Auto-extract variables from command
        break_into_steps: Break complex scripts into multiple exec/script steps
        node_filter: Node targeting
        schedule: Schedule configuration
        timeout: Max runtime
        retry_count: Retry attempts
        execution_enabled: Enable execution
        schedule_enabled: Enable schedule
        multiple_executions: Allow concurrent runs
        log_level: Logging level
        dupe_option: Duplicate handling
        server: Server name/alias

    Returns:
        Job creation response
    """
    client = get_client(server)

    # Extract variables from command if requested
    variables = []
    if extract_variables:
        variables = _extract_variables_from_command(command)

    # Break command into steps if requested
    if break_into_steps and len(command.split('\n')) > 5:
        steps = _break_command_into_steps(command, name)
    else:
        # Single step
        if command.strip().startswith("#!"):
            steps = [{"script": command, "description": f"Execute {name}"}]
        else:
            steps = [{"exec": command, "description": f"Execute {name}"}]

    # Create job options from extracted variables
    options = []
    if variables:
        options_dict = _create_job_options_from_variables(variables)
        for opt_name, opt_config in options_dict.items():
            formatted_opt = {
                "name": opt_name,
                "description": opt_config.get("description", ""),
                "required": opt_config.get("required", False),
            }
            if "defaultValue" in opt_config:
                formatted_opt["value"] = opt_config["defaultValue"]
            options.append(formatted_opt)

    # Substitute variables in steps with correct format based on step type
    if variables:
        for step in steps:
            if "script" in step:
                # Script step: Use @option.VAR@ format
                step["script"] = _substitute_variables_in_command(step["script"], variables, is_script=True)
            elif "exec" in step:
                # Exec step: Use ${option.VAR} format
                step["exec"] = _substitute_variables_in_command(step["exec"], variables, is_script=False)

    # Default node filter if not specified
    if not node_filter:
        node_filter = {"filter": "name: localhost"}

    # Normalize node_filter
    if isinstance(node_filter, str):
        node_filter = {"filter": node_filter}

    # Build job definition
    job_def = {
        "uuid": _generate_job_uuid(),
        "name": name,
        "description": description,
        "group": group,
        "loglevel": log_level,
        "multipleExecutions": multiple_executions,
        "executionEnabled": execution_enabled,
        "scheduleEnabled": schedule_enabled,
        "sequence": {"keepgoing": False, "strategy": "node-first", "commands": steps},
    }

    # Add optional fields
    if options:
        job_def["options"] = options
    if node_filter:
        job_def["nodefilters"] = node_filter
    if schedule:
        job_def["schedule"] = schedule
        job_def["schedules"] = []
    if timeout:
        job_def["timeout"] = timeout
    if retry_count:
        job_def["retry"] = str(retry_count)

    # Convert to YAML and import
    job_yaml = yaml.dump([job_def], default_flow_style=False)
    headers = {"Content-Type": "application/yaml"}
    params = {"fileformat": "yaml", "dupeOption": dupe_option}

    response = client._make_request(
        "POST", f"project/{project}/jobs/import", data=job_yaml, params=params, headers=headers
    )

    return response


def create_job(
    project: str,
    name: str,
    command: str = "",
    description: str = "",
    group: str | None = None,
    options: dict[str, Any] | list[dict[str, Any]] | str | None = None,
    schedule: dict[str, Any] | None = None,
    node_filter: dict[str, Any] | str | None = None,
    workflow: list[dict[str, Any]] | str | None = None,
    timeout: str | None = None,
    retry_count: int | None = None,
    execution_enabled: bool = True,
    schedule_enabled: bool = True,
    multiple_executions: bool = False,
    log_level: str = "INFO",
    dupe_option: str = "create",
    server: str | None = None,
) -> dict[str, Any]:
    """Create a Rundeck job with pre-defined workflow steps.

    Use this for: Jobs with multiple step types (exec, script, plugin steps)
    Supports: All Rundeck step types via workflow parameter

    Step Types Supported (via workflow parameter):
    - exec: Command execution - {"exec": "df -h", "description": "Check disk"}
    - script: Script execution - {"script": "#!/bin/bash\\necho test", "description": "Run script"}
    - jobref: Job reference - {"jobref": {"name": "Other Job", "uuid": "..."}, "description": "Chain job"}
    - Plugin steps: SQL, Ansible, HTTP, etc. - {"type": "plugin-name", "nodeStep": true/false, "configuration": {...}}

    Variable Format in Steps:
    - Script steps (script field): Use @option.variablename@
    - Exec steps (exec field): Use ${option.variablename}
    - Plugin steps: Depends on plugin (usually ${option.variablename})

    Args:
        project: Project name
        name: Job name
        command: Single command or script (if workflow not provided)
        description: Brief job description
        group: Job group (optional)
        options: Job options as dict or list (optional)
        schedule: Schedule config (optional)
        node_filter: Node targeting (optional)
        workflow: List of step dicts supporting ALL Rundeck step types (optional)
        timeout: Max runtime (optional)
        retry_count: Retry attempts (optional)
        execution_enabled: Enable execution
        schedule_enabled: Enable schedule
        multiple_executions: Allow concurrent runs
        log_level: Logging level
        dupe_option: Duplicate handling (create/update/skip)
        server: Server name/alias

    Returns:
        Job creation response

    Example workflow with multiple step types:
        workflow = [
            {"exec": "echo 'Starting'", "description": "Start"},
            {"script": "#!/bin/bash\\ndf -h", "description": "Check disk"},
            {"type": "org.rundeck.sqlrunner.SQLRunnerNodeStepPlugin",
             "nodeStep": true,
             "configuration": {"jdbcUrl": "...", "scriptBody": "SELECT * FROM ..."}},
            {"jobref": {"name": "Other Job", "uuid": "abc-123"}}
        ]

    Note:
        For automatic variable extraction and step breaking from simple scripts,
        use build_job() instead.
    """
    client = get_client(server)

    # Parse JSON strings
    if isinstance(options, str):
        options = json.loads(options)
    if isinstance(workflow, str):
        workflow = json.loads(workflow)

    # Extract steps from workflow dict
    if isinstance(workflow, dict) and "steps" in workflow:
        workflow = workflow["steps"]

    # Format options for Rundeck
    # Rundeck expects options as a list of dicts with specific keys
    if isinstance(options, list):
        # Options are already in list format, ensure proper structure
        formatted_options = []
        for opt in options:
            if isinstance(opt, dict) and "name" in opt:
                # Ensure required fields and normalize field names
                formatted_opt = {
                    "name": opt["name"],
                    "description": opt.get("description", ""),
                    "required": opt.get("required", False),
                }

                # Add optional fields if present
                if "value" in opt:
                    formatted_opt["value"] = opt["value"]
                if "defaultValue" in opt:
                    formatted_opt["defaultValue"] = opt["defaultValue"]
                if "default" in opt:
                    # Handle "default" field (map to "value" for Rundeck)
                    formatted_opt["value"] = opt["default"]
                if "label" in opt:
                    # Use label if provided
                    formatted_opt["label"] = opt["label"]
                if "secure" in opt:
                    formatted_opt["secure"] = opt["secure"]
                    formatted_opt["storagePath"] = opt.get("storagePath", "")
                    formatted_opt["valueExposed"] = opt.get("valueExposed", False)
                if "type" in opt:
                    formatted_opt["type"] = opt["type"]
                if "values" in opt:
                    formatted_opt["values"] = opt["values"]

                formatted_options.append(formatted_opt)
            else:
                raise ValueError(f"Invalid option format: {opt}")
        options = formatted_options
    elif isinstance(options, dict):
        # Convert dict format to list format for Rundeck
        formatted_options = []
        for opt_name, opt_config in options.items():
            formatted_opt = {
                "name": opt_name,
                "description": opt_config.get("description", ""),
                "required": opt_config.get("required", False),
            }

            # Add optional fields
            if "value" in opt_config:
                formatted_opt["value"] = opt_config["value"]
            if "defaultValue" in opt_config:
                formatted_opt["defaultValue"] = opt_config["defaultValue"]
            if "default" in opt_config:
                # Handle "default" field (map to "value" for Rundeck)
                formatted_opt["value"] = opt_config["default"]
            if "label" in opt_config:
                # Use label if provided, otherwise use description
                formatted_opt["label"] = opt_config["label"]
            if "secure" in opt_config:
                formatted_opt["secure"] = opt_config["secure"]
                formatted_opt["storagePath"] = opt_config.get("storagePath", "")
                formatted_opt["valueExposed"] = opt_config.get("valueExposed", False)
            if "type" in opt_config:
                formatted_opt["type"] = opt_config["type"]
            if "values" in opt_config:
                formatted_opt["values"] = opt_config["values"]

            formatted_options.append(formatted_opt)
        options = formatted_options

    # Build workflow steps
    if workflow:
        steps = workflow
    elif command:
        if command.strip().startswith("#!"):
            steps = [{"script": command}]
        else:
            steps = [{"exec": command}]
    else:
        raise ValueError("Either 'command' or 'workflow' parameter must be provided")

    # Set to run locally if no node filter specified
    if not node_filter:
        node_filter = {
            "dispatch": {
                "excludePrecedence": True,
                "keepgoing": False,
                "rankOrder": "ascending",
                "successOnEmptyNodeFilter": False,
                "threadcount": "1"
            },
            "filter": "name: localhost"
        }

    # Normalize node_filter if it's a string (convert to proper structure)
    if isinstance(node_filter, str):
        node_filter = {
            "dispatch": {
                "excludePrecedence": True,
                "keepgoing": False,
                "rankOrder": "ascending",
                "successOnEmptyNodeFilter": False,
                "threadcount": "1"
            },
            "filter": node_filter
        }
    elif isinstance(node_filter, dict) and "filter" in node_filter and "dispatch" not in node_filter:
        # Has filter but missing dispatch - add default dispatch
        node_filter["dispatch"] = {
            "excludePrecedence": True,
            "keepgoing": False,
            "rankOrder": "ascending",
            "successOnEmptyNodeFilter": False,
            "threadcount": "1"
        }

    # Build job definition
    job_def = {
        "uuid": _generate_job_uuid(),
        "name": name,
        "description": description,
        "group": group,
        "loglevel": log_level,
        "multipleExecutions": multiple_executions,
        "executionEnabled": execution_enabled,
        "scheduleEnabled": schedule_enabled,
        "sequence": {"keepgoing": False, "strategy": "node-first", "commands": steps},
    }

    # Add optional fields
    if options:
        job_def["options"] = options

    if schedule:
        if "cron" in schedule:
            job_def["schedule"] = {"time": schedule}
            job_def["schedules"] = []
        else:
            job_def["schedule"] = schedule
            job_def["schedules"] = []

    if node_filter:
        job_def["nodefilters"] = node_filter

    if timeout:
        job_def["timeout"] = timeout

    if retry_count:
        job_def["retry"] = str(retry_count)

    # Convert to YAML format (list format for job import)
    job_yaml = yaml.dump([job_def], default_flow_style=False)

    # Import the job via the API
    headers = {"Content-Type": "application/yaml"}
    params = {"fileformat": "yaml", "dupeOption": dupe_option}

    response = client._make_request(
        "POST", f"project/{project}/jobs/import", data=job_yaml, params=params, headers=headers
    )

    return response


def job_import(
    project: str,
    content: str,
    format: str,
    dupe_option: str = "create",
    uuid_option: str = "remove",
    server: str | None = None,
) -> dict[str, Any]:
    """Import jobs from YAML or JSON format with intelligent enhancements.

    Consolidates job import operations for different formats with automatic UUID generation
    and variable extraction capabilities.

    Args:
        project: Project name where jobs will be created
        content: Job definition content (YAML or JSON string)
        format: Import format - "yaml" or "json"
        dupe_option: Behavior for duplicate jobs (create, update, skip)
        uuid_option: UUID handling (preserve, remove)
        server: Server name/alias to use (e.g., "demo"), not the project name

    Returns:
        Job import response

    Raises:
        ValueError: If format is not supported or content is invalid

    Examples:
        # YAML import
        yaml_content = \'\'\'
        - name: Hello World Job
          description: A simple greeting job
          loglevel: INFO
          sequence:
            keepgoing: false
            strategy: node-first
            commands:
              - exec: echo "Hello, World!"
        \'\'\'
        job_import(project="my-project", content=yaml_content, format="yaml", server="demo")

        # JSON import
        json_content = \'\'\'
        [{
          "name": "Hello World Job",
          "description": "A simple greeting job",
          "loglevel": "INFO",
          "sequence": {
            "keepgoing": false,
            "strategy": "node-first",
            "commands": [{"exec": "echo \'Hello, World!\'"}]
          }
        }]
        \'\'\'
        job_import(project="my-project", content=json_content, format="json", server="demo")
    """
    valid_formats = ["yaml", "json"]
    if format not in valid_formats:
        raise ValueError(f"Invalid format '{format}'. Must be one of: {', '.join(valid_formats)}")

    client = get_client(server)

    if format == "yaml":
        # Handle YAML format
        try:
            parsed_jobs = yaml.safe_load(content)
            if not isinstance(parsed_jobs, list):
                raise ValueError("YAML must contain a list of job definitions")

            # Basic validation and UUID generation
            for i, job in enumerate(parsed_jobs):
                if not isinstance(job, dict):
                    raise ValueError(f"Job {i + 1} must be a dictionary")
                if "name" not in job:
                    raise ValueError(f"Job {i + 1} missing required \'name\' field")
                if "sequence" not in job:
                    raise ValueError(f"Job {i + 1} missing required \'sequence\' field")

                # Add UUID if not present (always generate new 16-digit alphanumeric UUID)
                job["uuid"] = _generate_job_uuid()

            # Convert back to YAML with UUIDs
            job_yaml = yaml.dump(parsed_jobs, default_flow_style=False)

        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML format: {e}") from e
        except Exception as e:
            raise ValueError(f"YAML validation failed: {e}") from e

    elif format == "json":
        # Handle JSON format with enhanced processing
        try:
            parsed_jobs = json.loads(content)
            if not isinstance(parsed_jobs, list):
                raise ValueError("JSON must contain a list of job definitions")

            # Convert JSON to YAML for Rundeck import with enhancements
            for job in parsed_jobs:
                # Add UUID if not present (always generate new 16-digit alphanumeric UUID)
                job["uuid"] = _generate_job_uuid()

                # Extract all script/command content for variable extraction
                all_scripts = []

                # Collect scripts from sequence
                if "sequence" in job:
                    if isinstance(job["sequence"], list):
                        for step in job["sequence"]:
                            if "script" in step:
                                all_scripts.append(step["script"])
                            elif "exec" in step:
                                all_scripts.append(step["exec"])
                    elif isinstance(job["sequence"], dict) and "commands" in job["sequence"]:
                        for cmd in job["sequence"]["commands"]:
                            if "script" in cmd:
                                all_scripts.append(cmd["script"])
                            elif "exec" in cmd:
                                all_scripts.append(cmd["exec"])

                # Extract variables from all scripts
                all_variables = set()
                for script in all_scripts:
                    if script:
                        variables = _extract_variables_from_command(script)
                        all_variables.update(variables)

                all_variables = sorted(list(all_variables))

                # Create or enhance job options
                existing_options = {}

                # Fix options format - convert array to dict if needed
                if "options" in job and isinstance(job["options"], list):
                    for opt in job["options"]:
                        if isinstance(opt, dict) and "name" in opt:
                            opt_name = opt.pop("name")
                            # Convert JSON format to YAML format
                            yaml_option = {}
                            if "description" in opt:
                                yaml_option["description"] = opt["description"]
                            if "required" in opt:
                                yaml_option["required"] = opt["required"]
                            if "value" in opt:
                                yaml_option["defaultValue"] = opt["value"]
                            if "values" in opt:
                                yaml_option["values"] = opt["values"]
                            if "secure" in opt:
                                yaml_option["secure"] = opt["secure"]
                            existing_options[opt_name] = yaml_option
                    job["options"] = existing_options
                elif "options" in job and isinstance(job["options"], dict):
                    existing_options = job["options"]

                # Add extracted variables as new options
                if all_variables:
                    extracted_options = _create_job_options_from_variables(all_variables)
                    extracted_options.update(existing_options)
                    job["options"] = extracted_options

                # Fix sequence structure - ensure commands array format
                if "sequence" in job and isinstance(job["sequence"], list):
                    # Convert list of steps to proper sequence format
                    job["sequence"] = {"keepgoing": False, "strategy": "node-first", "commands": job["sequence"]}
                elif "sequence" in job and isinstance(job["sequence"], dict):
                    # Ensure it has commands array
                    if "commands" not in job["sequence"]:
                        job["sequence"]["commands"] = []

                    # Process each command in the sequence with variable substitution
                    for step in job["sequence"]["commands"]:
                        if "script" in step:
                            # Apply variable substitution to script commands
                            script_content = step["script"]
                            if all_variables:
                                script_content = _substitute_variables_in_command(script_content, all_variables)
                            step["script"] = script_content
                        elif "exec" in step:
                            # Apply variable substitution to exec commands
                            exec_content = step["exec"]
                            if all_variables:
                                exec_content = _substitute_variables_in_command(exec_content, all_variables)
                            step["exec"] = exec_content

                # Fix variable substitution format
                job_str = json.dumps(job)
                # Replace @@option.VAR@@ with @option.VAR@
                job_str = re.sub(r"@@option\.([^@]+)@@", r"@option.\\1@", job_str)
                job.update(json.loads(job_str))

            # Convert to YAML
            job_yaml = yaml.dump(parsed_jobs, default_flow_style=False)

        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {e}") from e
        except Exception as e:
            raise ValueError(f"JSON processing failed: {e}") from e

    # Import the jobs via the API
    headers = {"Content-Type": "application/yaml"}
    params = {"fileformat": "yaml", "dupeOption": dupe_option, "uuidOption": uuid_option}

    response = client._make_request(
        "POST", f"project/{project}/jobs/import", data=job_yaml, params=params, headers=headers
    )

    return response


def modify_job(
    job_id: str,
    name: str | None = None,
    command: str | None = None,
    description: str | None = None,
    group: str | None = None,
    options: dict[str, Any] | None = None,
    schedule: dict[str, Any] | None = None,
    node_filter: dict[str, Any] | None = None,
    timeout: str | None = None,
    retry_count: int | None = None,
    execution_enabled: bool | None = None,
    schedule_enabled: bool | None = None,
    multiple_executions: bool | None = None,
    log_level: str | None = None,
    enhance_job: bool = True,
    confirmed: bool = False,
    server: str | None = None,
) -> dict[str, Any]:
    """Modify an existing Rundeck job by deleting and recreating with same UUID.

    🟡 MEDIUM RISK: This operation deletes and recreates the job, preserving the UUID.

    IMPORTANT: This operation follows the pattern: delete job, modify, and replace
    with the same UUID. The job will be temporarily unavailable during the process.

    Args:
        job_id: Job ID to modify
        name: New job name (optional - uses existing if not provided)
        command: New command to execute (optional - uses existing if not provided)
        description: New job description (optional - uses existing if not provided)
        group: New job group name (optional - uses existing if not provided)
        options: New job input options (optional - uses existing if not provided)
        schedule: New schedule configuration (optional - uses existing if not provided)
        node_filter: New node targeting configuration (optional - uses existing if not provided)
        timeout: New maximum runtime (optional - uses existing if not provided)
        retry_count: New number of retry attempts (optional - uses existing if not provided)
        execution_enabled: New execution enabled state (optional - uses existing if not provided)
        schedule_enabled: New schedule enabled state (optional - uses existing if not provided)
        multiple_executions: New concurrent executions setting (optional - uses existing if not provided)
        log_level: New logging level (optional - uses existing if not provided)
        enhance_job: Enable job enhancement features (default: True)
        confirmed: Must be True to confirm modification (required safety check)
        server: Server name/alias to use (e.g., "demo"), not the project name

    Returns:
        Job modification response

    Raises:
        ValueError: If confirmed is not True
    """
    if not confirmed:
        # Get job details for user confirmation
        try:
            job_def = get_job_definition(job_id, server)
            job_info = f"Job '{job_def.name}' (ID: {job_id}) in project '{job_def.project}'"
            if job_def.description:
                job_info += f"\nDescription: {job_def.description}"
        except Exception:
            job_info = f"Job ID: {job_id}"

        raise ValueError(
            f"🚨 CONFIRMATION REQUIRED 🚨\n\n"
            f"You are about to MODIFY this job:\n{job_info}\n\n"
            f"This operation will:\n"
            f"1. Delete the existing job\n"
            f"2. Create a new job with the same UUID\n"
            f"3. Apply the specified modifications\n\n"
            f"The job will be temporarily unavailable during this process.\n\n"
            f"To proceed, call this function again with confirmed=True"
        )

    # Get existing job definition to preserve UUID and unspecified values
    existing_job = get_job_definition(job_id, server)
    existing_uuid = existing_job.uuid
    project = existing_job.project

    # Use existing values for unspecified parameters
    final_name = name if name is not None else existing_job.name
    final_description = description if description is not None else existing_job.description
    final_group = group if group is not None else existing_job.group
    final_execution_enabled = execution_enabled if execution_enabled is not None else existing_job.execution_enabled
    final_schedule_enabled = schedule_enabled if schedule_enabled is not None else existing_job.schedule_enabled
    final_multiple_executions = multiple_executions if multiple_executions is not None else existing_job.multiple_executions
    final_log_level = log_level if log_level is not None else existing_job.log_level

    # Handle complex fields
    final_options = options if options is not None else (existing_job.options or {})
    final_schedule = schedule if schedule is not None else existing_job.schedule
    final_node_filter = node_filter if node_filter is not None else existing_job.node_filter
    final_timeout = timeout if timeout is not None else existing_job.timeout
    final_retry_count = retry_count if retry_count is not None else existing_job.retry_count

    # Extract command from existing job if not provided
    if command is None:
        # Extract command from existing workflow steps
        if existing_job.workflow_steps:
            final_command = "\n".join([step.get("exec", "") for step in existing_job.workflow_steps if "exec" in step])
            if not final_command:
                final_command = "\n".join([step.get("script", "") for step in existing_job.workflow_steps if "script" in step])
        else:
            final_command = "echo 'No command specified'"
    else:
        final_command = command

    # Step 1: Delete the existing job
    delete_response = delete_job(job_id, confirmed=True, server=server)

    # Step 2: Create the modified job with the same UUID
    try:
        # Build the job definition with preserved UUID
        job_def = {
            "uuid": existing_uuid,  # Preserve the original UUID
            "name": final_name,
            "description": final_description,
            "group": final_group,
            "loglevel": final_log_level,
            "multipleExecutions": final_multiple_executions,
            "executionEnabled": final_execution_enabled,
            "scheduleEnabled": final_schedule_enabled,
        }

        # Process command with enhancement if enabled
        if enhance_job:
            # Extract variables from command
            variables = _extract_variables_from_command(final_command)

            # Break command into logical steps
            steps = _break_command_into_steps(final_command, final_name)

            # Apply variable substitution to steps using @option.VAR@ format
            for step in steps:
                step["exec"] = _substitute_variables_in_command(step["exec"], variables)

            # Generate enhanced description with markdown
            if variables:
                markdown_doc = _generate_markdown_documentation(final_name, final_description, variables, steps)
                job_def["description"] = f"{final_description}\n\n{markdown_doc}" if final_description else markdown_doc

                # Merge extracted options with provided options
                extracted_options = _create_job_options_from_variables(variables)
                extracted_options.update(final_options)
                final_options = extracted_options

            job_def["sequence"] = {"keepgoing": False, "strategy": "node-first", "commands": steps}
        else:
            # Simple single-step job
            job_def["sequence"] = {"keepgoing": False, "strategy": "node-first", "commands": [{"exec": final_command}]}

        # Add optional fields
        if final_options:
            job_def["options"] = final_options

        if final_schedule:
            if isinstance(final_schedule, dict) and "cron" in final_schedule:
                job_def["schedule"] = {"crontab": final_schedule["cron"]}
            else:
                job_def["schedule"] = final_schedule

        if final_node_filter:
            job_def["nodefilters"] = final_node_filter

        if final_timeout:
            job_def["timeout"] = final_timeout

        if final_retry_count:
            job_def["retry"] = str(final_retry_count)

        # Convert to YAML and import
        job_yaml = yaml.dump([job_def], default_flow_style=False)

        client = get_client(server)
        headers = {"Content-Type": "application/yaml"}
        params = {"fileformat": "yaml", "dupeOption": "create"}

        response = client._make_request(
            "POST", f"project/{project}/jobs/import", data=job_yaml, params=params, headers=headers
        )

        return {
            "success": True,
            "message": f"Job successfully modified and recreated with UUID {existing_uuid}",
            "delete_response": delete_response,
            "create_response": response,
            "preserved_uuid": existing_uuid
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to recreate job after deletion: {str(e)}",
            "delete_response": delete_response,
            "preserved_uuid": existing_uuid,
            "warning": "Original job was deleted but recreation failed. Manual intervention may be required."
        }


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
        build_job,
        create_job,
        job_import,
        modify_job,
        job_control,
        delete_job,
    ],
}
