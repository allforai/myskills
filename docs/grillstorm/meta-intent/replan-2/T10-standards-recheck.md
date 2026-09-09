# T10 independent standards recheck

Reviewed only `git diff b5c66303ce62618bd587ffa0ec705b8af61a6336...HEAD` at `3f66d7acc367cdb39ee12ae10827c8d81298ae0a`: `3f66d7ac fix(meta-skill): separate question identities and preserve retained product work (#10)` (four files).

## Hard violations

None identified against CLAUDE.md, CONTEXT.md, codex/meta-skill/AGENTS.md, ADR0001, or ADR0002 as amended by ADR0003.

The correction stays in canonical Claude assets, consistent with the Codex adapter's **Shared Asset Strategy** (`codex/meta-skill/AGENTS.md`), which intentionally reuses canonical knowledge, helpers, and tests. Workflow and decision artifacts retain the documented `.allforai/` data-bus contract (CLAUDE.md, **Shared Data Contract**). Question validation and retained-history classification remain cross-node validation concerns, consistent with CONTEXT.md's **Protocol** definition and ADR0001's rule that cross-node musts live in protocols, expanders, and validators. No fixed node sequence, unattended human stop, or visual-review policy change is introduced. Tooling-enforced checks are excluded.

## Optional heuristic

- **Duplicated Code:** `claude/meta-skill/scripts/orchestrator/product_intent.py:389–390` and `:394–395` repeat parent-directory creation and JSON-frontmatter/Markdown serialization. Consider selecting the historical or current body first, then sharing the write operation while preserving the existing-file skip for retained nodes. This is a small maintenance suggestion, not a documented-rule violation.

All twelve supplied smells were considered. The extracted `_retained_nodes` already centralizes history classification; the identity validator has a descriptive name. JSON identifiers and dictionaries fit the documented machine-readable data bus and do not independently require domain classes. No additional actionable smell was identified.

Read only the prior `T10-standards-review.md`; its optional journal-resolution duplication and `_item` naming observations are outside this corrective delta and are not recounted as new findings. No other-axis report or root-owned uncommitted document content was read. Static review only: no tests, production edits, commits, or subagents. HEAD was verified unchanged before writing this report.

Result: **0 hard violations; 1 optional heuristic.**
