# Openencode Skill 安装指南

## 安装步骤

### 1. 配置 MCP Server

OpenRouter MCP 服务器已配置在 `~/.config/opencode/mcp.json`：

```json
{
  "mcpServers": {
    "openrouter": {
      "command": "node",
      "args": ["/home/hello/Documents/myskills/product-design-skill/mcp-openrouter/dist/index.js"],
      "env": {
        "OPENROUTER_API_KEY": "YOUR_API_KEY"
      }
    }
  }
}
```

### 2. 配置 Skills

项目级配置在 `~/Documents/myskills/.opencode/config.json`：

```json
{
  "skills": [
    {
      "name": "product-design",
      "path": "../product-design-skill/skills",
      "commands": "../product-design-skill/commands"
    },
    {
      "name": "dev-forge",
      "path": "../dev-forge-skill/skills",
      "commands": "../dev-forge-skill/commands"
    },
    {
      "name": "deadhunt",
      "path": "../deadhunt-skill/skills"
    },
    {
      "name": "code-tuner",
      "path": "../code-tuner-skill/skills"
    }
  ]
}
```

### 3. 验证安装

```bash
# 检查 MCP 服务器
opencode mcp list

# 测试 OpenRouter 连接
cd ~/Documents/myskills/product-design-skill/mcp-openrouter
./test-connection.sh
```

## 可用 Skills

### Product Design (v3.3.0)
- `/product-concept` - 产品概念发现
- `/product-map` - 产品功能地图
- `/screen-map` - 界面地图
- `/use-case` - 用例集生成
- `/feature-gap` - 功能查漏
- `/feature-prune` - 功能剪枝
- `/ui-design` - UI 设计
- `/design-audit` - 设计审计

### Dev Forge (v2.3.0)
- `/project-forge` - 项目锻造全流程
- `/seed-forge` - 种子数据锻造
- `/product-verify` - 产品验收

### Deadhunt (v1.9.0)
- `/deadhunt` - 死链猎杀 + 产品完整性验证

### Code Tuner (v1.0.0)
- `/code-tuner` - 代码架构质量分析

## 创新增强功能

Product Design v3.3.0+ 支持创新增强流程：

- **多模型协作** - 自动选择最佳模型（Qwen/DeepSeek/Llama）
- **区域自适应** - 中国区/国际区自动检测
- **LLM 智能选模型** - 24 小时缓存，一天一更新
- **创新流程** - 假设清零、创新机会、对抗性生成

## 环境变量

```bash
export OPENROUTER_API_KEY="sk-or-v1-YOUR_KEY"
```

## 测试

```bash
# 运行创新流程测试
cd ~/Documents/myskills/product-design-skill/mcp-openrouter
./test-innovation-flow.sh

# 输出目录
ls -la ~/Documents/myskills/.allforai/product-concept/innovation-test/
```
