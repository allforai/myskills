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
| Passes after correction | Writing the document and republishing with the real acceptance argv yields `valid`, `diff = {}`, no `repair`, reconciliation `keep`. |
| Explicit diff and repair responsibility | Every withheld completion carries `diff` (`files`, `requirements`, `baseline_scope`, `contract`, `outputs`, `upstream`, `unpublished`) and `repair.owner` (`node`, stale producer, or `interactive-bootstrap`). Readiness `stale_evidence` messages name the owner and diff. |
| Approved product change propagates | `decide adjust` → `stale_requirement`, owner `interactive-bootstrap` (`replan`); `resume` has no pending topics (not asked again); refreeze v2 + `plan` bind the new acceptance into workflow and Node-spec; owner moves to the node (`requirement-sync`, `contract`); republish restores completion. |
| Unattended cannot fabricate a decision | `reopen` → `pending_requirement` blocker, owner `interactive-bootstrap` (`product-decision`); Run Policy `accept` returns `action: accept` but an `accepted_with_gaps` report is a blocking artifact status in both gates. Recovery goes through `confirm` → freeze v3 → `plan` → republish. |
| Unrelated work stays valid | Retained completed `warehouse` branch remains `valid`/`all_exist=true` at every step; prior requirement revisions retained. |
| SG01 inside synchronization | Observe A, change to B before publish → `stale`; re-observe and reverify B → `valid`; repeated checks are byte-identical. |
| Non-blocking review note | All-legacy history with no `evidence-freshness.json` no longer short-circuits past a corrupt `observed-input-dependencies.json`: gates fail closed, file left in place, repair restores. |

Journal authority, one-time Run Policy, ADR-0001 interactive boundary and ADR-0003
are unchanged. No new retry or interview mechanism: ownership derives from the
existing `validate_scope` blockers and freshness records.

## Automated verification (scripted, not host proof)

- `python3 -m pytest claude/meta-skill/tests/unit/test_delivery_closure.py -q` — 6 passed (3 tests × 2 hosts).
- Full `claude/meta-skill/tests/unit` — see the commit hook output recorded in the worker report.
- `uvx mypy --follow-imports=silent --check-untyped-defs` on `evidence_freshness.py`,
  `check_artifacts.py`, `reconcile_bootstrap_workflow.py`: no issues.
  `validate_unattended_readiness.py:313` reports one pre-existing assignment error
  present at `ed430dfc`; not introduced or fixed here.

## Still pending: real Claude/Codex behavior verification

These scripted runs drive the copied CLIs with JSON requests. They do not show
that a real `/bootstrap`, `/run`, Codex `bootstrap` or `flow.py` session reads
`diff`/`repair`, returns `interactive-bootstrap` items to the user, or refuses
to declare documents inside a run. #17 host units (8 scenarios × 2 hosts) and
the SG01 host cell remain open.
