# Synchronization module

Spec revision 2. Sources: #8 R20–R30 and #12–#14. Owns I-freshness/I-sync/I-drift and SG-01 observation-to-publication identity as defined in ../program-spec.md. Depends on I-intent; I-drift also consumes I-resume.

#12 delivers content snapshots and baseline versions with dependency-aware invalidation and idempotent unchanged inspection at reconciliation/artifact/readiness seams. #13 closes internal implementation -> fact/docs/contracts -> current evidence -> completion and owner-directed repair. #14 uses that closure for external fact-only/accept/reject/defer transitions and resume. Do not build a second journal or verification engine.

Owned surfaces: existing reconcile_bootstrap_workflow.py/check_artifacts.py/validate_unattended_readiness.py, shared freshness/synchronization helper if justified by invariant ownership, bootstrap planning and node contract guidance, both run templates (Codex flow-template.py; Claude run-engine eligible-node flow), canonical tests. Product baseline authority remains intent's contract; synchronization does not infer confirmation.

Unknown effects are explicitly uncertain, not zero-impact or automatic global rebuild. Input sets exclude generated outputs/logs but retain actual product source and confirmed baseline dependencies. Same commit different dirty content differs; unchanged checks stable. Errors preserve prior accepted state while marking affected evidence unusable. Required docs must be meaningful and current, not empty JSON or cloned old reports. Runtime: change fixture source/baseline, call actual reconciliation and completion/readiness, inspect selected invalidation, repair/sync/revalidate and unchanged rerun on both hosts. Completion includes #17/#18 adversarial platform evidence.
