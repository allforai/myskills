---
name: game-audio-40-qa-runtime-audio-import
description: 验证 SFX 与 BGM 文件、manifest、mixer、事件绑定和目标引擎/前端运行时导入是否真实可用。
---

# Runtime Audio Import Skill

> game-audio 内置子 skill。用于把音频生产结果交付给程序运行时并做导入验收。

## 概述

本 skill 是音频管线的程序交付 gate。它不接受“文件存在”作为充分条件，必须验证 manifest、事件绑定、格式、路径、mixer 分组、loop/SFX 播放和目标运行时导入。

如果目标引擎或运行时无法启动，必须返回 blocked，不得用静态检查替代导入验收。

## 输入契约

必需：

- `.allforai/game-design/audio/sfx/sfx-manifest.json` 或 SFX 分支 manifest；
- `.allforai/game-design/audio/music/bgm-loop-manifest.json`；
- `.allforai/game-design/audio/audio-loudness-qa-report.json`；
- `.allforai/game-design/audio/music/audio-loop-qa-report.json`（存在 BGM 时）；
- `.allforai/game-design/design/program-development-node-handoff.json`。

可选：

- 目标引擎导入配置；
- game-frontend asset binding；
- mixer 配置；
- 自动化运行命令。

## 输出契约

写入：

- `.allforai/game-runtime/audio/engine-ready-audio-manifest.json`
- `.allforai/game-design/audio/runtime-audio-import-report.json`

manifest 必须包含：

- `audio_id`
- `runtime_id`
- `kind`
- `event_or_cue_ref`
- `file_path`
- `format`
- `mixer_group`
- `loop`
- `volume_policy`
- `ducking_policy`
- `fallback`
- `import_status`
- `runtime_validation`

允许状态：

- `imported`
- `engine_ready`
- `needs_revision`
- `blocked_by_missing_runtime`
- `blocked_by_failed_loudness_qa`
- `blocked_by_failed_loop_qa`
- `failed_import`

## 调用契约

```json
{
  "skill": "game-audio/runtime-audio-import",
  "mode": "import_validate",
  "input_paths": {
    "sfx_manifest": ".allforai/game-design/audio/sfx/sfx-manifest.json",
    "bgm_loop_manifest": ".allforai/game-design/audio/music/bgm-loop-manifest.json",
    "loudness_qa": ".allforai/game-design/audio/audio-loudness-qa-report.json",
    "loop_qa": ".allforai/game-design/audio/music/audio-loop-qa-report.json",
    "program_handoff": ".allforai/game-design/design/program-development-node-handoff.json"
  },
  "output_root": ".allforai/game-runtime/audio"
}
```

支持模式：`import_validate`、`validate_existing`、`repair_existing`。

## 自动验证

检查：

- 所有音频文件路径存在且目标运行时可访问；
- 格式、采样率、声道、压缩设置符合目标平台；
- SFX 绑定到正确事件，BGM 绑定到正确场景/状态；
- mixer 分组和音量策略明确；
- BGM loop policy 能被运行时表达；
- loudness QA / loop QA 未通过时不得导入为 engine_ready；
- 运行时可启动时必须真实播放或加载验证；
- 运行时不可启动时返回 blocked，不得静态替代。

## 完成条件

当所有必需音频都导入并通过运行时验证时，返回 `COMPLETED`。

如果运行时不可用或 QA 未通过，返回 blocked / failed 状态。

