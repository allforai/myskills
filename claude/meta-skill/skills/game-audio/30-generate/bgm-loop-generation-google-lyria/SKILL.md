---
name: game-audio-30-generate-bgm-loop-generation-google-lyria
description: 使用 Google Lyria 生成游戏 BGM loop，并输出音频文件、生成记录、loop 元数据和 QA 入口。
---

# BGM Loop Generation Google Lyria Skill

> game-audio 内置子 skill。用于在拥有 Google key 的环境中生成短 BGM / loop。

## 概述

本 skill 只负责 BGM loop，不生成完整歌曲。它读取 `bgm-loop-spec.json`，通过 Google Lyria 生成候选音频，保留 prompt、参数、候选版本、来源记录和后处理需求。

如果当前环境没有 Google Lyria 可用能力，必须返回 blocked 状态，不得把 prompt-only 输出当成已生成音乐。

## 输入契约

必需：

- `.allforai/game-design/audio/music/bgm-loop-spec.json`
- `.allforai/game-design/audio/audio-style-design.json`
- Google Lyria 可用凭据或环境说明

可选：

- `.allforai/game-design/audio/music-cue-spec.json`
- `.allforai/game-design/audio/audio-registry.json`
- 参考音乐说明、负面参考、目标平台格式要求

## 输出契约

写入：

- `.allforai/game-design/audio/music/lyria-generation-plan.json`
- `.allforai/game-design/audio/music/bgm-loop-manifest.json`
- `.allforai/game-design/audio/music/bgm-loop-generation-report.json`
- `.allforai/game-design/audio/music/generated/<cue_id>/*`

manifest 条目必须包含：

- `cue_id`
- `provider`
- `provider_model`
- `prompt`
- `negative_prompt`
- `generation_params`
- `candidate_id`
- `source_file`
- `processed_file`
- `duration_seconds`
- `loop_metadata`
- `format`
- `license_or_provider_terms_ref`
- `qa_status`
- `state`

允许状态：

- `generated`
- `processed`
- `qa_ready`
- `needs_revision`
- `blocked_by_missing_google_key`
- `blocked_by_provider_unavailable`
- `failed_generation`

## 调用契约

```json
{
  "skill": "game-audio/bgm-loop-generation-google-lyria",
  "mode": "generate_validate",
  "input_paths": {
    "bgm_loop_spec": ".allforai/game-design/audio/music/bgm-loop-spec.json",
    "audio_style": ".allforai/game-design/audio/audio-style-design.json",
    "audio_registry": ".allforai/game-design/audio/audio-registry.json"
  },
  "output_root": ".allforai/game-design/audio/music"
}
```

支持模式：`generate_validate`、`generate_candidates`、`validate_existing`、`repair_existing`。

## 自动验证

检查：

- 每个生成请求都来自 `bgm-loop-spec.json`，不得自由发挥完整歌曲；
- prompt 必须包含场景、情绪、强度、BPM、时长、loop 需求、乐器、负面约束；
- 候选音频必须保留 provider、model、参数、生成时间和文件路径；
- 每个 cue 至少保留一个候选进入 `audio-loop-qa`；
- 后处理需求明确：裁剪、fade、响度标准化、转码、loop seam 修复；
- 生成失败必须分类：凭据缺失、provider 不可用、prompt 不可接受、音频不可解析、输出不符合时长。

## 完成条件

当每个适用 BGM cue 都生成至少一个可进入 loop QA 的候选音频时，返回 `COMPLETED`。

如果 Google Lyria 不可用，返回 blocked 状态；不得用 OpenRouter 或文字 prompt 替代生成结果。

