# chatgpt-image-gen Skill Design

**Date:** 2026-05-07
**Status:** Approved

## Overview

A Claude Code slash command (`/chatgpt-image-gen`) that uses `chrome-devtools-mcp` to automate ChatGPT image generation in batch, then downloads and organizes the results by category.

## Invocation

```
/chatgpt-image-gen prompts.json
```

## Skill File Structure

The skill lives at `.claude/commands/chatgpt-image-gen.md` with this frontmatter:

```yaml
---
description: Batch generate images on ChatGPT and download/organize by category
argument-hint: <path-to-prompts.json>
---
```

The command body contains the full instruction set (this design doc's execution steps, translated into directive prose for Claude to follow).

## Input Format

A JSON file with an `outputDir` and a `categories` map:

```json
{
  "outputDir": "./chatgpt-images",
  "categories": {
    "风景": ["a sunset over mountains", "misty forest at dawn"],
    "人物": ["a samurai warrior", "a Victorian lady"]
  }
}
```

## Architecture

### Flow

```
Read + validate JSON (file exists, outputDir present, categories non-empty)
→ For each category:
    Create directory: outputDir/category/ (mkdir -p, skip if exists)
    → For each prompt:
        [Browser] navigate_page → https://chatgpt.com
        [Browser] take_snapshot → click "New chat" button
        [Browser] take_snapshot → check current model label
                  If not GPT-4o (image-capable), click model selector → choose GPT-4o
        [Browser] take_snapshot → fill prompt textarea → press_key Enter
        [Browser] wait_for: CSS selector for completed assistant message image
                  (poll every 5s, timeout 120s)
        [Browser] evaluate_script → extract image src URL and session cookies
        [Shell]   curl with cookies → download to outputDir/category/slug_N.png
    → Print category summary (N succeeded, M skipped)
→ Print global summary (total success, total skip, failure list with reasons)
```

### Output Directory Structure

```
chatgpt-images/
├── 风景/
│   ├── a_sunset_over_mountains_01.png
│   └── misty_forest_at_dawn_01.png
└── 人物/
    ├── a_samurai_warrior_01.png
    └── a_victorian_lady_01.png
```

### File Naming Rules

- Take first 40 chars of the prompt text
- Lowercase, spaces → `_`, strip all non-alphanumeric characters except `_`
- Append `_01`, `_02`... — scan existing files in target dir and increment, never overwrite
- If multiple images are returned for one prompt, save all with `_01`, `_02`... and log the count

## Browser Interaction Steps (per prompt)

1. `navigate_page` → `https://chatgpt.com`

2. `take_snapshot` → locate "New chat" button by accessible name, `click` it

3. `take_snapshot` → read the model selector label (top-center of page).
   - If label is not "GPT-4o": `click` model selector → `take_snapshot` → `click` "GPT-4o"
   - GPT-4o supports image generation natively (DALL-E 3 is embedded); do not select a separate DALL-E option

4. `take_snapshot` → locate the prompt textarea (role: textbox), `fill` with prompt text

5. `press_key Enter` to submit

6. `wait_for` with condition: an `<img>` element inside an assistant turn container whose `src` starts with `https://files.oaiusercontent.com` is present and the "Stop generating" button has disappeared (generation complete signal)
   - Poll interval: 5s, timeout: 120s

7. `evaluate_script` to extract image data:
   ```javascript
   (() => {
     const imgs = [...document.querySelectorAll('img')].filter(
       img => img.src.startsWith('https://files.oaiusercontent.com')
     );
     const cookies = document.cookie;
     return { urls: imgs.map(i => i.src), cookies };
   })()
   ```
   - Take all matching URLs (handles multi-image responses)
   - Note: session auth is carried by `__Secure-next-auth.session-token` cookie in the browser profile; pass it to curl via `--cookie`

8. For each extracted URL:
   ```bash
   mkdir -p "<outputDir>/<category>"
   curl -L "<url>" \
     --cookie "<cookie_string>" \
     -H "Referer: https://chatgpt.com/" \
     -o "<outputDir>/<category>/<slug>_<N>.png"
   ```
   Download immediately — `files.oaiusercontent.com` URLs expire within minutes.

## Error Handling

| Scenario | Behavior |
|----------|----------|
| JSON file not found / invalid | Abort immediately with clear error message |
| `outputDir` not writable | Abort immediately |
| Generation timeout (>120s) | Skip prompt, record as `TIMEOUT`, continue |
| Rate limited (HTTP 429 or "limit reached" text in page) | Wait 60s, retry once; if still rate-limited, skip all remaining prompts in current category, record as `RATE_LIMITED` |
| Image URL extraction returns empty list | Skip prompt, record as `NO_IMAGE_FOUND`, print snapshot for debug |
| `curl` download fails (non-2xx) | Retry once after 5s; if still fails, record as `DOWNLOAD_FAILED` |
| URL expired during download (403) | Re-run `evaluate_script` to refresh URL once, retry; if still 403 record as `URL_EXPIRED` |

All skipped/failed prompts are listed at the end of the global summary with their error codes.

## Preconditions

- User is logged into ChatGPT in the persistent Chrome profile used by `chrome-devtools-mcp`
- `chrome-devtools-mcp` MCP server is configured and running in Claude Code settings
- Input JSON file path is valid and readable
- `curl` is available in the shell environment

## Implementation Location

```
.claude/commands/chatgpt-image-gen.md   ← slash command (this repo, for dev/testing)
```

Users copy or symlink this into their own project's `.claude/commands/` to use it.
