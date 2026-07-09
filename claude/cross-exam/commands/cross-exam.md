---
name: cross-exam
description: 对"自称完成"的交付做实证盘问，产出带证据的完成度报告（只记账不修）。
arguments:
  - name: target
    description: 被盘问的交付物/项目（可留空，进入定靶对话）
    required: false
---

Invoke the cross-exam skill to cross-examine the delivery: $ARGUMENTS

> Read ${CLAUDE_PLUGIN_ROOT}/skills/cross-exam.md and follow its protocol, starting at 定靶 (intake).
