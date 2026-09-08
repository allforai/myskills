# Source, baseline and evidence freshness

Bootstrap and resume use the copied `evidence_freshness.py` and
`reconcile_bootstrap_workflow.py` before reusing prior work. Both platforms use
these same helpers. This is a boundary check, not a background watcher.

For each workflow node, declare `source_inputs` as project-relative files,
directories or globs (explicit `[]` only when no product source is relevant),
`input_dependencies` for additional consumed files, and `required_documents`
for generated fact documents that must accompany delivery. Keep existing
`requirement_refs`, `decision_inputs` and `hard_blocked_by` contracts. Declare
other generated files in workflow `generated_outputs`; never classify product
source as generated merely to silence drift. Missing dependency knowledge is
uncertain impact and must be coordinated before affected work can proceed.
Every node that consumes `requirement_refs` must carry `source_inputs`; the
bootstrap, artifact, readiness and reconciliation gates report
`missing_source_inputs` or `invalid_source_inputs` for an omitted or malformed
declaration instead of skipping freshness or passing. Retained completed nodes
outside the current scope, without declarations or recorded observations, keep
their legacy gate behavior and are reported as `undeclared` with no provenance
claimed. A completion label cannot exempt current scoped work; removing a
previously recorded input declaration cannot downgrade verification to legacy.
Reopening historical work requires a declaration.

The source inventory excludes `.allforai`, generated host configuration, Git
metadata, dependency/cache directories and explicitly declared outputs. Inputs
inside those directories still participate when explicitly consumed. Selected
requirement content and baseline scope are fingerprinted independently of
unrelated decisions; the observed baseline version is retained as provenance.
The journal remains the sole product-decision authority. Freshness never accepts
changed implementation as a product decision and never edits that journal.

Use JSON on stdin to `python3 .allforai/bootstrap/scripts/evidence_freshness.py .`:

1. After declaring a node and its inputs, before generating its documents, send
   `{"operation":"observe","node_id":"NODE","kind":"contract"}`. Retain the
   returned content-addressed `observation` token. Generate/reconcile the Node-spec
   and required documents from those observed inputs.
2. If analysis discovers another input, send
   `{"operation":"read","observation":"TOKEN","path":"path/to/input"}`.
   Consume the returned content and replace TOKEN with the returned observation.
   This read is durably retained even when publication subsequently fails.
3. Publish with `{"operation":"publish","observation":"TOKEN",
   "verification_command":["python3","path/to/project-contract-validator.py"]}`.
   Supply a real project-specific validation argv that checks the relevant
   contract/documents; file existence or a no-op is not verification. The helper
   executes it and rejects nonzero exit, missing outputs, or inputs changed
   before/during verification. Contract publication permits execution but cannot
   prove completion; it binds the Node-spec, while required documents and exit
   artifacts are bound only when evidence is published.
4. After implementation has settled, observe again with `kind:"evidence"` before
   running acceptance and refreshing required documents. Publish that token with
   the real project-specific acceptance command. A newly observed snapshot alone
   cannot refresh old evidence: publication runs verification against that input.
   If the source changes, re-observe and actually reverify the new state. A
   missing required document or exit artifact returns `inconsistent` with the
   missing `diff.outputs` and its `repair` owner: passing tests do not complete
   a delivery whose facts are absent.
5. On bootstrap/resume send `{"operation":"check"}`, then run reconciliation
   with `--write`. `check_artifacts.py` consumes evidence freshness and
   `validate_unattended_readiness.py` consumes contract readiness. Do not bypass
   either gate, including when transition history says completed.

Changed source content, path/glob membership, relevant baseline scope, consumed
inputs or generated evidence invalidate direct and transitive consumers. An
unmapped source change is explicitly `uncertain`; coordinate the input mapping
and affected documents rather than claiming zero impact or rebuilding everything.
Revalidating a producer does not refresh its consumers. Reconcile only affected
work, preserve unrelated valid records, and reverify affected consumers in order.
Repeated checks are read-only and identical publication does not rewrite state.

Every withheld completion is an explicit difference with a repair owner, never a
bare warning. `check`, `check_artifacts.py`, the readiness `stale_evidence`
blocker and reconciliation `invalidate` items carry `diff` (changed `files`,
`requirements`, `baseline_scope`, `contract`, `outputs`, stale `upstream`, or an
`unpublished` contract/evidence) and `repair` (`owner` plus the drifted
`responsibilities`). A pending or not-yet-replanned product decision names
`interactive-bootstrap` (`product-decision` / `replan`); a stale producer names
that producer (`upstream`); everything else returns to the owning node
(`implementation`, `documentation`, `verification`, `contract`,
`requirement-sync`). Repair at the owner, re-observe, and republish against the
current inputs; the new evidence restores completion while unrelated valid
records keep their provenance. An approved product change is applied through
its recorded decision, refreeze and replan; it is never asked again and never
rewritten by implementation. `accepted_with_gaps` is a qualified Run Policy
outcome and a blocking artifact status: it cannot become verified or completed.
Unattended execution reports unresolved freshness prerequisites; product choices
return to interactive bootstrap. Existing Run Policy and visual-review rules apply.
