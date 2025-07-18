#!/bin/bash

# GitHub Repository Setup Commands for Rundeck MCP Server
# Run these commands in your terminal to create and push to a new private repository

echo "=== GitHub Repository Setup ==="
echo ""

# Step 1: Initialize git repository (if not already done)
echo "Step 1: Initialize git repository..."
git init

# Step 2: Add all files to git
echo "Step 2: Adding files to git..."
git add .

# Step 3: Create initial commit
echo "Step 3: Creating initial commit..."
git commit -m "Initial commit: Rundeck MCP Server

- Complete MCP server implementation with 30+ tools
- Support for VS Code and Claude Desktop integration
- Multi-server configuration support
- Comprehensive security features with opt-in write operations
- Full test suite and documentation
- Modern Python 3.12+ with uv dependency management"

# Step 4: Create GitHub repository (choose one of these methods)
echo ""
echo "Step 4: Create GitHub repository..."
echo "Choose one of these methods:"
echo ""
echo "Method A: Using GitHub CLI (if you have it installed)"
echo "gh repo create pagerduty-rundeck-mcp --private --description 'Rundeck MCP Server for AI-powered automation management'"
echo ""
echo "Method B: Using GitHub web interface"
echo "1. Go to https://github.com/new"
echo "2. Repository name: pagerduty-rundeck-mcp"
echo "3. Description: Rundeck MCP Server for AI-powered automation management"
echo "4. Set to Private"
echo "5. Don't initialize with README, .gitignore, or license (we already have them)"
echo "6. Click 'Create repository'"
echo ""

# Step 5: Add remote origin (replace YOUR_USERNAME with your GitHub username)
echo "Step 5: Add remote origin..."
echo "git remote add origin https://github.com/YOUR_USERNAME/pagerduty-rundeck-mcp.git"
echo ""
echo "Replace YOUR_USERNAME with your actual GitHub username"
echo ""

# Step 6: Push to GitHub
echo "Step 6: Push to GitHub..."
echo "git branch -M main"
echo "git push -u origin main"
echo ""

echo "=== Additional Setup Commands ==="
echo ""

# Optional: Set up branch protection
echo "Optional: Set up branch protection (after first push)"
echo "gh repo edit pagerduty-rundeck-mcp --enable-wiki=false --enable-issues=true --enable-projects=false"
echo ""

# Optional: Add topics/tags
echo "Optional: Add repository topics"
echo "gh repo edit pagerduty-rundeck-mcp --add-topic rundeck --add-topic mcp --add-topic automation --add-topic ai --add-topic python"
echo ""

echo "=== Manual Steps Required ==="
echo ""
echo "1. Replace YOUR_USERNAME in the remote URL with your GitHub username"
echo "2. Run the commands one by one"
echo "3. You may need to authenticate with GitHub (use personal access token)"
echo "4. Verify the repository was created successfully"
echo ""
echo "Example complete workflow:"
echo "git remote add origin https://github.com/yourusername/pagerduty-rundeck-mcp.git"
echo "git branch -M main"
echo "git push -u origin main"