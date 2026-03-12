#!/bin/bash

# MySkills 远程安装脚本（OpenCode + Git 方式）
# 用途：从 GitHub 仓库克隆技能，配置全局技能注册

set -e

# 配置
REPO_URL="git@github.com:allforai/myskills.git"
REPO_HTTPS="https://github.com/allforai/myskills.git"
INSTALL_DIR="$HOME/.opencode/skills/myskills"
OPENCODE_CONFIG_DIR="$HOME/.config/opencode"
SKILLS_CONFIG="$OPENCODE_CONFIG_DIR/skills.json"

echo "🚀 MySkills 远程安装（Git 方式）"
echo "=================================="
echo ""

# 1. 选择克隆方式
echo "📦 选择克隆方式："
echo "  1) SSH (git@github.com:allforai/myskills.git) - 推荐，需要配置 SSH key"
echo "  2) HTTPS (https://github.com/allforai/myskills.git) - 无需配置"
echo ""
read -p "请选择 (1/2, 默认 1): " clone_choice

if [ "$clone_choice" = "2" ]; then
    REPO_USE="$REPO_HTTPS"
    echo "✓ 使用 HTTPS 方式"
else
    REPO_USE="$REPO_URL"
    echo "✓ 使用 SSH 方式"
fi

echo ""

# 2. 创建安装目录
echo "📁 创建安装目录：$INSTALL_DIR"
mkdir -p "$INSTALL_DIR"

# 3. 克隆或更新仓库
if [ -d "$INSTALL_DIR/.git" ]; then
    echo "🔄 检测到已安装的仓库，执行 git pull..."
    cd "$INSTALL_DIR"
    git pull origin main
    echo "✓ 仓库已更新"
else
    echo "📥 克隆仓库..."
    git clone "$REPO_USE" "$INSTALL_DIR"
    echo "✓ 仓库已克隆"
fi

echo ""

# 4. 创建全局配置目录
echo "📁 创建配置目录：$OPENCODE_CONFIG_DIR"
mkdir -p "$OPENCODE_CONFIG_DIR"

# 5. 生成 skills.json（使用绝对路径）
echo "📝 生成全局 skills.json"
cat > "$SKILLS_CONFIG" << EOF
{
  "skills": [
    {
      "name": "product-design",
      "path": "$INSTALL_DIR/product-design-skill/skills",
      "commands": "$INSTALL_DIR/product-design-skill/commands",
      "description": "产品设计套件：产品概念、功能地图、界面地图、用例集、功能查漏、功能剪枝、UI 设计、设计审计",
      "source": {
        "type": "git",
        "repo": "$REPO_USE",
        "branch": "main",
        "subPath": "product-design-skill"
      }
    },
    {
      "name": "dev-forge",
      "path": "$INSTALL_DIR/dev-forge-skill/skills",
      "commands": "$INSTALL_DIR/dev-forge-skill/commands",
      "description": "开发锻造套件：项目引导、设计转规格、脚手架生成、任务执行、种子数据锻造、产品验收",
      "source": {
        "type": "git",
        "repo": "$REPO_USE",
        "branch": "main",
        "subPath": "dev-forge-skill"
      }
    },
    {
      "name": "deadhunt",
      "path": "$INSTALL_DIR/deadhunt-skill/skills",
      "description": "死链猎杀 + 产品完整性验证",
      "source": {
        "type": "git",
        "repo": "$REPO_USE",
        "branch": "main",
        "subPath": "deadhunt-skill"
      }
    },
    {
      "name": "code-tuner",
      "path": "$INSTALL_DIR/code-tuner-skill/skills",
      "description": "代码架构质量分析：合规检查、重复检测、抽象分析",
      "source": {
        "type": "git",
        "repo": "$REPO_USE",
        "branch": "main",
        "subPath": "code-tuner-skill"
      }
    }
  ],
  "auto_load": true,
  "version": "2.0.0",
  "installed_at": "$(date -Iseconds)",
  "last_updated": "$(date -Iseconds)"
}
EOF

echo "✓ skills.json 已创建"

echo ""

# 6. 验证配置
echo "✅ 验证配置..."
if [ -f "$SKILLS_CONFIG" ]; then
    echo "✓ skills.json 存在"
    
    # 验证技能目录
    if [ -d "$INSTALL_DIR/product-design-skill/skills" ]; then
        echo "✓ product-design 技能目录存在"
    else
        echo "⚠️  product-design 技能目录不存在"
    fi
    
    if [ -d "$INSTALL_DIR/dev-forge-skill/skills" ]; then
        echo "✓ dev-forge 技能目录存在"
    else
        echo "⚠️  dev-forge 技能目录不存在"
    fi
else
    echo "❌ skills.json 创建失败"
    exit 1
fi

echo ""

# 7. 创建项目模板
echo "📁 创建项目模板配置..."
PROJECT_TEMPLATE="$INSTALL_DIR/.opencode.template"
cat > "$PROJECT_TEMPLATE" << EOF
{
  "\$schema": "https://opencode.ai/config.schema.json",
  "skills": {
    "inherit": true,
    "description": "继承全局技能配置 (~/.config/opencode/skills.json)"
  },
  "mcp": {
    "inherit": true
  }
}
EOF
echo "✓ 项目模板已创建：$PROJECT_TEMPLATE"

# 8. 创建更新脚本
UPDATE_SCRIPT="$INSTALL_DIR/update-skills.sh"
cat > "$UPDATE_SCRIPT" << 'EOF'
#!/bin/bash
# MySkills 更新脚本（OpenCode + Claude Code 双通道）

INSTALL_DIR="$HOME/.opencode/skills/myskills"
CC_MARKETPLACE_DIR="$HOME/.claude/plugins/marketplaces"

# 1. 更新 OpenCode 技能仓库
if [ -d "$INSTALL_DIR/.git" ]; then
    echo "🔄 更新 OpenCode 技能..."
    cd "$INSTALL_DIR"
    git pull origin main
    echo "✓ OpenCode 技能已更新"
else
    echo "⏭️  OpenCode 技能未安装，跳过"
fi

# 2. 更新 Claude Code marketplace 缓存
if [ -d "$CC_MARKETPLACE_DIR" ]; then
    for dir in "$CC_MARKETPLACE_DIR"/*/; do
        if [ -d "$dir/.git" ]; then
            name=$(basename "$dir")
            echo "🔄 更新 Claude Code marketplace 缓存: $name"
            git -C "$dir" pull origin main 2>/dev/null || git -C "$dir" pull 2>/dev/null || echo "⚠️  $name 同步失败"
        fi
    done
    echo "✓ Claude Code marketplace 缓存已更新"
else
    echo "⏭️  Claude Code 插件未安装，跳过"
fi

# 3. 更新 OpenCode 时间戳
SKILLS_CONFIG="$HOME/.config/opencode/skills.json"
if [ -f "$SKILLS_CONFIG" ]; then
    echo "📝 更新时间戳..."
    # 使用 sed 更新 last_updated 字段（兼容 Linux 和 macOS）
    if sed --version 2>/dev/null | grep -q GNU; then
        sed -i "s/\"last_updated\": \"[^\"]*\"/\"last_updated\": \"$(date -Iseconds)\"/" "$SKILLS_CONFIG"
    else
        sed -i '' "s/\"last_updated\": \"[^\"]*\"/\"last_updated\": \"$(date -Iseconds)\"/" "$SKILLS_CONFIG"
    fi
    echo "✓ 时间戳已更新"
fi

echo "🎉 更新完成！"
EOF
chmod +x "$UPDATE_SCRIPT"
echo "✓ 更新脚本已创建：$UPDATE_SCRIPT"

# 9. 输出使用说明
echo ""
echo "=================================="
echo "🎉 安装完成！"
echo ""
echo "📚 使用方法："
echo ""
echo "✅ 全局配置已完成，所有新项目自动可用，无需额外配置！"
echo ""
echo "可选：如果项目需要特定覆盖，可以创建 .opencode/config.json："
echo '   {'
echo '     "skills": { "inherit": true },'
echo '     "mcp": { "inherit": true }'
echo '   }'
echo ""
echo "现在可以在任何项目中使用以下命令："
echo "   产品设计：/product-concept  /product-map  /screen-map  /ui-design"
echo "   测试用例：/use-case  /feature-gap  /feature-prune  /design-audit"
echo "   开发锻造：/design-to-spec  /project-scaffold  /project-setup  /task-execute"
echo "   数据验证：/seed-forge  /product-verify  /e2e-verify"
echo "   架构分析：/deadhunt  /code-tuner"
echo ""
echo "📂 配置文件位置："
echo "   全局配置：$SKILLS_CONFIG"
echo "   技能目录：$INSTALL_DIR"
echo "   项目配置：your-project/.opencode/config.json"
echo ""
echo "🔄 更新技能："
echo "   $UPDATE_SCRIPT"
echo ""
echo "🌐 仓库地址：$REPO_HTTPS"
echo ""
