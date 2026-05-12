---
name: game-audio-30-generate-sfx-procedural-generation
description: 使用 sox、ffmpeg 或 Python 音频库程序化生成 UI/反馈类短 SFX，并输出 manifest 与 QA 记录。
---

# SFX Procedural Generation Skill

> game-audio 内置子 skill。用于稳定生成 UI 点击、确认、失败、奖励、拾取等短音效。

## 概述

本 skill 不依赖音乐生成模型。它根据 `sfx-source-strategy-spec.json` 中 `procedural_synthesis` 的条目，用可脚本化音频工具生成短 SFX。

## 输入契约

必需：

- `.allforai/game-design/audio/sfx/sfx-source-strategy-spec.json`
- `.allforai/game-design/audio/sfx-spec.json`
- `.allforai/game-design/audio/audio-style-design.json`

可选：

- 工具能力检测结果；
- 目标平台格式；
- UI registry、VFX event、animation event。

## 输出契约

写入：

- `.allforai/game-design/audio/sfx/procedural-sfx-manifest.json`
- `.allforai/game-design/audio/sfx/procedural-sfx-generation-report.json`
- `.allforai/game-design/audio/sfx/generated/<audio_id>/*`

manifest 条目必须包含：

- `audio_id`
- `event_ref`
- `recipe`
- `toolchain`
- `source_file`
- `processed_file`
- `duration_ms`
- `format`
- `sample_rate`
- `loudness_target`
- `variants`
- `qa_status`
- `state`

允许状态：

- `generated`
- `processed`
- `qa_ready`
- `needs_revision`
- `blocked_by_missing_tool`
- `failed_generation`

## 调用契约

```json
{
  "skill": "game-audio/sfx-procedural-generation",
  "mode": "generate_validate",
  "input_paths": {
    "source_strategy": ".allforai/game-design/audio/sfx/sfx-source-strategy-spec.json",
    "sfx_spec": ".allforai/game-design/audio/sfx-spec.json",
    "audio_style": ".allforai/game-design/audio/audio-style-design.json"
  },
  "output_root": ".allforai/game-design/audio/sfx"
}
```

支持模式：`generate_validate`、`generate_variants`、`validate_existing`、`repair_existing`。

## 自动验证

检查：

- 只处理 `source_strategy == "procedural_synthesis"` 的条目；
- 每个音效 recipe 明确波形/噪声、频率、包络、滤波、pitch、混响、长度；
- 输出长度符合 SFX spec，不拖尾、不削波、不全静音；
- UI 音效之间有一致音色，但确认/失败/奖励具备可辨识差异；
- 变体不会破坏事件语义；
- 工具不存在时返回 `blocked_by_missing_tool`，不得生成空文件或占位文件。

## 完成条件

当所有程序化 SFX 都生成音频文件并进入 loudness QA 时，返回 `COMPLETED`。

