#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Installing Codex meta-skill adapter..."

if [ -d "$SCRIPT_DIR/mcp-ai-gateway" ] && [ ! -d "$SCRIPT_DIR/mcp-ai-gateway/node_modules" ]; then
  echo "Building MCP AI Gateway..."
  cd "$SCRIPT_DIR/mcp-ai-gateway"
  npm install
  npm run build
fi

echo ""
echo "Codex meta-skill adapter is ready."
echo ""
echo "Usage:"
echo "  1. Point Codex at this skill directory"
echo "  2. Run: bootstrap [path]"
echo "  3. In the target project, use the generated .codex/commands/run.md entry"
echo ""
echo "Notes:"
echo "  - Canonical bootstrap graph: .allforai/bootstrap/workflow.json"
echo "  - Generated Codex run entry: .codex/commands/run.md"
echo "  - Optional MCP gateway env vars: OPENROUTER_API_KEY GOOGLE_API_KEY FAL_KEY BRAVE_API_KEY"
