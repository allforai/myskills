# T15 / large-code-local-button / codex — independent semantic evaluation

Role: evaluator. Read-only over the campaign tree; the only file written by this
evaluation is this report. Gate reproductions ran on scratch copies of the
preserved archives and of the project, never on the campaign tree itself.

## Verdict

**Not a host pass. Semantic requirements substantially met with one substantive
scoping defect; evidence not yet fully admissible.**

Evaluation complete is not scenario passed. The cell should stay `unverified`
in the ledger until the admissibility fixes in §6 land. Nothing found here
requires a fresh actor run: every defect is either a recording/normalisation gap
that can be closed from preserved material, or a candidate-side finding for the
producer, or a bounded question-quality observation on the actor's first turn.

## 1. Identity and what was actually under test

| Item | Observed | Method |
|---|---|---|
| Candidate root | `/private/tmp/meta-intent-host-campaign.XX6yRo/T15/candidate` | `receipt.json.candidate_source_root` |
| `source_commit` / `production_commit` | `e30ccc7cec9120815f0d9bc92204adf465f666d4` | `candidate-manifest.json` |
| Recorded `tree_sha256` | `c1114a94d89c2ea8d8e7bc8c496576b9750957e347769980dc75dee006704fc4` | matches the launch-request binding |
| Manifest coverage | 504 files, 19 symlinks, 523 git modes | recomputed |
| Manifest-tracked bytes vs disk | **0 changed, 0 missing** | independent SHA-256 sweep |
| Git modes / symlink targets vs disk | **0 mismatches** | independent `lstat`/`readlink` sweep |
| Actor `loaded_assets` | **57 / 57 verified** against the pinned manifest *and* current bytes; none outside the candidate root | independent sweep |
| Native entry in the loaded list | yes — `codex/meta-skill/SKILL.md`, `526dc095…c6065` | independent sweep |

Session: `CODEX_THREAD_ID 01a08383-76f9-70e0-a3ea-f7fc25225b96`, Orca terminal
`term_11383f06-4e76-480d-8a98-dd22d88007ef`, primary dispatch `ctx_d19bc67f4ff4`
(task `task_1f6124b04caa`), BOM turn `ctx_2492b68bb8e4` (task `task_eb55ae29c116`),
recovery turn `ctx_ecaa06f0f8de` (task `task_591de0cf0ae7`). Message ids across
all three dispatches run continuously in the `01a0839x` series, so the three
turns are one underlying Codex thread, not three independent contexts.

The actor read `candidate/claude/**` from a Codex host. That is correct, not
cross-cell contamination: the Codex adapter delegates to the canonical Claude
knowledge and `actor-input.md` instructs resolving canonical references in the
candidate root. No path from another scenario cell, from `replan-2` evaluator
material, or from test sources appears anywhere in the five captures.

### 1a. Campaign hygiene finding — the "immutable" export was written into

`candidate/claude/meta-skill/scripts/orchestrator/__pycache__/product_intent.cpython-314.pyc`
exists on disk and is **not** in the manifest (birth time `2026-09-09T08:41:09`).
Consequences:

- Recomputing the aggregate over the export now yields
  `bea857f35beb91a476c1b407de78acb7be78828fbe5965f323a2f579d12fc310`, not the
  recorded `c1114a94…`. The recorded fingerprint is no longer reproducible from
  the export — the exact failure mode `evaluator-private.md` already flags for
  the superseded `88e7beca` packet.
- `admit_evidence.py` does not detect it. It iterates `git_modes` and the
  receipt's `loaded_files`; an *added* untracked file inside the candidate root
  is invisible to every one of its checks.

This does **not** taint this cell. The file was created at 08:41, after this
cell's last turn (08:36), and all 57 assets the actor read still hash correctly.
It is a campaign-level invariant break that will mislead any later recomputation.

## 2. Was the initial reconfirmation necessary, or a needless interview?

**Necessary under the candidate's own documented protocol, correctly bounded in
scope — but wider in content than it needed to be, with a candidate-side cause.**

The fixture recorded (`before-answer-001.tar.gz`):

- `.allforai/product-concept/decision-journal.json` — schema 1.0, batch
  `export-choice`, `chosen` = "Only signed-in merchant account, current filters,
  id/status/total columns", `rationale` = "Prevent cross-account disclosure",
  no `intent` payload.
- `.allforai/bootstrap/local-requirements.json` — a hand projection, `export`
  revision 1, `status: confirmed`, goal "Export the currently filtered merchant
  orders as CSV", pointing at that journal decision.

The actor copied the candidate's `product_intent.py` and ran `{"operation":"resume"}`
(capture-001, msg 11). The candidate returned the item as
`"status": "pending"`, `"pending_reason": "journal choice does not record this
requirement's goal and reason"` (capture-001, msg 12 — verbatim in the raw page).

Why: `candidate/claude/meta-skill/scripts/orchestrator/product_intent.py:374-388`
accepts a journal decision without an `intent` payload only when
`decision.chosen == item.goal` **and** `decision.rationale == confirmation.reason`.
Here the rationale matched; the `chosen` string ("…signed-in merchant account,
current filters, id/status/total columns") is a *rules* statement while the
projection's `goal` is a paraphrased sentence, so string equality failed and the
item fell into the mismatch branch.

`candidate/claude/meta-skill/knowledge/product-intent-confirmation.md:47-54,101-103`
states the intended semantics: a legacy projection whose journal decision lacks
the full `intent` payload "needs one explicit `confirm` decision, **not a
whole-product interview**, before freeze." So one narrow confirmation turn here
is the designed behaviour, not an actor invention. Judged against that:

- **Bounded correctly.** One question, local export only, no target-users /
  problem / value / monetisation interview, no proposed redesign, no product
  summary. The 240 unrelated storage-view files and the other five app surfaces
  are never opened or discussed. Route recorded as `task_route: "local-change"`.
- **Content wrong in both directions.** The question asked the user to
  re-confirm exactly what the journal already records (account boundary,
  current filters, id/status/total) and asked **nothing** about the four things
  that genuinely were not recorded anywhere: button placement, all-matching-rows
  vs current page, header row, empty-results message. The user's reply supplied
  all four unprompted. Had the reply been a bare "confirmed", the plan would
  have frozen a contract missing four decided behaviours.

Split of responsibility:

- **Candidate (C1).** The doc defines a `legacy_reuse` field that names the
  evidenced field (`goal`) and the unconfirmed ones (`scope`, `business_rules`,
  `acceptance`) — but only on the *matching* branch. On the mismatch branch the
  actor gets one opaque sentence and no per-field evidence breakdown, so it
  cannot tell that the account boundary and the filter rule are in fact
  user-recorded verbatim while the goal wording and the UI details are not.
  The all-or-nothing verdict is what pushes a re-ask of settled scope.
- **Actor (A1).** Even without a breakdown, the journal text was in front of it
  (it quoted the owner decision in the question itself). It could have asked the
  delta — "these three are recorded; placement, paging, header, empty state are
  not, please decide" — and did not.

Not a needless interview; a correctly-fenced confirmation carrying the wrong
payload. Impact was contained, not avoided.

## 3. Requirement-by-requirement

### 3.1 Source preservation — PASS

Independent sweep of all 255 paths in `source-before.json` against the current
project tree: **0 missing, 0 changed** except the two decision-record files that
the bootstrap decision surface legitimately owns
(`.allforai/bootstrap/local-requirements.json`,
`.allforai/product-concept/decision-journal.json`). **0** new files outside
`.allforai` / `.git` / `.codex`. No product code was created, edited or removed.
`receipt.source_unchanged` independently pins the three orders-surface files and
matches.

### 3.2 Local route, no imposed redesign — PASS

`workflow.json.task_route = "local-change"`, `goals = ["implement","product-verify"]`,
five nodes, all `profile_slice.areas = ["orders"]`, all
`source_inputs = {apps/merchant-web/app/orders/page.tsx, apps/merchant-web/next.config.ts,
services/api/orders.py}`. Every node spec carries an explicit
`Non-goals: other merchant features, other client platforms, unrelated service
domains, product reconstruction, redesign and new export product options`, and
`Do not scan the entire repository`. No product-concept / experience-map /
whole-product stage was generated.

### 3.3 Scope propagation into requirements and node acceptance — PASS (content-level, not word-level)

Revision 2 (post-answer) and revision 3 (post-BOM) carry all six rules and all
six acceptance clauses. Propagation is enforced executably, not by keyword:

- `scripts/check_export_contract.py` asserts revision + `confirmed` status, the
  BOM business rule, `visual-acceptance.json.requirement_revision`, that every
  node's `requirement_refs` and `source_inputs` are exactly right, that each node
  spec contains all six structural sections, `EF BB BF`, `utf8-bom`,
  a current-filter phrase and `signed-in` — and it parses the *actual fixture
  source*, asserting `list_orders(account, status)` and that the orders page
  renders `order.id/status/total`. A stale or invented contract fails it.
- `scripts/check_export_delivery.py` requires
  `acceptance_passed == {account-isolation, all-filtered-pages, csv-schema,
  utf8-bom, button-placement, empty-results}`, reads the raw downloaded bytes,
  rejects a missing BOM *and* a duplicated BOM, then decodes `utf-8-sig` and
  asserts the header is exactly `['id','status','total']` with 3 columns per row,
  plus hashed evidence, a verifier distinct from the generator, and two
  independent visual reviewers distinct from the screenshot producer.
- `visual-acceptance.json` names placement, empty-state and readability criteria
  across `loaded/export-success/empty/error/permission` and two viewports.

No fabricated user authority: every recorded decision traces to a journal batch
with a `user_reference` naming the real dispatch and timestamp, and
`decision-coverage.json` explicitly states it "grants no product authority."

### 3.4 Executable plan — PASS, honestly labelled not-ready

Five nodes, acyclic, `hard_blocked_by` chain implement → stitch → verify →
repair → accept, per-artifact `validation_commands`, generated
`.codex/commands/run.md` (177 lines) and `.allforai/codex/flow.py` (840 lines).
Reproduced on a scratch copy of the current project:

```
check_decision_inputs.py .              exit 0  OK: decision_inputs present and every decision is wired to a consumer
validate_bootstrap.py .allforai/bootstrap exit 0  {"errors": [], "passed": true}
validate_dag_structure.py .             exit 0  OK: DAG structurally sound (no cycles, no missing deps)
validate_unattended_readiness.py .      not_ready — blocker: missing_runtime_command
```

`not_ready` is an **honest fixture prerequisite, not a candidate or actor
failure**: the synthetic materials supply no merchant-web launch command and no
authenticated orders wiring. The actor recorded
`authenticated_orders_connection: declared_unchecked` rather than asserting it,
and both reports say execution must not start. No `.allforai/bootstrap/artifacts/`
directory exists — nothing was executed or marked complete.

### 3.5 BOM contrast: record before plan update, then pause — PASS

capture-bom-001 (`ctx_2492b68bb8e4`, msgs 41-49): the actor re-read
`local-requirements.json`, ran `resume`, recorded the choice through the
candidate CLI as `export-utf8-bom-ctx_2492b68bb8e4` / revision 3 with
`user_reference` naming the dispatch, hashed `workflow.json`,
`bootstrap-profile.json` and all node specs **before and after** the write and
asserted they were unchanged, then sent `worker_done` — "Paused before updating
the plan… the existing plan still references revision 2 and awaits
reconciliation when resumed." It did not reconnect despite the pause, so the
contrast is **complete**, not manufactured.

Archive states confirm it: `before-bom-contrast.tar.gz` = rev 2 confirmed;
`after-bom-before-plan.tar.gz` = rev 3 confirmed while `workflow.json` still
carries five `"revision": 2` refs and zero rev-3 refs.

### 3.6 Public gate rejection before, recovery after — PASS (reproduced independently)

Reproduced by this evaluator on scratch extractions of the preserved archives,
using the project's own copied gate. **Labelled evaluator CLI evidence, distinct
from host dialogue.**

```
# after-bom-before-plan.tar.gz  (decision recorded, plan not yet updated)
$ python3 .allforai/bootstrap/scripts/check_decision_inputs.py .
BLOCKED: decision wiring incomplete:
  - stale_requirement: implement-export: export: reference does not select the current requirement revision
  - stale_requirement: stitch-export:   export: reference does not select the current requirement revision
  - stale_requirement: verify-export:   export: reference does not select the current requirement revision
  - stale_requirement: repair-export:   export: reference does not select the current requirement revision
  - stale_requirement: accept-export:   export: reference does not select the current requirement revision
exit 1
```

Orphan control — the same gate on `before-bom-contrast.tar.gz`, where the
historical `export-choice` batch and superseded revision 1 are still present but
no new decision is outstanding:

```
$ python3 .allforai/bootstrap/scripts/check_decision_inputs.py .
OK: decision_inputs present and every decision is wired to a consumer
exit 0
```

So the gate blocks on a genuinely applicable unconnected decision and does
**not** turn the historical journal alone into an orphan. Both directions of the
oracle are satisfied. This matches the coordinator's reported reproduction; I
reproduced it independently rather than accepting the claim.

Post-recovery (current project, scratch copy): `check_decision_inputs.py` exit 0,
`validate_bootstrap.py` `{"errors": [], "passed": true}`, `validate_dag_structure.py`
exit 0. `validation-results.json` and `bom-validation-results.json` preserve the
actual `argv` / `exit_code` / `stdout` / `stderr` of every run, including the
`exit 1` of `validate_unattended_readiness.py` — no invented green.

### 3.7 Recovery preserved unrelated history — PASS

Structural diff, `before-bom-contrast` vs current `workflow.json`: node ids
identical; `transition_log`, `diagnosis_history`, `corrections_applied`,
`planning_notes`, `expanders`, `task_route`, `goals` byte-identical; with the
revision field normalised, **every node differs in zero keys**. Only
`reconciliation_applied` grew (0 → 5 entries, one per node, each with a reason).
Node-spec diffs are surgical: one encoding sentence, the acceptance-key list, an
appended BOM section — plus a genuine correction (pre-BOM `implement-export` and
`stitch-export` still said "Final verify-export…" after the three-way split; the
update corrected them to "Final accept-export"). All three journal batches and
both superseded revisions are retained, not rewritten.

## 4. Candidate findings for the producer

**C1 — `product_intent.py` mismatch branch gives no per-field evidence, forcing a
re-ask of settled scope.** Evidence:
`candidate/claude/meta-skill/scripts/orchestrator/product_intent.py:374-388`
(`_journal_payload`) raises a single opaque `ValueError` when
`decision.chosen != item.goal`, while
`candidate/claude/meta-skill/knowledge/product-intent-confirmation.md:49-54`
promises a `legacy_reuse` breakdown naming evidenced vs unconfirmed fields — but
only on the matching branch. Minimum fix: emit `legacy_reuse` on the mismatch
branch too, carrying the recorded `chosen`/`rationale` text and a per-field
evidenced/unconfirmed map, so the caller can ask the delta instead of the whole
item. Strict string equality on `goal` also means a semantically identical
paraphrase is treated exactly like a fabricated projection; at minimum the
`pending_reason` should say which side mismatched and quote both strings.

**C2 — G0 routes a purely internal restructure to a user turn.**
`candidate/claude/meta-skill/knowledge/bootstrap-audits.md:223-252` ("Queue
non-trivial restructures for Phase A confirmation") caused the third of three
user turns in this cell to be spent confirming a QA → repair → acceptance split
that changes no product decision; the actor said so itself in the question. In a
scenario family whose premise is minimal interviewing on a local change, that is
an avoidable interview cost. Minimum fix: distinguish restructures that change
product scope or acceptance content (confirm) from those that only change
internal node granularity with identical acceptance (record in
`granularity-audit.json` and report, do not ask).

**C3 (minor) — capability naming is not discoverable from the goal noun.**
`receipt.failed_asset_lookups` records one miss:
`candidate/claude/meta-skill/knowledge/capabilities/implement.md`. No such file
exists and nothing in the candidate references that path — the actor guessed it
from `goals: ["implement"]` and then correctly resolved to the `translate`
capability. It reported the failed lookup honestly rather than inventing
content. A one-line goal→capability map would remove the guess.

## 5. Actor observations

**A1 — first question inverted the necessary/unnecessary split.** See §2. Real
defect, contained impact, contributing candidate cause (C1).

**A2 — receipt written in a shape the campaign's own admission CLI rejects.**
`receipt.json` uses `session_identity` / `candidate_source_root` / `loaded_assets`
/ `transcript`, while `admit_evidence.py` reads `session_id` / `source_root` /
`loaded_files` / `raw_dialogue`. `transcript.exported_path` is `null` with
`metadata_unavailable: ["Native transcript filesystem path not queried"]` — an
honest report of something not looked up, but it leaves no dialogue digest bound
to the receipt. The actor-input did not specify the CLI's field names, so this is
a coordination gap as much as an actor error.

Positive observations worth recording: it hashed the plan before and after the
BOM write to *prove* the pause rather than asserting it; it recorded
`declared_unchecked` instead of claiming auth wiring; it recorded the failed
asset lookup; it wrote "This is a planning outcome, not an export implementation
or product-verification claim" into its own report; and it invented no product
decision beyond the four the user supplied.

## 6. Evidence admissibility — why this is not yet a pass

Run against the cell as it stands:

```
$ python3 …/T15/admit_evidence.py …/candidate-manifest.json …/candidate \
      …/codex/large-code-local-button/receipt.json
{"status": "unverified",
 "reasons": ["candidate-mismatch", "missing-raw-dialogue", "missing-session-identity"], …}
exit 1
```

Normalising the same receipt into the CLI's field names in scratch (nothing
written to the campaign tree) and binding `capture-001/page-0001.stdout.json` as
`raw_dialogue` yields `{"status": "admissible-for-evaluation", "reasons": []}`,
exit 0; corrupting one `loaded_files` hash correctly yields
`["candidate-mismatch","changed-candidate"]`, exit 1. So the material *can* be
admitted — it simply has not been.

Open admissibility gaps:

1. **No normalised receipt on file.** The cell currently has no CLI-admitted
   identity record. Fix: the coordinator normalises the actor receipt (preserving
   the original) and re-runs `admit_evidence.py`.
2. **No raw-dialogue digest bound anywhere.** Fix: bind the capture pages by
   path + SHA-256. Note the CLI's `raw_dialogue` takes a *single* path, while
   this dialogue spans five captures × two pages; a single-page binding proves
   one page. Minimum fix on the CLI: accept a list, or a manifest of pages with a
   chained digest.
3. **Clipping on every page.** All five `capture.json` indexes carry
   `full_dialogue_proven: false` and runtime warnings — "Oversized transcript
   text was clipped", "Oversized tool input was clipped". This is
   **unavailable/clipped dialogue evidence, not an actor or candidate flaw**, but
   it means the transcript alone cannot prove byte-completeness of what the actor
   ran. The semantic judgements in §2-§3 do not rest on clipped regions: they
   rest on the on-disk artifacts, the preserved archives, `validation-results.json`
   and my own re-runs of the gates.
4. **Window limits.** `capture-bom-001` page 1 reports `transcript.limited: true`
   and `initial-window-limited`; `capture-bom-recovery-001` reports "Older
   transcript messages were omitted from the bounded archive."
5. **Unexplained source-identity change.** capture-001/002/003 and
   capture-bom-001 record `sourceIdentity vDJd2AGX4hbg1NVJ4o6zB8QcAhz5qUNI`;
   capture-bom-recovery-001 records `gcD-AW8uqkrzd-pPZApS-iRhAD7uQkxG` for
   `ctx_ecaa06f0f8de`. Message-id chronology (`01a0839x`, continuous, and the
   recovery page replays the earlier turns) says this is the same underlying
   Codex thread, so I read it as an Orca-side identity record rather than a
   session break — but the discrepancy is unexplained in the record and should
   be reconciled before the ledger credits this as one continuous session.
6. **Nested audit dialogue is unrecoverable.** `receipt.audit_agents` names
   `/root/intent_audit` and `/root/plan_audit` with `session_uuid: null`, and
   their `followup_task` payloads are Fernet-encrypted in the transcript. Their
   findings are self-reported. Partial corroboration exists on disk
   (`granularity-audit.json`, `bootstrap-node-expansion-qa-report.json`, and the
   visible `accept-export.md` edit that the actor attributed to the audit), but
   the audit reasoning itself is not admissible evidence.
7. **Campaign hygiene, §1a.** `__pycache__` inside the candidate export.
   Minimum fix: add an extra-file check to `admit_evidence.py` (any regular file
   under the candidate root absent from `sha256`/`symlinks` is a reason), export
   the candidate read-only, and set `PYTHONDONTWRITEBYTECODE=1` for anything that
   imports from it.

## 7. Minimum fixes, ranked

| # | Owner | Fix | Evidence |
|---|---|---|---|
| 1 | coordinator | Normalise this receipt to `session_id`/`source_root`/`loaded_files`/`raw_dialogue`, bind the capture pages by SHA-256, re-run `admit_evidence.py` | §6.1-6.2 |
| 2 | producer (#9/#10 surface) | `product_intent.py:374-388` — emit `legacy_reuse` with a per-field evidenced/unconfirmed map on the mismatch branch, and quote both strings in `pending_reason` | §2, §4 C1 |
| 3 | evaluator tooling | `admit_evidence.py` — reject untracked extra files under the candidate root; accept a multi-page `raw_dialogue` | §1a, §6.2, §6.7 |
| 4 | coordinator | Reconcile the `sourceIdentity` discrepancy on `ctx_ecaa06f0f8de` before crediting one continuous session | §6.5 |
| 5 | producer | `bootstrap-audits.md` G0 — do not route product-neutral granularity restructures to a user confirmation turn | §4 C2 |
| 6 | producer | Add a goal→capability map so `implement` resolves without a guessed path | §4 C3 |

None of these require re-running the actor. Fixes 1, 3 and 4 close the
admissibility gap from preserved material; 2, 5 and 6 are candidate corrections
that, per `evaluator-private.md`, would require a new accepted candidate and
fresh affected host executions **only if** the producer changes candidate bytes.

## 8. Reproduction commands used by this evaluation

All run on scratch copies; the campaign tree was not written to.

```
tar xzf …/T15/codex/large-code-local-button/before-answer-001.tar.gz    -C <scratch>/ba1
tar xzf …/T15/codex/large-code-local-button/before-bom-contrast.tar.gz  -C <scratch>/bbc
tar xzf …/T15/codex/large-code-local-button/after-bom-before-plan.tar.gz -C <scratch>/abp
cd <scratch>/abp && python3 .allforai/bootstrap/scripts/check_decision_inputs.py .   # exit 1, 5x stale_requirement
cd <scratch>/bbc && python3 .allforai/bootstrap/scripts/check_decision_inputs.py .   # exit 0
cd <scratch>/cur && python3 .allforai/bootstrap/scripts/check_decision_inputs.py .   # exit 0
cd <scratch>/cur && python3 .allforai/bootstrap/scripts/validate_bootstrap.py .allforai/bootstrap
cd <scratch>/cur && python3 .allforai/bootstrap/scripts/validate_dag_structure.py .
cd <scratch>/cur && python3 .allforai/bootstrap/scripts/validate_unattended_readiness.py .
python3 docs/grillstorm/meta-intent/replan-2/T15/admit_evidence.py \
    …/candidate-manifest.json …/candidate …/codex/large-code-local-button/receipt.json
```

Raw dialogue was read from the preserved capture pages
(`capture-001..003`, `capture-bom-001`, `capture-bom-recovery-001`,
`page-000{1,2}.stdout.json`), not from any paraphrase.
