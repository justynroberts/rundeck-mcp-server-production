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
    """Generate a 16-digit alphanumeric random UUID for job creation.

    Returns:
        16-character string containing random letters and numbers
    """
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(16))


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
    """Break a command into logical script steps."""
    lines = [line.strip() for line in command.split("\n") if line.strip()]

    if len(lines) <= 1:
        # Single line command - return as single step
        return [{"exec": command, "description": f"Execute {name}"}]

    steps = []
    current_step_lines = []
    step_counter = 1

    for line in lines:
        # Check if this line starts a new logical step
        if (
            line.startswith("#")
            or line.startswith('echo "=')
            or line.startswith('echo "===')
            or any(
                keyword in line.lower()
                for keyword in [
                    "install",
                    "download",
                    "setup",
                    "configure",
                    "start",
                    "stop",
                    "restart",
                    "deploy",
                    "backup",
                    "cleanup",
                ]
            )
        ) and current_step_lines:
            step_command = "\n".join(current_step_lines)
            steps.append(
                {
                    "exec": step_command,
                    "description": f"Step {step_counter}: {_infer_step_description(current_step_lines[0])}",
                }
            )
            step_counter += 1
            current_step_lines = []

        current_step_lines.append(line)

    # Add final step
    if current_step_lines:
        step_command = "\n".join(current_step_lines)
        steps.append(
            {
                "exec": step_command,
                "description": f"Step {step_counter}: {_infer_step_description(current_step_lines[0])}",
            }
        )

    return steps


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


def _substitute_variables_in_command(command: str, variables: list[str]) -> str:
    """Replace variable references with Rundeck option syntax.

    Rules:
    - One line commands: use ${option.variablename} format
    - Multi-line scripts: use @option.variablename@ format
    """
    modified_command = command
    is_single_line = len([line for line in command.split('\n') if line.strip()]) <= 1

    for var in variables:
        if is_single_line:
            # Single line command - use ${option.VAR} format
            modified_command = re.sub(rf"\${{{var}}}", f"${{option.{var}}}", modified_command, flags=re.IGNORECASE)
            modified_command = re.sub(rf"\${var}(?![A-Za-z0-9_])", f"${{option.{var}}}", modified_command, flags=re.IGNORECASE)
        else:
            # Multi-line script - use @option.VAR@ format
            modified_command = re.sub(rf"\${{{var}}}", f"@option.{var}@", modified_command, flags=re.IGNORECASE)
            modified_command = re.sub(rf"\${var}(?![A-Za-z0-9_])", f"@option.{var}@", modified_command, flags=re.IGNORECASE)

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
            doc += f"   {step['exec']}\n"
            doc += "   ```\n\n"
    else:
        doc += "## Execution\n\n"
        doc += f"```bash\n{steps[0]['exec']}\n```\n\n"

    doc += "## Notes\n\n"
    doc += "- Job runs locally if no target nodes specified\n"
    doc += "- Variables are automatically extracted and created as job options\n"
    doc += "- Variable substitution rules:\n"
    doc += "  - Single-line commands: `${option.VARIABLENAME}` format\n"
    doc += "  - Multi-line scripts: `@option.VARIABLENAME@` format\n"

    return doc


def create_job(
    project: str,
    name: str,
    command: str,
    description: str = "",
    group: str | None = None,
    options: dict[str, Any] | None = None,
    schedule: dict[str, Any] | None = None,
    node_filter: dict[str, Any] | None = None,
    timeout: str | None = None,
    retry_count: int | None = None,
    execution_enabled: bool = True,
    schedule_enabled: bool = True,
    multiple_executions: bool = False,
    log_level: str = "INFO",
    dupe_option: str = "create",
    enhance_job: bool = True,
    server: str | None = None,
) -> dict[str, Any]:
    """Create a new Rundeck job.

    Args:
        project: Project name where job will be created
        name: Job name
        command: Command to execute
        description: Job description (optional)
        group: Job group name (optional)
        options: Job input options (optional)
        schedule: Schedule configuration (optional, e.g., {"cron": "0 0 * * *"})
        node_filter: Node targeting configuration (optional)
        timeout: Maximum runtime (optional, e.g., "30m")
        retry_count: Number of retry attempts (optional)
        execution_enabled: Whether job execution is enabled
        schedule_enabled: Whether job schedule is enabled
        multiple_executions: Allow concurrent executions
        log_level: Logging level (DEBUG, VERBOSE, INFO, WARN, ERROR)
        dupe_option: Behavior for duplicate jobs (create, update, skip)
        enhance_job: Enable job enhancement features (default: True)
        server: Server name/alias to use (e.g., "demo"), not the project name

    Returns:
        Job creation response

    Enhancement Features (when enhance_job=True):
        - Breaks commands into logical script steps
        - Generates markdown documentation
        - Extracts variables and creates job options automatically
        - Substitutes variables with @option.VARIABLENAME@ format
        - Sets job to run locally if no target nodes specified

    Example:
        create_job(
            project="my-project",
            name="Hello World Job",
            command="echo 'Hello, World!'",
            description="A simple greeting job",
            group="examples",
            schedule={"cron": "0 9 * * MON-FRI"},
            server="demo"
        )
    """
    client = get_client(server)

    # Enhanced job processing
    if enhance_job:
        # Extract variables from command
        variables = _extract_variables_from_command(command)

        # Break command into logical steps
        steps = _break_command_into_steps(command, name)

        # Generate markdown documentation
        markdown_doc = _generate_markdown_documentation(name, description, variables, steps)
        enhanced_description = f"{description}\n\n{markdown_doc}" if description else markdown_doc

        # Create job options from variables
        if variables:
            extracted_options = _create_job_options_from_variables(variables)
            # Merge with user-provided options
            if options:
                extracted_options.update(options)
            options = extracted_options

            # Substitute variables in steps
            for step in steps:
                step["exec"] = _substitute_variables_in_command(step["exec"], variables)

        # Set to run locally if no node filter specified
        if not node_filter:
            node_filter = {"dispatch": {"threadcount": "1"}, "filter": "name: localhost"}
    else:
        # Simple single-step job
        steps = [{"exec": command, "description": f"Execute {name}"}]
        enhanced_description = description

    # Build the job definition in YAML format
    job_def = {
        "uuid": _generate_job_uuid(),
        "name": name,
        "description": enhanced_description,
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
            job_def["schedule"] = {"crontab": schedule["cron"]}
        else:
            job_def["schedule"] = schedule

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


def create_job_from_yaml(
    project: str,
    job_yaml: str,
    dupe_option: str = "create",
    uuid_option: str = "remove",
    server: str | None = None,
) -> dict[str, Any]:
    """Create job(s) from YAML definition.

    Args:
        project: Project name where jobs will be created
        job_yaml: YAML string containing job definition(s)
        dupe_option: Behavior for duplicate jobs (create, update, skip)
        uuid_option: UUID handling (preserve, remove)
        server: Server name/alias to use (e.g., "demo"), not the project name

    Returns:
        Job import response

    Example:
        yaml_content = '''
        - name: Hello World Job
          description: A simple greeting job
          loglevel: INFO
          sequence:
            keepgoing: false
            strategy: node-first
            commands:
              - exec: echo "Hello, World!"
          schedule:
            crontab: "0 9 * * MON-FRI"
        '''

        create_job_from_yaml(
            project="my-project",
            job_yaml=yaml_content,
            server="demo"
        )
    """
    client = get_client(server)

    # Validate YAML format
    try:
        parsed_jobs = yaml.safe_load(job_yaml)
        if not isinstance(parsed_jobs, list):
            raise ValueError("YAML must contain a list of job definitions")

        # Basic validation and UUID generation
        for i, job in enumerate(parsed_jobs):
            if not isinstance(job, dict):
                raise ValueError(f"Job {i + 1} must be a dictionary")
            if "name" not in job:
                raise ValueError(f"Job {i + 1} missing required 'name' field")
            if "sequence" not in job:
                raise ValueError(f"Job {i + 1} missing required 'sequence' field")

            # Add UUID if not present (always generate new 16-digit alphanumeric UUID)
            job["uuid"] = _generate_job_uuid()

        # Convert back to YAML with UUIDs
        job_yaml = yaml.dump(parsed_jobs, default_flow_style=False)

    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML format: {e}") from e
    except Exception as e:
        raise ValueError(f"YAML validation failed: {e}") from e

    # Import the jobs via the API
    headers = {"Content-Type": "application/yaml"}
    params = {"fileformat": "yaml", "dupeOption": dupe_option, "uuidOption": uuid_option}

    response = client._make_request(
        "POST", f"project/{project}/jobs/import", data=job_yaml, params=params, headers=headers
    )

    return response


def create_multiple_jobs_from_yaml(
    project: str,
    yaml_file_content: str,
    dupe_option: str = "create",
    uuid_option: str = "remove",
    server: str | None = None,
) -> dict[str, Any]:
    """Create multiple jobs from a YAML file content.

    Args:
        project: Project name where jobs will be created
        yaml_file_content: Full YAML file content with multiple job definitions
        dupe_option: Behavior for duplicate jobs (create, update, skip)
        uuid_option: UUID handling (preserve, remove)
        server: Server name/alias to use (e.g., "demo"), not the project name

    Returns:
        Job import response with details of succeeded/failed/skipped jobs

    Example:
        yaml_content = '''
        - name: Job 1
          description: First job
          loglevel: INFO
          sequence:
            commands:
              - exec: echo "Job 1"

        - name: Job 2
          description: Second job
          loglevel: INFO
          sequence:
            commands:
              - exec: echo "Job 2"
        '''

        create_multiple_jobs_from_yaml(
            project="my-project",
            yaml_file_content=yaml_content,
            server="demo"
        )
    """
    return create_job_from_yaml(
        project=project, job_yaml=yaml_file_content, dupe_option=dupe_option, uuid_option=uuid_option, server=server
    )


def create_job_from_json(
    project: str,
    json_content: str,
    dupe_option: str = "create",
    uuid_option: str = "remove",
    server: str | None = None,
) -> dict[str, Any]:
    """Create job(s) from JSON definition.

    Args:
        project: Project name where jobs will be created
        json_content: JSON string containing job definition(s)
        dupe_option: Behavior for duplicate jobs (create, update, skip)
        uuid_option: UUID handling (preserve, remove)
        server: Server name/alias to use (e.g., "demo"), not the project name

    Returns:
        Job import response

    Example:
        json_content = '''
        [{
          "name": "Hello World Job",
          "description": "A simple greeting job",
          "loglevel": "INFO",
          "sequence": {
            "keepgoing": false,
            "strategy": "node-first",
            "commands": [
              {"exec": "echo 'Hello, World!'"}
            ]
          }
        }]
        '''

        create_job_from_json(
            project="my-project",
            json_content=json_content,
            server="demo"
        )
    """
    client = get_client(server)

    # Parse JSON and validate structure
    try:
        parsed_jobs = json.loads(json_content)
        if not isinstance(parsed_jobs, list):
            raise ValueError("JSON must contain a list of job definitions")

        # Convert JSON to YAML for Rundeck import
        # Fix common JSON format issues and enhance jobs
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
                        if "enforced" in opt:
                            yaml_option["enforced"] = opt["enforced"]
                        if "regex" in opt:
                            yaml_option["regex"] = opt["regex"]
                        if "regexError" in opt:
                            yaml_option["regexError"] = opt["regexError"]
                        existing_options[opt_name] = yaml_option
            elif "options" in job and isinstance(job["options"], dict):
                existing_options = job["options"]

            # Add extracted variables as job options (if not already present)
            if all_variables:
                extracted_options = _create_job_options_from_variables(all_variables)
                # Merge existing options with extracted ones (existing takes precedence)
                for var, config in extracted_options.items():
                    if var not in existing_options:
                        existing_options[var] = config

            # Set the final options
            job["options"] = existing_options if existing_options else {}

            # Fix sequence format - ensure it's the right structure
            if "sequence" in job and isinstance(job["sequence"], list):
                # Convert list of steps to proper sequence format
                steps = job["sequence"]
                job["sequence"] = {"keepgoing": False, "strategy": "node-first", "commands": []}
                for step in steps:
                    if "script" in step:
                        # Convert script to exec command and apply variable substitution
                        script_content = step["script"]
                        if all_variables:
                            script_content = _substitute_variables_in_command(script_content, all_variables)
                        command = {"exec": script_content}
                        if "description" in step:
                            command["description"] = step["description"]
                        job["sequence"]["commands"].append(command)
                    elif "exec" in step:
                        # Apply variable substitution to exec commands
                        exec_content = step["exec"]
                        if all_variables:
                            exec_content = _substitute_variables_in_command(exec_content, all_variables)
                        step_copy = step.copy()
                        step_copy["exec"] = exec_content
                        job["sequence"]["commands"].append(step_copy)
                    else:
                        job["sequence"]["commands"].append(step)

            # Fix variable substitution format
            job_str = json.dumps(job)
            # Replace @@option.VAR@@ with @option.VAR@
            job_str = re.sub(r"@@option\.([^@]+)@@", r"@option.\1@", job_str)
            job.update(json.loads(job_str))

        # Convert to YAML
        job_yaml = yaml.dump(parsed_jobs, default_flow_style=False)

    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format: {e}") from e
    except Exception as e:
        raise ValueError(f"JSON processing failed: {e}") from e

    # Import the jobs via the API using YAML format
    headers = {"Content-Type": "application/yaml"}
    params = {"fileformat": "yaml", "dupeOption": dupe_option, "uuidOption": uuid_option}

    response = client._make_request(
        "POST", f"project/{project}/jobs/import", data=job_yaml, params=params, headers=headers
    )

    return response


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
        create_job,
        create_job_from_yaml,
        create_job_from_json,
        create_multiple_jobs_from_yaml,
        enable_job,
        disable_job,
        enable_job_schedule,
        disable_job_schedule,
        delete_job,
    ],
}
