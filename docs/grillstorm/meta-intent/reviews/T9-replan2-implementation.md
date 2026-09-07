# Ticket 9 revised implementation evidence

Fresh attempt from `c1893395b8ea49084a6bbb9a63c671868d236a56` on
`j08069099777/meta-intent-t9`; historical implementation and failure records are retained.

The decision-input gate now recognizes a canonical journal consumed through a
validated scoped requirement. All three public gates resolve journal references
independently of whether provenance paths are requested by the caller. They reject
missing sources, invalid schema, non-user batches, pending/removed choices,
ambiguous batch IDs, invalid fragments, escaping paths, and explicitly superseded
decisions. Other decision files still require consumers; historical inputs remain
consumed by retained completed nodes, including both native history formats.

The shared planning protocol documents the canonical schema 1.0 reference shape.
Codex uses the same script and knowledge assets through its existing source links.
No installed assets, product source, later tickets, or historical records were changed.

## Verification

- Original diagnostic before changes: `python3 /Users/aa/orca/workspaces/myskills/grillstorm-meta-intent/docs/grillstorm/meta-intent/reviews/probes/T9-journal-provenance.py /Users/aa/orca/workspaces/myskills/meta-intent-t9` reported `passed: false`; decision-input gates on both adapters rejected the journal as orphan while the other four gates accepted.
- First public-boundary cycle: `python3 -m pytest claude/meta-skill/tests/unit/test_bootstrap_scope.py -k journal_backed -q` failed twice before implementation, then passed twice.
- Missing/forged provenance cycle: `python3 -m pytest claude/meta-skill/tests/unit/test_bootstrap_scope.py -k forged_journal -q` reproduced acceptance of nonexistent sources, then invalid canonical records, before their corresponding repairs.
- Superseded-choice cycle: `python3 -m pytest claude/meta-skill/tests/unit/test_bootstrap_scope.py -k superseded -q --tb=short` failed on both adapters before repair.
- Final focused run: `python3 -m pytest claude/meta-skill/tests/unit/test_bootstrap_scope.py -q` — **128 passed**. Includes pending requirements, scope enforcement, retained work, malformed history and stale-readiness replacement.
- Final full run: `python3 -m pytest claude/meta-skill/tests -q` — **228 passed**.
- Typecheck: `uvx mypy --follow-imports=silent --check-untyped-defs claude/meta-skill/scripts/orchestrator/product_intent.py claude/meta-skill/scripts/check_decision_inputs.py` — **no issues in 2 source files**. No repository Python typecheck configuration or installed mypy/pyright was found; uvx supplied mypy without modifying project dependencies. This checks untyped function bodies, not a strict whole-repository typing contract.
- Final original diagnostic: **passed**, all six copied public gates exit 0, empty stderr, protected inputs unchanged. Fixture: `/var/folders/yk/1lzd8nn12m50n2l4gd8r28340000gp/T/T9-journal-provenance-2exq1wfd`.
- `git diff --check` — clean.

## Limits and next ownership

These are scripted generated-project inputs and real copied CLI executions on both
adapter asset paths, not actual Claude/Codex dialogue executions. References establish
recorded provenance, not semantic proof that arbitrary natural-language projections
faithfully paraphrase user intent. Explicit `supersedes` links are checked; no natural
language contradiction inference or unrelated journal migration was introduced.
Unknown unconsumed decision files remain fail-closed rather than being assumed historical.
Coordinator owns independent two-axis review, integration and final ticket acceptance;
no subworkers, push, main merge, issue close, or installation were performed.
