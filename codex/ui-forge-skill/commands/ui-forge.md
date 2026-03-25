---
name: ui-forge
description: >
  Refine an already-implemented frontend UI. Use for post-implementation polish
  or design restoration, with fidelity restoration checked before polish. Not
  for initial feature implementation.
---

# UI Forge Command

## 命令定位

这是一个 UI 后处理工作流。

- 适合：功能已经完成，要提升界面质量或修复设计偏差
- 不适合：页面还没实现、业务逻辑未完成、接口未联通

## 执行规则

1. 先读取 `skills/ui-forge.md`
2. 识别目标界面或组件（从用户请求的自然语言中推断）
3. 先做 `fidelity-check`
4. 判断模式：`restore` 或 `polish`
5. 只在必要范围内读代码与 `.allforai` 产物
6. 在不改变业务语义的前提下完成 UI 优化

## 目标推断

当用户未明确指定目标页面或组件时，假设目标为当前工作目录下最近修改的前端界面文件。如果无法合理推断，则询问用户。

## 模式判定

- 存在可信设计基线且当前实现偏差明显 → `restore`
- 已基本对齐设计，或根本没有上游 UI 基线，但观感粗糙 → `polish`

## 判定优先级

- 先判断有没有设计基线
- 有基线时先判断漂移程度
- 漂移明显时先修还原度，再考虑增强
- 只有在偏差已可接受时才进入 `polish`

## 明确禁止

- 不把本命令当作首次页面生成功能
- 不替代 `dev-forge` 写业务功能
- 不因为追求视觉效果而擅自改业务流程
