# Codex Capability Matrix

Date: 2026-03-26

Purpose:
- Shift Codex validation away from industry-specific or stack-specific projects
- Define reusable capability dimensions that can be combined across plugins
- Make regression validation focus on workflow behavior, artifact contracts, and degradation rules

## Core Principle

Do not treat validation as:
- "Can this plugin handle food delivery?"
- "Can this plugin handle Go + Flutter?"

Treat validation as:
- "Can this plugin handle multi-role modeling?"
- "Can this plugin continue with partial upstream artifacts?"
- "Can this plugin stop correctly when prerequisites are missing?"
- "Can this plugin preserve contract shape under degraded tool conditions?"

## Capability Dimensions

| ID | Capability | Description | Typical Evidence |
|----|------------|-------------|------------------|
| C01 | Entry-point discovery | Plugin exposes valid `AGENTS.md` entry and can be routed correctly | `AGENTS.md` exists and references real playbook/skills |
| C02 | Phase orchestration | Workflow phases match implementation docs | `AGENTS.md` and `execution-playbook.md` agree |
| C03 | Artifact contract write | Plugin writes expected `.allforai/` artifacts with current names and locations | output contract matches docs |
| C04 | Artifact contract read | Plugin consumes upstream artifacts in the documented order | prerequisites and fallback chain are explicit |
| C05 | Resume / partial progress | Plugin can interpret existing artifacts and continue safely | completion markers / resume semantics documented |
| C06 | Missing prerequisite stop | Plugin stops early and clearly when required inputs are missing | explicit stop condition |
| C07 | Graceful degradation | Plugin continues with reduced capability when optional tools are absent | fallback chain documented |
| C08 | Low-assumption defaults | Plugin assumes reasonable defaults and only asks when blocking | default policy documented |
| C09 | Shape-based outputs | Outputs are structurally constrained but not overfit to exact counts | schema, lower bounds, contract checks |
| C10 | Guardrail preservation | Plugin avoids changing unrelated business behavior | explicit non-goals / guardrails |
| C11 | Runtime sensitivity | Plugin clearly distinguishes runtime-required vs runtime-free phases | runtime prerequisites separated |
| C12 | Cross-phase closure | Downstream artifacts remain compatible with adjacent plugins | handoff contract is explicit |

## Plugin Coverage Map

| Plugin | Primary Capabilities |
|--------|----------------------|
| `product-design` | C01, C02, C03, C05, C07, C08, C12 |
| `dev-forge` | C01, C02, C03, C04, C05, C06, C08, C11, C12 |
| `demo-forge` | C01, C02, C03, C04, C07, C08, C11, C12 |
| `code-tuner` | C01, C02, C03, C04, C05, C06, C08, C09 |
| `code-replicate` | C01, C02, C03, C05, C08, C09, C12 |
| `ui-forge` | C01, C02, C04, C06, C08, C10 |

## Validation Styles

Use three validation styles together:

### 1. Static Contract Validation

Checks:
- file presence
- doc consistency
- output names
- prerequisite chains

Best for:
- C01, C02, C03, C04, C05

### 2. Behavior Prompt Validation

Checks:
- whether prompts exercise the right capability
- whether assertions are shape-based instead of brittle
- whether degradation/stop behavior is represented

Best for:
- C06, C07, C08, C09, C10

### 3. Local Script Execution

Checks:
- utility scripts
- artifact transforms
- merge/generation logic

Best for:
- C03, C05, C09, C12

## What To Avoid

Avoid validation that depends on:
- one business domain
- one framework
- one language
- exact counts that naturally vary by discovery or generation
- hidden assumptions about tool availability

Examples of brittle assertions:
- "must generate exactly 8 tasks"
- "must produce exactly 35 endpoints"
- "must score exactly 82"

Prefer:
- "at least one role"
- "at least one main business flow"
- "all required JSON artifacts parse"
- "degradation path is explicit"
- "completion marker matches documented workflow"

## Recommended Next Step

Build a small generic fixture set around capability combinations, not projects.

Examples:
- `minimal-product-map`
- `minimal-ui-baseline`
- `minimal-project-forge`
- `minimal-runtime-config`
- `minimal-reverse-engineering-source-summary`
