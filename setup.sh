#!/bin/bash

# Setup script for Jenkins MCP Server

echo "Setting up Jenkins MCP Server..."

# Create directory structure
mkdir -p ~/jenkins-mcp-server
cd ~/jenkins-mcp-server

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Make the server executable
chmod +x jenkins-mcp-server.py

# Load environment variables
if [ -f .env ]; then
    source .env
    echo "Environment variables loaded from .env"
fi

echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Update the .env file with your Jenkins credentials"
echo "2. Update the Claude Desktop configuration file"
echo "3. Restart Claude Desktop"
echo ""
echo "Configuration file locations:"
echo "- macOS: ~/Library/Application Support/Claude/claude_desktop_config.json"
echo "- Windows: %APPDATA%\\Claude\\claude_desktop_config.json"
echo "- Linux: ~/.config/claude/claude_desktop_config.json"