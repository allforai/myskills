---
description: "前端复刻：逆向工程前端/移动端代码库 → 生成 allforai 产物。分析组件树、路由、状态管理、API 调用层。"
argument-hint: "[mode] <path-or-url> [--scope full|modules|feature]"
allowed-tools: ["Read", "Write", "Grep", "Glob", "Bash", "AskUserQuestion", "Agent", "WebSearch"]
---

# CR Frontend — 前端复刻

用户请求: $ARGUMENTS

## 插件根目录

所有文档路径基于插件安装目录: `${CLAUDE_PLUGIN_ROOT}`

## 执行方式

固定 `project_type = frontend`，从 `$ARGUMENTS` 解析 `mode` 和 `path`（或 git URL）参数（如已提供），然后加载并执行：

`${CLAUDE_PLUGIN_ROOT}/skills/cr-frontend.md`

### 参数缺失引导

当 `$ARGUMENTS` 为空或缺少必要参数时，用 AskUserQuestion 逐步引导：

1. **源码地址**（若缺失）：「要复刻的前端源码在哪里？」选项：当前目录 `.` / 输入本地路径 / 输入 Git URL
2. **信度等级**（若缺失）：「需要什么级别的复刻？」选项：interface（仅组件 Props 合约）/ functional（业务行为，推荐）/ architecture（含架构分析）/ exact（百分百复刻含 bug）

收集完毕后，按正常流程继续。

Preflight 时：
- 项目类型已锁定为 `frontend`，不询问
- 仅询问缺失的参数（目标技术栈）

## 快速参考

```
/cr-frontend ./src                                   # 交互式选择信度等级
/cr-frontend functional ./src                        # 复刻业务行为（推荐）
/cr-frontend functional ./src --scope "用户个人中心"   # 只复刻某个功能的前端
/cr-frontend functional ./src --scope "src/pages/dashboard" # 只复刻仪表盘页面
/cr-frontend exact ./src                             # 百分百复刻（含 bug）
/cr-frontend functional https://github.com/org/repo.git   # 远程仓库
/cr-frontend functional https://github.com/org/repo#v2.0 # 指定 tag
/cr-frontend functional git@github.com:org/repo.git      # SSH 地址
```

## 适用场景

- React → Vue / Vue → React 等框架迁移
- Flutter → React Native 或反向迁移
- 前端代码现代化（jQuery → React 等）
- 移动端跨平台迁移

## 后续步骤

复刻分析完成后，继续 dev-forge 流水线：

```
/design-to-spec   ← 生成目标技术栈实现规格
/task-execute     ← 逐任务生成代码
```
