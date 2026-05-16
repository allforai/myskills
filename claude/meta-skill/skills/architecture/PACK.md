---
name: architecture
description: meta-skill 内置的技术架构能力包，用于技术架构验证 gate 与面向程序实现的交付契约。
---

# 技术架构 Skill 包

> meta-skill 内置子能力包。
> 状态：随 meta-skill 安装，但默认不作为顶层 skill 单独调用；只有生成的
> node-spec 明确读取某个子 skill 路径时才会执行。

## 目标

技术架构能力包负责把产品、App 设计、游戏设计的交付契约转换成可进入程序实现的技术决策。它不替代代码实现 skill，而是在代码节点开始前验证：

- 技术栈是否明确；
- 项目形态是否覆盖所有端与运行时；
- 模块边界是否清楚；
- 数据、API、状态归属是否一致；
- 安全与权限边界是否可执行；
- 构建、测试、运行、导入验证路径是否真实存在。

## 当前子能力

| 层级 | 子 skill | 职责 |
|---|---|---|
| `10-design` | `architecture-concept-validation` | 在程序实现前生成中文 HTML/JSON gate，验证技术框架与技术架构决策是否闭合。 |

## 标准调用路径

node-spec 调用子 skill 时使用以下路径：

```text
${CLAUDE_PLUGIN_ROOT}/skills/architecture/10-design/architecture-concept-validation/SKILL.md
```

## 契约规则

- 技术架构 gate 必须读取上游产品、App、游戏设计交付物，不能依赖对话记忆。
- 每个下游实现节点都必须映射到明确的模块、运行时表面、数据/API/状态边界与验证路径。
- 如果当前环境无法构建、运行、导入或验证所选技术栈，必须报告具体 blocked 状态；不得用静态检查替代运行时验收。
- 技术架构输出是面向程序实现的契约。它可以展示在审批看板里，但除非 workflow 节点显式设置 `human_gate: true`，否则不写入人工审批记录。

