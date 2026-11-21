---
status: accepted
---

# The user may name a cheaper model for steps that do not judge

Since the 2026-09 strong-model audit every step of a run has used the session model: no skill names a model, and a child keeps what the session runs on. On a host where the strongest model has its own, smaller allowance, that rule spends it on work that needs none of it. The Claude engine holds no filesystem, so every ledger call, wave marker and measurement is an agent that runs one command and reports what it printed — several per node — and each starts on the session model.

## Decision

**A. The choice is the user's, per project.** `.allforai/bootstrap/model-routing.json` holds `{"relay": "<name>", "routine": "<name>"}`. Both keys are optional and a missing key, or a missing file, means the session model. An interactive bootstrap asks once and records the answer; the run entry passes the file to the engine unchanged. No skill, template or script in this repository contains a model name: the names come from what the user's host offers when they answer.

**B. `relay` covers a step that runs one command and reports what it printed.** Run policy, wave markers, repair-ledger operations, measurements and the quarantine call. The engine classifies these by label (`RELAY_LABEL`), and a test fails until a new label is classified.

**C. `routine` covers a node bootstrap declared `model_class: "routine"`.** The declaration is for work where every choice was made upstream and commands or a schema decide the result. The validator refuses any value but `routine`, and refuses it on the QA node of an `inline_review`.

**D. Whatever judges or writes the record keeps the session model.** The node gate, the inherit check, inline review, repair, repair routing, the DAG summary, expanders and commits are never routed. A routine node is therefore still accepted or refused by the session model.

## Cross-host (ADR-0004)

| Decision | Claude | Codex | Pi |
|---|---|---|---|
| A–D | Workflow engine routes by `args.models` | not applied: the driver runs commands itself, so there are no relay agents, and its allowance is not the one this decision protects | not applied: children keep the session model and cost is controlled by thinking level |

`model_class` in a workflow is ignored by Codex and Pi.

## Consequences

- With no `model-routing.json`, nothing changes.
- A relay model that misreports a command's output is caught where the engine already checks the verdict's shape and identity; a wrong ledger verdict stops the run rather than passing work.
- A node wrongly declared routine fails its gate and is repaired on the session model, costing more than it saved. The planning rule says to omit the declaration when unsure.
- A name the host no longer offers fails the dispatch; the user edits or deletes the file.
- This narrows the 2026-09 rule from "never downgrade" to "never downgrade a judge, and only where the user asked".
