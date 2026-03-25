---
name: code-replicate
description: "代码复刻：逆向工程已有代码库 → 生成 allforai 产物 → 交还 dev-forge 流水线。模式: interface / functional / architecture / exact"
---

# Code Replicate — 代码复刻

## 参数解析

从用户请求中推断：

| 参数 | 格式 | 说明 |
|------|------|------|
| `mode` | 位置参数 #1 | interface / functional / architecture / exact |
| `path` | 位置参数 #2 | 本地路径或 Git URL |
| `--type` | backend / frontend / fullstack / module | 项目类型（缺省自动检测） |
| `--scope` | full / modules / feature / 自由文本 | 分析范围 |
| `--module` | 路径 | 模块级复刻时指定模块路径 |
| `--from-phase` | 1-4 | 从指定阶段重跑（保留之前产物） |

### Git URL 支持

支持以下格式，可选 `#branch` 后缀指定分支/tag：

- HTTPS: `https://github.com/org/repo.git`
- SSH: `git@github.com:org/repo.git`
- GitHub 短语法: `org/repo`（自动展开为 `https://github.com/org/repo.git`）
- 分支/Tag: `https://github.com/org/repo#v2.0`

检测到 Git URL 时，clone 到临时目录后继续分析。

## 参数缺失处理

当参数缺失时，按以下默认值处理：

1. **源码地址**（若缺失）：假定当前目录 `.`，除非上下文明确无代码
2. **信度等级**（若缺失）：默认 `functional`（最常用场景）
3. **项目类型**（若缺失）：自动检测（扫描代码库判断）

仅在源码地址完全无法推断时才询问用户。

## 项目类型自动检测

当 `--type` 未指定时，扫描代码库判断项目类型：

- **backend**: routes/controllers/middleware/models 目录或文件
- **frontend**: components/pages/store/hooks/screens 目录或文件
- **fullstack**: 前后端代码共存（monorepo 或全栈框架）
- **module**: 需显式 `--type module --module <path>` 指定

## 技能分发

根据项目类型加载对应技能文件，读取后按其完整工作流执行：

1. **`--type backend`**（或自动检测为后端）→ 加载 `./skills/cr-backend.md`
2. **`--type frontend`**（或自动检测为前端）→ 加载 `./skills/cr-frontend.md`
3. **`--type fullstack`**（或自动检测为全栈）→ 加载 `./skills/cr-fullstack.md`
4. **`--type module`** → 加载 `./skills/cr-module.md`（需 `--module` 参数）

所有技能文件内部加载 `./skills/code-replicate-core.md` 作为 4 阶段协议基础。

## 信度等级速查

| 等级 | 适用场景 |
|------|---------|
| `interface` | 后端重写，前端不动；API 兼容迁移 |
| `functional` | 技术栈迁移，保留业务逻辑（**推荐默认**） |
| `architecture` | 大规模重构，保持架构决策 |
| `exact` | 行为零容忍回归；监管合规 |

## 后续步骤

复刻分析完成后，继续 dev-forge 流水线：

```
code-replicate   →  逆向分析，生成 .allforai/ 产物
    ↓
project-setup    →  基于产物初始化目标项目
    ↓
design-to-spec   →  生成目标技术栈实现规格
    ↓
task-execute     →  逐任务生成代码
```
