# Contributing to Rundeck MCP Server

Thank you for your interest in contributing to the Rundeck MCP Server! This document provides guidelines for contributing to the project.

## Code of Conduct

This project adheres to a code of conduct. By participating, you are expected to uphold this code. Please report unacceptable behavior to the project maintainers.

## How to Contribute

### Reporting Bugs

Before creating bug reports, please check the existing issues to avoid duplicates. When creating a bug report, please include:

- **Clear title**: Summarize the issue in the title
- **Environment**: Python version, OS, Rundeck version
- **Steps to reproduce**: Detailed steps to reproduce the issue
- **Expected behavior**: What you expected to happen
- **Actual behavior**: What actually happened
- **Logs**: Relevant log output or error messages
- **Configuration**: Relevant configuration details (redact sensitive info)

### Suggesting Enhancements

Enhancement suggestions are welcome! Please provide:

- **Clear title**: Summarize the enhancement in the title
- **Use case**: Explain why this enhancement would be useful
- **Detailed description**: Provide a detailed description of the enhancement
- **Examples**: Include examples of how it would work
- **Alternatives**: Describe alternatives you've considered

### Contributing Code

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes**: Follow the development guidelines below
4. **Test your changes**: Ensure all tests pass
5. **Commit your changes**: Use conventional commits
6. **Push to the branch**: `git push origin feature/amazing-feature`
7. **Open a Pull Request**: Provide a clear description of your changes

## Development Setup

### Prerequisites

- Python 3.12 or higher
- uv (for dependency management)
- Git

### Setting Up the Development Environment

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-username/rundeck-mcp-server.git
   cd rundeck-mcp-server
   ```

2. **Set up the development environment**:
   ```bash
   make dev-setup
   ```

3. **Install dependencies**:
   ```bash
   make install
   ```

4. **Configure environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your Rundeck server details
   ```

5. **Validate setup**:
   ```bash
   make validate
   ```

### Running Tests

```bash
# Run all tests
make test

# Run specific test categories
make test-server
make test-multi
make debug-jobs

# Run competency tests
make test-evals

# Run with coverage
make coverage
```

### Code Quality

We use several tools to maintain code quality:

```bash
# Format code
make format

# Run linting
make lint

# Run type checking
make type-check

# Run all quality checks
make check
```

## Development Guidelines

### Project Structure

The project follows a modular architecture:

```
rundeck_mcp/
├── __init__.py
├── __main__.py          # Entry point
├── server.py            # Server implementation
├── client.py            # API client management
├── utils.py             # Shared utilities
├── models/              # Data models
│   ├── __init__.py
│   ├── base.py          # Base models
│   └── rundeck.py       # Rundeck-specific models
└── tools/               # MCP tools
    ├── __init__.py
    ├── projects.py      # Project management
    ├── jobs.py          # Job management
    ├── executions.py    # Execution management
    ├── nodes.py         # Node management
    ├── system.py        # System management
    └── analytics.py     # Analytics and reporting
```

### Coding Standards

1. **Python Style**:
   - Follow PEP 8 style guide
   - Use type hints throughout
   - Maximum line length: 120 characters
   - Use meaningful variable and function names

2. **Code Quality**:
   - Write comprehensive docstrings
   - Include type hints for all functions
   - Handle errors gracefully
   - Use logging for debugging information

3. **Testing**:
   - Write unit tests for all new functionality
   - Use mocking for external dependencies
   - Aim for high test coverage (>80%)
   - Include integration tests for complex features

### Adding New Tools

When adding new MCP tools:

1. **Create the tool function**:
   ```python
   def new_tool(param1: str, param2: Optional[str] = None) -> ResponseModel:
       """Tool description.
       
       Args:
           param1: Description of parameter 1
           param2: Description of parameter 2
           
       Returns:
           Response model with results
       """
       # Implementation
   ```

2. **Add to appropriate module**:
   - Place in the correct tool module (projects, jobs, etc.)
   - Add to the tool categories (read_tools or write_tools)

3. **Update tool_prompts.json**:
   ```json
   {
     "new_tool": {
       "description": "Clear description of what the tool does",
       "prompt": "Detailed prompt for AI assistants"
     }
   }
   ```

4. **Write tests**:
   ```python
   def test_new_tool(self):
       """Test new tool functionality."""
       # Test implementation
   ```

5. **Update documentation**:
   - Add to CLAUDE.md if needed
   - Update README if it's a major feature

### Tool Safety Guidelines

1. **Read-Only Tools**:
   - Mark with `readOnlyHint=True`
   - Should not modify system state
   - Safe to call multiple times

2. **Write Tools**:
   - Mark with `readOnlyHint=False`
   - Add appropriate `destructiveHint` flag
   - Include clear warnings in descriptions
   - Implement proper error handling

3. **Destructive Tools**:
   - Mark with `destructiveHint=True`
   - Add risk indicators (🔴, 🟡, 🟢)
   - Require explicit confirmation
   - Include detailed documentation

### Security Considerations

1. **Never log sensitive information**:
   ```python
   # Good
   logger.info(f"Using API token: {api_token[:4]}...")
   
   # Bad
   logger.info(f"Using API token: {api_token}")
   ```

2. **Validate all inputs**:
   ```python
   def tool_function(input_data: str) -> Result:
       if not input_data or len(input_data) > 1000:
           raise ValueError("Invalid input data")
   ```

3. **Use proper error handling**:
   ```python
   try:
       result = api_call()
   except requests.exceptions.HTTPError as e:
       if e.response.status_code == 401:
           raise ValueError("Authentication failed")
       raise
   ```

## Commit Guidelines

We use conventional commits for clear commit messages:

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes
- `refactor:` Code refactoring
- `test:` Test changes
- `chore:` Maintenance tasks

Examples:
```
feat: add job visualization tool
fix: handle empty response from API
docs: update installation instructions
test: add tests for multi-server setup
```

## Pull Request Process

1. **Update documentation**: If you're adding new features
2. **Add tests**: For new functionality
3. **Update CHANGELOG**: Add your changes to the unreleased section
4. **Ensure CI passes**: All tests and checks must pass
5. **Request review**: From project maintainers
6. **Address feedback**: Make requested changes

### Pull Request Template

```markdown
## Description
Brief description of the changes.

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing performed

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Tests added and passing
- [ ] No breaking changes (or clearly documented)
```

## Release Process

1. **Version bump**: Update version in pyproject.toml
2. **Update CHANGELOG**: Move changes from unreleased to new version
3. **Create release**: Tag and create GitHub release
4. **Build and publish**: Automated through CI/CD
5. **Update documentation**: Update installation instructions

## Getting Help

- **GitHub Issues**: For bug reports and feature requests
- **GitHub Discussions**: For questions and general discussion
- **Email**: For security issues (see SECURITY.md)

## Recognition

Contributors are recognized in:
- CHANGELOG.md
- GitHub contributors list
- Release notes for significant contributions

Thank you for contributing to the Rundeck MCP Server!