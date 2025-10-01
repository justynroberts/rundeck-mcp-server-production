# Rundeck Variable Substitution Rules

## Quick Reference

### Step Type Decision
- **Script steps** → Multi-line, any complexity, heredocs, interpreters → **USE THIS BY DEFAULT**
- **Exec steps** → Single simple command only (ls, echo, df) → **RARELY USE**
- **Plugin steps** → SQL, Ansible, HTTP, Job References → **USE WHEN APPLICABLE**

### Variable Format
- **Script step** (`script:` field) → `@option.variablename@`
- **Everything else** (exec, plugins, jobrefs) → `${option.variablename}`

## Examples

### Script Step (Use @option.VAR@)
```yaml
- description: Deploy database schema
  script: |
    #!/bin/bash
    echo "Deploying to @option.environment@"
    mysql -u @option.db_user@ -p@option.db_password@ @option.database@ < schema.sql
```

### Exec Step (Use ${option.VAR})
```yaml
- description: Show environment
  exec: echo "Environment is ${option.environment}"
```

### SQL Plugin (Use ${option.VAR})
```yaml
- description: Run database query
  nodeStep: true
  type: org.rundeck.sqlrunner.SQLRunnerNodeStepPlugin
  configuration:
    jdbcUrl: jdbc:mysql://localhost:3306/${option.database}
    user: ${option.db_user}
    scriptBody: SELECT * FROM users WHERE env = '${option.environment}';
```

### Ansible Plugin (Use ${option.VAR})
```yaml
- description: Deploy application
  nodeStep: true
  type: com.batix.rundeck.plugins.AnsiblePlaybookInlineWorkflowNodeStep
  configuration:
    ansible-playbook: |
      ---
      - hosts: all
        tasks:
          - name: Deploy ${option.app_name}
            command: /opt/deploy.sh ${option.version}
```

## When to Split Into Multiple Steps

Split scripts when you see:
1. **Echo separators** → `echo "==== STAGE 1 ====="` = NEW STEP
2. **Numbered phases** → Comments like `# Stage 1:`, `# Phase 2:` = NEW STEP
3. **Different technologies** → SQL then Ansible then HTTP = SEPARATE STEPS
4. **Long scripts** → >20 lines = consider splitting
5. **Natural boundaries** → Setup → Execute → Verify = 3 STEPS

## Multi-Step Example

**GOOD:**
```yaml
sequence:
  commands:
  - description: Stop service
    script: |
      #!/bin/bash
      systemctl stop @option.service_name@

  - description: Log deployment
    nodeStep: true
    type: org.rundeck.sqlrunner.SQLRunnerNodeStepPlugin
    configuration:
      jdbcUrl: jdbc:mysql://localhost/${option.database}
      user: ${option.db_user}
      scriptBody: INSERT INTO deploys VALUES ('${option.app}', NOW());

  - description: Deploy files
    script: |
      #!/bin/bash
      cp -r /staging/@option.version@/* /opt/app/

  - description: Start service
    script: |
      #!/bin/bash
      systemctl start @option.service_name@
```

**BAD (all in one step):**
```yaml
sequence:
  commands:
  - description: Deploy application
    script: |
      #!/bin/bash
      systemctl stop service
      # Can't log to database from bash easily
      cp -r /staging/* /opt/app/
      systemctl start service
```

## When to Use Plugins Instead of Scripts

| You See | Use This Plugin | Not Bash Script |
|---------|----------------|-----------------|
| SQL queries (SELECT, INSERT, UPDATE) | SQL Runner | ❌ No heredocs in bash |
| Package install (apt, yum) | Ansible | ❌ No bash loops |
| systemctl commands | Ansible | ❌ No bash scripts |
| curl/wget to APIs | HTTP Plugin | ❌ No curl in bash |
| Calling other jobs | Job Reference | ❌ No copy/paste |

### SQL: Use SQL Runner Plugin
**BAD:**
```yaml
- script: mysql -u root <<EOF\nINSERT INTO deploys VALUES ('app', NOW());\nEOF
```
**GOOD:**
```yaml
- type: org.rundeck.sqlrunner.SQLRunnerNodeStepPlugin
  configuration:
    jdbcUrl: jdbc:mysql://localhost/mydb
    user: ${option.db_user}
    scriptBody: INSERT INTO deploys VALUES ('${option.app}', NOW());
```

### Packages/Services: Use Ansible Plugin
**BAD:**
```yaml
- script: apt-get install nginx && systemctl start nginx
```
**GOOD:**
```yaml
- type: com.batix.rundeck.plugins.AnsiblePlaybookInlineWorkflowNodeStep
  configuration:
    ansible-playbook: |
      - hosts: all
        tasks:
          - apt: name=nginx state=present
          - service: name=nginx state=started
```

### API Calls: Use HTTP Plugin
**BAD:**
```yaml
- script: curl -X POST https://api.com/deploy -d '{"app":"myapp"}'
```
**GOOD:**
```yaml
- type: edu.ohio.ais.rundeck.HttpWorkflowStepPlugin
  configuration:
    method: POST
    url: https://api.com/deploy
    body: '{"app":"${option.app_name}"}'
```
