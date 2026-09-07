# Model Role Policy

Grillstorm uses three reasoning roles. They may map to three models or inherit one host
model, but their contexts and responsibilities remain separate.

| Role | Work | Requirement |
|---|---|---|
| `THINK` | Grill synthesis, reuse radar, spec/abstraction/task critics, replan | strongest available reasoning |
| `BUILD` (`bulk` in runner JSON) | scoped TDD implementation in task worktrees | host model, or one tier below it when the user chooses cost-first |
| `VERIFY` | supervisor acceptance reruns, Standards/Spec reviews, final proof | never weaker than BUILD; independent context |

## Route policy

- `diagnostic` and `direct`: default to `inherited`. Fresh contexts still separate BUILD
  from VERIFY, but model-tier overhead is usually unjustified.
- `ticketed` and `program`: `tiered` only when the user chooses option B below and the host
  proves model overrides are available and the effective model sources are controllable.
  Otherwise use `inherited`.

Do not equate model identity with independence. VERIFY must never receive executor narrative,
even when both roles inherit the same model.

## Recommendation rule

Default: `inherited` for all three roles. The host session model runs Grill synthesis,
critics, replan, implementation, supervision and review. `THINK` and `VERIFY` are never set
below the host model: a verifier weaker than the code it checks is not a trust root, and a
critic that misses a seam costs a whole layer. The only optional downgrade is `BUILD`.

At orientation, read the model list the host actually exposes (Claude: the Workflow `model`
enum; Codex: the CLI's model list and the native subagent enum, which may differ). Order it by
what you know of those models and name the tier one step below the host model — never the
cheapest tier, implementation is the most agentic work in the run. Then put two concrete
options in the frontier round with a stated recommendation:

- **A evidence-first:** all roles `inherited`.
- **B cost-first:** `BUILD` on `<next tier down>`; `THINK` and `VERIFY` inherited.

Recommend B when the user mentioned cost, or the route is `ticketed`/`program` with many small,
well-specified tasks where implementation volume dominates. Recommend A for `diagnostic` and
`direct`, and whenever tasks are exploratory, cross-cutting, or drive a UI: a weaker BUILD
fails more often there, and a failed BUILD is retried on the host model at a net loss. When
both rules apply, recommend A and say why; the user can still choose B. Say
that the ordering is your knowledge of the models, not a price list, and that the user can
overrule it. No model literal lives in this file or anywhere else in the skill; the literal
comes from the host list read at orientation and is recorded with the user's words.

## Freeze before launch

During orientation, inspect the effective model sources: wrapper, argv, profile, config,
project/user configuration, and host default.

- Any locked or unknown source -> `inherited`.
- All sources proven overridable -> `tiered` is allowed.
- Never freeze a literal that is not in the host list read at orientation; a user-given
  literal that the probe cannot find fails at launch, not in the first worker.
- Never silently downgrade after launch.

Record in `model-policy.md`:

```markdown
## Policy
- Mode: inherited|tiered
- THINK: <host-owned>
- VERIFY: <host-owned>
- BUILD: <host-owned or the literal the user chose>
- BUILD fallback on another host: <literal or none>
- Recommended: A|B — <one-sentence reason>
- Confirmed by user: "<their words>" at <ISO time>
- Evidence: <host model list read at orientation; model-source evidence>
- Failure policy: retry infrastructure once; a BUILD task rejected on a downgraded model is
  retried once there, then on the host model, each step recorded; no other substitution
```

Include this policy in the launch contract. The model options are one item of the single
frontier round, not a separate question; after the round closes, no model question is asked.

## Token discipline

- THINK does not implement routine tasks.
- Post-delivery probe sampling and related-gap expansion use THINK; probe execution and
  evidence capture use fresh VERIFY contexts; interactive critique stays in the root Grill
  context.
- BUILD receives only one task, relevant specs/interfaces, and supervisor feedback.
- VERIFY receives only the frozen task, repository state, acceptance command, and diff.
- Escalation changes the work state, not the model silently. A BUILD task that fails on the
  downgraded model is retried once there, then on the host model with the change recorded; if
  still exhausted, it becomes an escalation/replan input for THINK.

## Platform mapping

Claude Workflow agents omit `model` for THINK and VERIFY (inherit) and pass the frozen literal
for BUILD only under option B.
Codex native subagents receive the same role contract. The bundled headless runner reads
`think`, `bulk`, and `verify` mappings; `prepare_codex_policy.py` creates either a
conservative inherited policy or a tiered policy backed by explicit model-source evidence.
