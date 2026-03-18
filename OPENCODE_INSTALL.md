# Skills 安装和使用指南

## ⚠️ 重要说明

这些 skills 是为 **Claude Code** 设计的插件系统，使用 `.md` 技能文件格式。

**Opencode** 使用不同的架构（内置 agents + MCP servers），不直接支持外部 skills。

---

## 方案 1: 在 Claude Code 中使用（推荐）

这些 skills 已配置为 Claude Code 插件：

```bash
# 1. 安装插件
cd ~/Documents/myskills
claude plugin add ./product-design-skill
claude plugin add ./dev-forge-skill
claude plugin add ./code-tuner-skill

# 2. 使用 skills
/product-concept     # 产品概念
/product-map         # 产品地图
/experience-map      # 体验地图
/use-case            # 用例集
/feature-gap         # 功能查漏
/feature-prune       # 功能剪枝
/design-audit        # 设计审计
```

### MCP 服务器配置

OpenRouter MCP 服务器已配置在 `product-design-skill/.mcp.json`：

```json
{
  "mcpServers": {
    "openrouter": {
      "command": "node",
      "args": ["${CLAUDE_PLUGIN_ROOT}/mcp-ai-gateway/dist/index.js"],
      "env": {
        "OPENROUTER_API_KEY": "${OPENROUTER_API_KEY}"
      }
    }
  }
}
```

---

## 方案 2: 在 Opencode 中使用 MCP

Opencode 支持 MCP 服务器，可以配置 OpenRouter：

```bash
# MCP 配置位置：~/.config/opencode/mcp.json
# 已配置 OpenRouter 服务器
```

### 测试 MCP 连接

```bash
cd ~/Documents/myskills/product-design-skill/mcp-ai-gateway
./test-connection.sh
```

---

## 可用 Skills 列表

### Product Design Suite (v4.16.1)
| 命令 | 功能 |
|------|------|
| `/product-concept` | 产品概念发现（支持创新增强） |
| `/product-map` | 产品功能地图 |
| `/experience-map` | 体验地图 |
| `/use-case` | 用例集生成 |
| `/feature-gap` | 功能查漏 |
| `/feature-prune` | 功能剪枝 |
| `/ui-design` | UI 设计 |
| `/design-audit` | 设计审计 |

### Dev Forge Suite (v5.8.1)
| 命令 | 功能 |
|------|------|
| `/project-forge` | 项目锻造全流程 |
| `/seed-forge` | 种子数据锻造 |
| `/product-verify` | 产品验收 |

### Deadhunt
| 命令 | 功能 |
|------|------|
| `/deadhunt` | 死链猎杀 + 产品完整性验证 |

### Code Tuner (v1.1.1)
| 命令 | 功能 |
|------|------|
| `/code-tuner` | 代码架构质量分析 |

### UI Forge (v0.1.2)
| 命令 | 功能 |
|------|------|
| `/ui-forge` | 功能完成后的界面增强与设计还原 |

---

## 创新增强功能

Product Design v3.3.0+ 支持创新增强：

- ✅ 多模型协作（Qwen3/DeepSeek-V3.2/Llama4）
- ✅ 区域自适应（中国区/国际区自动检测）
- ✅ LLM 智能判断最新模型（24 小时缓存）
- ✅ 创新流程（假设清零/创新机会/对抗性生成）

---

## 环境变量

```bash
export OPENROUTER_API_KEY="sk-or-v1-YOUR_KEY"
```

---

## 测试

```bash
# 运行创新流程测试
cd ~/Documents/myskills/product-design-skill/mcp-ai-gateway
./test-innovation-flow.sh

# 查看输出
ls -la ~/Documents/myskills/.allforai/product-concept/innovation-test/
```
