# meta-skill First Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Land the first, low-risk batch from the 2026-11-26 expert review of meta-skill: transitions are written by a script, a failed relay is retried once, the retired `human_gate` stops being taught, the entry files stop describing things that no longer exist, and every readiness blocker tells the user what to do.

**Architecture:** One new deterministic CLI (`record_transition.py`) replaces the model hand-editing `workflow.json` on Claude and Pi; the Claude engine relays it the way it already relays `repair_authorization.py`, checks its receipt, and retries a relay that returned nothing. The other three tasks are prose and table fixes, each pinned by a test so the drift cannot come back.

**Tech Stack:** Python 3 (unittest/pytest under `claude/meta-skill/tests/unit`), Node `node:test` (`claude/meta-skill/knowledge/run-engine/tests`), Markdown skill files.

**Spec:** the expert synthesis delivered in this session (items 3, 4, 11, 14, 15 of the 17-item list). Items 1 (repair loop), 7 (upgrade refresh + version stamp) and the rest get their own plans.

## Global Constraints

- Public repo: before every commit scan the diff for project names, home paths, the email local part, ids.
- No CI. Automatic guards go in `.githooks/pre-commit`; a new test directory goes in `shared/suites/suites.txt`.
- Work on `main`, one commit per task, `git add` with an explicit pathspec. No `git stash` / `checkout` / `reset`. Do not push.
- Never hard-code a model name or vendor in a skill.
- Skills state acceptance, not method; keep each skill's guiding-philosophy sections untouched.
- `engine-core.js` is inlined into `run-engine.workflow.js`; after editing the core, resync it the way `sync-check.test.js` expects (run that test to confirm).
- A rule stated in several run templates is a registered clause (`shared/seam-contracts/clauses.json`); after changing its authority text, restamp every copy (`check_clauses.py --hashes`).
- A script `/run` calls must be in the bootstrap copy list on Claude (`skills/bootstrap/SKILL.md` Step 6.2) and Pi (`pi/meta-skill/skills/bootstrap/SKILL.md` §3).

## Review Focus

1. The relay succeeded but the model returned nothing, so the retry runs the CLI a second time → must not leave two identical transitions (Task 1 replay test, Task 2 retry test).
2. A model "returns" a made-up receipt naming another node → the engine must refuse it, not mark the node done (Task 2 receipt test).
3. `workflow.json` is unreadable or has no `transition_log` → the CLI refuses with a reason and exit 1 rather than writing a fresh file (Task 1).
4. A readiness code added later with no action entry → test fails until one is written (Task 4 coverage test).
5. A legacy project that still has `human_gate: true` nodes → the validator and readiness keep handling it; only the teaching text goes (Task 3 leaves `validate_approval_records` and `pending_human_gate` alone).

---

### Task 1: `record_transition.py` — transitions written by code

**Files:**
- Create: `claude/meta-skill/scripts/orchestrator/record_transition.py`
- Test: `claude/meta-skill/tests/unit/test_record_transition.py`
- Modify: `claude/meta-skill/skills/bootstrap/SKILL.md` (Step 6.2 copy list, after the `repair_authorization.py` line)
- Modify: `pi/meta-skill/skills/bootstrap/SKILL.md` (§3 copy list)
- Modify: `codex/meta-skill/AGENTS.md:42` is NOT changed — Codex records in `flow.py` already.

**Interfaces:**
- Produces: CLI `printf '%s' '<json>' | python3 .allforai/bootstrap/scripts/record_transition.py <project_root>`.
  - Input JSON: `{"node_id": str, "status": "completed"|"failed", "artifacts_created": [str], "verification"?: object, "error"?: str, "assumed_decisions"?: [object], "clear_corrections"?: bool}`.
  - Success (exit 0): `{"status": "recorded", "node_id": str, "transition_index": int, "replayed": bool}`.
  - Refusal (exit 1, still prints): `{"status": "refused", "node_id": str|null, "reason": str}`.
- Entry written: `{"node_id", "status", "started_at"?, "completed_at": <UTC ISO>, "artifacts_created", "verification"?, "error"?}` — the `node_id` spelling Claude already writes; readers accept both spellings.
- Replay rule (decided): if the node's latest transition equals the request on every field except `completed_at`, append nothing and answer `replayed: true` with that entry's index. This makes a retried relay safe without an id the engine cannot keep across restarts.

- [ ] **Step 1: Write the failing tests** in `test_record_transition.py` (run the CLI as a subprocess against a temp project with `.allforai/bootstrap/workflow.json`):
  - `test_completed_transition_is_appended_with_receipt` — receipt `status == "recorded"`, `replayed is False`, `transition_index == len(log)-1`; entry has `node_id`, `status`, `artifacts_created`, `verification` verbatim, `completed_at`.
  - `test_same_request_twice_is_a_replay_not_a_second_entry` — second run: `replayed is True`, log length unchanged.
  - `test_failed_transition_requires_error` — `status: "failed"` without `error` → exit 1, `status == "refused"`.
  - `test_unknown_status_is_refused` — `status: "done"` → refused.
  - `test_missing_workflow_is_refused_not_created` — no `workflow.json` → refused, file still absent.
  - `test_other_entries_are_untouched` — pre-existing entries for other nodes byte-equal after the write.
  - `test_assumed_decisions_are_appended` — list appended to `.allforai/bootstrap/assumed-decisions.json` (created as `[]` if absent).
  - `test_clear_corrections_deletes_the_node_file` — `.allforai/bootstrap/diagnosis-corrections/<node_id>.json` removed; absent file is not an error.
- [ ] **Step 2: Run** `python3 -m pytest claude/meta-skill/tests/unit/test_record_transition.py -q` → FAIL (script missing).
- [ ] **Step 3: Implement `main(argv) -> int`** in `record_transition.py`. Write `workflow.json` via temp file + `os.replace` (same pattern as `repair_authorization.py`); preserve key order and `indent=2`.
- [ ] **Step 4: Add the script to both bootstrap copy lists.**
- [ ] **Step 5: Run** the new test file and `python3 -m pytest claude/meta-skill/tests/unit/test_validate_skills.py -q` → PASS.
- [ ] **Step 6: Commit** `fix(meta-skill): 运行记录改由脚本写入，不再让模型手改 workflow.json`.

### Task 2: Engine relays the CLI, checks the receipt, retries once

**Files:**
- Modify: `claude/meta-skill/knowledge/run-engine/engine-core.js` — `commitPrompt` (534), `repairRoutePrompt` (550), `commitNode` (866), the repair-route call (~1301), and every ledger/measure/freshness relay call site.
- Modify: `claude/meta-skill/knowledge/run-engine/run-engine.workflow.js` (resync).
- Modify: `claude/meta-skill/knowledge/orchestrator-template.md` §Recording Transitions (441) and `pi/meta-skill/knowledge/orchestrator-template.md` (511): the JSON shape is replaced by the CLI command as a `snippet:` block; "never edit `transition_log` by hand" stays.
- Test: `claude/meta-skill/knowledge/run-engine/tests/ledger-receipts.test.js`, `prompts.test.js`, `engine-integration.test.js`.

**Interfaces:**
- Consumes: Task 1 CLI and receipt.
- Produces (exported from engine-core.js): `transitionPrompt(request) -> string` (same "Run EXACTLY this command" shape as `authorizationPrompt`), `TRANSITION_RECEIPT_SCHEMA`, `transitionReceiptError(receipt, nodeId) -> string|null`, `relay(agent, prompt, opts) -> Promise<object|null>`.
- `relay` calls `agent` once; if the result is `null`/non-object or `status === "invalid"` (the command could not run), it calls once more with the same prompt and label suffix `:retry`, and returns the second result. It never retries a `refused` or any other answer.
- `commitNode` and the repair-route step use `relay(transitionPrompt(...))`; on `transitionReceiptError` the node is NOT added to `done` and the run stops with a blocking finding `{type: 'unrecorded_transition', detail}`. `relay` also wraps every existing ledger, measure and freshness relay (the replay rules of `repair_authorization.py` and the read-only freshness helper make one retry safe).
- `LIGHT_LABEL` must classify the new `:retry` labels as light; the existing every-label-classified test enforces it.

- [ ] **Step 1: Write the failing tests:**
  - `prompts.test.js`: `transitionPrompt` contains `record_transition.py`, the shell-quoted JSON, and "Do not edit any file yourself"; `commitPrompt`'s old "Append to .allforai/bootstrap/workflow.json" text no longer appears.
  - `ledger-receipts.test.js`: `relay retries once when the relay returns null` (fake agent answers `null` then a receipt → 2 calls, receipt returned); `relay does not retry a refusal` (1 call); `relay gives up after one retry` (2 calls, `null` returned).
  - `engine-integration.test.js`: `a receipt for another node does not complete this one` → finding `unrecorded_transition`, node not in the completed set; `a replayed receipt completes the node`.
- [ ] **Step 2: Run** `node --test claude/meta-skill/knowledge/run-engine/tests/` → new tests FAIL.
- [ ] **Step 3: Implement** the four exports and switch the call sites; extend `LIGHT_LABEL` for `:retry`; resync `run-engine.workflow.js`.
- [ ] **Step 4: Update both run templates' Recording Transitions sections**; run `python3 -m pytest claude/meta-skill/tests/unit/test_template_snippets.py -q` and `python3 shared/seam-contracts/check_clauses.py` (restamp any clause copy the edit touched).
- [ ] **Step 5: Run** `node --test claude/meta-skill/knowledge/run-engine/tests/` and `python3 -m pytest pi/meta-skill -q` → PASS.
- [ ] **Step 6: Commit** `fix(meta-skill): 引擎经脚本记录节点结果并核对回执；中转无回音时重试一次`.

### Task 3: Stop teaching the retired `human_gate`

**Files:**
- Modify: `claude/meta-skill/skills/bootstrap/SKILL.md:589` (example node: drop the field), `:624` (drop "+ human_gate approved if applicable"), `:882` item 17 (delete; renumber the list).
- Modify: `claude/meta-skill/knowledge/bootstrap-art-pipeline.md` (18, 27, 86–95, 181, 301, 309, 321): remove `human_gate` lines and the "approval-records entry" bullets; an art direction choice that needs the user is a Phase A decision feeding `decision_inputs`, as SKILL.md:659 already says.
- Modify: `claude/meta-skill/knowledge/safety.md:32` (delete the carve-out).
- Modify: every other file `grep -rl human_gate --include='*.md' claude/meta-skill` lists (`capabilities/app-design.md`, `capabilities/concept-contract.md`, `capabilities/game-design.md`, `domains/art-tools.md`, `skills/architecture/PACK.md`, `skills/meta-orchestration/20-spec/dynamic-skill-composition/SKILL.md`, `skills/meta-orchestration/40-qa/unattended-run-readiness-qa/SKILL.md`, `tests/prompts/domain-codex.md`): remove the instruction to set it; a sentence that only says it is retired may stay.
- Not changed (legacy projects): `validate_bootstrap.py::validate_approval_records`, readiness `pending_human_gate`.
- Test: `claude/meta-skill/tests/unit/test_retired_human_gate.py`.

**Interfaces:** none.

- [ ] **Step 1: Write the failing test** `test_no_skill_text_tells_bootstrap_to_set_human_gate`: over every `*.md` under `claude/meta-skill` (skip `tests/fixtures`), no line matches `human_gate:\s*true`, `"human_gate":\s*true`, or `human_gate: false`; the only allowed lines mentioning `human_gate` are the ones in SKILL.md's "`human_gate` is not a runtime concept" paragraph and lines containing `retired` / `legacy`.
- [ ] **Step 2: Run it** → FAIL, listing the files above.
- [ ] **Step 3: Edit the files** until it passes.
- [ ] **Step 4: Run** `python3 -m pytest claude/meta-skill/tests/unit/test_validate_art_pipeline.py claude/meta-skill/tests/unit/test_validate_skills.py claude/meta-skill/tests/unit/test_retired_human_gate.py -q` → PASS.
- [ ] **Step 5: Commit** `fix(meta-skill): 删掉仍在教 human_gate 的说明`.

### Task 4: Entry text matches what ships; readiness blockers carry an action

**Files:**
- Modify: `claude/meta-skill/SKILL.md:5` (drop "state machine configurations"), `:18` (`/setup` checks agent CLIs + API keys, no MCP), `:29` (no "state machine"), `:52` (capability count = number of files in `knowledge/capabilities/`, and list the missing ones in the table).
- Modify: `claude/meta-skill/skills/bootstrap/SKILL.md:8` → `# Bootstrap Protocol` (no version; the plugin manifest owns it).
- Modify: `claude/meta-skill/scripts/orchestrator/validate_unattended_readiness.py`: `BLOCKER_ACTIONS: dict[str, str]` — one plain-language "what to do" per code (each distinct code `_add` emits today, 33 at time of writing: e.g. `stale_evidence` → "rerun `/run`; the stale node reruns first", `unverified_external_change` → "run the external-changes step, or rerun `/bootstrap` to rule on it", `dependency_outside_graph` → "add the producing node at `/bootstrap`, or remove the dependency"). `_add` sets `item["action"]`; the Markdown report shows it after each message.
- Test: `claude/meta-skill/tests/unit/test_entry_text_drift.py`, `claude/meta-skill/tests/unit/test_validate_unattended_readiness.py`.

**Interfaces:**
- Produces: every readiness blocker dict gains `"action": str`. The run templates already tell the run to show the blockers from `unattended-run-readiness.md` (clause `run-preflight-readiness`), so no template text changes.

- [ ] **Step 1: Write the failing tests:**
  - `test_entry_text_drift.py::test_capability_count_matches_files` — the integer in `## Capabilities (N)` equals the count of `*.md` in `knowledge/capabilities/`, and every file's stem appears in that table.
  - `test_entry_text_drift.py::test_entry_does_not_describe_retired_parts` — `SKILL.md` has no `state machine configurations`, no `MCP tools`; bootstrap SKILL.md heading has no `v0.`.
  - `test_validate_unattended_readiness.py::test_every_blocker_code_has_an_action` — parse the codes from `_add(blockers, "<code>"` in the source; each is a key of `BLOCKER_ACTIONS` with a non-empty value.
  - `test_validate_unattended_readiness.py::test_report_shows_the_action` — a project with a `missing_workflow` blocker: JSON item has `action`; the `.md` contains it.
- [ ] **Step 2: Run** them → FAIL.
- [ ] **Step 3: Implement** the text edits and `BLOCKER_ACTIONS`.
- [ ] **Step 4: Run** `python3 -m pytest claude/meta-skill/tests/unit/test_entry_text_drift.py claude/meta-skill/tests/unit/test_validate_unattended_readiness.py -q` → PASS.
- [ ] **Step 5: Commit** `fix(meta-skill): 入口说明与实际一致；就绪检查的每个卡点附上解决办法`.

### Task 5: Whole-suite check

- [ ] **Step 1: Run** `bash shared/suites/run_suites.sh` (~9 min) → every group PASS. A failure goes back to the task that owns the file.
- [ ] **Step 2: Report** results; version bump and push wait for the user.
