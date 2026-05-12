---
name: game-audio
description: meta-skill 内置的游戏音频能力包，用于 SFX、BGM loop、音频 QA 和运行时导入。
---

# Game Audio Skill Pack

> meta-skill 内置子 skill 包。状态：随 meta-skill 安装，只有 node-spec 明确调用子 skill 路径时才执行。

## Purpose

Game Audio 负责游戏音效与 BGM loop 的规划、生成/获取、后处理、QA 和运行时导入契约。它读取游戏事件、UI 事件、叙事语气、美术风格、VFX/动画事件和程序运行时约束。

本包不以“生成完整歌曲”为目标。推荐生产路线：

```text
音频风格
-> SFX/BGM 规格
-> SFX 来源策略 / BGM loop 规格
-> Google Lyria 生成 BGM loop
-> 程序化 SFX 或素材库改造
-> loudness / loop QA
-> runtime audio import
```

Google Lyria 用于 BGM / loop；SFX 优先走程序化合成、素材库搜索/改造和工具后处理。

## Current Children

| Layer | Child skill | Responsibility |
|---|---|---|
| `00-env` | `audio-registry` | Audio IDs, paths, states, owners, consumers. |
| `10-design` | `audio-style-design` | Sonic palette, mood, instrumentation, mix direction. |
| `20-spec` | `sfx-spec` | Event SFX semantics, timing, layers, variants, loudness target. |
| `20-spec` | `music-cue-spec` | Music cues, loops, transitions, stems, states. |
| `20-spec` | `sfx-source-strategy-spec` | Decide procedural synthesis, asset library adaptation, user asset reuse, hybrid layering, or manual-required route per SFX. |
| `20-spec` | `bgm-loop-spec` | Scene/state BGM loop duration, emotion, BPM, instrumentation, loop point, transition, runtime contract. |
| `30-generate` | `sfx-generation` | Legacy/general SFX manifest orchestration; prefer the finer source-strategy branches below for new workflows. |
| `30-generate` | `sfx-procedural-generation` | Generate short UI/feedback SFX via sox/ffmpeg/Python synthesis recipes. |
| `30-generate` | `sfx-source-adaptation` | Search/register/adapt existing SFX assets with license, trimming, conversion, variants, provenance. |
| `30-generate` | `music-prompt-generation` | Legacy/general music prompt/stem specs and generation manifest. |
| `30-generate` | `bgm-loop-generation-google-lyria` | Generate short BGM loop candidates through Google Lyria and preserve provider metadata. |
| `40-qa` | `audio-loudness-qa` | Loudness, clipping, duration, loop, and mix validation. |
| `40-qa` | `audio-loop-qa` | Dedicated BGM loop seam, fade, transition, and long-loop acceptability validation. |
| `40-qa` | `runtime-audio-import` | Program-facing engine/runtime audio manifest and import/playback validation. |

## Canonical Invocation Paths

```text
${CLAUDE_PLUGIN_ROOT}/skills/game-audio/00-env/audio-registry/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-audio/10-design/audio-style-design/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-audio/20-spec/sfx-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-audio/20-spec/music-cue-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-audio/20-spec/sfx-source-strategy-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-audio/20-spec/bgm-loop-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-audio/30-generate/sfx-generation/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-audio/30-generate/sfx-procedural-generation/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-audio/30-generate/sfx-source-adaptation/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-audio/30-generate/music-prompt-generation/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-audio/30-generate/bgm-loop-generation-google-lyria/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-audio/40-qa/audio-loudness-qa/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-audio/40-qa/audio-loop-qa/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-audio/40-qa/runtime-audio-import/SKILL.md
```

## Layering Rules

Dependencies flow from earlier numbered layers to later numbered layers only.

## Recommended Chains

### SFX

```text
00-env/audio-registry
-> 10-design/audio-style-design
-> 20-spec/sfx-spec
-> 20-spec/sfx-source-strategy-spec
-> 30-generate/sfx-procedural-generation       (UI/feedback/simple events)
-> 30-generate/sfx-source-adaptation           (complex Foley/combat/environment)
-> 40-qa/audio-loudness-qa
-> 40-qa/runtime-audio-import
```

### BGM loop

```text
00-env/audio-registry
-> 10-design/audio-style-design
-> 20-spec/music-cue-spec
-> 20-spec/bgm-loop-spec
-> 30-generate/bgm-loop-generation-google-lyria
-> 40-qa/audio-loop-qa
-> 40-qa/audio-loudness-qa
-> 40-qa/runtime-audio-import
```

## Hard Rules

- BGM loop 使用 Google Lyria；如果 Google Lyria 不可用，返回 blocked，不用 OpenRouter 替代音频生成。
- SFX 不默认使用音乐生成模型。简单 SFX 走程序化合成，复杂 SFX 走素材库/已有素材改造。
- 任何音频文件进入运行时前，必须通过 loudness QA；BGM 还必须通过 loop QA。
- 运行时不可启动时必须返回 blocked，不得用静态检查替代导入和播放验收。
