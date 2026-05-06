# chatgpt-image-gen Skill Design

**Date:** 2026-05-07
**Status:** Approved

## Overview

A Claude Code slash command (`/chatgpt-image-gen`) that uses `chrome-devtools-mcp` to automate ChatGPT image generation in batch, then downloads and organizes the results by category.

## Invocation

```
/chatgpt-image-gen prompts.json
```

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
Read JSON
→ For each category:
    → For each prompt:
        [Browser] Navigate to chatgpt.com (persistent profile, user pre-logged-in)
        [Browser] Open new chat
        [Browser] Switch to DALL-E/GPT-Image model if needed
        [Browser] Fill prompt input, press Enter
        [Browser] wait_for image element (max 120s)
        [Browser] evaluate_script → extract <img> src URL
        [Shell]   curl download → outputDir/category/slug_N.png
    → Print category summary
→ Print global summary (success count, skip list)
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
- Replace spaces with `_`, strip special characters
- Append `_01`, `_02`... suffix (increments if file already exists, never overwrites)

## Browser Interaction Steps (per prompt)

1. `navigate_page` → `https://chatgpt.com`
2. `take_snapshot` → locate and `click` "New chat"
3. `take_snapshot` → locate model selector, switch to DALL-E / GPT-Image if not already selected
4. `fill` → type prompt into input box
5. `press_key Enter`
6. `wait_for` → poll for generated `<img>` element (timeout: 120s)
7. `evaluate_script` → extract `src` URL from generated image (typically `https://files.oaiusercontent.com/...`)
8. Bash `curl -L "<url>" -o "<output_path>"`

## Error Handling

| Scenario | Behavior |
|----------|----------|
| Generation timeout (>120s) | Skip prompt, print warning, continue |
| Image URL extraction fails | Save screenshot as fallback, print warning |
| `curl` download fails | Retry once; if still fails, add to final failure list |

## Preconditions

- User is logged into ChatGPT in the persistent Chrome profile used by `chrome-devtools-mcp`
- Input JSON file path is valid and readable
- `chrome-devtools-mcp` MCP server is configured and running

## Implementation Location

```
.claude/commands/chatgpt-image-gen.md   ← slash command entry point
```

This is a project-level command (lives in the consuming project's `.claude/commands/`, or in this repo for development/testing).
