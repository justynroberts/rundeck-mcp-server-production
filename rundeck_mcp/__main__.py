"""Main entry point for Rundeck MCP Server."""

import asyncio
import sys

import typer

from .server import main as server_main
from .utils import setup_logging, validate_environment

app = typer.Typer(
    name="rundeck-mcp",
    help="Rundeck MCP Server - Model Context Protocol server for Rundeck automation platform",
    add_completion=False,
)


@app.command()
def serve(
    enable_write_tools: bool = typer.Option(
        False, "--enable-write-tools", help="Enable write operations (job execution, system control, etc.)"
    ),
    log_level: str = typer.Option("INFO", "--log-level", help="Set logging level (DEBUG, INFO, WARNING, ERROR)"),
    validate_config: bool = typer.Option(
        True, "--validate-config/--no-validate-config", help="Validate configuration before starting"
    ),
):
    """Start the Rundeck MCP Server."""
    setup_logging(log_level)

    if validate_config:
        validation = validate_environment()
        if not validation["valid"]:
            typer.echo("Configuration validation failed:", err=True)
            for error in validation["errors"]:
                typer.echo(f"  ❌ {error}", err=True)
            sys.exit(1)

        if validation["warnings"]:
            for warning in validation["warnings"]:
                typer.echo(f"  ⚠️  {warning}", err=True)

        server_count = len(validation["servers"])
        typer.echo(f"✅ Configuration valid - {server_count} server(s) configured")

    if enable_write_tools:
        typer.echo("⚠️  Write operations enabled - destructive operations are allowed")
    else:
        typer.echo("🔒 Read-only mode - write operations disabled")

    try:
        asyncio.run(server_main(enable_write_tools=enable_write_tools))
    except KeyboardInterrupt:
        typer.echo("\\nServer stopped by user")
    except Exception as e:
        typer.echo(f"Server error: {e}", err=True)
        sys.exit(1)


@app.command()
def validate():
    """Validate configuration and test server connectivity."""
    setup_logging("WARNING")  # Quiet logging for validation

    typer.echo("Validating Rundeck MCP Server configuration...")

    validation = validate_environment()

    if validation["errors"]:
        typer.echo("\\n❌ Configuration Errors:", err=True)
        for error in validation["errors"]:
            typer.echo(f"  - {error}", err=True)

    if validation["warnings"]:
        typer.echo("\\n⚠️  Configuration Warnings:")
        for warning in validation["warnings"]:
            typer.echo(f"  - {warning}")

    if validation["servers"]:
        typer.echo("\\n🔧 Configured Servers:")
        for server_id, config in validation["servers"].items():
            typer.echo(f"  - {config['name']}: {config['url']} (API v{config['api_version']})")

    if validation["valid"]:
        typer.echo("\\n✅ Configuration is valid")

        # Test connectivity
        typer.echo("\\nTesting server connectivity...")
        try:
            from .client import get_client_manager

            client_manager = get_client_manager()
            health_status = client_manager.health_check_all()

            for server_name, is_healthy in health_status.items():
                status = "✅ Healthy" if is_healthy else "❌ Unhealthy"
                typer.echo(f"  - {server_name}: {status}")

            healthy_count = sum(health_status.values())
            total_count = len(health_status)

            if healthy_count == total_count:
                typer.echo(f"\\n✅ All {total_count} server(s) are healthy")
            else:
                typer.echo(f"\\n⚠️  {healthy_count}/{total_count} server(s) are healthy")

        except Exception as e:
            typer.echo(f"\\n❌ Connectivity test failed: {e}", err=True)
    else:
        typer.echo("\\n❌ Configuration is invalid")
        sys.exit(1)


@app.command()
def info():
    """Show server information and capabilities."""
    typer.echo("Rundeck MCP Server Information")
    typer.echo("=" * 35)
    typer.echo()
    typer.echo("Version: 1.0.0")
    typer.echo("Protocol: Model Context Protocol (MCP)")
    typer.echo("Framework: FastMCP")
    typer.echo()
    typer.echo("Capabilities:")
    typer.echo("  - Project management")
    typer.echo("  - Job management and analysis")
    typer.echo("  - Execution monitoring and control")
    typer.echo("  - Node inventory and management")
    typer.echo("  - System administration")
    typer.echo("  - Analytics and reporting")
    typer.echo()
    typer.echo("Tool Categories:")
    typer.echo("  - Read-only tools: Always available")
    typer.echo("  - Write tools: Require --enable-write-tools flag")
    typer.echo()
    typer.echo("Security Features:")
    typer.echo("  - Opt-in write operations")
    typer.echo("  - Tool safety annotations")
    typer.echo("  - Risk assessment indicators")
    typer.echo()
    typer.echo("For more information, visit:")
    typer.echo("https://github.com/your-username/rundeck-mcp-server")


def main():
    """Main entry point for the rundeck-mcp command."""
    app()


if __name__ == "__main__":
    main()
