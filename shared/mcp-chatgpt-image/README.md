# mcp-chatgpt-image

Batch ChatGPT image generation via the user's **already-logged-in Chrome** on macOS.

- No Playwright, no remote debugging port, no re-login
- Uses `osascript` to execute JavaScript in Chrome's active tab
- **File-based interaction**: batch jobs run in the background; Claude polls progress files
- Supports resume: progress saved to `{outputDir}/.progress.json`

## Setup

```bash
cd shared/mcp-chatgpt-image
npm install
```

Add to Claude Code's MCP config (`.claude/settings.json`):

```json
{
  "mcpServers": {
    "chatgpt-image": {
      "command": "node",
      "args": ["/absolute/path/to/shared/mcp-chatgpt-image/src/index.js"]
    }
  }
}
```

## Usage

Create a prompts JSON file:

```json
{
  "outputDir": "./my-images",
  "categories": {
    "landscapes": ["a sunset over mountains", "misty forest at dawn"],
    "portraits": ["a samurai warrior in armor"]
  }
}
```

In Claude Code:

```
Start a batch job with /path/to/prompts.json
```

Claude calls `start_batch` → job starts in background → Claude periodically calls
`check_progress` to report status. Chrome must be open and logged into chatgpt.com.

## Tools

| Tool | Description |
|------|-------------|
| `start_batch(prompts_file)` | Spawn background runner, return immediately |
| `check_progress(output_dir, tail_lines?)` | Read job status + recent log lines |
| `stop_batch(output_dir)` | Kill the running job |

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

runner.js (background)
  → osascript → Chrome JS execution
      → chatgpt.com (already logged in)
  → Browser fetch → ~/Downloads
  → mv to outputDir/{category}/
  → writes .progress.json (resume support)
  → writes .log.txt (real-time log)
  → updates .job.json (status + counters)
```

## Requirements

- macOS (uses `osascript`)
- Google Chrome logged into chatgpt.com
- Node.js 18+
