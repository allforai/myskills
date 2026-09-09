# T14 standards re-review — #14 correction (11f9a44c → 9bade2ff)

Axis: documented rules (`CLAUDE.md`, `CONTEXT.md`, `codex/meta-skill/AGENTS.md`, ADR-0001–0003,
`knowledge/input-freshness.md`, both `orchestrator-template.md`) versus optional Fowler
heuristics. No lint/format config exists in the repo, so nothing is excluded as
tooling-enforced and line width is not a documented rule. Evidence is copied-CLI in a
temporary `git archive` extraction (`GIT_*` stripped, checkout untouched) — **not** real
Claude/Codex host dialogue proof, which stays 0/16 for #14 and 0/60 overall.

**Prior blocker closed.** The 00b5 breach (an unwritable store deleting the conflict from
every gate) is fixed at the seam, not papered over: the gates now route through the
read-only `standing_changes`, and `cache_classifications` (`evidence_freshness.py:532-547`)
fails soft instead of raising or returning `{}`. `test_an_unwritable_store_keeps_the_conflict_it_could_not_record`
covers it; 108/108 pass in the three touched unit files.

## Documented-standard violation

**1. `orchestrator-template.md` enumerates the external-change blockers exhaustively and
this commit made that enumeration false.** `claude/…/orchestrator-template.md:98-101` and
`codex/…/orchestrator-template.md:150-153` say "`unresolved_external_change`,
`unverified_external_change` or `external_change_repair_pending` … **All three** are
preflight blockers". The same commit adds a fourth external-change readiness code,
`undetermined_external_change` (`validate_unattended_readiness.py:360`), documented in
neither template nor `input-freshness.md`'s outcome list. Behaviour still fails closed via
the template's generic "do not execute newly exposed work when readiness is not `ready`"
(`:76-78`), so this is doc-vs-code, not an open gate — but the generated run meets a
blocker code its own instructions do not name.

## Heuristic smells (judgement calls, not blockers)

- **Speculative Generality / dead read** — `standing_changes` opens the workflow and never
  uses it: `workflow = read_json(root, WORKFLOW, {})` (`:561`); one extra JSON read on
  every gate call.
- **Speculative Generality** — `cache_classifications`' docstring promises to "report
  whether the cache was written"; the sole caller discards it: `cache_classifications(root, changes)` (`:611`).
- **Middle Man** — `external_conflicts` is now `return routed_external_changes(root)[0]`
  (`:308-310`), a positional-index passthrough.
- **Duplicated Code** — `state['nodes'].get(change['node_id']) if change['node_id'] else None`
  at `:568` and `:600`, each after its own `state = read_json(root, STATE, …)` (`:562`, `:595`).
- **Docstring drift** — `routed_external_changes` claims "It raises, so every gate fails
  closed"; the function contains no `raise` (it inherits one from `standing_changes`).

Carried over from 00b5, untouched here: `product_intent.py:801` duplicate
`detect_external_changes` rescan; `validate_unattended_readiness.py:375` binds `state` to an
English clause. Host parity (both templates, both bootstrap entries) is word-identical;
ADR-0001–0003 and `AGENTS.md` contract notes are unaffected.
