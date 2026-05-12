---
name: game-audio-20-spec-bgm-loop-spec
description: 定义游戏 BGM loop 的场景、情绪、时长、循环点、层级、转场和运行时消费契约。
---

# BGM Loop Spec Skill

> game-audio 内置子 skill。用于把游戏场景/状态需求转换成可由 Google Lyria 或其他音乐生成器生产的短循环 BGM 规格。

## 概述

本 skill 只定义 BGM / loop，不生成完整歌曲。它面向菜单、关卡、战斗、剧情、结算、商店、探索、失败、胜利等游戏状态，定义短段落、可循环、可转场、可导入引擎的音乐需求。

## 输入契约

必需：

- `.allforai/game-design/game-design-doc.json`
- `.allforai/game-design/audio/audio-style-design.json`
- `.allforai/game-design/audio/audio-registry.json`

可选：

- `.allforai/game-design/audio/music-cue-spec.json`
- `.allforai/game-design/design/level-plan.json`
- `.allforai/game-design/design/program-development-node-handoff.json`
- 美术风格、叙事风格、关卡节奏、战斗节奏、UI 场景列表

## 输出契约

写入：

- `.allforai/game-design/audio/music/bgm-loop-spec.json`
- `.allforai/game-design/audio/music/bgm-loop-spec-report.json`

`bgm-loop-spec.json` 必须包含：

- `cue_id`
- `scene_or_state_ref`
- `emotion_target`
- `intensity_level`
- `bpm_range`
- `duration_seconds`
- `loop_required`
- `loop_point_policy`
- `instrumentation`
- `negative_constraints`
- `transition_rules`
- `runtime_mix_priority`
- `target_format`
- `qa_requirements`
- `consumer_refs`
- `state`

允许状态：

- `ready_for_generation`
- `needs_revision`
- `blocked_by_missing_audio_style`
- `blocked_by_missing_scene_contract`
- `not_applicable`

## 调用契约

```json
{
  "skill": "game-audio/bgm-loop-spec",
  "mode": "spec_validate",
  "input_paths": {
    "game_design_doc": ".allforai/game-design/game-design-doc.json",
    "audio_style": ".allforai/game-design/audio/audio-style-design.json",
    "audio_registry": ".allforai/game-design/audio/audio-registry.json",
    "music_cue_spec": ".allforai/game-design/audio/music-cue-spec.json"
  },
  "output_root": ".allforai/game-design/audio/music"
}
```

支持模式：`spec_validate`、`validate_existing`、`repair_existing`。

## 自动验证

检查：

- 每个需要 BGM 的游戏场景或状态都有 `cue_id`；
- BGM loop 不承担 SFX 职责，不遮挡 UI 和关键 gameplay feedback；
- 每个 cue 的时长、BPM、情绪、乐器、强度与游戏节奏一致；
- loop 必须声明循环策略：无缝 loop、自然尾音 loop、引擎 crossfade loop 或一次性播放；
- 转场规则明确：进入、退出、暂停、战斗升级、胜利/失败、场景切换；
- 运行时消费方明确：场景、状态机、音频 mixer、ducking 规则；
- QA 要求明确：loop seam、响度、静音、削波、格式、体积。

## 完成条件

当所有适用 BGM cue 都具备可生成、可 QA、可导入运行时的规格时，返回 `COMPLETED`。

如果缺少音频风格或场景状态契约，返回 blocked 状态，不得自行编造完整音乐需求。

