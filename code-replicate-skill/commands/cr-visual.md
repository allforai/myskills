---
description: "视觉还原度：截图对比源 App vs 目标 App 的 UI 还原程度。需要两个 App 都能运行，或提供源 App 截图"
argument-hint: "[--source <url-or-path>] [--target <url-or-path>] [--screenshots <path>]"
allowed-tools: ["Read", "Write", "Grep", "Glob", "Bash", "AskUserQuestion", "Agent", "mcp__plugin_playwright_playwright__browser_navigate", "mcp__plugin_playwright_playwright__browser_take_screenshot", "mcp__plugin_playwright_playwright__browser_snapshot"]
---

# CR Visual — 视觉还原度对比

用户请求: $ARGUMENTS

## 插件根目录

所有文档路径基于插件安装目录: `${CLAUDE_PLUGIN_ROOT}`

## 参数解析

| 参数 | 格式 | 说明 |
|------|------|------|
| `--source` | URL 或路径 | 源 App 地址（如 http://localhost:3000）或启动命令 |
| `--target` | URL 或路径 | 目标 App 地址（如 http://localhost:5000）或启动命令 |
| `--screenshots` | 目录路径 | 源 App 截图目录（源 App 无法运行时替代 --source） |

## 参数缺失引导

当参数为空时，用 AskUserQuestion 引导：
1. **源 App 截图来源**：选项：源 App 可运行（输入 URL）/ 有截图目录 / 都没有（退出）
2. **目标 App 地址**：输入目标 App 的 URL 或启动方式

## 前置条件

- `.allforai/experience-map/experience-map.json` 必须存在（提供 screen 列表）
- 源 App 或源截图至少有一个可用
- 目标 App 可访问

## 执行

> 详见 ${CLAUDE_PLUGIN_ROOT}/skills/cr-visual.md

## 快速参考

```
/cr-visual                                            # 交互式引导
/cr-visual --source http://localhost:3000 --target http://localhost:5000
/cr-visual --screenshots ./source-screenshots --target http://localhost:5000
```
