# Standards review — 47ea2855 (since 2cc347af)

Independent review of `git diff 2cc347af...47ea2855`. Sources read: `CLAUDE.md`, `CONTEXT.md`,
`docs/adr/0001-0003`, `codex/meta-skill/AGENTS.md`, `run-engine/README.md`, the QA skill's
blocker-code convention. Tooling-enforced facts verified once, not reported: sync-check green,
95/95 matches the README count.

## Hard violations

**1. `codex/meta-skill/AGENTS.md:40` — the documented Codex helper set no longer covers what
`/run` loads.** That line enumerates the helpers the generated run and `flow.py` consume
(`product_intent.py`, `evidence_freshness.py`, `validate_unattended_readiness.py`,
`check_artifacts.py`, `record_run_event.py`, `summarize_run_log.py`). This diff adds a
module-level dependency to the run boundary:
```python
from validate_bootstrap import plan_confirmation_blockers   # validate_unattended_readiness.py:14
```
`codex/meta-skill/skills/bootstrap.md:147` copies `validate_bootstrap.py`, so the adapter's own
contract note is what is now stale — the rule is stated in AGENTS.md, and this change was
required to update it in the same pass.

**2. `codex/meta-skill/AGENTS.md:20-27` and `CLAUDE.md` `.allforai/bootstrap/` — new persisted
contract files are undocumented.** `plan-confirmation.json` and `plan-confirmation-journal.json`
are now mandatory Step 3.4 output (`skills/bootstrap/SKILL.md:686`, item 3 of the persist list)
and are read at the `/run` boundary, but neither the Generated Outputs block nor the `.allforai/`
data-bus listing in `CLAUDE.md` names them.

## Judgment calls (smells)

- **Mysterious Name / misleading comment, `engine-core.js:112-113`.** Two comments describing
  `DEFAULT_REPAIR_ATTEMPTS` sit above `MEASUREMENT_SCHEMA`; the constant below is uncommented.
  Mirrored verbatim into `run-engine.workflow.js`, so the defect is duplicated by design.
- **Brittle citation, `product_intent.py:183,202`:** `# bootstrap-audits.md:287` and
  `bootstrap-audits.md:264`. The same commit inserts lines above both anchors; the coverage-audit
  shape now sits at 267-268. Cite the section, not the line.
- **Feature Envy, `validate_bootstrap.py:27`:** imports `product_intent._journal_decision`. If
  provenance resolution is a shared contract, it should be public.
- **Duplicated Code, divergent rigor.** `check_artifacts.recorded_binding` hashes
  `{kind, inputs}` via `evidence_freshness.digest` with shape validation; `flow-template.py:426`
  hashes `{bucket, kind, inputs}` with none. Likewise `artifact_digest` (containment + TOCTOU
  re-stat) vs `file_digest` (`read_bytes`). One name, two guarantees.
- **Mysterious Name, `flow-template.py:348`:** `repair_progress` returns the spent-attempt count
  in a local named `delivered`.
- **`CONTEXT.md` "Protocol … is not a step-by-step tutorial"** vs the new shell recipe
  "Recovering a legacy node's repair route" (`codex/…/orchestrator-template.md:210-232`).
- **Divergent Change:** the commit also rewrites unrelated install/sandbox parity assertions
  (`shared/scripts/orchestrator/check_codex_meta_skill_parity.py`, `smoke_codex_generated_run.py`).

## Compliant

New blocker codes follow the QA skill's "Allowed blocker codes" convention; the three findings of
the 2cc347af standards review (wave `continue`, per-QA budget, the false "already shape-validated"
claim) are each addressed in text and in code.
