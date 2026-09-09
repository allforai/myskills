# T13 independent standards review

Reviewed `git diff ed430dfc...000c9242` (HEAD verified `000c9242`; commits `705ec156`, `e79db1e8`, `000c9242`). Sources: CLAUDE.md, CONTEXT.md, `codex/meta-skill/AGENTS.md`, ADR-0001, ADR-0003. Sibling review report not read. No source, test, Git state or issue touched; the worktree stayed clean.

## Hard breaches

None. Scripts stay under the canonical `claude/meta-skill/scripts` with `codex/meta-skill/scripts` a symlink, matching AGENTS.md "Shared Asset Strategy". No new `.allforai/` directory or Markdown/JSON duplication (CLAUDE.md "Output contract"). ADR-0001's interactive boundary holds: the new prose makes a product-decision owner "a preflight blocker for the next `/run`, never something to answer or invent inside the run". ADR-0003 untouched. `input-freshness.md` remains a cross-node invariant per CONTEXT.md "Protocol", though it is growing narrative.

## Compatibility fix (000c9242)

Verified by trace and isolated run: absent register returns the pre-freshness `{}`; a present corrupt register raises in `observed_reads`, falls through to `evaluate`, which raises again, so every legacy node becomes `invalid` and `freshness_admits` refuses it; the file is left in place. `test_delivery_closure.py`, `test_corrupt_freshness_reads.py` and `test_resume_runs_real_validation_commands` passed (57) in an isolated environment. Automated evidence only; host evidence stays 0/60.

## Baseline smells (judgement calls, not mandatory)

- **Duplicated Code** `evidence_freshness.py` session: three identical `return {'status': 'inconsistent', 'diff': diff, 'repair': repair_responsibility(root, node, diff), 'reason': ...}` hunks, and the document loop repeats the existing `verification_command` subprocess/`failed_verification` shape. Extracting `_inconsistent(diff, reason)` would keep the contract in one place.
- **Duplicated Code** argv validity `isinstance(argv, list) and argv and all(isinstance(s, str) and s ...)` appears in `document_checks`, `document_verification_errors` and the existing publication check. One shared predicate.
- **Shotgun Surgery** `"accepted_with_gaps"` was added to two separate `BLOCKING_STATUS_VALUES` sets (`check_artifacts.py:20`, `reconcile_bootstrap_workflow.py:40`), and the same paragraph landed in both orchestrator templates plus `SKILL.md` and `bootstrap.md`. The canonical `input-freshness.md` could be the single statement the others point to (CLAUDE.md's on-demand `详见` convention).
- **Data Clumps** `{'owner': node['node_id'], 'responsibilities': ['documentation']}` at `evidence_freshness.py:436` builds repair inline, bypassing `repair_responsibility`; `diff`/`repair` also travel together through evaluate, reconcile `_repair_fields` and readiness.
- **Primitive Obsession** `'unobserved-check:' + identity` packs kind and path into one string; `validate_unattended_readiness.py:561` serialises `diff` with `json.dumps` into a message string although `_add` could carry it as a field.
- **Speculative Generality / silent downgrade** `scope_blockers` returns `{}` on `ImportError`, so a missing `product_intent.py` would attribute a pending product decision to the node instead of `interactive-bootstrap`. AGENTS.md lists that helper as always present; either drop the fallback or fail closed.
- **Mysterious Name** `own` (`repair_responsibility`) and `bound` (`evaluate`) hide intent; `non_upstream_diff` and `binding_record` read directly.
- **Divergent Change** `session` now exceeds 120 lines covering observe, read, verify, document checks and re-snapshot.

Result: **0 hard breaches; 8 optional judgements.**
