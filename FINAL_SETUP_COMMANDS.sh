#!/bin/bash

# Final GitHub Repository Setup Commands for justynroberts/pagerduty-rundeck-mcp
# Run these commands in your terminal to create and push to your new private repository

echo "🚀 Setting up GitHub repository: justynroberts/pagerduty-rundeck-mcp"
echo ""

# Step 1: Stage and commit all changes
echo "📦 Step 1: Staging and committing all changes..."
git add .

git commit -m "feat: complete refactor to modern MCP server architecture

- 🏗️ Refactored from single-file to modular architecture
- 🔄 Migrated from standard MCP to FastMCP framework  
- 🐍 Updated Python requirement to 3.12+
- 📦 Migrated dependency management to uv
- 🛡️ Implemented opt-in write operations with --enable-write-tools flag
- 🔧 Added comprehensive tool safety annotations
- 📊 Enhanced with 30+ tools across 10 categories
- 🧪 Created comprehensive test suite with unit, integration, and evaluation tests
- 📚 Added complete documentation: CLAUDE.md, CONTRIBUTING.md, SECURITY.md, DEPLOYMENT_GUIDE.md
- 🎯 Added VS Code and Claude Desktop integration guides
- 🌐 Enhanced multi-server support (up to 9 additional servers)
- 🔍 Added job analysis and visualization tools
- 📈 Implemented execution metrics and ROI calculation
- 🎨 Added risk assessment system with emoji indicators
- 🔐 Enhanced security with credential protection and input validation

🚀 Ready for production deployment with modern Python tooling and best practices"

echo "✅ Changes committed successfully!"
echo ""

# Step 2: Create GitHub repository using GitHub CLI
echo "🏗️ Step 2: Creating private GitHub repository..."
gh repo create pagerduty-rundeck-mcp --private --description "🚀 Rundeck MCP Server: AI-powered automation management through Claude Desktop and VS Code. Features 30+ tools, multi-server support, job analysis, and comprehensive security."

echo "✅ Repository created successfully!"
echo ""

# Step 3: Remove existing remote and add new one
echo "🔗 Step 3: Setting up remote origin..."
git remote remove origin 2>/dev/null || true  # Remove if exists, ignore error if not
git remote add origin https://github.com/justynroberts/pagerduty-rundeck-mcp.git

echo "✅ Remote origin set!"
echo ""

# Step 4: Push to new repository
echo "🚀 Step 4: Pushing to GitHub..."
git branch -M main
git push -u origin main

echo "✅ Code pushed successfully!"
echo ""

# Step 5: Configure repository settings
echo "⚙️ Step 5: Configuring repository settings..."
gh repo edit pagerduty-rundeck-mcp --enable-wiki=false --enable-issues=true --enable-projects=false

# Add repository topics
gh repo edit pagerduty-rundeck-mcp --add-topic rundeck --add-topic mcp --add-topic automation --add-topic ai --add-topic python --add-topic claude --add-topic vscode --add-topic fastmcp

echo "✅ Repository configured!"
echo ""

# Step 6: Display repository information
echo "📋 Step 6: Repository information..."
gh repo view pagerduty-rundeck-mcp

echo ""
echo "🎉 SUCCESS! Your repository is ready at:"
echo "https://github.com/justynroberts/pagerduty-rundeck-mcp"
echo ""
echo "🔧 Next steps:"
echo "1. Visit your repository to verify everything looks correct"
echo "2. Test the installation by following the README instructions"
echo "3. Share the repository with collaborators if needed"
echo "4. Consider setting up branch protection for the main branch"
echo ""
echo "📚 Your repository includes:"
echo "- 🏗️ Modern modular architecture with 30+ tools"
echo "- 🔐 Comprehensive security with opt-in write operations"
echo "- 📖 Complete documentation suite"
echo "- 🧪 Full test suite with evaluation framework"
echo "- 🎯 VS Code and Claude Desktop integration guides"
echo "- 🌐 Multi-server support"
echo "- 📊 Job analysis and ROI calculation tools"
echo ""
echo "🚀 Happy automating!"