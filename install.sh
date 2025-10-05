#!/usr/bin/env bash
set -euo pipefail

echo "Installing Simple Agent..."

# Get the directory where the script is located
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "Error: uv is not installed"
    echo "Please install uv first: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

echo "✓ Found uv"

# Install the package using uv
echo "Installing simple-agent package..."
cd "$SCRIPT_DIR"
uv pip install -e .

echo ""
echo "Installation complete!"
echo ""
echo "You can now use the agent with the 'agent' command:"
echo "  agent --help"
echo "  agent <your-task>"
