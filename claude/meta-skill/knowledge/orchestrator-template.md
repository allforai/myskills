# Orchestrator Template

> Template for generating .claude/commands/run.md in target projects.
> Bootstrap reads this and writes a customized version.

## Template: run.md

Below is the complete content that bootstrap writes to `.claude/commands/run.md`.

---

~~~markdown
---
name: run
description: Execute the project workflow. Specify a goal.
arguments:
  - name: goal
    description: What you want to achieve (natural language)
    required: true
---

# Workflow Orchestrator

You are the workflow orchestrator. Execute nodes to achieve the goal.

## Ground Truth

Read `.allforai/bootstrap/workflow.json` at every iteration. Trust it over conversation history.

## Preflight Gate

Before executing any workflow node, run unattended readiness:

```bash
python3 .allforai/bootstrap/scripts/record_run_event.py . --event run_started --status started --message "run command invoked"
python3 .allforai/bootstrap/scripts/validate_unattended_readiness.py . --write-report
```

If it exits non-zero or `.allforai/bootstrap/unattended-run-readiness.json`
has `status != "ready"`, stop immediately. Do not start partial execution, do
not ask the user mid-run, and do not silently weaken validation. Report the
blockers from `.allforai/bootstrap/unattended-run-readiness.md` and ask the user
to resolve them through `/setup check`, `/bootstrap`, or the approval dashboard
before re-running `/run`.
Before stopping, record `preflight_blocked` with
`record_run_event.py`, then run `summarize_run_log.py --write-report`.

### Dynamic preflight reconciliation

Before every execution wave, run every idempotent expander declared by
`workflow.json.expanders`, including `expand_game_2d_production.py`. An expander may add or
repair nodes after an upstream node creates a trigger artifact. Re-read the changed DAG and
rerun `validate_unattended_readiness.py`; do not execute newly exposed work when readiness
is not `ready`.

### Generic QA repair loop

After a node reports success, independently run `check_artifacts.py --node <node_id> --json`.
Non-empty `code_gaps` or `test_gaps`, partial/conditional status, placeholders, failed
validation, or other blocking findings cannot be committed as complete. Invoke the
`execution-repair-loop`, repair within its three-attempt budget, and **Rerun affected QA evidence**
through the original node plus the independent artifact gate. Exhaustion is a hard failure;
never waive, downgrade, or hide a gap.

## Phase B execution (CC: Workflow engine)

`/run` is fully autonomous — no questions, no human stops. Drive it as:

1. Invoke the Workflow engine script at
   `${CLAUDE_PLUGIN_ROOT}/knowledge/run-engine/run-engine.workflow.js`.
   It reads `workflow.json`, schedules ready nodes (alignment_refs run in parallel),
   self-heals soft failures, commits each node immediately, and returns one of:
   - `{ status: "complete" }`
   - `{ status: "needs_diagnosis", hardFailures: [...] }`

2. On `complete`: run the learning-protocol extraction, then produce the Phase C report:
   a. **Evidence-anchored completeness (verification honesty).** Run
      `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/compute_completeness.py <base>` — it derives each
      node's TRUE state from its recorded `verification` evidence and writes
      `.allforai/bootstrap/completeness-report.json`. **Report the two-column result as the
      headline: VERIFIED (真验过) % vs unverified (只生成没验) %.** Never present "completed
      node count" as completeness — a node without real evidence is `unverified`, never counted.
   b. Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/check_evidence.py <base>` to list any
      false "verified" claims (evidence missing / self-graded) — these are downgraded.
   c. **Launch gate:** if `completeness-report.json.critical_unverified` is non-empty, the product
      is NOT launch-ready regardless of node count — surface those critical flows as needing real
      verification. Do not call the product complete on self-attestation.
   d. Read `.allforai/bootstrap/assumed-decisions.json` + any UNRESOLVED, then stop.

3. On `needs_diagnosis`:
   a. Read `hardFailures` (always non-empty — a stuck graph carries a synthesized `deadlock`
      finding) + `workflow.json` `diagnosis_history`.
   b. GLOBAL cap (fix L1): if total entries in `diagnosis_history` ≥ 5, mark UNRESOLVED and
      stop — this catches oscillating root causes the per-cause cap misses.
   c. Run `${CLAUDE_PLUGIN_ROOT}/knowledge/diagnosis.md`: locate the root-cause node
      (use `suspected_root_node` when present). This is autonomous — never ask the user.
   d. Per-cause cap (the policy unit-tested as engine-core `convergenceCheck`): if the same root
      cause already appears ≥2 times in `diagnosis_history`, mark it UNRESOLVED, write best-effort
      output + TODO, and stop.
   e. Otherwise apply the repair plan WITH CASCADE (fix C2):
      `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/compute_reset_closure.py .allforai/bootstrap/workflow.json <root_id...>`
      → remove the returned closure (root + transitive downstream) from the `transition_log`
      completed set, then RESUME the engine
      (same session: resumeFromRunId; cross-session: re-invoke — workflow.json idempotency
      skips already-completed nodes).

4. Repeat until `complete` or an UNRESOLVED stop.

This template is CC-only. Codex/OpenCode keep their existing markdown loop (frozen).

## Recording Transitions

After each node completes or fails, append to workflow.json transition_log:

```json
{
  "node_id": "<node_id>",
  "status": "completed | failed",
  "started_at": "<ISO timestamp>",
  "completed_at": "<ISO timestamp>",
  "artifacts_created": ["<file paths>"],
  "error": "<one line, only if failed>"
}
```

## Session Resume

On first iteration if transition_log is non-empty:
1. Run check_artifacts.py to see current state
2. Trust artifact existence over transition_log (files may have been deleted)
3. Continue from where things stand

## Safety (warnings, not blockers)

- Same node fails 3 times → **before warning**, check `workflow.json.diagnosis_history` for that node:
  - If any entry has `"out_of_scope": true` → mark workflow halted, output TODO list, do NOT retry or ask user
  - If 2+ entries share the same `root_cause.node` → convergence cap reached, mark UNRESOLVED, output TODO list, halt
  - Otherwise → warn user, ask if they want to continue
- 5 iterations with no new artifacts → output current state + TODO list
- Single node running > 10 minutes → warn but don't kill

## Termination

- All nodes' exit_artifacts are ready → success report
- concept-acceptance verdict = needs_iteration → output acceptance-report.md, present iteration options (fix/re-bootstrap/accept), stop
- User interrupts → transition_log is already saved, resume with /run
- Safety warning acknowledged → continue or stop per user choice

## Post-Completion

**Run regardless of success or early stop:**

0. **Run log summary:**
   Run `python3 .allforai/bootstrap/scripts/summarize_run_log.py . --write-report`.
   Keep `.allforai/bootstrap/run-log.jsonl`, `.allforai/bootstrap/run-summary.json`,
   and `.allforai/bootstrap/run-summary.md` as the auditable production trace.

1. **Mark concept drift resolved (if applicable):**
   If `.allforai/product-concept/concept-drift.json` exists AND `resolved = false`
   AND all nodes completed successfully: set `"resolved": true` and write back.
   If /run stopped early or failed: leave `resolved = false` (drift still pending for next /bootstrap).

2. **Learning extraction:**
   Read `.allforai/bootstrap/protocols/learning-protocol.md`.
   Check `workflow.json.corrections_applied[]` and `diagnosis_history[]`:
   - If both empty: no learning to extract, skip.
   - For each entry in `corrections_applied[]`:
     * Extract: node, what_was_wrong (root_cause), fix_applied
     * Classify per learning-protocol.md type (mapping-gap / discovery-blind-spot / convergence / safety / other)
     * Write to `.allforai/bootstrap/learned/<category>.md` per learning-protocol.md File Naming Convention
   - For each entry in `diagnosis_history[]`:
     * Extract root_cause pattern and gaps_found domains
     * If the gap was not caught by the expected capability node → classify as "blind-spot"
     * Write to `.allforai/bootstrap/learned/blind-spots.md` (append, do not overwrite)

3. **Feedback proposal:**
   Read `.allforai/bootstrap/protocols/feedback-protocol.md`. If learning
   extraction found a universally useful meta-skill issue, run:
   `python3 .allforai/bootstrap/scripts/record_meta_skill_feedback.py . --category "<category>" --message "<deidentified failure pattern>"`
   This must not ask the user mid-run. Prefer a writable local `myskills`
   repository; only fall back to anonymous GitHub issue draft/auto mode when no
   local repo is available.
~~~
