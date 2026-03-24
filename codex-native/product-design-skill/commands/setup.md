# Product Design Setup For Codex Native

This document replaces the Claude-specific setup command with Codex-native
operating rules for capability detection and configuration guidance.

## When to use

Use this workflow when the user wants to:

- inspect which external capabilities are ready
- understand downgrade behavior before running product-design or demo-forge
- configure keys or supporting services for richer workflows

Do not treat this as plugin-registration parity. It is a capability and
configuration workflow, not a Claude plugin installer.

## Modes

| Mode | Meaning |
|---|---|
| unspecified | inspect status, then guide only the missing items |
| `check` | inspect status only |
| `reset` | ignore previous assumptions and review every configurable capability |
| `update` | inspect installed components and report what would need updating |

## Capability classes

### Browser automation

- Playwright
- used by demo-forge and dev-forge verification workflows
- if missing, verification remains blocked rather than silently downgraded

### AI gateway and external services

- OpenRouter
- Google AI
- fal.ai
- Brave Search

These are optional enhancements. If missing, product-design and demo-forge
must report the downgrade chain explicitly.

### Visual generation support

- Stitch UI or equivalent host-managed visual tooling

In Codex native mode this is treated as optional. If unavailable, fall back to
text-first UI design outputs.

## Required output

The setup workflow should always produce a plain-language status summary with:

- capability name
- readiness state
- affected workflows
- downgrade effect when unavailable
- next action if the user wants to configure it

## Codex-native detection rules

- prefer repository-local evidence and environment evidence
- do not assume Claude deferred tool state exists
- do not claim MCP registration succeeded unless there is local proof
- distinguish clearly between "configured", "detectable", and "usable here"

## Recommended status table

| Capability | Status | Used by | Native behavior if missing |
|---|---|---|---|
| Playwright | ready / missing / unknown | demo-forge, dev-forge | verification blocked |
| OpenRouter | ready / missing / unknown | product-design, demo-forge | no enhanced cross-model path |
| Brave Search | ready / missing / unknown | demo-forge | degrade to ordinary search |
| Google AI | ready / missing / unknown | demo-forge | skip Google generation path |
| fal.ai | ready / missing / unknown | demo-forge | skip fal.ai generation path |
| Stitch-style visual tooling | ready / missing / unknown | product-design | use text-only visual specs |

## Response contract

For `check`:

- return only the status table and downgrade notes

For unspecified mode:

- return the status table
- identify the smallest missing set relevant to the user's stated goal
- ask follow-up questions only if the user wants configuration help

For `reset` and `update`:

- do not mutate plugin registrations automatically
- explain what would need to be changed and what cannot be made Claude-equivalent

## Safety rules

- never ask the user to paste secrets unless configuration work is explicitly
  requested
- never imply Claude plugin registration semantics are available in Codex
- never hide uncertainty when capability detection is incomplete
