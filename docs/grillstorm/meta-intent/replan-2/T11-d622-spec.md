# T11 spec re-review: recording/removal correction (d622402c)

HEAD `d622402cb1f5`; diff `2916e183...HEAD`, one commit, 7 files (1 protocol line, 1 guard pair
in `product_intent.py`, 2 tests, 4 reports). Spec axis, issue #11 v2 refetched (`ready-for-agent`,
0 comments; body matches the earlier read). Evidence: my own copied-CLI probes in temp projects
(GIT_* stripped) plus `test_legacy_profile_authority.py` 26 passed and 171 related tests. Copied
CLIs are not host proof (0/60). Root report treated as claims.

## Verified

**A1 closed on the recording route.** Legacy user-turn item, `decide confirm` with an invented
`user_reference`, and separately an invented reason, both exit 1 "Record the original user
reference and reason unchanged". With the original pair: exit 0, one revision, payload unchanged,
`prior_confirmation` kept, `confirmation.user_reference` = the original turn, local `freeze`
then succeeds. A second recording is refused ("Reuse recorded confirmation"), so the batch
reference cannot be laundered into the consent slot.

**C1 closed.** `remove` on a `source: code` tombstone yields revisions `(1, removed, code)`,
`(2, removed, user)` with no active intermediate and no pending topic on `resume`; the old
tombstone bytes are retained. Afterwards `confirm` is refused and only `restore` revives it.

**No regression on accepted boundaries.** Valid journal-verified removal still refuses both
`remove` and `confirm` ("cannot be silently restored"); a removal excluded at freeze refuses both
("needs explicit restore"); only `restore` revives either.

## (a) Missing / partial

**A2. `reopen` + `confirm` in one batch still fabricates the consent source.** #11: "不捏造回答";
"没有确认来源的旧代码推断不能伪装为已批准需求". Probe: one batch, `user_reference: "FABRICATED turn"`,
actions `reopen` then `confirm` (reason "FABRICATED reason") → exit 0, item becomes revision 2
confirmed with the unchanged payload, never observably pending, and `freeze` accepts it as
baseline. Milder than A1 — revision 1 survives as `superseded` with its original confirmation and
the journal records the reopen — but the new guard is one batch away from being optional.

## (b) Scope creep

None. The `remove` allowance also reaches the product-concept route (unverified tombstone there
accepts direct `remove`), mirroring the pre-existing `confirm` allowance; consistent, not creep.

## (c) Wrong behavior

None new.

## Acceptance

The delta does what it claims. A2 is the residual reuse-consent gap; recommend closing or
recording it as accepted before issue closure.
