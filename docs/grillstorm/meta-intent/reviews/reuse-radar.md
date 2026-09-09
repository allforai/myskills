# Reuse radar

- Extend canonical bootstrap + Codex adapter for goal/authority; no second planner.
- Extend existing journal batch schema and check_decision_inputs for stable user decisions; no parallel fact source.
- Extend reconciliation audit state and existing check_artifacts/readiness gates for source/baseline freshness; reconcile empty-report discrepancy under #12/#13.
- Keep semantic inference and user choice in bootstrap agent procedure; deterministic helper validates state, does not invent product meaning.
- Extend existing run engines only for relevant eligibility/closure; preserve human approval machinery and visual architecture.
- Reuse canonical fixture and pytest seams. Keep per-ticket scenario evaluation local unless real shared consumers justify extraction.
