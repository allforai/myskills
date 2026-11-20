---
status: accepted
---

# No MCP gateway: a second model is another agent CLI

meta-skill shipped `mcp-ai-gateway`, a Node MCP server with three jobs: `ask_model` (cross-model validation through OpenRouter), Brave search, and Google text-to-speech. ADR-0014 had already taken image and video generation away from it.

By 2026-11-21 nothing depended on it. No skill or capability named Brave search or text-to-speech: research is written against each host's own web search, and `demo-forge`, the documented consumer of both, no longer mentioned either. `ask_model` was named in four files, each time as "use it if present, otherwise a fresh-context sub-agent". The server also failed to start after every plugin upgrade, because an upgrade lands in a fresh directory without `node_modules`; the tools were silently absent until someone ran `/setup update`, and no run was reported as missing them. The last traces of use were model caches written on 2026-11-04 and 2026-04-12.

A self-healing launcher was written first (9223df9e) and never shipped: it added a mechanism to something with no remaining consumer.

## Decision

**A. The gateway is removed.** `claude/meta-skill/mcp-ai-gateway`, `shared/mcp-ai-gateway`, the Codex and Pi links to it, both `.mcp.json` files, the gateway steps of the three setup entries and of the installers are deleted. No plugin in this repository ships an MCP server.

**B. A second model is whatever second platform is already there.** Cross-model validation hands the summary to another platform's agent CLI installed on the machine, run headless and read-only; a host that can switch models (Pi) runs it on a different one. With neither, a fresh-context sub-agent gives the review and the record says it was the same model. The script channel through `OPENROUTER_API_KEY` is unchanged. Nothing is installed for the sake of XV, and which model ran is recorded, never prescribed.

**C. Keys follow their consumers.** `BRAVE_API_KEY` has none and is dropped from setup. `GOOGLE_API_KEY` stays for game-audio's Lyria music generation, which calls Google directly and never went through the gateway. `OPENROUTER_API_KEY` stays for script XV and jev.

**D. Demo media names its source.** `demo-forge` required populated media fields while the only named source was the unused Brave search. It now takes the project's own assets, then generated images through the image contract, then licensed material from the host's search, and records the origin of each file.

## Cross-host (ADR-0004)

| Decision | Claude | Codex | Pi |
|---|---|---|---|
| A | plugin has no `.mcp.json`; `/setup` has no build step | `install_bundle.py` runs no `npm`; parity check refuses a returned `.mcp.json` | package has no gateway link |
| B | `codex` / `grok` CLI, else sub-agent | `claude` / `grok` CLI, else sub-agent | model switch, else another CLI, else sub-agent |

## Consequences

- A machine with one agent CLI and no OpenRouter key gets same-model review, recorded as such. That was already the fallback.
- Sending a summary to another vendor's CLI sends it to that vendor, as `ask_model` did to OpenRouter. The screenshot boundary of visual acceptance (session model and the frozen second-platform reviewer only) is unchanged.
- An installed copy older than this keeps a gateway entry that fails to connect until the plugin is updated; nothing reads it.
- Text-to-speech and third-party media search are gone as built-in abilities. A project that needs one declares it as its own dependency.
