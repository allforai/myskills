# T11 spec review: C1' legacy profile correction (2916e183)

HEAD `2916e183`; diff `ed430dfc..HEAD`, 9 files. Spec axis only, issue #11 v2 (GitHub body matches `issues/11.md`). Scratch probes (GIT_* stripped) drove the copied CLIs; focused suites 172 passed on both hosts. Copied-CLI evidence only, not host proof. Standards report not consumed.

## Verified on the marker-less hand route

Goal-only matching journal with invented acceptance and added area: gates block `pending_requirement` on the consumer only, readiness `not_ready`, files untouched; `resume` shows the item pending with `legacy_reuse`, no questions, no product topics. Mismatched choice: pending without `legacy_reuse`. One `confirm` recovers gates in place (revision 1, no marker, prior batch byte-identical, `prior_confirmation` kept, journal consumed). Full-payload and user-turn projections stay accepted; drift loses authority. `admit` refuses. Valid removed items resume as removed, `confirm` refused, only `restore` revives; after the freeze marker an excluded removal stays removed with files unchanged.

## (a) Missing / partial

**A1. Recording step's "original user turn" is documented, not enforced.** #11: "有可信确认记录时按相关范围复用…无需重做已完成确认"; "不捏造回答". A local freeze refuses a user-turn item until re-recorded, and `product-intent-confirmation.md` requires that batch's `user_reference` to be the original turn and the recorded reason. Probe P2: `decide confirm` with `user_reference: "INVENTED brand new turn"` and a new reason is accepted, becomes the item's confirmation (old one demoted to `prior_confirmation`), and the freeze then passes. The payload is provably unchanged, so no requirement is invented, but the consent record can be. Fix: check the recording batch against `prior_confirmation` in `decide`, or let the legacy freeze accept a verified user-turn item. Partial.

## (b) Scope creep

None. The removed-plus-excluded skip and the excluded-removal `decide` guard also touch the product route, but they serve #11's removal history requirement.

## (c) Implemented-looking wrong behavior

**C1. Invalid tombstone recovery revives, never verifies, the removal.** New doc line: "An invalid tombstone is pending verification, not authoritative removal or approval." Probe P1: on a `source: code` removed item, `remove` is refused ("needs explicit confirmation") and the only accepted `confirm` turns it into an active confirmed requirement. Verifying it as a removal needs confirm-then-remove. Pre-existing; minor.

**Minor.** `plan` before a freeze fails with bare `'intent_scope'`; freeze on a mismatched journal item says "Product projection differs" on a local route.

## Acceptance

C1' is closed on the documented hand route with history preserved and no whole-product interview. A1 is the remaining gap for #11's reuse-without-reconfirmation clause; recommend fixing before closure. Repro: `T11-legacy-profile-spec-repro.md`.
