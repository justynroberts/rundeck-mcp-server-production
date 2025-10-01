# Rundeck Variable Substitution Rules

## When to Use Script vs Exec Steps

### DEFAULT: Use SCRIPT Steps (Recommended)

**ALWAYS prefer script steps unless you have a very simple single command.**

Use script steps for:
- **Multi-line scripts** (anything with more than one command)
- **Complex logic** (if statements, loops, functions)
- **Scripts with shebangs** (`#!/bin/bash`, `#!/usr/bin/env python3`)
- **Heredocs** (`cat <<EOF`, `sqlplus <<EOF`)
- **Scripts requiring interpreters** (PowerShell, Python, Ruby)
- **Error handling** (set -e, trap commands)
- **Variable assignments** and **command substitution**
- **Most automation tasks** (the safe default)

### Use EXEC Steps ONLY For:
- **Very simple single commands** (e.g., `echo "Hello"`, `ls -la`, `df -h`)
- When you're absolutely certain it's a one-liner with no complexity
- **When in doubt, use script instead**

### Examples:

**WRONG - Complex script in exec:**
```yaml
- exec: |
    echo "Dropping schema ${option.schema_name}..."
    sqlplus -s ${option.admin_user}/${option.admin_password}@${option.oracle_sid} <<EOF
    DROP USER ${option.schema_name} CASCADE;
    EOF
```

**CORRECT - Complex script in script:**
```yaml
- script: |
    #!/bin/bash
    echo "Dropping schema @option.schema_name@..."
    sqlplus -s @option.admin_user@/@option.admin_password@@@option.oracle_sid@ <<EOF
    DROP USER @option.schema_name@ CASCADE;
    EOF
  description: Drop Oracle schema
```

**CORRECT - Simple command in exec:**
```yaml
- exec: echo "Environment is ${option.environment}"
  description: Show environment
```

## CRITICAL RULES

### Script Steps (script field)
**MUST use `@option.variablename@` format**

```yaml
- description: Bash script step
  script: |
    #!/bin/bash
    echo "Dropping schema @option.schema_name@..."
    sqlplus -s @option.admin_user@/@option.admin_password@@@option.oracle_sid@ <<EOF
    DROP USER @option.schema_name@ CASCADE;
    EOF
```

```yaml
- description: PowerShell script step
  script: |
    $ServiceName = '@option.serviceName@'
    Get-Service -Name $ServiceName | Restart-Service
  scriptInterpreter: powershell.exe
```

### Exec Steps (exec field)
**MUST use `${option.variablename}` format**

```yaml
- description: Command step
  exec: echo "Environment is ${option.environment}"
```

```yaml
- description: PowerShell command
  exec: Get-Process -Name ${option.processName}
```

### Plugin Configuration Fields
**MUST use `${option.variablename}` format**

```yaml
- description: SQL step
  nodeStep: true
  type: org.rundeck.sqlrunner.SQLRunnerNodeStepPlugin
  configuration:
    jdbcDriver: com.mysql.jdbc.Driver
    jdbcUrl: jdbc:mysql://localhost:3306/${option.database}
    user: ${option.dbUser}
    passwordStoragePath: keys/db/password
    scriptBody: |
      SELECT * FROM users WHERE env = '${option.environment}';
      UPDATE metrics SET last_run = NOW() WHERE job = '${option.jobName}';
```

```yaml
- description: Ansible step
  nodeStep: true
  type: com.batix.rundeck.plugins.AnsiblePlaybookInlineWorkflowNodeStep
  configuration:
    ansible-inventory-inline: ${option.inventory}
    ansible-playbook: |
      ---
      - hosts: all
        tasks:
          - name: Deploy app
            command: echo "Deploying ${option.appName}"
```

### Job Reference Fields
**MUST use literal values or `${option.variablename}` format**

```yaml
- description: Chain job
  jobref:
    name: Backup Job
    group: maintenance
    project: ${option.targetProject}
    uuid: abc12345-1234-5678-90ab-cdef12345678
    nodeStep: 'true'
```

## Summary

| Step Type | Field | Variable Format | Example |
|-----------|-------|----------------|---------|
| Script | script | `@option.VAR@` | `@option.schema_name@` |
| Exec | exec | `${option.VAR}` | `${option.environment}` |
| SQL Plugin | configuration.jdbcUrl | `${option.VAR}` | `${option.database}` |
| SQL Plugin | configuration.scriptBody | `${option.VAR}` | `${option.table}` |
| Ansible Plugin | configuration.* | `${option.VAR}` | `${option.inventory}` |
| Job Ref | jobref.project | `${option.VAR}` or literal | `${option.project}` |

## Why Different Formats?

- **Script steps**: Rundeck processes these before passing to shell, use `@option.VAR@`
- **Exec/Plugin/JobRef**: Rundeck substitutes at runtime, use `${option.VAR}`

## Best Practices: Use Multiple Steps

**IMPORTANT: Break jobs into multiple logical steps whenever possible!**

### Benefits of Multiple Steps:
- **Better visibility** - See progress of each phase
- **Easier debugging** - Identify exactly which step failed
- **Cleaner organization** - Each step has a clear purpose
- **Reusability** - Steps can use different technologies (script, SQL, Ansible, etc.)
- **Better error handling** - Add error handlers per step

### When to Split Into Multiple Steps:

Split your workflow when you have:
- **Different logical phases** (setup → execute → cleanup)
- **Different technologies** (bash script → SQL query → REST API call)
- **Natural breakpoints** (comments, echo separators, major operation changes)
- **Error handling opportunities** (check status after critical operations)
- **Long scripts** (>20 lines should usually be multiple steps)

### Example - Multi-Step Workflow:

**GOOD - Multiple focused steps:**
```yaml
sequence:
  commands:
  - description: Validate prerequisites
    script: |
      #!/bin/bash
      if [ ! -d /opt/app ]; then
        echo "ERROR: App directory missing"
        exit 1
      fi

  - description: Stop application service
    script: |
      #!/bin/bash
      systemctl stop @option.service_name@
      sleep 2

  - description: Backup configuration
    script: |
      #!/bin/bash
      tar -czf /backup/config-$(date +%Y%m%d).tar.gz /opt/app/config

  - description: Log deployment to database
    nodeStep: true
    type: org.rundeck.sqlrunner.SQLRunnerNodeStepPlugin
    configuration:
      jdbcUrl: jdbc:mysql://localhost:3306/${option.database}
      user: ${option.db_user}
      scriptBody: |
        INSERT INTO deployments (app, version, timestamp)
        VALUES ('${option.app_name}', '${option.version}', NOW());

  - description: Deploy new version
    script: |
      #!/bin/bash
      cp -r /staging/@option.version@/* /opt/app/

  - description: Start application service
    script: |
      #!/bin/bash
      systemctl start @option.service_name@

  - description: Verify service health
    script: |
      #!/bin/bash
      sleep 5
      curl -f http://localhost:8080/health || exit 1
```

**BAD - Everything in one massive step:**
```yaml
sequence:
  commands:
  - description: Deploy application
    script: |
      #!/bin/bash
      # Validate
      if [ ! -d /opt/app ]; then exit 1; fi
      # Stop
      systemctl stop service
      # Backup
      tar -czf backup.tar.gz /opt/app/config
      # Database logging would need separate tool
      # Deploy
      cp -r /staging/* /opt/app/
      # Start
      systemctl start service
      # Verify
      sleep 5
      curl http://localhost:8080/health
```

### Use Different Step Types:

Don't just use script steps - leverage the right tool for each task:

- **Script steps** - Shell commands, system operations
- **SQL steps** - Database queries, logging, data updates
- **Ansible steps** - Configuration management, multi-node orchestration
- **Job references** - Call other jobs, chain workflows
- **HTTP steps** - REST API calls, webhooks
- **Progress badges** - Visual status indicators
