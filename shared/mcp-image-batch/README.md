# mcp-image-batch

Batch ChatGPT image generation via the user's **already-logged-in Chrome** on macOS.

- No Playwright, no remote debugging port, no re-login
- Uses `osascript` to execute JavaScript in Chrome's active tab
- **File-based interaction**: batch jobs run in the background; Claude polls progress files
- Supports resume: progress saved to `{outputDir}/.progress.json`

## Setup

```bash
cd shared/mcp-image-batch
npm install
```

Add to Claude Code's MCP config (`.claude/settings.json`):

```json
{
  "mcpServers": {
    "chatgpt-image": {
      "command": "node",
      "args": ["/absolute/path/to/shared/mcp-image-batch/src/index.js"]
    }
  }
}
```

## Prompts file format

```json
{
  "outputDir": "./my-images",
  "sessionMode": "per-category",
  "categories": {
    "landscapes": ["a sunset over mountains", "misty forest at dawn"],
    "portraits": ["a samurai warrior in armor"]
  }
}
```

### sessionMode

| Value | Behaviour |
|-------|-----------|
| `"per-category"` | **(default)** New ChatGPT session at the start of each category. Prompts within a category share the same conversation context. |
| `"per-prompt"` | Legacy behaviour — fresh session before every single prompt. |
| `"shared"` | One session for the entire batch. |

### Category-level config (`categoryConfig`)

```json
{
  "outputDir": "./my-images",
  "sessionMode": "per-category",
  "categoryConfig": {
    "portraits": {
      "contextImage": "/path/to/reference.png"
    }
  },
  "categories": {
    "portraits": ["Expression A", "Expression B"]
  }
}
```

**`contextImage`** — paste a reference image into the chat at the start of the category's session. The model can then reference it for subsequent prompts in that session.

### Edit mode (in-painting / img2img)

Locks character identity by **only regenerating the painted mask area** of an existing generated image. Unpainted regions are preserved pixel-for-pixel.

```json
{
  "outputDir": "./umeko-repair",
  "sessionMode": "per-category",
  "categoryConfig": {
    "umeko_expressions": {
      "editMode": {
        "contextImage": ".allforai/art/expressions/char_umeko_expr_default.png",
        "basePrompt": "Re-render this character in warm pastel watercolor chibi style, same face and clothing.",
        "maskRegion": [0.10, 0.30, 0.80, 0.45]
      }
    }
  },
  "categories": {
    "umeko_expressions": [
      "happy expression — full warm genuine smile, crinkle eyes",
      "thinking — eyes quiet, head tilted, mouth closed",
      "surprised — eyes open wide with honest delight"
    ]
  }
}
```

**Edit mode flow per category:**
1. Open fresh ChatGPT session
2. Upload `contextImage` via clipboard paste (reference for face/proportions)
3. Submit `basePrompt` → wait for ChatGPT to generate the base image
4. For each prompt:
   - Click 编辑 on the base image (index 0 in the conversation)
   - Draw the mask using `maskRegion` (raster brush strokes via PointerEvents)
   - Submit the prompt in the editor
   - Wait for the edited image → download

**`maskRegion`** format: `[xFraction, yFraction, widthFraction, heightFraction]`
where fractions are 0–1 relative to the canvas bounds.

Example for face/expression area (lower half of face):
```json
"maskRegion": [0.10, 0.30, 0.80, 0.50]
```

## Tools

### Regular batch (background runner)

| Tool | Description |
|------|-------------|
| `start_batch(prompts_file)` | Spawn background runner, return immediately |
| `check_progress(output_dir, tail_lines?)` | Read job status + recent log lines |
| `stop_batch(output_dir)` | Kill the running job |

### EditMode (Claude Code drives directly)

| Tool | Description |
|------|-------------|
| `prepare_edit_session(output_dir, context_image?, base_prompt?)` | Open fresh ChatGPT session, upload reference, generate base image. Use Browser MCP screenshot after to verify. |
| `run_edit_prompt(output_dir, category, prompt, mask_region, image_index?)` | Run one edit: click 编辑 → draw mask → paste prompt → wait → download. Use Browser MCP screenshot after to verify. |

**EditMode workflow:**
```
prepare_edit_session(...)          # sets up ChatGPT session (~2 min)
→ Browser MCP screenshot           # verify base image looks correct
run_edit_prompt(..., prompt1, ...) # edit prompt 1 (~2 min)
→ Browser MCP screenshot           # verify result
run_edit_prompt(..., prompt2, ...) # edit prompt 2
→ Browser MCP screenshot
...
```

Text input uses **pbcopy + AppleScript Cmd+V** to bypass ChatGPT's React event blocking.

## File-based state (in outputDir)

| File | Contents |
|------|----------|
| `.job.json` | PID, status, timestamps, counters |
| `.progress.json` | Map of completed `category::prompt` → saved file path |
| `.log.txt` | Append-only log of all runner activity |

## Architecture

```
Claude Code
  → start_batch(prompts_file)
      → MCP server spawns runner.js (detached, unref'd)
      ← returns immediately
  → check_progress(output_dir)   [called periodically]
      → reads .job.json + .log.txt + .progress.json
      ← returns status + recent log tail

runner.js (background — osascript only, no Browser MCP needed)
  → osascript → Chrome JS execution
      → chatgpt.com (already logged in)
  → pbcopy + Cmd+V (AppleScript keystroke)
      → bypasses ChatGPT's React synthetic event blocking for text input
  → Browser fetch → ~/Downloads
  → mv to outputDir/{category}/
  → writes .progress.json (resume support)
  → writes .log.txt (real-time log)
  → updates .job.json (status + counters)
```

### Text input strategy

ChatGPT's main textarea and edit-mode input are React `contenteditable` divs that block `execCommand('insertText')` and similar synthetic DOM events. The reliable approach:

1. **Focus** the input via `el.focus()` + `el.click()` (JS, works fine)
2. **Write text** to macOS clipboard via `pbcopy` (shell)
3. **Paste** via AppleScript `keystroke "v" using command down` — treated as real user input
4. **Submit** via AppleScript `key code 36` (Return) or `btn.click()` for send button

This works for both `submitPrompt` (main chat) and `submitEditPrompt` (image editor).

## Requirements

- macOS (uses `osascript` + `pbcopy`)
- Google Chrome logged into chatgpt.com
- Node.js 18+
