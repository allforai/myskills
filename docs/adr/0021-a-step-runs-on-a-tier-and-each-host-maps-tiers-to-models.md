---
status: accepted
---

# A step runs on a tier, and each host maps tiers to models

Since the 2026-09 strong-model audit every step of a run used the session model: no skill names a model, and a child kept what the session ran on. On a host whose strongest model has its own, smaller allowance, that spends it on work that needs none of it — the Claude engine alone dispatches several command-relay agents per node. Claude Code, Codex and Pi can each run a step on a different model, so what a skill has to say is how strong a model a step needs, not which one; a project then moves between hosts without changing its workflow.

## Decision

**A. Three tiers, named by what the work does.** `strong` makes a choice nobody made upstream or judges other work; `standard` builds to a spec that already settles every choice; `light` runs a command and reports what it printed, or writes a record. A node declares `model_tier` at bootstrap (absent means strong). The node gate, reviews, diagnosis and repair are strong whatever a node declares, and the validator refuses a lower tier on the QA node of an `inline_review`.

**B. The run maps tiers to models per host, without asking.** Before the first node a run reads `.allforai/bootstrap/model-tiers.json`. With no entry for its host (`claude`, `codex`, `pi`) it looks at the models the host can run, chooses one per tier itself — `strong` never weaker than the session model — records them under its host and lists the choice at completion. An existing entry is reused; the user edits it, or deletes it to have the next run choose again. A tier left out runs on the session model. No skill, template or script names a model. The run still asks nothing (ADR-0018): which model fits a tier is the model's call, not a product decision.

**C. Each host applies its entry where it dispatches work.** The tier decides the model; nothing else about a step changes.

## Cross-host (ADR-0004)

| | Claude | Codex | Pi |
|---|---|---|---|
| Where | Workflow engine: `args.models` → each `agent()` call's `model` | `flow.py`: `codex exec -m` per node | each child's `provider/id` |
| Engine steps | classified by label (`LIGHT_LABEL`); a test fails until a new label is classified | the driver runs helper scripts itself; only node workers, reviews and diagnosis are dispatched | per the run template |
| Judges | gate, inherit check, inline review, repair, repair route, DAG summary, expanders: strong | inline review and diagnosis: strong | gate, review, diagnosis, repair: strong |

## Consequences

- A project with no `model-tiers.json` gets one at its next run, chosen by that run and disclosed at completion.
- A step given a model too weak for it fails the gate and is repaired on strong, costing more than it saved; the planning rule says to go one tier up when unsure.
- A relay model that misreports a command's output meets the checks the engine already applies to a verdict's shape and identity; a wrong ledger verdict stops the run rather than passing work.
- A name the host no longer offers fails the dispatch; the user edits or deletes the entry.
- This narrows the 2026-09 rule from "never downgrade" to "never downgrade a judge; each host chooses its models per tier".
