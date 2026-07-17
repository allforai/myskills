#!/usr/bin/env bash
# Install myskills for Codex
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Installing myskills for Codex..."

# Build MCP gateway if needed
MCP_DIR="$SCRIPT_DIR/../shared/mcp-ai-gateway"
if [ -d "$MCP_DIR" ] && [ ! -d "$MCP_DIR/node_modules" ]; then
  echo "Building MCP AI Gateway..."
  cd "$MCP_DIR"
  npm install && npm run build
fi
if [ -f "$SCRIPT_DIR/cross-exam-skill/SKILL.md" ]; then
  ln -sfn "$SCRIPT_DIR/cross-exam-skill" "$CODEX_SKILLS/cross-exam"
  echo "Linked cross-exam -> $CODEX_SKILLS/cross-exam"
fi

# Link skills with a SKILL.md entry into codex's native skills directory
CODEX_SKILLS="$HOME/.codex/skills"
mkdir -p "$CODEX_SKILLS"
if [ -f "$SCRIPT_DIR/megastorm-skill/SKILL.md" ]; then
  ln -sfn "$SCRIPT_DIR/megastorm-skill" "$CODEX_SKILLS/megastorm"
  echo "Linked megastorm -> $CODEX_SKILLS/megastorm"
  if [ ! -f "$CODEX_SKILLS/brainstorming/SKILL.md" ]; then
    echo "WARNING: megastorm requires the 'brainstorming' skill in $CODEX_SKILLS"
    echo "         (Phase 0 depends on it). Install it before running megastorm."
  fi
fi

echo ""
echo "Codex installation complete."
echo ""
echo "Usage: Point Codex to this directory. Each plugin has an AGENTS.md"
echo "entry point that Codex will discover automatically."
echo ""
echo "Plugins available:"
for plugin in product-design-skill dev-forge-skill demo-forge-skill code-tuner-skill code-replicate-skill ui-forge-skill megastorm-skill cross-exam-skill; do
  if [ -d "$SCRIPT_DIR/$plugin" ]; then
    echo "  - $plugin (see $plugin/AGENTS.md)"
  fi
done
echo ""
echo "Optional env vars: OPENROUTER_API_KEY, GOOGLE_API_KEY, FAL_KEY"
