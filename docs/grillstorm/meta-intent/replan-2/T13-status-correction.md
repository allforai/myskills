# Residual status reporting correction

Base c77323da. Spec review accepted both prior partials; Standards identified
three pre-existing local-reporting omissions: existence_only, not_good_enough,
quality_failed. All already block the authoritative check_artifacts gate.

Added those three values to the Codex flow reporting set. No execution authority,
Run Policy, interface or product decision rule changes. Three literal public
artifact-readiness cases first failed (3 failed/25 deselected in 0.03s), then the
whole Codex flow suite passed (28 passed in 1.24s). Each negative has a passed
report as its positive control. Commit hook runs the unchanged canonical unit
suite; joint integration regression follows acceptance.

Optional duplicated-status-table refactoring and the pre-existing spec-only
frontmatter asymmetry remain separate maintenance observations, not new scope.
The 13 pre-existing typecheck diagnostics recorded in T13-parity-corrections.md
remain; no type cleanup is claimed. Actual host proof remains 0/60.
