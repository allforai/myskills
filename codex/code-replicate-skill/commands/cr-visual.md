---
name: cr-visual
description: "视觉还原度：截图+录像对比 → 修复差异 → 重新对比 → 直到视觉一致。模式: full / analyze / fix"
---

# CR Visual — 视觉还原度对比

## 参数解析

| 参数 | 格式 | 说明 |
|------|------|------|
| `--source` | URL 或路径 | 源 App 地址（如 http://localhost:3000）或启动命令 |
| `--target` | URL 或路径 | 目标 App 地址（如 http://localhost:5000）或启动命令 |
| `--screenshots` | 目录路径 | 源 App 截图目录（源 App 无法运行时替代 --source） |

## 参数缺失处理

When parameters are missing:
1. **源 App 截图来源**：check `.allforai/code-replicate/visual/source/` first (Phase 2 captures); then check `replicate-config.json` for `source_app` field
2. **目标 App 地址**：assume default dev server URL based on target stack; only ask if no reasonable default exists

## 前置条件

- `.allforai/experience-map/experience-map.json` 必须存在（提供 screen 列表）
- 源 App 或源截图至少有一个可用
- 目标 App 可访问

## 执行

> 详见 ./skills/cr-visual.md
