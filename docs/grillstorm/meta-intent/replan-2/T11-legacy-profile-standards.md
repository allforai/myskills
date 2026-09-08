# T11 legacy-profile correction: standards review

Range `ed430dfc...2916e183` (HEAD verified), 9 files. Standards axis only. Sources: CLAUDE.md, CONTEXT.md, `codex/meta-skill/AGENTS.md`, ADR-0001. Tests are scripted seam tests, not host proof; nothing is approved on that basis.

## Hard breaches (documented standard)

None found.

- **Canonical sharing (AGENTS.md § Shared Asset Strategy)**: `scripts/` and `tests/` are symlinks, so the Python change and new test reach Codex; `codex/meta-skill/knowledge/` holds only Codex-only extensions, so no mirror is owed. `bootstrap.md` updated alongside `SKILL.md`.
- **ADR-0001**: the planning must lands in `bootstrap-planning.md`; `/run` still does not stop, `pending_requirement` stays a decision input.
- **CONTEXT.md vocabulary**: no avoided terms in the hunks.
- **CLAUDE.md skill layout**: unchanged. New test parametrizes `host` over both adapters, matching sibling files.

## Judgement calls

1. **Protocol vs tutorial (CONTEXT.md "Protocol … not a step-by-step tutorial")** — `bootstrap-planning.md`: "`product_intent.py` `resume` presents the item pending with `legacy_reuse` … `admit` still refuses to overwrite it." CLI presentation detail inside a planning invariant, already carried by `product-intent-confirmation.md`. Keep only the invariant there.
2. **Skill text describes method** — `SKILL.md`/`bootstrap.md`: "it returns only the projections whose journal choice evidences the goal alone (`legacy_reuse`) or no longer verifies". The acceptance ("resumed, not re-admitted; one `confirm` recovers the gates") is right; the return-shape sentence belongs in knowledge.

## Baseline smells (product_intent.py)

- **Duplicated Code** — `_journal_decision` re-implements `_confirmed`'s batch lookup, schema check and supersedes scan (`if any(d.get("supersedes") in (fragment, reference) …`); `_journal_payload` repeats `_confirmed`'s `matches_payload` rule with different error text; `_hand_projection` repeats `validate_scope`'s `any(not isinstance(confirmation.get(key), str) … for key in ("reference", "decision_id", "reason"))`. Extract one resolver both routes call.
- **Repeated Switches** — the `intent_session_path == LOCAL` / route cascade recurs in `_session_path`, `_legacy_local`, and `session()`: `(LOCAL if profile.get("intent_session_path") == LOCAL else CONCEPT) if operation in ("draft", "admit") else _session_path(...)`. One resolver taking `operation`.
- **Primitive Obsession (flag argument)** — `_verified(..., legacy=False)` dispatches on a boolean; each caller recomputes `legacy=_legacy_local(root, profile)`.
- **Mysterious Name** — `_journal_payload`, `_hand_projection`, `_verified` read as getters or predicates but return `None` and raise; `_journal_payload` raises `LegacyProjection` on its accepted path. `_require_…` names would state the contract.
- **Divergent Change** — `_discussion` changes for exclusion handling, legacy verification and `LOCAL_TOPIC` defaulting in one hunk; minor.

Docs under `replan-2/` are report Markdown only; no JSON duplicated (CLAUDE.md output contract).
