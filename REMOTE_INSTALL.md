# MySkills 远程安装指南

## 🎯 目标

通过 Git 从 GitHub 仓库远程安装 myskills，**配置一次，所有项目自动可用**。

---

## 🚀 快速安装（一键脚本）

### 方式 1：自动安装（推荐）

```bash
# 使用 curl 下载并执行安装脚本
curl -fsSL https://raw.githubusercontent.com/allforai/myskills/main/install-remote.sh | bash
```

### 方式 2：手动安装

```bash
# 1. 克隆仓库
git clone git@github.com:allforai/myskills.git ~/.opencode/skills/myskills

# 2. 运行安装脚本
~/.opencode/skills/myskills/install-remote.sh
```

### 方式 3：HTTPS 方式（无 SSH key）

```bash
# 使用 HTTPS 克隆（适合没有配置 SSH key 的用户）
git clone https://github.com/allforai/myskills.git ~/.opencode/skills/myskills
~/.opencode/skills/myskills/install-remote.sh
```

---

## ✅ 安装完成后

**全局配置已自动生效，所有新项目无需任何配置即可使用技能！**

直接在任意项目中使用：

```bash
cd any-new-project
/product-map          # 直接使用，无需配置
/design-to-spec       # 直接使用，无需配置
/task-execute         # 直接使用，无需配置
```

---

## 📦 安装脚本做了什么？

安装脚本会自动完成以下步骤：

1. **克隆仓库** → `~/.opencode/skills/myskills`
2. **创建全局配置** → `~/.config/opencode/skills.json`（`auto_load: true`）
3. **创建更新脚本** → `~/.opencode/skills/myskills/update-skills.sh`

**全局配置说明**：
- `auto_load: true` — 自动加载所有技能到所有项目
- `global_enabled: true` — 全局技能启用
- `project_config_required: false` — 项目无需配置文件

---

## 📁 配置位置

| 类型 | 路径 | 说明 |
|------|------|------|
| **全局配置** | `~/.config/opencode/skills.json` | 所有项目共享，自动生效 |
| **全局 MCP** | `~/.config/opencode/mcp.json` | MCP 服务器配置 |
| **技能目录** | `~/.opencode/skills/myskills` | Git 克隆的技能源 |
| **项目配置** | `your-project/.opencode/config.json` | **可选**，仅用于覆盖全局配置 |

---

## 🎯 项目级配置（可选）

**只有需要覆盖全局配置时才需要项目级配置**。

### 场景 1：禁用某些技能

```json
{
  "skills": {
    "disable": ["code-tuner", "ui-forge"]
  }
}
```

### 场景 2：添加项目特定技能

```json
{
  "skills": [
    {
      "name": "custom-skill",
      "path": "./custom-skills/",
      "description": "项目特定技能"
    }
  ]
}
```

### 场景 3：明确继承全局配置（文档作用）

```json
{
  "$schema": "https://opencode.ai/config.schema.json",
  "skills": {
    "inherit": true,
    "description": "继承全局技能配置"
  },
  "mcp": {
    "inherit": true
  }
}
```

---

## 🔄 更新技能

### 方式 1：使用更新脚本（推荐）

```bash
~/.opencode/skills/myskills/update-skills.sh
```

### 方式 2：手动更新

```bash
cd ~/.opencode/skills/myskills
git pull origin main
```

---

## 📚 可用技能列表

### Product Design Suite (8 个)

| 命令 | 功能 |
|------|------|
| `/product-concept` | 产品概念设计 |
| `/product-map` | 产品功能地图 |
| `/experience-map` | 体验地图 |
| `/ui-design` | UI 设计规范 |
| `/use-case` | 测试用例集 |
| `/feature-gap` | 功能缺口检测 |
| `/feature-prune` | 功能优先级评估 |
| `/design-audit` | 设计审计 |

### Dev Forge Suite (6 个)

| 命令 | 功能 |
|------|------|
| `/project-setup` | 项目结构设计 |
| `/design-to-spec` | 设计转技术规格 |
| `/task-execute` | 执行编码任务 |
| `/seed-forge` | 生成演示数据 |
| `/product-verify` | 产品验收验证 |
| `/testforge` | 测试锻造 |

### QA & Architecture (1 个)

| 命令 | 功能 |
|------|------|
| `/code-tuner` | 代码架构质量分析 |

---

## 🔍 故障排查

### 问题 1：新项目中技能命令找不到

**症状**：在新项目中使用 `/product-map` 无响应

**检查**：
```bash
# 1. 验证全局配置存在且正确
cat ~/.config/opencode/skills.json

# 2. 验证 auto_load 为 true
cat ~/.config/opencode/skills.json | grep auto_load

# 3. 验证技能目录存在
ls ~/.opencode/skills/myskills/
```

**解决**：
```bash
# 重新运行安装脚本
~/.opencode/skills/myskills/install-remote.sh
```

### 问题 2：Git 克隆失败

**症状**：`git clone` 失败

**SSH 方式错误**：
```bash
# 检查 SSH key
ssh -T git@github.com
```

**解决**（切换到 HTTPS）：
```bash
git clone https://github.com/allforai/myskills.git ~/.opencode/skills/myskills
~/.opencode/skills/myskills/install-remote.sh
```

### 问题 3：技能更新后未生效

**症状**：运行旧命令，没有新技能

**解决**：
```bash
# 1. 更新技能
~/.opencode/skills/myskills/update-skills.sh

# 2. 重启 OpenCode 会话

# 3. 验证配置时间戳
cat ~/.config/opencode/skills.json | grep last_updated
```

---

## 📊 目录结构

```
~/.opencode/skills/myskills/
├── product-design-skill/
│   ├── skills/           # 技能定义
│   ├── commands/         # 命令定义
│   └── .mcp.json
├── dev-forge-skill/
│   ├── skills/
│   ├── commands/
│   └── .mcp.json
├── code-tuner-skill/
│   └── skills/
├── install-remote.sh     # 安装脚本
├── update-skills.sh      # 更新脚本
└── .opencode.template    # 项目模板（可选）

~/.config/opencode/
├── skills.json           # 全局技能配置（auto_load: true）
├── mcp.json              # 全局 MCP 配置
└── opencode.json         # OpenCode 主配置
```

---

## 🎉 验证安装

```bash
# 1. 检查全局配置
cat ~/.config/opencode/skills.json

# 2. 检查技能目录
ls -la ~/.opencode/skills/myskills/

# 3. 在新项目中测试（无需配置）
mkdir -p /tmp/test-project
cd /tmp/test-project
/product-map  # 应该可以直接使用
```

---

## 🌐 仓库信息

- **GitHub**: https://github.com/allforai/myskills
- **SSH**: git@github.com:allforai/myskills.git
- **分支**: main（稳定版）
- **版本**: rolling current plugin versions from repository manifests

---

## 💡 提示

1. **一次安装，所有项目可用** — 全局配置 `auto_load: true` 确保所有项目自动加载技能
2. **项目配置可选** — 只有需要覆盖全局配置时才创建 `.opencode/config.json`
3. **定期更新** — 运行 `update-skills.sh` 获取最新功能
4. **多设备同步** — 在多台设备上使用相同的 Git 仓库安装，保持一致性

---

## 📖 相关文档

- [OpenCode 配置详解](./OPENCODE_SETUP.md)
- [产品概念设计](./product-design-skill/README.md)
- [开发锻造套件](./dev-forge-skill/README.md)
