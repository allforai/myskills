# Model Role Policy

Grillstorm uses three reasoning roles. They may map to three models or inherit one host
model, but their contexts and responsibilities remain separate.

| Role | Work | Requirement |
|---|---|---|
| `THINK` | Grill synthesis, reuse radar, spec/abstraction/task critics, replan | strongest available reasoning |
| `BUILD` (`bulk` in runner JSON) | scoped TDD implementation in task worktrees | efficient model capable of repository coding |
| `VERIFY` | supervisor acceptance reruns, Standards/Spec reviews, final proof | never weaker than BUILD; independent context |

## Route policy

- `diagnostic` and `direct`: default to `inherited`. Fresh contexts still separate BUILD
  from VERIFY, but model-tier overhead is usually unjustified.
- `ticketed` and `program`: recommend `tiered` only when the host proves model overrides are
  available and the effective model sources are controllable. Otherwise use `inherited`.

Do not equate model identity with independence. VERIFY must never receive executor narrative,
even when both roles inherit the same model.

## Current recommendation ladder

Treat these as capability-checked recommendations, not timeless hard-coded requirements.
At orientation, inspect the host's actual model enum/registry and select the first available
candidate for each role. Record the selected literal and evidence before launch.

### Claude Code

| Role | Preferred | Pre-launch fallback order |
|---|---|---|
| `THINK` | `fable` / `claude-fable-5` | `opus` / `claude-opus-4-8` -> `sonnet` |
| `BUILD` | `sonnet` / `claude-sonnet-5` | latest available Sonnet -> `haiku` for tightly scoped low-risk work only |
| `VERIFY` | `opus` / `claude-opus-4-8` | `fable` -> latest available Opus -> `sonnet` |

Fable is reserved for the decision-heavy front of the workflow. Sonnet handles the
high-volume implementation plane. Opus supplies an independent, high-rigor verification
plane. A fallback is selected only before launch and recorded; it is never a mid-run
automatic downgrade.

### Codex

| Role | Preferred | Pre-launch fallback order |
|---|---|---|
| `THINK` | `gpt-5.6-sol` | strongest current agentic coding model exposed by the host |
| `BUILD` | `gpt-5.6-luna` | `gpt-5.6-terra` -> current efficient coding model |
| `VERIFY` | `codex-auto-review` | `gpt-5.6-terra` -> `gpt-5.6-sol` |

The Codex CLI registry and the native subagent model enum may differ. If Luna is absent
from the active worker launcher, resolve BUILD to Terra before approval. Never pass a model
literal merely because it appeared in another machine's cache.

## Freeze before launch

During orientation, inspect the effective model sources: wrapper, argv, profile, config,
project/user configuration, and host default.

- Any locked or unknown source -> `inherited`.
- All sources proven overridable -> `tiered` is allowed.
- Never assume a recommended vendor model exists without a current capability probe.
- Never silently downgrade after launch.

Record in `model-policy.md`:

```markdown
## Policy
- Mode: inherited|tiered
- THINK: <host-owned or resolved model>
- BUILD: <host-owned or resolved model>
- VERIFY: <host-owned or resolved model>
- Evidence: <capability/model-source evidence>
- Failure policy: retry infrastructure; no model substitution
```

Include this policy in the single launch-contract approval. Do not ask a separate model
question unless the user explicitly wants to override the recommendation.

## Token discipline

- THINK does not implement routine tasks.
- Post-delivery probe sampling and related-gap expansion use THINK; probe execution and
  evidence capture use fresh VERIFY contexts; interactive critique stays in the root Grill
  context.
- BUILD receives only one task, relevant specs/interfaces, and supervisor feedback.
- VERIFY receives only the frozen task, repository state, acceptance command, and diff.
- Escalation changes the work state, not the model silently. A failed BUILD task is retried
  within its frozen policy; if exhausted, it becomes an escalation/replan input for THINK.

## Platform mapping

Claude Workflow agents use the frozen role mapping in each `agent(..., {model: ROLE})`.
Codex native subagents receive the same role contract. The bundled headless runner reads
`think`, `bulk`, and `verify` mappings; `prepare_codex_policy.py` creates either a
conservative inherited policy or a tiered policy backed by explicit model-source evidence.
