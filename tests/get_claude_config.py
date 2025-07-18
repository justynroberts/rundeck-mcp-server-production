"""Generate Claude Desktop configuration for Rundeck MCP Server."""

import json
import os
import sys
from pathlib import Path
from typing import Dict, Any


def get_python_executable() -> str:
    """Get the current Python executable path."""
    return sys.executable


def get_server_script_path() -> str:
    """Get the path to the server script."""
    # Try to find the installed package
    try:
        import rundeck_mcp
        package_path = Path(rundeck_mcp.__file__).parent
        return str(package_path / "__main__.py")
    except ImportError:
        # Fall back to development path
        current_dir = Path(__file__).parent.parent
        return str(current_dir / "rundeck_mcp" / "__main__.py")


def collect_environment_variables() -> Dict[str, str]:
    """Collect Rundeck environment variables."""
    env_vars = {}
    
    # Primary server variables
    primary_vars = [
        'RUNDECK_URL',
        'RUNDECK_API_TOKEN',
        'RUNDECK_API_VERSION',
        'RUNDECK_NAME'
    ]
    
    for var in primary_vars:
        value = os.getenv(var)
        if value:
            env_vars[var] = value
    
    # Additional server variables (1-9)
    for i in range(1, 10):
        server_vars = [
            f'RUNDECK_URL_{i}',
            f'RUNDECK_API_TOKEN_{i}',
            f'RUNDECK_API_VERSION_{i}',
            f'RUNDECK_NAME_{i}'
        ]
        
        for var in server_vars:
            value = os.getenv(var)
            if value:
                env_vars[var] = value
    
    return env_vars


def generate_claude_desktop_config(enable_write_tools: bool = False) -> Dict[str, Any]:
    """Generate Claude Desktop configuration."""
    python_executable = get_python_executable()
    server_script = get_server_script_path()
    env_vars = collect_environment_variables()
    
    # Base configuration
    config = {
        "mcpServers": {
            "rundeck-mcp": {
                "command": python_executable,
                "args": [
                    "-m", "rundeck_mcp",
                    "serve"
                ],
                "env": env_vars
            }
        }
    }
    
    # Add write tools flag if requested
    if enable_write_tools:
        config["mcpServers"]["rundeck-mcp"]["args"].append("--enable-write-tools")
    
    return config


def generate_vs_code_config(enable_write_tools: bool = False) -> Dict[str, Any]:
    """Generate VS Code configuration."""
    python_executable = get_python_executable()
    env_vars = collect_environment_variables()
    
    # Base configuration
    config = {
        "mcp": {
            "servers": {
                "rundeck-mcp": {
                    "type": "stdio",
                    "command": python_executable,
                    "args": [
                        "-m", "rundeck_mcp",
                        "serve"
                    ],
                    "env": env_vars
                }
            }
        }
    }
    
    # Add write tools flag if requested
    if enable_write_tools:
        config["mcp"]["servers"]["rundeck-mcp"]["args"].append("--enable-write-tools")
    
    return config


def generate_uvx_config(enable_write_tools: bool = False) -> Dict[str, Any]:
    """Generate configuration using uvx."""
    env_vars = collect_environment_variables()
    
    # Base configuration for Claude Desktop
    config = {
        "mcpServers": {
            "rundeck-mcp": {
                "command": "uvx",
                "args": [
                    "rundeck-mcp-server",
                    "serve"
                ],
                "env": env_vars
            }
        }
    }
    
    # Add write tools flag if requested
    if enable_write_tools:
        config["mcpServers"]["rundeck-mcp"]["args"].append("--enable-write-tools")
    
    return config


def validate_configuration() -> bool:
    """Validate the configuration."""
    errors = []
    
    # Check required environment variables
    required_vars = ['RUNDECK_URL', 'RUNDECK_API_TOKEN']
    for var in required_vars:
        if not os.getenv(var):
            errors.append(f"Missing required environment variable: {var}")
    
    # Check Python executable
    python_executable = get_python_executable()
    if not Path(python_executable).exists():
        errors.append(f"Python executable not found: {python_executable}")
    
    # Check server script
    try:
        server_script = get_server_script_path()
        if not Path(server_script).exists():
            errors.append(f"Server script not found: {server_script}")
    except Exception as e:
        errors.append(f"Error finding server script: {e}")
    
    if errors:
        print("Configuration validation failed:")
        for error in errors:
            print(f"  ❌ {error}")
        return False
    
    return True


def main():
    """Main function to generate configurations."""
    print("=== Rundeck MCP Server Configuration Generator ===")
    print()
    
    # Validate configuration
    if not validate_configuration():
        sys.exit(1)
    
    print("✅ Configuration validation passed")
    print()
    
    # Collect environment info
    env_vars = collect_environment_variables()
    server_count = 1  # Primary server
    
    # Count additional servers
    for i in range(1, 10):
        if os.getenv(f'RUNDECK_URL_{i}') and os.getenv(f'RUNDECK_API_TOKEN_{i}'):
            server_count += 1
    
    print(f"Found {server_count} configured server(s)")
    print()
    
    # Generate configurations
    configs = {
        "Claude Desktop (Development)": generate_claude_desktop_config(enable_write_tools=False),
        "Claude Desktop (Production)": generate_claude_desktop_config(enable_write_tools=True),
        "VS Code (Development)": generate_vs_code_config(enable_write_tools=False),
        "VS Code (Production)": generate_vs_code_config(enable_write_tools=True),
        "uvx (Development)": generate_uvx_config(enable_write_tools=False),
        "uvx (Production)": generate_uvx_config(enable_write_tools=True),
    }
    
    # Display configurations
    for name, config in configs.items():
        print(f"=== {name} ===")
        print(json.dumps(config, indent=2))
        print()
    
    # Save configurations to files
    output_dir = Path("config_examples")
    output_dir.mkdir(exist_ok=True)
    
    for name, config in configs.items():
        filename = name.lower().replace(" ", "_").replace("(", "").replace(")", "") + ".json"
        filepath = output_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"Saved: {filepath}")
    
    print()
    print("=== Installation Instructions ===")
    print()
    print("1. Development Setup (Read-only):")
    print("   - Copy the appropriate config to your Claude Desktop settings")
    print("   - This enables read-only operations only")
    print()
    print("2. Production Setup (Read-write):")
    print("   - Copy the production config to your Claude Desktop settings")
    print("   - This enables all operations including write/destructive actions")
    print("   - Use with caution in production environments")
    print()
    print("3. Using uvx (Recommended):")
    print("   - Install: pip install rundeck-mcp-server")
    print("   - Use the uvx configuration for easier management")
    print()
    print("4. Claude Desktop Config Location:")
    print("   - macOS: ~/Library/Application Support/Claude/claude_desktop_config.json")
    print("   - Windows: %APPDATA%\\Claude\\claude_desktop_config.json")
    print("   - Linux: ~/.config/claude/claude_desktop_config.json")
    print()
    print("5. Environment Variables:")
    print("   - Set the following environment variables:")
    for var in ['RUNDECK_URL', 'RUNDECK_API_TOKEN']:
        value = os.getenv(var, '<not set>')
        print(f"     {var}={value}")


if __name__ == '__main__':
    main()