#!/bin/bash

# Rundeck MCP Server Setup Script
# This script sets up the Python virtual environment and installs dependencies

set -e

echo "Setting up Rundeck MCP Server..."
echo "================================"

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is required but not installed."
    echo "Please install Python 3.8 or higher and try again."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv .venv
else
    echo "📦 Virtual environment already exists."
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "⚙️  Creating configuration file..."
    cp config.env.example .env
    echo "📝 Please edit .env file with your Rundeck server details:"
    echo "   - RUNDECK_URL: Your Rundeck server URL"
    echo "   - RUNDECK_API_TOKEN: Your Rundeck API token"
    echo ""
    echo "To get an API token:"
    echo "   1. Log into Rundeck web interface"
    echo "   2. Go to User Profile > User API Tokens"
    echo "   3. Generate a new token"
else
    echo "⚙️  Configuration file .env already exists."
fi

# Make scripts executable
chmod +x rundeck_mcp_server.py
chmod +x tests/test_server.py

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your Rundeck server details"
echo "2. Test the connection: python tests/test_server.py"
echo "3. Run the MCP server: python rundeck_mcp_server.py"
echo ""
echo "For Claude Desktop integration, see README.md"