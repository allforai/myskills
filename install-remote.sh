#!/bin/bash

# MySkills remote installer for OpenCode
# Clones the repo and registers the current OpenCode skills globally

set -e

# 配置
REPO_URL="git@github.com:allforai/myskills.git"
REPO_HTTPS="https://github.com/allforai/myskills.git"
INSTALL_DIR="$HOME/.opencode/skills/myskills"
OPENCODE_CONFIG_DIR="$HOME/.config/opencode"
SKILLS_CONFIG="$OPENCODE_CONFIG_DIR/skills.json"

echo "[myskills] Remote OpenCode native install"
echo "=================================="
echo ""

# 1. Choose clone mode
echo "Choose clone mode:"
echo "  1) SSH (git@github.com:allforai/myskills.git)"
echo "  2) HTTPS (https://github.com/allforai/myskills.git)"
echo ""
read -p "Choose (1/2, default 1): " clone_choice

if [ "$clone_choice" = "2" ]; then
    REPO_USE="$REPO_HTTPS"
    echo "Using HTTPS"
else
    REPO_USE="$REPO_URL"
    echo "Using SSH"
fi

echo ""

# 2. Create install directory
echo "Creating install directory: $INSTALL_DIR"
mkdir -p "$INSTALL_DIR"

# 3. Clone or update repository
if [ -d "$INSTALL_DIR/.git" ]; then
    echo "Repository already installed, pulling latest changes..."
    cd "$INSTALL_DIR"
    git pull origin main
    echo "Repository updated"
else
    echo "Cloning repository..."
    git clone "$REPO_USE" "$INSTALL_DIR"
    echo "Repository cloned"
fi

echo ""

# 4. Create config directory
echo "Creating config directory: $OPENCODE_CONFIG_DIR"
mkdir -p "$OPENCODE_CONFIG_DIR"

# 5. Generate skills.json
echo "Generating global skills.json"
cat > "$SKILLS_CONFIG" << EOF
{
  "skills": [
    {
      "name": "product-design",
      "path": "$INSTALL_DIR/opencode/product-design-skill/skills",
      "commands": "$INSTALL_DIR/opencode/product-design-skill/commands",
      "description": "Product design suite: concept, map, journey, experience-map, use-case, feature-gap, feature-prune, ui-design, design-audit",
      "source": {
        "type": "git",
        "repo": "$REPO_USE",
        "branch": "main",
        "subPath": "opencode/product-design-skill"
      }
    },
    {
      "name": "dev-forge",
      "path": "$INSTALL_DIR/opencode/dev-forge-skill/skills",
      "commands": "$INSTALL_DIR/opencode/dev-forge-skill/commands",
      "description": "Development forge: setup, design-to-spec, scaffold, task-execute, testforge, deadhunt, fieldcheck, seed-forge, product-verify",
      "source": {
        "type": "git",
        "repo": "$REPO_USE",
        "branch": "main",
        "subPath": "opencode/dev-forge-skill"
      }
    },
    {
      "name": "code-tuner",
      "path": "$INSTALL_DIR/opencode/code-tuner-skill/references",
      "commands": "$INSTALL_DIR/opencode/code-tuner-skill/commands",
      "description": "Code architecture tuner: compliance, duplication, abstraction analysis",
      "source": {
        "type": "git",
        "repo": "$REPO_USE",
        "branch": "main",
        "subPath": "opencode/code-tuner-skill"
      }
    },
    {
      "name": "demo-forge",
      "path": "$INSTALL_DIR/opencode/demo-forge-skill/skills",
      "commands": "$INSTALL_DIR/opencode/demo-forge-skill/commands",
      "description": "Demo forge: design, media, execute, verify with multi-round iteration",
      "source": {
        "type": "git",
        "repo": "$REPO_USE",
        "branch": "main",
        "subPath": "opencode/demo-forge-skill"
      }
    },
    {
      "name": "ui-forge",
      "path": "$INSTALL_DIR/opencode/ui-forge-skill/skills",
      "commands": "$INSTALL_DIR/opencode/ui-forge-skill/commands",
      "description": "UI forge: post-implementation fidelity restore and polish",
      "source": {
        "type": "git",
        "repo": "$REPO_USE",
        "branch": "main",
        "subPath": "opencode/ui-forge-skill"
      }
    },
    {
      "name": "code-replicate",
      "path": "$INSTALL_DIR/opencode/code-replicate-skill/skills",
      "commands": "$INSTALL_DIR/opencode/code-replicate-skill/commands",
      "description": "Code replication bridge: reverse-engineer codebases into .allforai/ artifacts",
      "source": {
        "type": "git",
        "repo": "$REPO_USE",
        "branch": "main",
        "subPath": "opencode/code-replicate-skill"
      }
    }
  ],
  "auto_load": true,
  "version": "2.0.0",
  "installed_at": "$(date -Iseconds)",
  "last_updated": "$(date -Iseconds)"
}
EOF

echo "skills.json created"

echo ""

# 6. Validate config
echo "Validating config..."
if [ -f "$SKILLS_CONFIG" ]; then
    echo "skills.json present"
    
    if [ -d "$INSTALL_DIR/opencode/product-design-skill/skills" ]; then
        echo "product-design skill present"
    else
        echo "warning: product-design skill missing"
    fi

    if [ -d "$INSTALL_DIR/opencode/dev-forge-skill/skills" ]; then
        echo "dev-forge skill present"
    else
        echo "warning: dev-forge skill missing"
    fi

    if [ -d "$INSTALL_DIR/opencode/ui-forge-skill/skills" ]; then
        echo "ui-forge skill present"
    else
        echo "warning: ui-forge skill missing"
    fi
else
    echo "Failed to create skills.json"
    exit 1
fi

echo ""

# 7. Create project template
echo "Creating project template..."
PROJECT_TEMPLATE="$INSTALL_DIR/.opencode.template"
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

# 7.5 Make scripts executable
echo "Making Python scripts executable..."
find "$INSTALL_DIR" -type d -name "scripts" -exec find {} -name "*.py" -exec chmod +x {} \; \;
echo "Permissions updated"

# 8. Create update script
UPDATE_SCRIPT="$INSTALL_DIR/update-skills.sh"
cat > "$UPDATE_SCRIPT" << 'EOF'
#!/bin/bash
# MySkills updater for OpenCode + Claude Code

INSTALL_DIR="$HOME/.opencode/skills/myskills"
CC_MARKETPLACE_DIR="$HOME/.claude/plugins/marketplaces"

# 1. Update OpenCode repository
if [ -d "$INSTALL_DIR/.git" ]; then
    echo "Updating OpenCode repository..."
    cd "$INSTALL_DIR"
    git pull origin main
    echo "OpenCode repository updated"
else
    echo "OpenCode repository not installed, skipping"
fi

# 2. Update Claude Code marketplace cache
if [ -d "$CC_MARKETPLACE_DIR" ]; then
    for dir in "$CC_MARKETPLACE_DIR"/*/; do
        if [ -d "$dir/.git" ]; then
            name=$(basename "$dir")
            echo "Updating Claude marketplace cache: $name"
            git -C "$dir" pull origin main 2>/dev/null || git -C "$dir" pull 2>/dev/null || echo "warning: $name sync failed"
        fi
    done
    echo "Claude marketplace cache updated"
else
    echo "Claude plugins not installed, skipping"
fi

# 3. Update OpenCode timestamp
SKILLS_CONFIG="$HOME/.config/opencode/skills.json"
if [ -f "$SKILLS_CONFIG" ]; then
    echo "Updating timestamp..."
    # Use sed to update last_updated on Linux and macOS.
    if sed --version 2>/dev/null | grep -q GNU; then
        sed -i "s/\"last_updated\": \"[^\"]*\"/\"last_updated\": \"$(date -Iseconds)\"/" "$SKILLS_CONFIG"
    else
        sed -i '' "s/\"last_updated\": \"[^\"]*\"/\"last_updated\": \"$(date -Iseconds)\"/" "$SKILLS_CONFIG"
    fi
    echo "Timestamp updated"
fi

# 4. Make scripts executable again after update
echo "Making Python scripts executable..."
find "$INSTALL_DIR" -type d -name "scripts" -exec find {} -name "*.py" -exec chmod +x {} \; \;
echo "Permissions updated"

echo "Update complete"
EOF
chmod +x "$UPDATE_SCRIPT"
echo "Update script created: $UPDATE_SCRIPT"

# 9. Usage
echo ""
echo "=================================="
echo "Install complete"
echo ""
echo "Usage:"
echo ""
echo "Global OpenCode native configuration is ready."
echo ""
echo "Optional project-level override:"
echo '   {'
echo '     "skills": { "inherit": true },'
echo '     "mcp": { "inherit": true }'
echo '   }'
echo ""
echo "Available OpenCode native commands:"
echo "   /product-concept  /product-map  /experience-map  /ui-design"
echo "   /use-case  /feature-gap  /feature-prune  /design-audit"
echo "   /design-to-spec  /project-setup  /task-execute  /testforge"
echo "   /seed-forge  /product-verify  /demo-forge  /code-replicate"
echo "   /code-tuner  /ui-forge"
echo ""
echo "Config locations:"
echo "   Global: $SKILLS_CONFIG"
echo "   Skill repo: $INSTALL_DIR"
echo "   Project: your-project/.opencode/config.json"
echo ""
echo "Updater:"
echo "   $UPDATE_SCRIPT"
echo ""
echo "Repository: $REPO_HTTPS"
echo ""
