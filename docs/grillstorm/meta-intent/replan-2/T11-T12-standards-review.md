# T11/T12 independent standards review

Reviewed candidate `5cab4f8f` (HEAD verified equal) against base `a37ca40a`; production focus `git diff 88e7beca...0c10c285 -- claude/meta-skill codex/meta-skill` (commits `67446ad1`, `b6357a01`). Executed: `tests/unit` 363 passed, `codex/meta-skill/test_flow.py` 24 passed, engine `node --test` 55 passed. Scratch-project CLI probes below.

## Documented-standard breaches

1. **`codex/meta-skill/AGENTS.md:40` (Contract Notes)** lists the helpers `flow.py` and generated run consume; the list omits `product_intent.py` and `evidence_freshness.py`, which `flow-template.py:579–581` and `input-freshness.md:24` now require. Stale contract.
2. **Task acceptance commands** (`tasks/catalog.md:25–26`, `tasks/intent.md:115`, `tasks/synchronization.md:14`) name `test_bootstrap_resume.py` / `test_bootstrap_freshness.py`; neither file exists. Delivered tests are `test_product_intent_resume.py`, `test_run_policy_session.py`, `test_evidence_freshness.py`. The documented acceptance command does not resolve; root must reconcile names or the control plane.
3. **`CONTEXT.md:20` (Protocol "is not a step-by-step tutorial")**, soft: `knowledge/input-freshness.md:24–45` is copied into `protocols/` yet is a numbered stdin walkthrough. Keep invariants; move method steps to helper usage text.
4. Nit, no rule: `codex/meta-skill/skills/bootstrap.md:133` inserts a blank line that splits the helper list.

ADR checks: no `codex-*-visual-review`, `claude-code-visual-review`, or `blocked_by_missing_codex_cli` reintroduced (grep empty); one-time Run Policy stays before the first node (`orchestrator-template.md:49–56`, ADR-0001:5); input-floor wording retained (`product-intent-confirmation.md:116`).

## Smell judgements (heuristics)

- **Duplicated Code**: journal-reference validation now appears three times: `product_intent.py:278–303` (`_confirmed`), `:386–404` (`_question_pending`), `:410–424` (`_discussion`). T10 flagged two sites; a resolver would collapse all.
- **Duplicated Code / Shotgun Surgery**: identical freshness trigger plus lazy import in `check_artifacts.py:346–348`, `reconcile_bootstrap_workflow.py:222–224`, `validate_unattended_readiness.py:324–326`. Give `evidence_freshness` one `applies()`/no-op `evaluate` entry.
- **Duplicated state**: one-repair semantics persisted twice in `run-policy-state.json` under different keys: `product_intent.py:236–242` (`iteration_policy_consumed`) and `flow-template.py:609–612` (`iteration_repair_started`); engine keeps a third local flag. Flow should trust the CLI's consume result.
- **Mysterious Name**: `check_artifacts.py:353` `all_exist` is now false on stale freshness; the name no longer describes the value.
- **Mysterious Name**: `product_intent.py:83` calls `_discussion(root, local)` only for its raising side effect; extract a named verifier.
- **Divergent Change**: `product_intent.py:216–245` hosts `run_policy`, whose docstring says it is separate from the journal. Docs deliberately call it "the shared copied CLI" (`orchestrator-template.md:52`), so judgement only.
- Stale message: `product_intent.py:687` omits restore/reopen. Reproducer: decide with `{"operation":"bogus"}` → `Only explicit confirm/add/adjust/remove/answer operations are supported`.

Probes (scratch project): `--run-policy` without file → `needs_run_policy`, exit 1; persisted policy → `run_policy_ready`; `--policy-event on_needs_iteration` twice → `auto_fix_once` then `halt_with_report`, as documented.

Static review plus local test execution only; no host-dialogue pass claimed. Uncommitted `execution.json` and `T11-T12-root-verification.md` were neither read nor modified.

Result: **2 hard breaches (doc contracts), 1 soft, 1 nit; 7 optional judgements.**
