.PHONY: test lint format check install dev-setup dev-install clean build help
.DEFAULT_GOAL := help

# Development setup
dev-setup: ## Complete development setup
	@echo "Setting up development environment..."
	python3 -m venv .venv
	. .venv/bin/activate && pip install -e ".[dev]"
	@echo "Development environment ready!"

dev-install: ## Install with development dependencies
	uv sync --dev

install: ## Install package and dependencies
	uv sync

# Testing
test: ## Run all tests
	uv run python -m pytest tests/ -v --tb=short

test-server: ## Test server connection
	uv run python tests/test_server.py

test-multi: ## Test multi-server setup
	uv run python tests/test_multi_server.py

debug-jobs: ## Debug jobs functionality
	uv run python tests/debug_jobs.py

test-evals: ## Run competency evaluation tests
	uv run python tests/evals/run_tests.py

configure-claude: ## Generate Claude Desktop configuration
	uv run python tests/get_claude_config.py

# Code quality
format: ## Format code with ruff
	uv run ruff format .

lint: ## Run linting with ruff
	uv run ruff check .

type-check: ## Run type checking with pyright
	uv run pyright

coverage: ## Run tests with coverage
	uv run coverage run -m pytest tests/
	uv run coverage report
	uv run coverage html

check: format lint type-check test ## Run all quality checks

# Build and distribution
build: ## Build distribution packages
	uv build

clean: ## Clean build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .ruff_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Server management
serve: ## Start the server in development mode
	uv run rundeck-mcp serve

serve-write: ## Start the server with write tools enabled
	uv run rundeck-mcp serve --enable-write-tools

validate: ## Validate configuration
	uv run rundeck-mcp validate

info: ## Show server information
	uv run rundeck-mcp info

# Development utilities
shell: ## Open Python shell with package loaded
	uv run python -c "import rundeck_mcp; print('Rundeck MCP package loaded')"

docs: ## Generate documentation (placeholder)
	@echo "Documentation generation not implemented yet"

# Help
help: ## Show this help message
	@echo "Rundeck MCP Server - Development Commands"
	@echo "========================================"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "Quick Start:"
	@echo "  make dev-setup     # Set up development environment"
	@echo "  make check         # Run all quality checks"
	@echo "  make serve         # Start server in development mode"
	@echo ""
	@echo "Environment Variables:"
	@echo "  RUNDECK_URL        # Rundeck server URL"
	@echo "  RUNDECK_API_TOKEN  # API authentication token"
	@echo ""
	@echo "For production use:"
	@echo "  make serve-write   # Enable write operations"