# 美术概念 Skill Invocation Capability

> 节点：`art-concept`。
> 用途：把游戏设计中的美术方向转成可冻结、可生成、可验收的美术生产输入。

## 目标

该 capability 是 `art-concept` 节点的能力占位与上下文入口。实际执行由内置 skill 完成：

```text
${CLAUDE_PLUGIN_ROOT}/skills/art-concept.md
${CLAUDE_PLUGIN_ROOT}/skills/game-art/10-design/art-concept-validation/SKILL.md
```

它存在的原因是 workflow 的 `capability` 字段必须能解析到 `knowledge/capabilities/<capability>.md`，避免节点在 Context Pull 阶段成为游离能力。

## 必需输出

| 输出 | 说明 |
|---|---|
| `.allforai/game-design/art-pipeline-config.json` | 美术生产配置，包含维度、风格、动画系统、工具链、active_nodes |
| `.allforai/game-design/art/art-concept-validation.html` | 中文人类阅读的美术概念 HTML gate |
| `.allforai/game-design/art/art-concept-validation.json` | 美术概念验证状态，`state` 必须可被后续 concept-freeze 读取 |

## 验收规则

- `art-pipeline-config.json.status` 必须为 `final`。
- `art-concept-validation.json.state` 必须为 `passed` 或 `passed_with_warnings`。
- 如果美术方向、产品概念、玩法可读性、目标受众、人类偏好、运行时约束之间存在冲突，必须阻断后续 `concept-freeze` 和 art-gen。

## 下游消费者

| Artifact | 字段 | Consumer Capability | Required | 原因 |
|---|---|---|---|---|
| `.allforai/game-design/art-pipeline-config.json` | `active_nodes` | game-design | required | bootstrap 需要据此注入 art-gen 节点 |
| `.allforai/game-design/art/art-concept-validation.json` | `state` | concept-contract | required | concept-freeze 必须确认美术概念 gate 通过 |
| `.allforai/game-design/art/art-concept-validation.html` | 人类阅读输出 | game-design | optional | 审批看板只读展示 |

