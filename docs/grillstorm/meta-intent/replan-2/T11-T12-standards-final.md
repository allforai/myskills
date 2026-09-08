# T11/T12 standards final recheck

HEAD `ed430dfc` verified; fixed diff `90257b15...HEAD`; standards axis only. Read-only; tooling counts (root's 581 Python, 55 Node, 3 core, hook 557) not repeated. Codex `scripts/` and `tests/` are symlinks to the Claude tree, so helper copies cannot diverge. Scratch probe (isolated, `GIT_*` stripped) on `observed_reads`: `../x`, `[1]`, `{bad`, empty node id all refused with the documented `Malformed observed-input dependencies (...)` prefix, file left in place; a valid register admitted.

## Previous findings

1. **Soft legacy warning wording — resolved.** `orchestrator-template.md:91–95` (Claude) and `:36–38` (Codex) now say retained legacy nodes are warning-only "when dependency declarations and recorded freshness state are readable and valid" and that malformed or unreadable state "block[s] even retained nodes". Matches fail-closed `check_artifacts.py` behaviour probed last round. Both adapter copies say the same thing.
2. **Blank-line nit — resolved.** `codex/meta-skill/skills/bootstrap.md:134` blank line removed; helper list is contiguous.
3. Prior items 1–3 stay resolved or repo-ruled; `validation-commands.md` lists the three new suites.

## Documented-standard breaches

None hard. CLAUDE.md (JSON vs Markdown contract, skill layout, no auto-invocation), CONTEXT.md glossary, AGENTS.md helper inventory, ADR-0001..0003: no hunk contradicts them. `product-intent-confirmation.md` describes `legacy_reuse`/`prior_confirmation`/`unchanged` as acceptance contracts, not method, consistent with the repo's stated skill-writing rule.

Carried, not introduced: `codex/meta-skill/skills/bootstrap.md:42` cites `knowledge/product-intent-confirmation.md`, which has no Codex-side symlink; it resolves only through AGENTS.md's "canonical root" rule. Pre-existing at the base commit.

## Smell judgements (optional, no rule)

- **Duplicated Code** — the path guard `Path(path).is_absolute() or '..' in Path(path).parts` appears at `evidence_freshness.py:74` and new `:107`; one `_relative_project_path(path)` helper.
- **Duplicated Code** — the six-exception tuple is now nine occurrences in `product_intent.py` (new at `:741`); name it once.
- **Mysterious Name / definition order** — `LegacyProjection` (`:334`) is declared after `_confirmed` (`:302`) raises it; legal, but a reader meets the exception before its class. Move above.
- **Speculative Generality** — `_frozen_scope_batch` returns `(journal, batch_id)`; the freeze caller discards `journal` (`:740`). Minor.
- **Data Clumps** — `(refs, exclude, intents)` travel into `_same_selection` and `contract`; a `Selection` tuple would name the concept. Minor.
- `# noqa: E731` lambda at `:565` is the only lint suppression in the orchestrator scripts; no repo lint config exists, so judgement only. A nested `def` would need no comment.
- Prior carried judgements are untouched by this diff.

Result: **0 hard breaches, 0 soft, 0 nits open; 6 optional judgements.** Static reading plus one isolated scratch probe; no host-dialogue evidence claimed.
