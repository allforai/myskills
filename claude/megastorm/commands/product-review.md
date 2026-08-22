---
name: product-review
description: 用产品思维审视交付：工作在不在、走不走得完、竞品有没有可借鉴的定位。只出意见，不改代码。
arguments:
  - name: target
    description: 被审视的产品/项目（可留空，进入定靶）
    required: false
---

Invoke the product-review skill: $ARGUMENTS

> Read ${CLAUDE_PLUGIN_ROOT}/skills/product-review.md and follow it from intake.
> Do not load the cross-exam skill.
