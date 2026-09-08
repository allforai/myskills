# T11/T12 standards recheck

Candidate `90257b15` (HEAD verified equal, tree clean) reviewed on the fixed diff `5cab4f8f...HEAD`, standards axis only. Independently executed: `tests/unit` 495 passed, `codex/meta-skill/test_flow.py` 24 passed; Claude/Codex `scripts/orchestrator` copies byte-identical. Scratch probe (temp project, no Git): completed out-of-scope node → `legacy/undeclared`; scoped node without `source_inputs` → `missing/undeclared`, not admitted; `../x` entry → `invalid`. No `codex-*-visual-review`, `claude-code-visual-review`, `blocked_by_missing_codex_cli` introduced in the diff.

## Documented-standard breaches

Prior report disposition:

1. **Fixed.** `codex/meta-skill/AGENTS.md:40` now lists `product_intent.py` and `evidence_freshness.py`.
2. **Addressed by repo rule.** `validation-commands.md` is the current control plane; frozen task names stay historical. Repo rule overrides.
3. **Accepted by repo rule.** `input-freshness.md:33–51` remains a numbered walkthrough; `validation-commands.md` declares it the public API lifecycle. Not re-raised.
4. **Open nit, no rule.** `codex/meta-skill/skills/bootstrap.md:134` blank line still splits the helper list.

New, soft:

5. **`orchestrator-template.md:92` vs `check_artifacts.py:427–441`.** The doc says retained legacy nodes report `undeclared` as a warning only. Code marks every legacy node `invalid` (readiness then emits `stale_evidence`, not a warning) whenever any sibling declaration is malformed or evaluation raises. Probe confirmed. Fail-closed is defensible per the docstring; the doc should state it.

No hard breaches.

## Smell judgements

- **Duplicated Code** — `intent_baseline` (`evidence_freshness.py:86–90`) repeats the local-vs-product baseline choice in `_discussion` (`product_intent.py:525–527`). One helper, imported by both.
- **Duplicated Code** — `validate_bootstrap.py:527` `Path(wf_path).resolve().parents[2]` re-derives what `_project_root_from_bootstrap_dir` (`:1231`) already computes.
- **Repeated Switches** — admission→blocker code cascades twice: `_freshness_blocker` (`reconcile_bootstrap_workflow.py:289–295`) and `validate_unattended_readiness.py:329–335`. Export one map from `check_artifacts`.
- **Duplicated Code** — the six-exception tuple now appears eight times in `product_intent.py` (new at `:354`, `:462`). Name it once.
- **Mysterious Name / hidden coupling** — `freshness_states(project_root, workflow)`: the `workflow` argument governs admission only; `evaluate` re-reads `workflow.json` from disk (`check_artifacts.py:433`). The node `check_node_artifacts` appends (`:543–549`) is therefore never evaluated. Probe: passing two nodes while disk held a malformed third yielded `invalid` for all.
- **Mysterious Name** — `all_exist` (`check_artifacts.py:554`) still folds freshness; prior judgement stands.
- **Data Clumps** — `(root, workflow, profile, retained)` and `(label, path)` travel through `_product_contract`/`_local_contract`/`_intent_drift` (`product_intent.py:368–488`). Minor.
- **Speculative Generality** — `freshness_admission(..., project_root=None)` cwd fallback (`check_artifacts.py:390–403`); the only caller passes a root.
- **Carried** — journal-reference validation still triplicated (`_confirmed:302`, `_question_pending:501`, `_discussion:522`); untouched by this diff.

Result: **0 hard breaches, 1 soft, 1 nit; 9 optional judgements.** Static review plus local tests and scratch probes; no host-dialogue evidence claimed.
