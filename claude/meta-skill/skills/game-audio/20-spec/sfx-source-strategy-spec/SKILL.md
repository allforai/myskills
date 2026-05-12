---
name: game-audio-20-spec-sfx-source-strategy-spec
description: 为每个游戏 SFX 决定程序化合成、素材库搜索/改造、用户素材复用或人工缺口的来源策略。
---

# SFX Source Strategy Spec Skill

> game-audio 内置子 skill。用于在生成/获取 SFX 前，决定每个音效的来源路线。

## 概述

SFX 不默认走 AI 音乐生成。简单 UI 与反馈音效优先程序化合成；复杂 Foley、攻击、爆炸、脚步、环境声优先素材库搜索/改造；已有用户素材优先复用并规范化。

## 输入契约

必需：

- `.allforai/game-design/audio/sfx-spec.json`
- `.allforai/game-design/audio/audio-style-design.json`
- `.allforai/game-design/audio/audio-registry.json`

可选：

- 已有素材目录清单；
- 授权/来源要求；
- 目标平台格式限制；
- game-ui、vfx、combat、animation event 列表。

## 输出契约

写入：

- `.allforai/game-design/audio/sfx/sfx-source-strategy-spec.json`
- `.allforai/game-design/audio/sfx/sfx-source-strategy-report.json`

每个条目必须包含：

- `audio_id`
- `event_ref`
- `source_strategy`
- `strategy_reason`
- `tool_requirements`
- `license_requirements`
- `adaptation_required`
- `qa_requirements`
- `fallback_strategy`
- `blocked_reason`
- `state`

允许的 `source_strategy`：

- `procedural_synthesis`
- `asset_library_search`
- `existing_user_asset`
- `hybrid_layering`
- `manual_required`

允许状态：

- `ready`
- `needs_revision`
- `blocked_by_license`
- `blocked_by_missing_sfx_spec`
- `blocked_by_missing_tool`

## 调用契约

```json
{
  "skill": "game-audio/sfx-source-strategy-spec",
  "mode": "spec_validate",
  "input_paths": {
    "sfx_spec": ".allforai/game-design/audio/sfx-spec.json",
    "audio_style": ".allforai/game-design/audio/audio-style-design.json",
    "audio_registry": ".allforai/game-design/audio/audio-registry.json"
  },
  "output_root": ".allforai/game-design/audio/sfx"
}
```

支持模式：`spec_validate`、`validate_existing`、`repair_existing`。

## 自动验证

检查：

- UI 点击、确认、失败、奖励等短反馈优先 `procedural_synthesis`；
- 复杂材质、脚步、武器、爆炸、环境声优先 `asset_library_search` 或 `hybrid_layering`；
- 每个素材库来源必须声明商业可用、可修改、署名要求和来源记录；
- 每个程序化合成项必须声明基础波形/噪声、包络、滤波、pitch、混响、长度；
- 无法自动生成/获取的音效必须显式标记 `manual_required`，不得伪造通过。

## 完成条件

当每个 SFX 都具备明确来源策略、工具要求和 QA 路线时，返回 `COMPLETED`。

