# OpenCode 跨项目技能配置指南

## 🎯 目标

配置一次，所有 OpenCode 项目都可以使用 myskills 中的技能。

---

## 📦 架构说明

### 两层配置

```
全局配置 (~/.config/opencode/skills.json)
    ↓
    定义所有可用技能的路径和命令
    ↓
项目配置 (your-project/.opencode/config.json)
    ↓
    继承全局配置 + 项目特定覆盖
```

### 文件位置

| 类型 | 路径 | 用途 |
|------|------|------|
| **全局配置** | `~/.config/opencode/skills.json` | 注册所有技能，所有项目共享 |
| **项目配置** | `your-project/.opencode/config.json` | 继承全局 + 项目特定设置 |
| **技能源** | `/home/hello/Documents/myskills/{skill-name}/skills/` | 技能定义文件 |
| **命令源** | `/home/hello/Documents/myskills/{skill-name}/commands/` | 命令定义文件 |

---

## 🚀 快速开始

### 方式 1：自动安装（推荐）

```bash
cd /home/hello/Documents/myskills
./install-opencode.sh
```

脚本会自动：
1. 创建 `~/.config/opencode/skills.json`
2. 创建 `.opencode.template` 项目模板
3. 输出使用说明

### 方式 2：手动配置

#### Step 1: 创建全局配置

```bash
mkdir -p ~/.config/opencode
cat > ~/.config/opencode/skills.json << 'EOF'
{
  "skills": [
    {
      "name": "product-design",
      "path": "/home/hello/Documents/myskills/product-design-skill/skills",
      "commands": "/home/hello/Documents/myskills/product-design-skill/commands",
      "description": "产品设计套件"
    },
    {
      "name": "dev-forge",
      "path": "/home/hello/Documents/myskills/dev-forge-skill/skills",
      "commands": "/home/hello/Documents/myskills/dev-forge-skill/commands",
      "description": "开发锻造套件"
    },
    {
      "name": "deadhunt",
      "path": "/home/hello/Documents/myskills/deadhunt-skill/skills",
      "description": "死链猎杀"
    },
    {
      "name": "code-tuner",
      "path": "/home/hello/Documents/myskills/code-tuner-skill/skills",
      "description": "代码架构调优"
    }
  ],
  "auto_load": true
}
EOF
```

#### Step 2: 创建项目配置

在任意项目中：

```bash
mkdir -p your-project/.opencode
cat > your-project/.opencode/config.json << 'EOF'
{
  "$schema": "https://opencode.ai/config.schema.json",
  "skills": {
    "inherit": true
  },
  "mcp": {
    "inherit": true
  }
}
EOF
```

---

## 📚 可用技能列表

### Product Design Suite (8 个)

| 命令 | 功能 | 输入 | 输出 |
|------|------|------|------|
| `/product-concept` | 产品概念设计 | 用户对话 | product-concept.json |
| `/product-map` | 产品功能地图 | product-concept | product-map.json |
| `/screen-map` | 界面交互地图 | product-map | screen-map.json |
| `/ui-design` | UI 设计规范 | screen-map | ui-design-spec.md |
| `/use-case` | 测试用例集 | product-map + screen-map | use-case-tree.json |
| `/feature-gap` | 功能缺口检测 | product-map + 代码 | gap-report.json |
| `/feature-prune` | 功能优先级评估 | product-map | prune-report.json |
| `/design-audit` | 设计审计 | 所有设计产物 | audit-report.json |

### Dev Forge Suite (7 个)

| 命令 | 功能 | 输入 | 输出 |
|------|------|------|------|
| `/project-setup` | 项目结构设计 | product-map | project-manifest.json |
| `/design-to-spec` | 设计转技术规格 | product-map + project-manifest | requirements.md + design.md + tasks.md |
| `/project-scaffold` | 生成代码脚手架 | design-to-spec | 实际代码文件 |
| `/task-execute` | 执行编码任务 | tasks.md | 代码实现 |
| `/seed-forge` | 生成演示数据 | product-map + 代码 | 种子数据 |
| `/product-verify` | 产品验收验证 | product-map + 代码 | verify-report.json |
| `/e2e-verify` | E2E 测试验证 | 运行中的应用 | e2e-report.json |

### QA & Architecture (2 个)

| 命令 | 功能 | 输出 |
|------|------|------|
| `/deadhunt` | 死链猎杀 + 产品完整性验证 | deadhunt-report.json |
| `/code-tuner` | 代码架构质量分析 | tuner-report.json (含评分 0-100) |

---

## 🔧 配置说明

### 全局配置字段

```json
{
  "skills": [
    {
      "name": "技能名称",
      "path": "技能定义文件路径 (.md 文件目录)",
      "commands": "命令定义文件路径 (可选)",
      "description": "技能描述"
    }
  ],
  "auto_load": true,  // 自动加载所有技能
  "version": "1.0.0"  // 配置版本
}
```

### 项目配置字段

```json
{
  "$schema": "https://opencode.ai/config.schema.json",
  "skills": {
    "inherit": true,   // 继承全局配置
    "description": "可选的项目特定描述"
  },
  "mcp": {
    "inherit": true    // 继承全局 MCP 配置
  }
}
```

---

## 📁 项目结构示例

```
your-project/
├── .opencode/
│   └── config.json          # 项目配置（继承全局）
├── .allforai/               # 技能输出目录
│   ├── product-concept/
│   ├── product-map/
│   ├── screen-map/
│   ├── use-case/
│   ├── project-forge/
│   └── ...
├── apps/                    # 代码目录
│   ├── flydict-api/
│   ├── flydict-mobile/
│   └── flydict-admin/
└── packages/
    └── shared/
```

---

## 🎯 典型工作流

### 新产品开发（从 0 到 1）

```bash
# 1. 产品概念
/product-concept

# 2. 产品功能地图
/product-map

# 3. 界面交互地图
/screen-map

# 4. UI 设计规范
/ui-design

# 5. 项目结构设计
/project-setup

# 6. 设计转规格
/design-to-spec

# 7. 生成代码脚手架
/project-scaffold

# 8. 开始编码实现
/task-execute

# 9. 生成演示数据
/seed-forge

# 10. 产品验收
/product-verify
```

### 全链路一键执行

```bash
/full-pipeline  # 在 product-design 技能中
```

---

## 🔍 故障排查

### 问题 1：技能命令找不到

**症状**：`/design-to-spec` 等命令无响应

**检查**：
```bash
# 1. 验证全局配置存在
cat ~/.config/opencode/skills.json

# 2. 验证项目配置存在
cat your-project/.opencode/config.json

# 3. 验证技能文件存在
ls /home/hello/Documents/myskills/dev-forge-skill/skills/
```

**解决**：
```bash
# 重新运行安装脚本
cd /home/hello/Documents/myskills
./install-opencode.sh
```

### 问题 2：技能文件路径错误

**症状**：技能加载失败

**检查**：
```bash
# 验证路径
ls /home/hello/Documents/myskills/product-design-skill/skills/
```

**解决**：更新 `~/.config/opencode/skills.json` 中的路径

### 问题 3：项目配置未继承全局

**症状**：只有部分技能可用

**检查项目配置**：
```json
{
  "skills": {
    "inherit": true  // 确保此项存在
  }
}
```

---

## 📊 与 Claude Code 对比

| 特性 | OpenCode | Claude Code |
|------|----------|-------------|
| **配置位置** | `~/.config/opencode/skills.json` | `~/.claude/settings.json` |
| **项目配置** | `.opencode/config.json` | 无（纯全局） |
| **技能格式** | `.md` 文件 | 插件缓存 |
| **命令触发** | `/command-name` | `/skill-name` |
| **MCP 配置** | `~/.config/opencode/mcp.json` | `~/.claude/plugins/marketplaces/` |

---

## 🎉 完成！

现在你可以在任何 OpenCode 项目中使用 myskills 的所有技能，无需重复配置！

**下一步**：
- 查看技能列表：`cat ~/.config/opencode/skills.json`
- 开始使用：`/product-map`
- 查看文档：`cat /home/hello/Documents/myskills/README.md`
