---
description: "还原度验证：对比源码 vs 目标代码，按多维度评分，不达标则分析→修复→重评闭环。模式: full / analyze / fix"
argument-hint: "[mode] [--target <target-path>] [--threshold 90]"
allowed-tools: ["Read", "Write", "Grep", "Glob", "Bash", "AskUserQuestion", "Agent"]
---

# CR Fidelity — 还原度验证

用户请求: $ARGUMENTS

## 插件根目录

所有文档路径基于插件安装目录: `${CLAUDE_PLUGIN_ROOT}`

## 参数解析

从 `$ARGUMENTS` 解析：

| 参数 | 格式 | 说明 |
|------|------|------|
| `mode` | 位置参数 #1 | full（完整闭环）/ analyze（仅分析）/ fix（仅修复上次分析的差距） |
| `--target` | 路径 | 目标代码根目录（默认：当前目录） |
| `--threshold` | 数字 | 达标分数（默认：90，范围 0-100） |

## 参数缺失引导

当 `$ARGUMENTS` 为空时，用 AskUserQuestion 引导：
1. **目标代码位置**：「dev-forge 生成的目标代码在哪里？」选项：当前目录 `.` / 输入路径
2. **验证模式**：「需要什么级别的验证？」选项：full（分析+修复闭环，推荐）/ analyze（仅出报告）

## 前置条件检查

1. `.allforai/code-replicate/source-summary.json` 必须存在（code-replicate 已跑过）
2. `.allforai/product-map/task-inventory.json` 必须存在（产物已生成）
3. 目标代码目录必须存在且含代码文件

缺失任何前置条件 → 提示用户先执行 `/code-replicate` 和 `/task-execute`

## 执行

加载技能文件执行验证：

> 详见 ${CLAUDE_PLUGIN_ROOT}/skills/cr-fidelity.md

## 快速参考

```
/cr-fidelity                              # 交互式引导
/cr-fidelity full                         # 完整闭环：分析→修复→重测直到达标
/cr-fidelity analyze                      # 仅分析出报告，不修复
/cr-fidelity fix                          # 修复上次分析发现的差距
/cr-fidelity full --threshold 95          # 设置 95 分达标线
/cr-fidelity full --target ./target-app   # 指定目标代码路径
```
