---
description: "后端复刻：逆向工程后端/API/微服务代码库 → 生成 allforai 产物。分析 API 合约、Service 逻辑、ORM 映射、中间件链。"
argument-hint: "[mode] <path-or-url> [--scope full|modules|feature]"
allowed-tools: ["Read", "Write", "Grep", "Glob", "Bash", "AskUserQuestion", "Agent", "WebSearch"]
---

# CR Backend — 后端复刻

用户请求: $ARGUMENTS

## 插件根目录

所有文档路径基于插件安装目录: `${CLAUDE_PLUGIN_ROOT}`

## 执行方式

固定 `project_type = backend`，从 `$ARGUMENTS` 解析 `mode` 和 `path`（或 git URL）参数（如已提供），然后加载并执行：

`${CLAUDE_PLUGIN_ROOT}/skills/cr-backend.md`

### 参数缺失引导

当 `$ARGUMENTS` 为空或缺少必要参数时，用 AskUserQuestion 逐步引导：

1. **源码地址**（若缺失）：「要复刻的后端源码在哪里？」选项：当前目录 `.` / 输入本地路径 / 输入 Git URL
2. **信度等级**（若缺失）：「需要什么级别的复刻？」选项：interface（仅 API 合约）/ functional（业务逻辑，推荐）/ architecture（含架构分析）/ exact（百分百复刻含 bug）

收集完毕后，按正常流程继续。

Preflight 时：
- 项目类型已锁定为 `backend`，不询问
- 仅询问缺失的参数（目标技术栈）

## 快速参考

```
/cr-backend ./src                                    # 交互式选择信度等级
/cr-backend functional ./src                         # 复刻业务行为（推荐）
/cr-backend functional ./src --scope "支付流程"       # 只复刻支付相关功能
/cr-backend functional ./src --scope "src/order"     # 只复刻订单模块
/cr-backend exact ./src                              # 百分百复刻（含 bug）
/cr-backend functional https://github.com/org/repo.git   # 远程仓库
/cr-backend functional https://github.com/org/repo#main  # 指定分支
/cr-backend functional git@github.com:org/repo.git       # SSH 地址
```

## 适用场景

- 后端 API 服务迁移到新技术栈
- 微服务架构的逆向分析
- 后端重写，保持 API 兼容
- 从单体提取微服务

## 后续步骤

复刻分析完成后，继续 dev-forge 流水线：

```
/design-to-spec   ← 生成目标技术栈实现规格
/task-execute     ← 逐任务生成代码
```
