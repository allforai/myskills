# v2.5-cleanup Requirements

## Goal

清理 product-audit-skill 中的遗留内容（过时文档、过时示例、版本不一致），使仓库状态与实际 v2.4.0 架构完全一致。

## Background

product-audit-skill 经历了一次大重构（feature-audit → product-map 体系），但重构后遗留了大量旧架构的文档和示例文件，版本号也存在多处不一致。

## Requirements

### REQ-1: marketplace.json 版本同步

**现状**：marketplace.json 版本为 `2.3.0`，plugin.json 为 `2.4.0`。
**要求**：marketplace.json 版本更新至 `2.5.0`（本次清理完成后的新版本）。

### REQ-2: 删除遗留文档

**现状**：`docs/` 下有 19 个遗留 Markdown 文件（共 9,554 行），使用旧术语（feature-audit, demo-forge），与当前 `skills/*.md` 内容重复且过时。

**要求**：
- 删除 `docs/overview.md`, `docs/report.md`, `docs/sources.md`, `docs/inventory.md`, `docs/gap.md`, `docs/closedloop.md`, `docs/closedloop-appendix.md`（7 个文件）
- 删除 `docs/feature-prune/` 整个目录（6 个文件）
- 删除 `docs/demo-forge/` 整个目录（6 个文件）
- 保留 `docs/plans/`（当前活跃的设计文档）

### REQ-3: 清理过时示例

**现状**：`examples/` 下 9 个文件中 7 个使用旧架构输出名，与当前技能输出不匹配。

**要求**：删除 `examples/` 整个目录。理由：所有 6 个 skill 文件内已内嵌完整的 JSON Schema 示例，独立 examples 目录已无附加价值。

### REQ-4: 删除已完成的重构 spec

**现状**：`.claude/specs/refactor-commands/` 下 3 个文件（451 行）是旧重构计划，目标已全部达成。

**要求**：删除 `.claude/specs/refactor-commands/` 目录。

### REQ-5: seed-forge 版本升级

**现状**：seed-forge.md 版本为 `2.0.0`，但已新增枚举全覆盖、灌入前自检、混合灌入策略三项功能。

**要求**：seed-forge.md frontmatter version 从 `2.0.0` 升至 `2.1.0`。

### REQ-6: plugin.json 版本升级

**要求**：plugin.json version 从 `2.4.0` 升至 `2.5.0`，反映本次清理。

### REQ-7: README/SKILL.md 版本同步

**要求**：README.md 中的版本号从 `v2.4.0` 更新至 `v2.5.0`。

## Out of Scope

- 不修改任何 skill 或 command 的功能逻辑
- 不新增示例文件（后续按需单独添加）
- 不修改其他插件（deadhunt, code-tuner）
