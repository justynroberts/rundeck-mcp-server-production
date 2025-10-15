# Rundeck MCP Tool Prompts - Complete Reference

This document consolidates ALL prompt rules and guidance for Rundeck MCP tools.

---

## 🌐 GLOBAL GUIDANCE (All Tools)

**Error Handling Philosophy:**
> IMPORTANT: If a tool encounters errors (node not found, project not found, job not found, connection issues, etc.), it's okay to stop and report the error clearly. Do not attempt workarounds or continue with partial information. Fail fast and fail clearly. When nodes are not found or unavailable, stop execution immediately and inform the user.

---

## 📊 SERVER & PROJECT MANAGEMENT

### list_servers
**Purpose:** List all configured Rundeck servers

**Rules:**
- Display as a table
- Shows URLs and API versions
- Use before specifying servers in other tools

---

### get_projects
**Purpose:** Get all Rundeck projects available in your instance

**Rules:**
- Use to discover available projects before working with jobs/executions
- Optionally specify server name for specific Rundeck instance

---

### create_project
**Purpose:** Create a new Rundeck project

**Rules:**
- Provide project name (REQUIRED)
- Description (optional)
- Custom configuration properties (optional)
- Use descriptive names
- ALWAYS specify target server
- Automatically sets up default node resources configuration

---

### get_project_stats
**Purpose:** Get comprehensive statistics for a project

**Rules:**
- Shows job counts (total, enabled, scheduled)
- Recent execution metrics
- Project configuration
- Ideal for project health dashboards

---

## 🔧 JOB MANAGEMENT

### get_jobs
**Purpose:** Get jobs from a Rundeck project with optional filtering

**Rules:**
- Human-readable formatting
- Status indicators:
  - ✅ enabled
  - ❌ disabled
  - ⏰ scheduled
  - 🔧 manual
- Organized by group

---

### get_job_definition
**Purpose:** Get detailed job definition

**Rules:**
- Shows workflow steps, input options, scheduling, execution settings
- Essential before execution
- If asked to describe in detail, also create flowchart avoiding special characters

---

### create_job ⚠️ CRITICAL RULES
**Purpose:** Create a new Rundeck job in a project

**MULTI-STEP JOBS (IMPORTANT):**
- WHERE POSSIBLE, create multi-step jobs by chaining commands in `sequence.commands` array
- Break complex workflows into logical phases: pre-check → execute → validate → cleanup
- Each step should have clear description
- Mix step types: script (complex), exec (simple), plugins (specialized)

**STEP TYPE DECISION MATRIX:**
- ⚠️ **ANY script (bash/PowerShell/Python/etc.) → ALWAYS use `script:` type**
- Multi-line commands → `script:`
- Pipes (|), redirects (>, <) → `script:`
- Command chaining (&&, ||, ;) → `script:`
- Loops, conditionals, heredocs → `script:`
- ✅ **ONLY use `exec:` for single simple commands** (ls, echo, df, etc.)
- SQL queries → SQL Runner plugin
- Package/service management → Ansible plugin
- API calls → HTTP plugin

**SCRIPT SPLITTING (CRITICAL):**
- Split scripts into separate steps where logical
- Each logical phase = separate script step
- Examples: setup → process → validate, pre-check → backup → deploy → verify
- Each step should have clear description of its purpose

**SCRIPT INTERPRETER (CRITICAL):**
- ALWAYS set `scriptInterpreter` field for script steps
- Match interpreter to script content:
  - Bash scripts → `scriptInterpreter: bash`
  - PowerShell scripts → `scriptInterpreter: powershell`
  - Python scripts → `scriptInterpreter: python3`
  - Match shebang: `#!/usr/bin/python3` → `scriptInterpreter: python3`

**VARIABLE RULES:**
- Script steps (`script:` field) → `@option.VAR@`
- Everything else (exec, plugins, jobrefs) → `${option.VAR}`

**JOB METADATA:**
- Tags should be relevant to job's purpose (deployment, monitoring, backup, database, etc.)
- UUIDs are auto-generated - do NOT provide id or uuid fields

**EXAMPLES:**

❌ **WRONG - Multi-line in exec:**
```yaml
- exec: |
    echo "Starting"
    cp /src/* /dest/
```

✅ **CORRECT - Multi-line in script:**
```yaml
- description: Copy files
  script: |
    #!/bin/bash
    echo "Starting"
    cp /src/@option.version@/* /dest/
  scriptInterpreter: bash
```

❌ **WRONG - Pipe in exec:**
```yaml
- exec: ps aux | grep java
```

✅ **CORRECT - Pipe in script:**
```yaml
- description: Find Java processes
  script: |
    #!/bin/bash
    ps aux | grep @option.process@
  scriptInterpreter: bash
```

✅ **ACCEPTABLE - Simple exec:**
```yaml
- exec: ls -la /tmp
  description: List temp files
```

**COMPLETE JOB EXAMPLE:**
```yaml
sequence:
  commands:
  - description: Check disk space
    exec: df -h

  - description: Deploy application
    script: |
      #!/bin/bash
      echo "Deploying version @option.version@"
      cp -r /staging/@option.version@/* /opt/app/
      chown -R appuser:appgroup /opt/app/
    scriptInterpreter: bash

  - description: Update database schema
    type: org.rundeck.sqlrunner.SQLRunnerNodeStepPlugin
    nodeStep: true
    configuration:
      jdbcUrl: jdbc:mysql://localhost/${option.database}
      user: ${option.db_user}
      password: keys/db_password
      scriptBody: |
        UPDATE config SET version='${option.version}' WHERE app='${option.app}';
        INSERT INTO deploy_log VALUES (NOW(), '${option.version}');

  - description: Restart service
    type: com.batix.rundeck.plugins.AnsiblePlaybookInlineWorkflowNodeStep
    nodeStep: true
    configuration:
      ansible-playbook-inline: |
        - hosts: all
          tasks:
          - name: Restart ${option.service}
            systemd:
              name: ${option.service}
              state: restarted

  - description: Health check
    script: |
      #!/bin/bash
      for i in {1..30}; do
        if curl -f http://localhost:@option.port@/health; then
          echo "Service healthy"
          exit 0
        fi
        sleep 2
      done
      echo "Health check failed"
      exit 1
    scriptInterpreter: bash
```

**Reference:** See SAMPLE_JOB.yaml and VARIABLE_RULES.md

---

### job_import
**Purpose:** Import jobs from YAML or JSON format

**CRITICAL:** Same rules as create_job

**MULTI-STEP:** Chain commands in sequence.commands array (pre-check → execute → validate)

**STEP TYPE:**
- ⚠️ **ANY script (bash/PowerShell/Python) → ALWAYS `script:` type**
- ✅ **ONLY use `exec:` for single simple commands**
- Split scripts into separate steps where logical

**SCRIPT INTERPRETER:** ALWAYS set for script steps (bash, python3, powershell)

**VARIABLES:** Script steps → `@option.VAR@`, Exec/plugins → `${option.VAR}`

**TAGS:** Relevant to job purpose (deployment, monitoring, backup, etc.)

**Additional:**
- Generates UUIDs automatically
- Validates structure
- Validates all jobs have `name` and `sequence.commands` array

**MULTI-STEP EXAMPLE:**
```yaml
sequence:
  commands:
  - description: Pre-check
    exec: echo "Starting"
  - description: Execute task
    script: |
      #!/bin/bash
      echo "test" | tee log.txt
    scriptInterpreter: bash
  - description: Validate
    exec: cat log.txt
```

**Reference:** See SAMPLE_JOB.yaml

---

### modify_job
**Purpose:** Modify an existing Rundeck job

**Risk:** 🟡 MEDIUM RISK - JOB MODIFICATION

**Process:** Delete/recreate with same UUID. Job temporarily unavailable during modification.

**CRITICAL:** Same rules as create_job

**MULTI-STEP:** Chain commands in sequence.commands array (pre-check → execute → validate)

**STEP TYPE:**
- ⚠️ **ANY script (bash/PowerShell/Python) → ALWAYS `script:` type**
- ✅ **ONLY use `exec:` for single simple commands**
- Split scripts into separate steps where logical

**SCRIPT INTERPRETER:** ALWAYS set for script steps (bash, python3, powershell)

**VARIABLES:** Script steps → `@option.VAR@`, Exec/plugins → `${option.VAR}`

**TAGS:** Relevant to job purpose (deployment, monitoring, backup, etc.)

**Safety:**
- Requires `confirmed=True` for safety
- ❌ WRONG: Multi-line or pipes in exec
- ✅ CORRECT: Use script with shebang and scriptInterpreter field

**Reference:** See SAMPLE_JOB.yaml

---

### job_control
**Purpose:** Control job execution and scheduling state

**Risk:** 🟡 MEDIUM RISK

**Operations:**
1. **'enable'** - Activate job execution and scheduling
   - 🟢 GREEN SQUARE, LOW RISK

2. **'disable'** - Completely disable job
   - 🟡 AMBER SQUARE, MEDIUM RISK - SERVICE IMPACT

3. **'enable_schedule'** - Enable only scheduling
   - 🟢 GREEN SQUARE, LOW RISK

4. **'disable_schedule'** - Disable only scheduling (manual execution still works)
   - 🟡 AMBER SQUARE, LOW-MEDIUM RISK - AUTOMATION IMPACT

**Usage:**
- Maintenance windows
- Bringing jobs online/offline
- Controlling automation vs manual execution
- Always show appropriate risk level emoji and impact assessment

---

### delete_job
**Purpose:** PERMANENTLY DELETE a job

**Risk:** 🔴 HIGH RISK - DESTRUCTIVE

**🚨 CRITICAL SAFETY PROTOCOL 🚨**
- ALWAYS show red square emoji and Impact assessment: HIGH RISK - PERMANENT DATA LOSS at beginning
- PERMANENTLY and IRREVERSIBLY deletes job from Rundeck
- Cannot be undone
- Destroys all job configuration, execution history, and schedules

**MANDATORY Two-Step Process:**
1. First call WITHOUT `confirmed=True` to show deletion preview and get user consent
2. Second call WITH `confirmed=True` to execute deletion

**Requirements:**
- Always display detailed job information
- Require explicit user confirmation before proceeding
- Use extreme caution

---

### analyze_job
**Purpose:** Comprehensive job analysis

**Analysis Includes:**
- Complete job definition download
- Purpose inference
- Node targeting analysis
- Workflow step breakdown
- Option requirements
- Schedule configuration
- Comprehensive risk assessment

**Output:**
- Impact level with colored emoji indicators
- Human-readable summary
- Complete raw JSON data

**Use Cases:**
- Understanding job behavior before execution
- Security review
- Operational planning

---

### visualize_job
**Purpose:** Generate visual flowchart representation

**Output Format:** Mermaid diagram syntax

**Shows:**
- Complete execution flow
- Job configuration
- Node filters
- Options
- Workflow steps
- Error handlers
- Color-coded nodes for different step types
- Emoji indicators
- Comprehensive legend

**Can Be Rendered In:**
- Mermaid Live Editor
- GitHub markdown
- VS Code
- Confluence
- Jira

**Use Cases:**
- Documentation
- Training
- Troubleshooting
- Understanding complex workflows

---

## ▶️ JOB EXECUTION

### run_job
**Purpose:** Execute a Rundeck job

**Rules:**
- Execute immediately with optional parameters and node filters
- Returns execution ID for monitoring
- Use get_job_definition first to understand required options

---

### run_job_with_monitoring
**Purpose:** Execute job with monitoring until completion

**Risk Assessment Required:**
- Estimate impact from risk/cost perspective
- ALWAYS show emoji (🔴 red, 🟡 amber, 🟢 green) and Impact assessment at beginning

**Job Options Display:**
- If job has options, display once as numbered list in table
- Use arrow emoji (→ or ←) to show:
  - → Required
  - ← Optional (with default value in brackets)
- Make sure required options are requested from user before execution

**Execution Flow:**
1. Stop to allow user to enter values in format: number/value
2. If only predefined values available, only let these be selected
3. Do NOT run without confirmation of options or defaults
4. Execute and wait for completion
5. Show output in code box
6. Include timeout protection
7. Return final execution status

**Use Cases:**
- Automated workflows requiring completion confirmation

---

### get_execution_status
**Purpose:** Get status and details of job execution

**Rules:**
- Shows execution state, timing, user, and node results
- Use execution ID returned from run_job

---

### get_execution_output
**Purpose:** Get output logs of job execution

**Rules:**
- Retrieve complete output logs
- Useful for debugging failed jobs or reviewing execution details

---

### get_executions
**Purpose:** Get executions for a project with filtering

**Display:**
- Human-readable formatting
- Status icons:
  - ✅ succeeded
  - ❌ failed
  - 🔄 running
- Supports pagination and filtering
- Returns formatted summaries by default
- Perfect for browsing recent activity

---

### get_all_executions
**Purpose:** Get all executions with automatic pagination

**Features:**
- Automatic pagination (up to specified limit)
- Status summaries
- Overview statistics
- Recent executions in human-readable format
- Ideal for comprehensive project analysis and reporting

---

### get_execution_metrics
**Purpose:** Get comprehensive execution metrics and analytics

**Metrics Include:**
- Success rates
- Duration statistics
- Job frequency analysis
- Performance trends over specified time period
- Perfect for project health assessment

---

### get_bulk_execution_status
**Purpose:** Get status for multiple executions efficiently

**Rules:**
- Check status in single operation
- More efficient than individual status checks
- Use when monitoring multiple jobs

---

### abort_execution
**Purpose:** Abort a running execution

**Risk:** 🔴 HIGH RISK

**Rules:**
- ALWAYS show red square emoji and Impact assessment: HIGH RISK at beginning
- Emergency stop for running job executions

**Use When:**
- Jobs consuming excessive resources
- Running longer than expected
- Need immediate termination

**Requirements:**
- Requires confirmation before proceeding
- Shows abort status
- Provides execution details

---

### retry_execution
**Purpose:** Retry a failed execution

**Risk:** 🟢 LOW RISK

**Rules:**
- Show green square emoji and Impact assessment: LOW RISK
- Re-execute failed job with optional parameter overrides

**Use Cases:**
- Transient failures
- Network issues
- When conditions have been corrected

**Features:**
- Can modify job options and node filters for retry
- Returns new execution ID for monitoring

---

### delete_execution
**Purpose:** Delete execution from system

**Risk:** 🟡 MEDIUM RISK - DATA LOSS

**Rules:**
- ALWAYS show amber square emoji and Impact assessment: MEDIUM RISK - DATA LOSS at beginning
- Permanently remove execution records from Rundeck
- Cannot be undone
- Requires confirmation

**Use Cases:**
- Cleanup
- Compliance
- Removing sensitive execution data
- Housekeeping and storage management

---

## 🖥️ NODE MANAGEMENT

### get_nodes
**Purpose:** Get nodes for a Rundeck project with optional filtering

**Display:**
- Human-readable formatting
- Node names
- Hostnames
- Operating systems
- Tags

**Features:**
- Supports filtering by node attributes or tags
- Perfect for infrastructure discovery and node inventory management

---

### get_node_details
**Purpose:** Get detailed information about specific node

**Details Include:**
- Hostname
- Operating system details
- Architecture
- Version
- Description
- Tags
- All custom attributes

**Use Case:**
- Essential for understanding node configuration and capabilities before job execution

---

### get_node_summary
**Purpose:** Get summary of nodes in project

**Statistics Include:**
- Total counts
- Operating system distribution
- Status breakdown
- Most common tags
- Infrastructure statistics

**Use Cases:**
- Infrastructure health assessment
- Capacity planning

---

### suggest_node_filters
**Purpose:** Suggest node filter patterns for targeting specific nodes

**⚠️ ESSENTIAL for Windows node troubleshooting**

**Use When:**
- Adhoc commands fail with 'No nodes matched'
- Need to find correct filter syntax

**Input:**
- Provide search term (like 'Server-1' or 'windows')

**Output:**
- Exact filter patterns
- Regex options
- Troubleshooting guidance for targeting Windows and other remote nodes

---

### run_adhoc_command
**Purpose:** Execute ad hoc commands directly on Rundeck nodes

**Risk:** 🟡 MEDIUM RISK - DIRECT SYSTEM ACCESS

**⚠️ ESSENTIAL for Windows node troubleshooting**

**Rules:**
- ALWAYS show amber square emoji and Impact assessment: MEDIUM RISK - DIRECT SYSTEM ACCESS at beginning
- Execute shell commands without creating permanent job definitions
- Specify command to run
- Target nodes via filter pattern (REQUIRED - no defaults)

**Filter Examples:**
- `name: Server-1-infra` - Exact node name
- `name: localhost` - Local execution
- `.*Windows.*` - Regex patterns
- `osFamily: windows` - OS filtering

**Critical Error Handling:**
- If node filter doesn't match any nodes: STOP IMMEDIATELY
- Report error with troubleshooting guidance
- Do not continue

**Workflow:**
1. Use get_nodes or suggest_node_filters first to identify correct node names and filter syntax
2. Specify explicit node_filter parameter
3. Require confirmation before execution

**Output:**
- Returns execution ID and output details

**Use Cases:**
- Windows diagnostics
- Quick maintenance tasks
- One-off commands
- System troubleshooting

---

## ⚙️ SYSTEM MANAGEMENT

### get_system_info
**Purpose:** Get Rundeck system information and health metrics

**Information Includes:**
- Version
- Health status
- Configuration details

---

### get_execution_mode
**Purpose:** Get current system execution mode

**Modes:**
- **ACTIVE** - Normal operations
- **PASSIVE** - Executions disabled

**Use Case:**
- Essential for understanding system state during maintenance or troubleshooting

---

### set_execution_mode
**Purpose:** Set system execution mode

**Risk:** 🔴 HIGH RISK - SYSTEM-WIDE IMPACT

**Rules:**
- ALWAYS show red square emoji and Impact assessment: HIGH RISK - SYSTEM-WIDE IMPACT at beginning
- Change global system execution mode

**Modes:**
- **ACTIVE** - Enables all job executions
- **PASSIVE** - Disables all job executions system-wide

**Requirements:**
- Requires explicit confirmation
- Affects all projects and jobs

**Use Cases:**
- Maintenance windows
- Emergency situations

---

## 📈 ANALYTICS

### calculate_job_roi
**Purpose:** Calculate ROI metrics for specific job

**Analysis Includes:**
- Execution costs
- Estimated manual work savings
- ROI percentage

**Use Cases:**
- Justify automation investments
- Identify optimization opportunities

---

## 📁 REFERENCE DOCUMENTS

### SAMPLE_JOB.yaml
Complete annotated job template showing:
- Multi-step workflow pattern
- Proper step types (script, exec, plugins)
- Script interpreter usage
- Variable substitution formats
- Job metadata
- Critical rules summary

### VARIABLE_RULES.md
Comprehensive variable substitution examples:
- Script step variables (@option.VAR@)
- Exec step variables (${option.VAR})
- Plugin variables (${option.VAR})
- Job reference variables
- When to split steps
- Plugin usage examples

---

## 🎯 QUICK REFERENCE: RISK LEVELS

| Risk Level | Emoji | Impact | Requires Confirmation |
|-----------|-------|--------|---------------------|
| 🟢 LOW | Green Square | Minimal impact | Optional |
| 🟡 MEDIUM | Amber Square | Service/automation impact | Yes |
| 🔴 HIGH | Red Square | Permanent data loss/system-wide | Yes (explicit) |

---

## 🔑 KEY PRINCIPLES

1. **Fail Fast, Fail Clearly** - Don't attempt workarounds on errors
2. **Multi-Step by Default** - Break complex workflows into logical phases
3. **Scripts Use script: Type** - ANY script (bash/PowerShell/Python) ALWAYS uses `script:` type
4. **Simple Commands Use exec:** - ONLY for single simple commands
5. **Always Set scriptInterpreter** - Match to script content (bash, python3, powershell)
6. **Variable Format Matters** - Script steps use @option.VAR@, everything else uses ${option.VAR}
7. **Risk Assessment Required** - Show emoji and impact level for risky operations
8. **Meaningful Tags** - Use relevant tags (deployment, monitoring, backup, etc.)
9. **Node Filters Required** - Always specify explicit node filters for adhoc commands
10. **Confirmation Before Destruction** - All destructive operations require explicit confirmation

---

**Document Version:** 1.0
**Last Updated:** 2025-10-15
**Source:** tool_prompts.json, SAMPLE_JOB.yaml, VARIABLE_RULES.md
