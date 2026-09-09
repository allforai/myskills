# T14 standards review — `526ef960` (base `9bade2ff`)

Rules read: `CLAUDE.md`, `CONTEXT.md`, `codex/meta-skill/AGENTS.md`, ADR-0001–0003,
`input-freshness.md`, both `orchestrator-template.md`. Tooling-enforced items are excluded:
`.githooks/pre-commit` runs `py_compile`, the unit suite and the validators. No lint/format
config exists, so line width and layout are not documented rules.
Evidence: `pytest tests/unit/test_external_change_recovery.py -q --tb=short` → **42 passed**
(tmp_path fixtures). Copied-CLI only; real host proof stays 0/16 for #14, 0/60 overall.

## Documented-standard breaches (hard rules)

**None new.** The `9bade2ff` blocker is closed: `undetermined_external_change` is now named
in all three enumerations — `claude/…/orchestrator-template.md:98-108`,
`codex/…/orchestrator-template.md:150-160` ("All four"), and `input-freshness.md:137-140`.
`grep -rl external_change_repair_pending` finds no fourth enumeration, and the two templates
stay word-parallel per host parity.

**Docs match real blocking.** `validate_unattended_readiness.py:354-362` emits it from the
`except` around `routed_external_changes` with **no `node_id`** — project-wide, as documented
— for unreadable state / unparseable store, with "resolve it at the interactive bootstrap
entry". `test_unreadable_freshness_state_cannot_report_or_decide_external_changes:378-384`
asserts exactly `["undetermined_external_change"]` and `not_ready`. Verified.

## Heuristic smells (judgement, not blockers)

- **Mysterious Name / stale contract** — `routed_external_changes`'s docstring, one line above
  the changed hunk, still says the groups are "changes a standing verification classified as
  needing a decision, and changes no current verification covers". After
  `change['resolution'] or change['classification'] in (...)` (`:301-303`) group one also holds
  decision-routed changes with **no** standing verdict. Same in `external_conflicts:313`. The
  inline comment is correct; the docstrings above it are not.
- **Repeated Switches** — the classification-string cascade recurs: `:302` and `:582-583`
  (`in ('fact-update','product-conflict','uncertain')`). Two sites switching on one implicit
  type; `classification`/`resolution` remain **Primitive Obsession** (string + dict sentinels).
- **Duplicated Code** — the ~10-line undetermined paragraph is near-identical in both
  `orchestrator-template.md`; deliberate host parity, so heuristic only.

Not present in changed scope: Feature Envy, Data Clumps, Shotgun Surgery, Divergent Change,
Speculative Generality, Message Chains, Middle Man, Refused Bequest. `9bade2ff`'s dead
`workflow = read_json(...)` read is now used (`:571` feeds `inventory` at `:576`) — fixed incidentally.
