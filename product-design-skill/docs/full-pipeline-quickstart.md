# Full Pipeline 快速开始指南

> 统一编排产品设计、开发、测试、架构四层流程，实现全链路自动化。

## 什么是 Full Pipeline？

Full Pipeline 是一个统一的编排命令，将四个独立的 skill 套件整合成一个完整的自动化流程：

```
Product Design (产品设计层)
    ↓
Dev Forge (开发层)
    ↓
DeadHunt (QA层)
    ↓
Code Tuner (架构层)
```

**核心特性**：
- ✅ 统一编排：一个命令执行全部流程
- ✅ 质量门禁：每层都有明确的质量标准
- ✅ 反馈循环：下游发现问题自动反馈给上游
- ✅ 全局追踪：统一记录所有决策和问题
- ✅ 增量执行：只重跑有变更的部分

## 快速开始

### 1. 执行完整流程

```bash
/full-pipeline
```

这会从头到尾执行所有层，包括：
- 产品设计层的 8 个阶段
- 开发层的种子数据和验收
- QA 层的死链检测和 CRUD 验证
- 架构层的代码分析

### 2. 从断点继续

如果流程中断，可以继续执行：

```bash
/full-pipeline resume
```

自动检测已完成的阶段，从第一个未完成的阶段继续。

### 3. 增量执行

只执行有变更的部分（基于 git diff 或时间戳）：

```bash
/full-pipeline incremental
```

或者只执行最近 3 天变更的部分：

```bash
/full-pipeline incremental since:3days
```

### 4. 跳过某层

如果某些层暂时不需要，可以跳过：

```bash
/full-pipeline full skip:deadhunt
```

## 输出文件

所有输出位于 `.allforai/full-pipeline/` 目录：

```
.allforai/full-pipeline/
├── pipeline-report.json      # 全量报告（机器可读）
├── pipeline-report.md        # 人类可读摘要
└── global-decisions.json     # 全局决策追踪
```

## 查看结果

### 查看执行摘要

```bash
cat .allforai/full-pipeline/pipeline-report.md
```

### 查看全局决策

```bash
cat .allforai/full-pipeline/global-decisions.json
```

### 查看某个任务的状态

```bash
cat .allforai/full-pipeline/global-decisions.json | jq '.decisions.T008'
```

### 查看跨层冲突

```bash
cat .allforai/full-pipeline/pipeline-report.json | jq '.cross_layer_conflicts'
```

## 质量门禁

每层都有质量门禁标准：

| 层 | 质量门禁 | 标准 |
|----|----------|------|
| product-design | design-audit | ORPHAN=0, 覆盖率≥80%, CONFLICT=0 |
| dev-forge | 实现率 | CORE 任务实现率 ≥ 90% |
| deadhunt | 死链 | P0 级死链 = 0 |
| code-tuner | 架构评分 | 评分 ≥ 70 |

如果某层质量门禁失败，流程会暂停并向用户报告问题。

## 跨层反馈

Full Pipeline 会自动检测跨层冲突并提供解决建议：

- **gap × prune**: feature-gap 报缺口，但 feature-prune 标 CUT
- **verify × prune**: CORE 任务未实现
- **deadhunt × screen**: screen-map 中的界面链接死链
- **tuner × product**: 架构违规影响产品功能

所有冲突都会记录在 `pipeline-report.json` 的 `cross_layer_conflicts` 字段中。

## 使用场景

### 新项目启动

```bash
/full-pipeline full
```

完整执行所有层，建立完整的开发和测试基础。

### 日常开发

```bash
/full-pipeline incremental
```

代码变更后，只重跑受影响的层，节省时间。

### 发布前检查

```bash
/full-pipeline full
```

确保所有质量门禁都通过，无严重问题。

### 故障排查

```bash
# 查看跨层冲突
cat .allforai/full-pipeline/pipeline-report.json | jq '.cross_layer_conflicts'

# 查看需要关注的任务
cat .allforai/full-pipeline/pipeline-report.md | grep "需要关注的任务"
```

## 常见问题

### Q: Full Pipeline 需要多长时间？

A: 取决于项目规模：
- 小型项目（<50 任务）：约 5-10 分钟
- 中型项目（50-200 任务）：约 15-30 分钟
- 大型项目（>200 任务）：约 30-60 分钟

### Q: 可以只执行某层吗？

A: 可以，使用 skip 参数：
```bash
/full-pipeline full skip:deadhunt,code-tuner
```

### Q: 增量执行如何判断需要重跑哪些层？

A: 基于 git diff 或时间戳：
- 代码变更 → Layer 2, Layer 3, Layer 4
- 产品定义变更 → Layer 1
- UI 变更 → Layer 1, Layer 3
- 架构变更 → Layer 4

### Q: 质量门禁失败怎么办？

A: 流程会暂停并报告问题，你可以：
1. 修复问题后继续
2. 带问题继续（会记录风险）
3. 中止流程

### Q: 如何查看历史执行记录？

A: 查看 `global-decisions.json` 中的 `pipeline_run` 字段，包含了每次执行的元数据。

## 进阶用法

### 只执行指定层

```bash
/full-pipeline incremental layer:2,3
```

只执行开发层和 QA 层。

### 自定义质量门禁标准

编辑 `pipeline-report.json`，调整各层质量门禁的标准值。

### 集成到 CI/CD

```bash
#!/bin/bash

# CI 脚本示例
/full-pipeline full

# 检查总体健康评分
health_score=$(cat .allforai/full-pipeline/pipeline-report.json | jq '.summary.overall_health_score')

if [ $health_score -lt 80 ]; then
  echo "健康评分低于 80，发布中止"
  exit 1
fi
```

## 相关文档

- [完整分析报告](pipeline-analysis.md) - 详细的分析和改进说明
- [产品设计指导思想与设计原则](product-design-principles.md) - 各阶段方法论、设计思想与原则总览
- [命令文档](../commands/full-pipeline.md) - 命令的完整规格说明
- [产品设计套件 README](../README.md) - 产品设计层的详细说明

## 贡献

欢迎提出问题和改进建议！

---

**版本**: v1.0.0
**更新时间**: 2026-02-27