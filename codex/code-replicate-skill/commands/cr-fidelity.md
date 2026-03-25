---
name: cr-fidelity
description: "还原度验证：对比源码 vs 目标代码，按多维度评分，不达标则分析→修复→重评闭环。模式: full / analyze / fix"
---

# CR Fidelity — 还原度验证

## 参数解析

从用户请求中推断：

| 参数 | 格式 | 说明 |
|------|------|------|
| `mode` | 位置参数 #1 | full（完整闭环）/ analyze（仅分析）/ fix（仅修复上次分析的差距） |
| `--target` | 路径 | 目标代码根目录（默认：当前目录） |
| `--threshold` | 数字 | 达标分数（默认：90，范围 0-100） |

## 参数缺失处理

当参数缺失时，按以下默认值处理：
1. **目标代码位置**：假定当前目录 `.`
2. **验证模式**：默认 `full`（分析+修复闭环）

## 前置条件检查

1. `.allforai/code-replicate/source-summary.json` 必须存在（code-replicate 已跑过）
2. `.allforai/product-map/task-inventory.json` 必须存在（产物已生成）
3. 目标代码目录必须存在且含代码文件

缺失任何前置条件 → 提示用户先执行 code-replicate 和 task-execute

## 执行

加载技能文件执行验证：

> 详见 ./skills/cr-fidelity.md
