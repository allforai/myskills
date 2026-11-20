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
  for plugin in meta-skill superstorm; do
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

echo ""
echo "Done. Run 'claude' to start using the plugins."
echo "Optional: OPENROUTER_API_KEY (script cross-model checks, jev), GOOGLE_API_KEY (Lyria music). Images: Codex CLI. Video: Grok CLI (grok login)."
