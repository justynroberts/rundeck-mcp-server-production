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

**CRITICAL: Look for these clear indicators to split:**

1. **Echo separators with equals signs or dashes**
   ```bash
   echo "======================================"
   echo "STAGE 1: Database Setup"
   ```
   → This is a NEW STEP!

2. **Numbered stages or phases**
   ```bash
   # Stage 1: Install dependencies
   # Stage 2: Configure services
   # Stage 3: Deploy application
   ```
   → Each stage = separate step!

3. **Major section comments**
   ```bash
   # ── Core Infrastructure ──
   # ── Security Stack ──
   # ── Observability ──
   ```
   → Each section = separate step!

4. **Different technologies/operations**
   - Installing different components (Prometheus, then Grafana, then Loki)
   - Database operations then API calls
   - File operations then service restarts

5. **Natural failure points**
   - After each install/deploy
   - After validation checks
   - Before/after critical operations

6. **Long scripts** (>50 lines MUST be split, >20 lines should consider splitting)

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

### Use Different Step Types - NOT Just Scripts!

**CRITICAL: Match the step type to the operation!**

#### When to Use Each Plugin Type:

**1. SQL Runner Plugin** - Use when you see:
- SQL queries (`SELECT`, `INSERT`, `UPDATE`, `DELETE`)
- Database operations (`CREATE TABLE`, `ALTER`, `DROP`)
- Embedded SQL in heredocs (`sqlplus <<EOF`, `mysql -e "..."`)
- Database logging/auditing
- **DON'T**: Embed SQL in bash scripts!

**2. Ansible Plugin** - Use when you see:
- Package installation (`apt install`, `yum install`)
- Service management (`systemctl start/stop/restart`)
- File/directory management at scale
- Configuration file templating
- Multi-node coordination
- **DON'T**: Write bash loops to configure multiple servers!

**3. HTTP/REST Plugin** - Use when you see:
- `curl` or `wget` commands to APIs
- REST API calls (GET, POST, PUT, DELETE)
- Webhook notifications
- API integrations
- **DON'T**: Use bash curl in scripts for API calls!

**4. Job Reference** - Use when you see:
- Calling existing automation
- Workflow orchestration
- Reusing common tasks
- Sequential job chains
- **DON'T**: Copy/paste code from other jobs!

**5. Script Steps** - Use ONLY for:
- System commands without better alternatives
- Complex shell logic
- File processing
- Local operations

#### Examples of Plugin Detection:

**BAD - SQL in bash script:**
```yaml
- script: |
    #!/bin/bash
    mysql -u root <<EOF
    INSERT INTO deployments VALUES ('app', NOW());
    UPDATE status SET deployed=1;
    EOF
```

**GOOD - SQL Runner plugin:**
```yaml
- type: org.rundeck.sqlrunner.SQLRunnerNodeStepPlugin
  nodeStep: true
  configuration:
    jdbcUrl: jdbc:mysql://localhost/mydb
    user: ${option.db_user}
    scriptBody: |
      INSERT INTO deployments VALUES ('${option.app_name}', NOW());
      UPDATE status SET deployed=1 WHERE app='${option.app_name}';
```

**BAD - Package install in bash:**
```yaml
- script: |
    #!/bin/bash
    apt-get update
    apt-get install -y nginx
    systemctl start nginx
```

**GOOD - Ansible plugin:**
```yaml
- type: com.batix.rundeck.plugins.AnsiblePlaybookInlineWorkflowNodeStep
  nodeStep: true
  configuration:
    ansible-playbook: |
      ---
      - hosts: all
        tasks:
          - name: Install nginx
            apt:
              name: nginx
              state: present
              update_cache: yes
          - name: Start nginx
            service:
              name: nginx
              state: started
```

**BAD - API call in bash:**
```yaml
- script: |
    #!/bin/bash
    curl -X POST https://api.example.com/deploy \
      -H "Content-Type: application/json" \
      -d '{"app":"myapp","version":"1.0"}'
```

**GOOD - HTTP plugin:**
```yaml
- type: edu.ohio.ais.rundeck.HttpWorkflowStepPlugin
  nodeStep: false
  configuration:
    method: POST
    url: https://api.example.com/deploy
    headers: "Content-Type: application/json"
    body: '{"app":"${option.app_name}","version":"${option.version}"}'
```
