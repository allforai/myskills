# T13 implementation–documentation–acceptance closure (candidate on ed430dfc)

Ticket `issues/13.md`, parent #8. Baseline `ed430dfcebed485b913b54d7785f02cc86998303`
in checkout `meta-intent-t13`. Seam: observable bootstrap/resume I/O and the copied
public gate CLIs (`evidence_freshness.py`, `check_artifacts.py`,
`validate_unattended_readiness.py`, `reconcile_bootstrap_workflow.py`,
`product_intent.py`) on both host copies (`codex/meta-skill/scripts` is a symlink to
the canonical scripts, so one source serves both adapters).

## Delivered behavior

| Acceptance | Observable contract |
|---|---|
| Documentation omission refuses completion | Evidence `publish` with a missing `required_documents` entry returns `inconsistent` (exit 1) with `diff.outputs = {doc: missing}` and `repair = {owner: node, responsibilities: [documentation]}`; `check_artifacts` `all_exist=false`; reconciliation `invalidate` with `repair_owner`/`diff`. Contract publication binds the Node-spec only; documents bind at evidence. |
| Document sync is verified against current source (coordinator blocking finding) | Planning declares `document_verification` per required document: a project-specific argv executing the document's stated facts against the code (fixture: `python -m doctest docs/orders-export.md`, whose examples import and call `orders.list_orders`). Every gate refuses a required document without it (`missing_document_verification`; evidence publish → `inconsistent` with `diff.documents`). Decisive negative: code behavior changes, the document is retained, current inputs are observed, a code-only acceptance passes, and publication still returns `failed_verification` naming the `document`, owner node (`documentation`); the document is not rewritten; gates stay blocked. Touching the document without correcting its facts fails the same way. A record whose documents were not verified under the declared check is `stale` with `diff.documents`. After the last document check the helper rechecks the full current input snapshot (source, upstream, inventory) and outputs: a check that rewrites its own or an upstream source (copied-CLI negative, both hosts) returns `stale`, publishes nothing, and leaves the mutation visible; the producer's evidence is then stale too. A checker script named in the argv must be a consumed input (`unobserved-check:<script>` otherwise, with relative, `./relative` and absolute-in-project spellings normalized to one project-relative identity; files outside the project are never read), and weakening a tracked checker is a changed input. Existing publication-race protection is unchanged. |
| Passes after correction | Writing the document with facts that hold against the code and republishing yields `valid` with `verified_documents`, `diff = {}`, no `repair`, reconciliation `keep`; only the affected record changes and the unrelated branch stays valid. |
| Explicit diff and repair responsibility | Every withheld completion carries `diff` (`files`, `requirements`, `baseline_scope`, `contract`, `outputs`, `upstream`, `unpublished`) and `repair.owner` (`node`, stale producer, or `interactive-bootstrap`). Readiness `stale_evidence` messages name the owner and diff. |
| Approved product change propagates | `decide adjust` → `stale_requirement`, owner `interactive-bootstrap` (`replan`); `resume` has no pending topics (not asked again); refreeze v2 + `plan` bind the new acceptance into workflow and Node-spec; owner moves to the node (`requirement-sync`, `contract`); republish restores completion. |
| Unattended cannot fabricate a decision | `reopen` → `pending_requirement` blocker, owner `interactive-bootstrap` (`product-decision`); Run Policy `accept` returns `action: accept` but an `accepted_with_gaps` report is a blocking artifact status in both gates. Recovery goes through `confirm` → freeze v3 → `plan` → republish. |
| Unrelated work stays valid | Retained completed `warehouse` branch remains `valid`/`all_exist=true` at every step; prior requirement revisions retained. |
| SG01 inside synchronization | Observe A, change to B before publish → `stale`; re-observe and reverify B → `valid`; repeated checks are byte-identical. |
| Non-blocking review note | All-legacy history with no `evidence-freshness.json` no longer short-circuits past a corrupt `observed-input-dependencies.json`: gates fail closed, file left in place, repair restores. |

Journal authority, one-time Run Policy, ADR-0001 interactive boundary and ADR-0003
are unchanged. No new retry or interview mechanism: ownership derives from the
existing `validate_scope` blockers and freshness records.

The document check is host-supplied and project-specific, under the same trust
model as the existing evidence `verification_command`: the helper executes it
against the observed source inside the publication lock and records the argv on
the evidence record. No natural-language oracle is added; a check that is not a
real check is a planning defect the audits inspect, not something the helper can
judge. Two sibling fixtures (`test_dynamic_input_dependencies.py`,
`test_evidence_freshness.py::test_broad_source_selection…`) declared required
documents without any check; each now declares one, with its original assertions
unchanged.

## Automated verification (scripted, not host proof)

- `python3 -m pytest claude/meta-skill/tests/unit/test_delivery_closure.py -q` — 18 passed (6 tests, two of them parametrized, × 2 host copies).
- Full `claude/meta-skill/tests/unit` — see the commit hook output recorded in the worker report.
- `uvx mypy --follow-imports=silent --check-untyped-defs` on `evidence_freshness.py`,
  `check_artifacts.py`, `reconcile_bootstrap_workflow.py`: no issues.
  `validate_unattended_readiness.py:313` reports one pre-existing assignment error
  present at `ed430dfc`; not introduced or fixed here.

## Still pending: real Claude/Codex behavior verification

These scripted runs drive the copied CLIs with JSON requests. They do not show
that a real `/bootstrap`, `/run`, Codex `bootstrap` or `flow.py` session reads
`diff`/`repair`, declares a meaningful `document_verification` rather than a
trivial one, returns `interactive-bootstrap` items to the user, or refuses to
declare documents inside a run. Actual host evidence for this ticket is 0. #17
host units (8 scenarios × 2 hosts) and the SG01 host cell remain open.
