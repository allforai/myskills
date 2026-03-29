#!/usr/bin/env bash
# Install myskills Claude Code plugins
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Installing myskills Claude Code plugins..."
for plugin in product-design-skill dev-forge-skill demo-forge-skill code-tuner-skill code-replicate-skill ui-forge-skill meta-skill; do
  if [ -d "$SCRIPT_DIR/$plugin" ]; then
    echo "  Adding $plugin..."
    claude plugin add "$SCRIPT_DIR/$plugin" 2>/dev/null || echo "  Warning: could not add $plugin (is claude CLI available?)"
  fi
done

# Build MCP gateway if needed
MCP_DIR="$SCRIPT_DIR/../shared/mcp-ai-gateway"
if [ -d "$MCP_DIR" ] && [ ! -d "$MCP_DIR/node_modules" ]; then
  echo "Building MCP AI Gateway..."
  cd "$MCP_DIR"
  npm install && npm run build
  echo "MCP AI Gateway built at $MCP_DIR/dist/index.js"
fi

echo ""
echo "Done. Run 'claude' to start using the plugins."
echo "Set OPENROUTER_API_KEY for cross-model XV and image generation."
echo "Optional: GOOGLE_API_KEY (Imagen 4/Veo 3.1), FAL_KEY (FLUX 2 Pro/Kling)"
