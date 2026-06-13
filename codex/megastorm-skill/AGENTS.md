# AGENTS.md — megastorm (Codex port, v0.2.0)

> Drive a large goal end-to-end: decompose into modules, front-load every human
> decision, then autonomously design → validate (closed-loop) → plan → reverse-review
> → orchestrate a task DAG → concurrently execute with anti-fake-completion
> supervision. Heavy and token-intensive; invoke explicitly ("megastorm <goal>").

## Architecture (minimal-compat port of the Claude Code plugin)

The interactive Codex session is the orchestration brain for Phases -1/0/2 and
the short Phase 1 stages; each headless agent is a fresh `codex exec` process.
The long §1.6 execute+supervise loop is NOT prose — it runs in a deterministic
Python runner (a stateless prose loop drifts; the retry ledger must be code).

| Piece | File | Role |
|---|---|---|
| Playbook | `./execution-playbook.md` | Full phase-by-phase orchestration (read this first) |
| Agent prompts | `./prompts/*.md` | 6 inlined-methodology prompts for headless `codex exec` agents |
| Schemas | `./schemas.md` | JSON contracts: registry, design-manifest, plan-task, verdict |
| Closure gate | `./scripts/check_closure.py` | Deterministic requirement/interface closure check |
| Plan gate | `./scripts/validate_plan_tasks.py` | touched_paths + non-vacuous acceptance_cmd + registry vocab |
| DAG builder | `./scripts/build_task_dag.py` | Layers + isolate_groups + cross-module interface edges |
| Execution runner | `./scripts/run_layers.py` | §1.6: ready-set scheduling, mutex groups, worktrees, retry ledger, skip-on-escalation, supervision |
| Model tiers | `./models.example.json` | THINK/VERIFY/BULK — resolved by the HUMAN in Phase 0 |

## Invariant

Decisions front-loaded → autonomous → self-fix loop, escalate-to-stop.
All human interaction happens in Phase 0; Phase 1 runs without human stops
except on escalation. No automatic model downgrade, no automatic re-decomposition.

## Quickstart

1. Read `./execution-playbook.md` and follow it phase by phase.
2. Phase 0 produces: overview doc with frozen registry + `models.json` (copy
   `models.example.json`, fill real model names with the human).
3. Phase 1 ends with: `python3 scripts/run_layers.py orchestration.json all-tasks.json
   --models models.json --prompts prompts --root <repo>` — exit 0 = all supervised
   done; exit 1 = escalations in `execution-report.json`, render them to the human.

Requirements: `codex` CLI on PATH, `git`, `python3`. Run script tests with
`python3 -m pytest scripts/ -q` (77 tests).
