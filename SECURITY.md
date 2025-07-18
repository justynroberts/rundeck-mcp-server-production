# Security Policy

## Supported Versions

We actively support the following versions of the Rundeck MCP Server:

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Security Features

### Built-in Security Measures

1. **Opt-in Write Operations**
   - Write operations are disabled by default
   - Must explicitly enable with `--enable-write-tools` flag
   - Clear separation between read-only and write operations

2. **Tool Safety Annotations**
   - All tools have safety annotations (readOnlyHint, destructiveHint, idempotentHint)
   - Destructive operations are clearly marked
   - Risk assessment indicators for high-risk operations

3. **Authentication & Authorization**
   - Uses Rundeck API tokens for authentication
   - Respects Rundeck's built-in authorization system
   - No credentials stored in code or logs

4. **Input Validation**
   - All inputs validated using Pydantic models
   - Type checking enforced throughout the codebase
   - SQL injection protection through parameterized queries

5. **Error Handling**
   - Sensitive information never exposed in error messages
   - Proper error logging without credential exposure
   - Graceful degradation on failures

## Security Best Practices

### For Users

1. **Environment Variables**
   - Store API tokens in environment variables, never in code
   - Use `.env` files for local development (excluded from version control)
   - Rotate API tokens regularly

2. **Network Security**
   - Use HTTPS for all Rundeck server connections
   - Implement proper firewall rules
   - Consider VPN or bastion hosts for production access

3. **Access Control**
   - Follow principle of least privilege
   - Use separate API tokens for different environments
   - Regularly audit API token usage

4. **Production Deployment**
   - Only enable write operations when necessary
   - Use read-only mode for monitoring and reporting
   - Implement approval workflows for high-risk operations

### For Developers

1. **Code Security**
   - Never commit API tokens or other secrets
   - Use secure coding practices
   - Implement proper input validation

2. **Testing**
   - Use mock data for testing, never real credentials
   - Test security features thoroughly
   - Implement security-focused unit tests

3. **Documentation**
   - Document security implications of new features
   - Provide clear security guidelines for users
   - Keep security documentation up to date

## Reporting Security Vulnerabilities

We take security seriously and appreciate responsible disclosure of security vulnerabilities.

**Please do NOT report security vulnerabilities through public GitHub issues.**

Instead, please report them privately by:

1. **Email**: Send details to [security@your-domain.com](mailto:security@your-domain.com)
2. **Subject**: Include "SECURITY" in the subject line
3. **Content**: Provide detailed information about the vulnerability

### What to Include

Please include the following information in your report:

- Description of the vulnerability
- Steps to reproduce the issue
- Potential impact assessment
- Suggested fix or mitigation (if known)
- Your contact information for follow-up

### What to Expect

- **Acknowledgment**: We will acknowledge receipt within 24 hours
- **Initial Assessment**: We will provide an initial assessment within 72 hours
- **Updates**: We will keep you informed of our progress
- **Resolution**: We aim to resolve critical vulnerabilities within 30 days
- **Disclosure**: We will coordinate public disclosure once the issue is resolved

## Security Response Process

1. **Triage**: Security team reviews and triages the report
2. **Verification**: We verify the vulnerability and assess its impact
3. **Fix Development**: We develop and test a fix
4. **Release**: We release a security patch
5. **Disclosure**: We publish a security advisory

## Security Hardening Guide

### Environment Configuration

```bash
# Use strong, unique API tokens
export RUNDECK_API_TOKEN="your-secure-token-here"

# Use HTTPS endpoints only
export RUNDECK_URL="https://your-rundeck-server.com"

# Set appropriate API version
export RUNDECK_API_VERSION="47"
```

### Claude Desktop Configuration

```json
{
  "mcpServers": {
    "rundeck-mcp": {
      "command": "uvx",
      "args": ["rundeck-mcp", "serve"],
      "env": {
        "RUNDECK_URL": "https://your-rundeck-server.com",
        "RUNDECK_API_TOKEN": "${RUNDECK_API_TOKEN}"
      }
    }
  }
}
```

### Production Deployment

1. **Read-Only Mode** (Recommended for most use cases)
   ```bash
   rundeck-mcp serve
   ```

2. **Write Mode** (Use with caution)
   ```bash
   rundeck-mcp serve --enable-write-tools
   ```

3. **Validation**
   ```bash
   rundeck-mcp validate
   ```

## Compliance

### Standards Compliance

- **OWASP Top 10**: We address common web application security risks
- **CWE**: We follow Common Weakness Enumeration guidelines
- **SANS**: We implement SANS security best practices

### Audit Trail

- All API calls are logged with timestamps
- User actions are tracked through Rundeck's audit system
- Security events are logged for monitoring

## Contact

For security-related questions or concerns:

- **Security Team**: security@your-domain.com
- **General Support**: support@your-domain.com
- **Documentation**: https://github.com/your-username/rundeck-mcp-server

## Changelog

### Version 1.0.0
- Initial security policy
- Implemented opt-in write operations
- Added tool safety annotations
- Established vulnerability reporting process