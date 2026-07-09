#!/usr/bin/env bash
# Install myskills Claude Code plugins
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Installing myskills Claude Code plugins..."
if ! command -v claude >/dev/null 2>&1; then
  echo "  Warning: 'claude' CLI not on PATH — skipping plugin install."
else
  # Each plugin dir carries its own .claude-plugin/marketplace.json whose marketplace
  # name == the dir name == the plugin name, so the install ref is <plugin>@<plugin>.
  # (The old 'claude plugin add <path>' verb no longer exists; the CLI now uses
  #  'marketplace add' to register the source, then 'install <name>@<marketplace>'.)
  for plugin in meta-skill megastorm; do
    dir="$SCRIPT_DIR/$plugin"
    [ -d "$dir" ] || continue
    echo "  Registering marketplace for $plugin..."
    if ! claude plugin marketplace add "$dir" >/dev/null 2>&1; then
      # already registered — refresh it from source
      claude plugin marketplace update "$plugin" >/dev/null 2>&1 || true
    fi
    if claude plugin list 2>/dev/null | grep -q "$plugin@$plugin"; then
      echo "  Updating $plugin@$plugin..."
      claude plugin update "$plugin@$plugin" >/dev/null 2>&1 \
        && echo "    updated (restart claude to apply)" \
        || echo "    Warning: update failed for $plugin@$plugin"
    else
      echo "  Installing $plugin@$plugin..."
      claude plugin install "$plugin@$plugin" >/dev/null 2>&1 \
        && echo "    installed" \
        || echo "    Warning: install failed for $plugin@$plugin"
    fi
  done
fi

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
