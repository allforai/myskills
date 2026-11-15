---
status: accepted
---

# Images come from Codex, video from Grok

The game-art pipeline used to treat image generation as a routing problem: a capability registry probed Google, fal.ai, OpenRouter and MCP providers and tagged each model with 22 capability labels, then a prompt compiler and a batch planner prepared the work. A long-task `mcp-image-batch` server ran it through file handoff, and LoRA training covered identity lock. That was about 1,150 lines across six skills on top of a 646-line contract, plus a validator that pinned their phrases. The ai-gateway also carried FLUX, Imagen, GPT Image, Veo and Kling tools.

Image models have since improved enough that this machinery costs more than it protects. Codex generates and edits images itself, including true alpha and reference-based variation; the Grok CLI (Grok Build, `grok`) generates video from a still or from references under a SuperGrok login. Both were run headless on 2026-11-12: Codex produced a 1254×1254 RGBA icon with real transparency, and Grok turned an image into a 6 s 544×544 clip.

## Decision

**A. One generator per medium.** Images (new, edited, or varied from reference images) come from Codex: natively on Codex, through `codex exec` (`codex-cli-task`) on Claude Code and Pi. Video comes from the Grok CLI limited to `image_to_video` or `reference_to_video`. There is no provider fallback: a missing generator is `blocked_by_missing_image_cli` or `blocked_by_missing_video_cli`, and the unattended readiness gate blocks on `image_generation_cli` / `video_generation_cli` before `/run` starts.

**B. The contract keeps acceptance, not method.** `image-generation-contract` keeps the request fields, the accepted-image manifest gate (`consumer_ready` only after checks on the actual pixels), candidate selection, and the downstream feedback loop. Provider catalogs, model routing, prompt compilation, batch planning, MCP batch handoff and LoRA training are removed. Identity lock means generating from approved reference images and judging the result in visual QA.

**C. The gateway stops generating media.** ai-gateway keeps `ask_model`, `refresh_models`, `text_to_speech` and Brave search. `FAL_KEY` is no longer used; `GOOGLE_API_KEY` remains for TTS only.

Thought testing (seven Sonnet scenarios, isolated packet) checked the slim contract against: no Codex while an OpenRouter image tool is loaded, a result left in Codex's cache, a recurring character, Grok blocked by zero data retention while OpenRouter lists a Grok video model, a downstream seam failure, a marketplace icon pack, and pressure to pass `--always-approve`. The first round showed agents re-generating instead of copying a cached result and found that `codex-cli-task` named a non-existent `--output` flag. Both were fixed and the two affected scenarios re-run green.

## Cross-host (ADR-0004)

| Decision | Claude | Codex | Pi |
|---|---|---|---|
| A | `codex exec` via `codex-cli-task`; `grok -p` | Native image generation; `grok -p` | `codex exec`; `grok -p` |
| C | `/setup` checks `codex` and `grok` | `commands/setup.md` | `skills/setup` |

## Consequences

- Projects need a working `codex` for images and a logged-in `grok` on a plan with video for video. Neither is installed automatically.
- Grok video is unavailable while the account has zero data retention on; enabling it means opting in to coding-data sharing via `/privacy` or configuring a user-owned bucket.
- The `shared/mcp-image-batch` server and `.claude/commands/chatgpt-image-gen.md` were kept at first as personal tools that no pipeline skill referenced, and were removed from the repo on 2026-11-15.
