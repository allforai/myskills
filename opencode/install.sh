#!/usr/bin/env bash
# Install myskills for OpenCode
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_JSON="${HOME}/.config/opencode/skills.json"

echo "Installing myskills for OpenCode..."

# Ensure config directory exists
mkdir -p "$(dirname "$SKILLS_JSON")"

# Generate skills.json
cat > "$SKILLS_JSON" << JSONEOF
{
  "skills": [
    {
      "name": "product-design",
      "path": "$SCRIPT_DIR/product-design-skill/skills",
      "commands": "$SCRIPT_DIR/product-design-skill/commands",
      "description": "Product design suite: concept, map, journey, experience-map, use-case, feature-gap, feature-prune, ui-design, design-audit"
    },
    {
      "name": "dev-forge",
      "path": "$SCRIPT_DIR/dev-forge-skill/skills",
      "commands": "$SCRIPT_DIR/dev-forge-skill/commands",
      "description": "Development forge: setup, design-to-spec, scaffold, task-execute, testforge, deadhunt, fieldcheck, seed-forge, product-verify"
    },
    {
      "name": "demo-forge",
      "path": "$SCRIPT_DIR/demo-forge-skill/skills",
      "commands": "$SCRIPT_DIR/demo-forge-skill/commands",
      "description": "Demo forge: design, media, execute, verify with multi-round iteration"
    },
    {
      "name": "code-tuner",
      "path": "$SCRIPT_DIR/code-tuner-skill/references",
      "commands": "$SCRIPT_DIR/code-tuner-skill/commands",
      "description": "Code architecture tuner: compliance, duplication, abstraction analysis"
    },
    {
      "name": "code-replicate",
      "path": "$SCRIPT_DIR/code-replicate-skill/skills",
      "commands": "$SCRIPT_DIR/code-replicate-skill/commands",
      "description": "Code replication bridge: reverse-engineer codebases into .allforai/ artifacts"
    },
    {
      "name": "ui-forge",
      "path": "$SCRIPT_DIR/ui-forge-skill/skills",
      "commands": "$SCRIPT_DIR/ui-forge-skill/commands",
      "description": "UI forge: post-implementation fidelity restore and polish"
    }
  ],
  "auto_load": true,
  "version": "1.0.0"
}
JSONEOF

echo "Skills registered at: $SKILLS_JSON"

# Build MCP gateway if needed
MCP_DIR="$SCRIPT_DIR/../shared/mcp-ai-gateway"
if [ -d "$MCP_DIR" ] && [ ! -d "$MCP_DIR/node_modules" ]; then
  echo "Building MCP AI Gateway..."
  cd "$MCP_DIR"
  npm install && npm run build
fi

echo ""
echo "Done. OpenCode will auto-discover all 6 plugins."
echo "Optional env vars: OPENROUTER_API_KEY, GOOGLE_API_KEY, FAL_KEY"
