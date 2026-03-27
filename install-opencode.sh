#!/bin/bash

# MySkills global installer for OpenCode
# Registers the current OpenCode skills in ~/.config/opencode/

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OPENCODE_CONFIG_DIR="$HOME/.config/opencode"

echo "[myskills] Installing OpenCode native layer"
echo "=================================="

# 1. Create config directory
echo "Creating config directory: $OPENCODE_CONFIG_DIR"
mkdir -p "$OPENCODE_CONFIG_DIR"

# 2. Generate skills.json
echo "Generating global skills.json"
cat > "$OPENCODE_CONFIG_DIR/skills.json" << EOF
{
  "skills": [
    {
      "name": "product-design",
      "path": "$SCRIPT_DIR/opencode/product-design-skill/skills",
      "commands": "$SCRIPT_DIR/opencode/product-design-skill/commands",
      "description": "Product design suite: concept, map, journey, experience-map, use-case, feature-gap, feature-prune, ui-design, design-audit"
    },
    {
      "name": "dev-forge",
      "path": "$SCRIPT_DIR/opencode/dev-forge-skill/skills",
      "commands": "$SCRIPT_DIR/opencode/dev-forge-skill/commands",
      "description": "Development forge: setup, design-to-spec, scaffold, task-execute, testforge, deadhunt, fieldcheck, seed-forge, product-verify"
    },
    {
      "name": "code-tuner",
      "path": "$SCRIPT_DIR/opencode/code-tuner-skill/references",
      "commands": "$SCRIPT_DIR/opencode/code-tuner-skill/commands",
      "description": "Code architecture tuner: compliance, duplication, abstraction analysis"
    },
    {
      "name": "demo-forge",
      "path": "$SCRIPT_DIR/opencode/demo-forge-skill/skills",
      "commands": "$SCRIPT_DIR/opencode/demo-forge-skill/commands",
      "description": "Demo forge: design, media, execute, verify with multi-round iteration"
    },
    {
      "name": "ui-forge",
      "path": "$SCRIPT_DIR/opencode/ui-forge-skill/skills",
      "commands": "$SCRIPT_DIR/opencode/ui-forge-skill/commands",
      "description": "UI forge: post-implementation fidelity restore and polish"
    },
    {
      "name": "code-replicate",
      "path": "$SCRIPT_DIR/opencode/code-replicate-skill/skills",
      "commands": "$SCRIPT_DIR/opencode/code-replicate-skill/commands",
      "description": "Code replication bridge: reverse-engineer codebases into .allforai artifacts"
    }
  ],
  "auto_load": true,
  "version": "1.0.0"
}
EOF

# 3. Validate config
echo "Validating config..."
if [ -f "$OPENCODE_CONFIG_DIR/skills.json" ]; then
    echo "skills.json created"
    echo ""
    echo "Generated config:"
    cat "$OPENCODE_CONFIG_DIR/skills.json"
    echo ""
else
    echo "Failed to create skills.json"
    exit 1
fi

# 4. Create project template
echo "Creating project template..."
PROJECT_TEMPLATE="$SCRIPT_DIR/.opencode.template"
cat > "$PROJECT_TEMPLATE" << EOF
{
  "\$schema": "https://opencode.ai/config.schema.json",
  "skills": {
    "inherit": true,
    "description": "Inherit global OpenCode native skills configuration"
  },
  "mcp": {
    "inherit": true
  }
}
EOF
echo "Project template created: $PROJECT_TEMPLATE"

# 5. Usage
echo ""
echo "=================================="
echo "Install complete"
echo ""
echo "Usage:"
echo ""
echo "1. Copy the project template into any project:"
echo "   cp $PROJECT_TEMPLATE your-project/.opencode/config.json"
echo ""
echo "2. Or create .opencode/config.json manually:"
echo '   {'
echo '     "skills": { "inherit": true },'
echo '     "mcp": { "inherit": true }'
echo '   }'
echo ""
echo "3. Available OpenCode native commands:"
echo "   /product-concept    /product-map       /experience-map"
echo "   /use-case           /feature-gap       /feature-prune"
echo "   /ui-design          /design-audit"
echo "   /design-to-spec     /project-setup     /task-execute"
echo "   /seed-forge         /product-verify    /testforge"
echo "   /demo-forge         /code-replicate"
echo "   /code-tuner"
echo "   /ui-forge"
echo ""
echo "Config locations:"
echo "   Global: $OPENCODE_CONFIG_DIR/skills.json"
echo "   Project: your-project/.opencode/config.json"
echo ""
