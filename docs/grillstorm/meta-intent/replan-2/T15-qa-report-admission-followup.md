# T15 follow-up — Codex QA report admission

Repairs the part of spec finding 2 that the previous dispatch (ctx_b8ffbd5b1934) left
incomplete. Scope: `codex/meta-skill/knowledge/flow-template.py`, `codex/meta-skill/test_flow.py`,
and the one bullet of `codex/meta-skill/knowledge/orchestrator-template.md` that states the
rule. `validate_bootstrap.py`, `product_intent.py` and `evidence_freshness.py` belong to the
planning worker (ctx_a377a4a12a25) and are read but never written here. No commit.

> `msg_27c1329da958` was not readable from this dispatch's inbox, so the work below follows
> the TASK block's summary of it; the gap was reported as `msg_b43a8c392ad9` before any code
> changed. The coordinator then confirmed that summary and forwarded the original text
> (`msg_c31da8948b81`): *"qa_report_usable checks mtime against started_at but not current
> inputs; touching stale or different-input reports can pass. JSON arrays/empty objects pass
> without positive QA verdict. Use existing input snapshot/freshness and attempt-bound
> artifact evidence, with recent-stale-input/malformed/no-failed-transition negatives and
> legitimate recovery."* Every clause of it is implemented below.

## What was still wrong

The previous fix bound a QA report to the run by `transition_log.started_at` plus the file's
mtime. Three holes remained:

1. **mtime is not provenance.** `touch verify.json` moved the report past any `started_at`
   check, so a verdict produced against inputs that have since changed still opened a repair.
   Nothing tied the report to the inputs it actually judged.
2. **Parseable was treated as a verdict.** `{}`, `{"gaps": [], "test_gaps": []}`, `[]`, or a
   report that states no outcome all passed admission — there was nothing for the repair node
   to act on, and the loop opened anyway.
3. **No failed attempt was required.** `last_dispatch_started_at` returned the newest
   transition's timestamp whatever its status, so a node whose latest attempt *completed*, or
   one with a bare `failed` entry carrying no `started_at`, could still route.

## The rule now

`qa_report_usable` admits a repair only when all three hold:

- **A failed attempt on record.** `last_failed_dispatch` returns `started_at` only when the
  node's *latest* transition is `failed`; a completed latest attempt, a missing entry, or an
  entry with no timestamp all refuse. The report must still be no older than that timestamp.
- **A positive QA verdict.** `qa_verdict` requires a failing status the node itself produced,
  or a non-empty gap/finding list. Empty documents, empty arrays, and non-dict reports carry
  no verdict; `non_qa_report_status` still rejects `failed_env`, `blocked`, `not_ready`,
  `not_generated`, `existence_only` and `blocked_by_*`, the on-disk mirror of the engine's
  `NON_QA_FAILURE_TYPES`.
- **Inputs still current.** `node_freshness` reads the freshness state through the seam the
  independent artifact gate already uses — `check_artifacts.py --node <id> --json`, field
  `freshness` — and `qa_inputs_current` refuses on any input drift: `files`, `requirements`,
  `contract`, `baseline_scope` or `upstream` in the diff, an `external` change that is
  `conflict` or `unverified`, an `uncertain` status, or a `missing`/`invalid` declaration.

The last one needed care. `status: valid` is the wrong predicate for a *failed* QA node: it
can never publish evidence, so requiring `valid` would refuse every repair the loop exists
for. What the rule tests instead is that nothing the report was observed against has moved —
`evidence: unpublished`, changed `outputs` and unverified `documents` are the drift a failed
node necessarily has, and they are the only keys tolerated. A node with `source_inputs`
declared and nothing published shows `contract: unpublished` and is refused: it has no
provenance at all. A project that runs no freshness system yields `freshness: null`, and the
pre-freshness gate applies — the same convention `check_artifacts.freshness_admits` uses.

The freshness call is made last, after the cheap on-disk checks, because it costs a helper
process.

## Verification

Written test-first. Exact commands and observed results:

```
python3 -m pytest codex/meta-skill/test_flow.py -q --tb=short          63 passed (was 49)
node --test 'claude/meta-skill/knowledge/run-engine/tests/**/*.test.js'  82/82 pass (unchanged)
```

**Red before the fix.** A scratch copy of the working tree with only `qa_report_usable`,
`last_dispatch_started_at` and a stubbed `node_freshness` reverted to the pre-dispatch
version (scratch only — no shared production file was swapped) ran the same tests:

```
cd <scratch>; python3 -m pytest codex/meta-skill/test_flow.py -q --tb=no    13 failed, 50 passed
```

Eleven of those are the new admission tests: `test_an_empty_report_carries_no_qa_verdict`,
all five `test_a_report_without_a_positive_verdict_never_opens_repair` cases,
`test_repair_needs_an_actual_failed_qa_attempt[transition_log1]` and `[transition_log3]`,
`test_a_touched_report_whose_inputs_moved_is_not_current`,
`test_a_report_bound_to_no_freshness_record_is_not_current`, and
`test_an_unreadable_freshness_gate_admits_nothing`. The other two,
`test_canonical_entry_is_resolvable` and `test_standalone_installer_keeps_canonical_entry`,
fail only because that scratch holds a partial tree; both pass in the working tree.

`test_repair_needs_an_actual_failed_qa_attempt[transition_log0]` (never ran) and
`[transition_log2]` (failed with no `started_at`) were already green before this dispatch —
they are regression pins for the previous fix, not new coverage.

**Test seam.** The three freshness tests are not stubbed. `freshness_project` copies the real
`check_artifacts.py` and `evidence_freshness.py` the generated runtime ships into the scratch
project, declares `input_dependencies: ['src/orders.py']` on the QA node, and publishes a real
contract observation through the `evidence_freshness.py` CLI. The positive case
(`test_a_current_failed_qa_with_current_inputs_reaches_its_repair`) then runs through the real
`independent_artifact_gate` with no monkeypatch at all. The negatives change the declared input
and `touch` the report, delete the freshness state, and delete `check_artifacts.py`.

The older fixtures keep `gate_by_ready_artifacts`, which now also stubs `node_freshness` to
`None`; those projects ship no freshness state, so the pre-freshness gate is what they are
actually testing, and the helper's docstring says so.

**Git-context scratch.** Because four shared files are being changed concurrently by the
planning worker, all suites were re-run in a scratch `git archive HEAD` tree, `git init` +
committed so git-dependent helpers have real context, carrying only this task's files. Results
in the Isolated run section below.

## Isolated run (git-context scratch)

Scratch built as `git archive HEAD` → `git init` → commit, then this task's files overlaid,
so `git rev-parse` and the rest of the git-dependent helpers have real context:

```
cd <gitctx-scratch>
node --test 'claude/meta-skill/knowledge/run-engine/tests/**/*.test.js'   82/82 pass
python3 -m pytest codex/meta-skill/test_flow.py -q --tb=short             63 passed
python3 -m pytest claude/meta-skill/tests -q --tb=line                    655 passed in 244.65s
```

This also settles the previous dispatch's report, which recorded `653 passed, 2 failed`
because its scratch tree was not a git repository. In real git context both
`test_evidence_freshness.py::test_same_commit_distinct_dirty_states_and_unrelated_baseline_revisions`
cases pass; the suite is 655 passed, 0 failed. The earlier number was a harness artifact, and
it is now verified rather than assumed.

## Residual risk

- **No host proof.** Everything is unit and scratch-project level. No real Codex run drove
  `flow.py`, and the Claude engine path was not exercised on the Workflow harness.
- **A project with no freshness system still admits on mtime alone.** `freshness: null` keeps
  the pre-freshness gate, so a touched leftover report can still open a repair there, provided
  it also has a recorded failed attempt and a positive verdict. Closing that would refuse every
  repair loop in a legacy project; the convention follows `freshness_admits`.
- **`NON_QA_FAILURE_TYPES` and `NON_QA_REPORT_STATUSES` remain two hand-kept lists** in two
  languages, now joined by `qa_verdict`'s positive side. Nothing fails if one drifts.
- **The freshness check costs a helper process per candidate QA node**, and `_pending_state`
  is computed twice per iteration (`first_pending_node` and `blocked_pending_nodes`), so a
  workflow with many declared QA nodes pays it twice. The call is deferred until the cheap
  checks pass, but the duplicate `_pending_state` computation flagged in the standards review
  is still there.
- **`qa_inputs_current` reads a diff shape owned by another file.** If `evidence_freshness`
  adds a new non-input diff key, this rule will read it as input drift and refuse a legitimate
  repair — fail-closed, but it needs coordinating with the planning worker.
