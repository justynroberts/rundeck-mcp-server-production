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
