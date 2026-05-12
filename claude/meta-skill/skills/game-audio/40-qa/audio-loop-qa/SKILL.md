---
name: game-audio-40-qa-audio-loop-qa
description: 验证 BGM loop 的循环点、接缝、时长、淡入淡出、转场和长时间播放可接受性。
---

# Audio Loop QA Skill

> game-audio 内置子 skill。用于 BGM loop 专项验收。

## 概述

本 skill 验证 BGM 是否真的适合游戏循环播放。响度通过不代表 loop 通过；必须单独检查循环接缝、尾音、节拍、淡入淡出和 runtime transition。

## 输入契约

必需：

- `.allforai/game-design/audio/music/bgm-loop-manifest.json`
- `.allforai/game-design/audio/music/bgm-loop-spec.json`

可选：

- 生成原始文件；
- 后处理文件；
- runtime audio mixer 规则；
- 场景/状态机转场规则。

## 输出契约

写入：

- `.allforai/game-design/audio/music/audio-loop-qa-report.json`
- `.allforai/game-design/audio/music/loop-repair-plan.json`（有问题时）

问题条目必须包含：

- `cue_id`
- `severity`
- `metric`
- `expected`
- `actual`
- `loop_seam_ms`
- `root_cause`
- `repair_target`
- `blocks_runtime`

允许状态：

- `passed`
- `passed_with_warnings`
- `failed_validation`
- `blocked_by_missing_audio`
- `blocked_by_unreadable_audio`

## 调用契约

```json
{
  "skill": "game-audio/audio-loop-qa",
  "mode": "validate",
  "input_paths": {
    "bgm_loop_manifest": ".allforai/game-design/audio/music/bgm-loop-manifest.json",
    "bgm_loop_spec": ".allforai/game-design/audio/music/bgm-loop-spec.json"
  },
  "output_root": ".allforai/game-design/audio/music"
}
```

支持模式：`validate`、`validate_existing`、`repair_plan`。

## 自动验证

检查：

- 音频文件存在且可解码；
- 时长符合 spec；
- loop 接缝没有明显点击、突兀断裂、节拍错位或尾音截断；
- fade-in/fade-out 与 loop policy 一致；
- 长时间循环播放不会出现明显疲劳点或过度旋律抢占；
- 转场点能被运行时消费；
- 失败时明确 repair_target：重新生成、裁剪、fade、crossfade、BPM/loop spec 修订。

## 完成条件

当所有必需 loop 没有 blocker/major 问题时，返回 `COMPLETED`。

存在重大 loop 接缝或不可解码问题时，返回 `FAILED_VALIDATION`。

