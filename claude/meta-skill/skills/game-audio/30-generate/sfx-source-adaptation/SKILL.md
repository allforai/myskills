---
name: game-audio-30-generate-sfx-source-adaptation
description: 搜索、登记、裁剪、转码和改造现成 SFX 素材，使其符合游戏事件、授权、响度和运行时契约。
---

# SFX Source Adaptation Skill

> game-audio 内置子 skill。用于复杂 SFX 的素材库搜索/改造路线。

## 概述

攻击、命中、爆炸、脚步、材质、环境声等复杂音效通常不适合纯程序化合成。本 skill 根据来源策略登记现成素材，完成裁剪、转码、响度标准化、变体生成和来源记录。

## 输入契约

必需：

- `.allforai/game-design/audio/sfx/sfx-source-strategy-spec.json`
- `.allforai/game-design/audio/sfx-spec.json`

可选：

- 已有素材目录；
- 素材库搜索结果；
- 授权记录；
- 目标平台音频格式；
- VFX / animation event / combat event。

## 输出契约

写入：

- `.allforai/game-design/audio/sfx/sfx-source-adaptation-manifest.json`
- `.allforai/game-design/audio/sfx/sfx-source-adaptation-report.json`
- `.allforai/game-design/audio/sfx/adapted/<audio_id>/*`

manifest 条目必须包含：

- `audio_id`
- `event_ref`
- `source_strategy`
- `source_url_or_path`
- `license`
- `attribution_required`
- `adaptation_steps`
- `processed_file`
- `duration_ms`
- `format`
- `variants`
- `qa_status`
- `state`

允许状态：

- `adapted`
- `registered`
- `qa_ready`
- `needs_revision`
- `blocked_by_license`
- `blocked_by_missing_source`
- `failed_adaptation`

## 调用契约

```json
{
  "skill": "game-audio/sfx-source-adaptation",
  "mode": "adapt_validate",
  "input_paths": {
    "source_strategy": ".allforai/game-design/audio/sfx/sfx-source-strategy-spec.json",
    "sfx_spec": ".allforai/game-design/audio/sfx-spec.json"
  },
  "output_root": ".allforai/game-design/audio/sfx"
}
```

支持模式：`search_adapt_validate`、`adapt_validate`、`register_existing`、`validate_existing`、`repair_existing`。

## 自动验证

检查：

- 只处理 `asset_library_search`、`existing_user_asset`、`hybrid_layering` 的条目；
- 每个外部素材必须有来源、授权、可修改性和署名要求；
- 禁止接收授权不明或不可商用素材；
- 裁剪和转码后不得削波、全静音、拖尾过长；
- 音效语义必须匹配事件，不得用“听起来相似”的无关素材替代；
- 复杂音效可生成多个变体，但变体要保持同一事件语义。

## 完成条件

当所有可自动获取/改造的 SFX 都登记、处理并进入 loudness QA 时，返回 `COMPLETED`。

授权或来源缺失必须 blocked，不得通过。

