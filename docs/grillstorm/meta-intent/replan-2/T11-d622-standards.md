# T11 #11 delta — standards re-review (d622402c)

Scope: `git diff 2916e183...HEAD`, one commit `d622402c`. Pinned HEAD `d622402cb1f5cc2b34a53854deaf058c41a4c676`. Report only; no edits, no commits, no host runs (copied CLI tests are not host proof, 0/60).

## Documented-rule breaches

**None.** Read `CLAUDE.md`, `CONTEXT.md`, `codex/meta-skill/AGENTS.md`, `docs/adr/0001-bootstrap-free-planning.md`, `docs/agents/domain.md`. None documents a Python style rule the delta could break. CONTEXT.md vocabulary (`capability`/`skill`/`protocol`) is untouched. `knowledge/product-intent-confirmation.md:69-70` states the new rule in the surrounding voice and wrapping. No hard violations.

## Optional judgements (smell baseline)

1. **Duplicated Code — `product_intent.py:941-946`.** `_verified(root, item, statuses=…, legacy=_legacy_local(root, profile))` is this file's route-dispatch seam; it is used exactly that way at `:695` and `:914`, and `_verified(legacy=True)` is nothing but `_hand_projection(root, item, statuses=statuses)`. The new hunk re-derives that branch inline (`_legacy_local(root, profile)` guard + a direct `_hand_projection` call), so the legacy-route decision now lives in three places instead of one. Calling `_verified(root, item, legacy=True)` would fold it back without changing behaviour.

2. **Convention deviation — `product_intent.py:946`.** `except (ValueError, TypeError, KeyError, AttributeError)` is the only narrow tuple in the file; the other nine sites (`:164, :460, :568, :624, :698, :848, :915, :956, :1051`) all use `(OSError, …, IndexError)`. Today the guard's `not _journal_reference(previous)` keeps `_hand_projection` off the file-reading path, so the omission is inert — but it is load-bearing on that guard, and a later change to `_hand_projection` would raise here instead of falling through to the intended "needs a fresh explicit decision" path. Match the file's tuple.

3. **Naming — `product_intent.py:948-950`.** The same user turn is compared as `request["user_reference"]` against `original["reference"]`, then written back as `confirmation.user_reference` (test asserts `confirmation["user_reference"] == confirmation["reference"]`). One value, two field names across two records; a reader cannot tell they are the same concept. Worth a comment or a field rename.

No Feature Envy, Data Clumps, Primitive Obsession, Repeated Switches, Shotgun Surgery, Divergent Change, Speculative Generality, Message Chains, Middle Man or Refused Bequest introduced. Test additions match the file's parametrize/`snapshot`/`invoke` idiom.

## Regression check on accepted boundaries

`:916` widening (`op not in ("confirm", "remove")`) is additive; the `restore`/`reopen` refusals and the C1-prime tombstone-preservation shape at `:930-937` are unchanged in this diff. No accepted boundary regressed on the standards axis.
