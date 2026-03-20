#!/bin/bash

# MySkills 全局安装脚本（OpenCode 版本）
# 用途：在 ~/.config/opencode/ 中配置全局技能，使所有项目可用

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OPENCODE_CONFIG_DIR="$HOME/.config/opencode"

echo "🔧 MySkills OpenCode 全局配置安装"
echo "=================================="

# 1. 创建配置目录
echo "📁 创建配置目录：$OPENCODE_CONFIG_DIR"
mkdir -p "$OPENCODE_CONFIG_DIR"

# 2. 生成 skills.json
echo "📝 生成全局 skills.json"
cat > "$OPENCODE_CONFIG_DIR/skills.json" << EOF
{
  "skills": [
    {
      "name": "product-design",
      "path": "$SCRIPT_DIR/product-design-skill/skills",
      "commands": "$SCRIPT_DIR/product-design-skill/commands",
      "description": "产品设计套件：产品概念、产品地图、体验地图、用例集、功能查漏、功能剪枝、UI 设计、设计审计"
    },
    {
      "name": "dev-forge",
      "path": "$SCRIPT_DIR/dev-forge-skill/skills",
      "commands": "$SCRIPT_DIR/dev-forge-skill/commands",
      "description": "开发锻造套件：项目引导、设计转规格、任务执行、种子数据锻造、产品验收、测试锻造"
    },
    {
      "name": "code-tuner",
      "path": "$SCRIPT_DIR/code-tuner-skill/skills",
      "description": "代码架构质量分析：合规检查、重复检测、抽象分析"
    },
    {
      "name": "ui-forge",
      "path": "$SCRIPT_DIR/ui-forge-skill/skills",
      "commands": "$SCRIPT_DIR/ui-forge-skill/commands",
      "description": "UI 锻造：功能完成后的界面增强与设计还原，面向专业研发团队"
    }
  ],
  "auto_load": true,
  "version": "1.0.0"
}
EOF

# 3. 验证配置
echo "✅ 验证配置..."
if [ -f "$OPENCODE_CONFIG_DIR/skills.json" ]; then
    echo "✓ skills.json 已创建"
    echo ""
    echo "📄 配置内容："
    cat "$OPENCODE_CONFIG_DIR/skills.json"
    echo ""
else
    echo "❌ 创建失败"
    exit 1
fi

# 4. 创建项目模板配置
echo "📁 创建项目模板配置..."
PROJECT_TEMPLATE="$SCRIPT_DIR/.opencode.template"
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

# 5. 使用说明
echo ""
echo "=================================="
echo "🎉 安装完成！"
echo ""
echo "📚 使用方法："
echo ""
echo "1. 在任何项目中，复制项目模板配置："
echo "   cp $PROJECT_TEMPLATE your-project/.opencode/config.json"
echo ""
echo "2. 或者手动创建 .opencode/config.json："
echo '   {'
echo '     "skills": { "inherit": true },'
echo '     "mcp": { "inherit": true }'
echo '   }'
echo ""
echo "3. 现在可以在任何项目中使用以下命令："
echo "   /product-concept    /product-map       /experience-map"
echo "   /use-case           /feature-gap       /feature-prune"
echo "   /ui-design          /design-audit"
echo "   /design-to-spec     /project-setup     /task-execute"
echo "   /seed-forge         /product-verify    /testforge"
echo "   /code-tuner"
echo "   /ui-forge"
echo ""
echo "📂 配置文件位置："
echo "   全局配置：$OPENCODE_CONFIG_DIR/skills.json"
echo "   项目配置：your-project/.opencode/config.json"
echo ""
