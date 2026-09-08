# A2 adjudication: `reopen` + `confirm` in one decide batch (d622402c)

Scope: the single residual finding of `T11-d622-spec.md`, which recommended
"closing or recording it as accepted before issue closure". This report records it
as an **accepted boundary**; no source or protocol change was made.

HEAD `d622402c`; both host copies of `scripts/orchestrator/product_intent.py` are
byte-identical (`diff` clean), so one probe covers both adapters. Evidence is my own
copied-CLI probes in temporary projects plus the focused suites. Copied CLIs are not
real-host dialogue proof and discharge no cell of the 60-cell matrix.

## The finding, reproduced

Legacy hand-projected local file (`task_route: local-change`, no `intent_session_path`),
one confirmed item whose only provenance is a user turn (`reference: "bootstrap user
turn 2"`). One batch, `user_reference: "FABRICATED turn 99"`, actions `reopen` then
`confirm` → exit 0. The item becomes revision 2, `confirmed`, payload unchanged, and a
later local `freeze` accepts it as baseline version 1. Reproduced exactly as reported.

What the probe also shows, which the finding did not weigh:

- Revision 1 is retained as `superseded` with its original confirmation intact.
- Journal batch `b1` records **two** decisions: `0 reopen supersedes "bootstrap user
  turn 2"`, `1 confirm supersedes ".../decision-journal.json#b1/decisions/0"`. The
  original user turn is explicitly and durably marked as superseded by a recorded
  reconsideration. Nothing is silently re-attributed.

## Why this is the host trust boundary, not a runtime contract violation

**1. The end state is reachable in two batches, identically.** Probe `p2`: batch 1
`reopen` (resume then shows `export` pending), batch 2 `confirm` with a second
fabricated reference → the same revision-2 confirmed item with the same superseded
revision 1. Any single-batch guard would remove no authority the model does not already
have; it would only mandate an extra CLI round trip, i.e. invent a required extra user
turn. A guard that also covered the two-batch case would have to refuse confirming any
reopened legacy item — that is a ban on genuine reversal.

**2. `reopen` → `confirm` is the sanctioned reversal channel on the verified route too.**
Probe `p4`, same local file but journal-backed provenance with the full `intent` payload:
a direct `decide confirm` is refused ("Reuse recorded confirmation; do not reconfirm it"),
while `reopen` + `confirm` succeeds. The behaviour A2 describes is the documented meaning
of `reopen` ("records the user's reconsideration"), not a legacy-specific escape. It also
predates `d622402c`: the new guard sits in the `confirm`-on-non-pending branch, which a
reopened (pending) item never enters, so the commit introduced no regression here.

**3. The A1 guard is enforceable exactly because its ground truth is in the store.**
`confirm` on a still-confirmed legacy item claims "record the consent that already
exists"; the correct reference and reason are readable from the item itself, so the CLI
can and does require them unchanged. `reopen` claims "the user reconsidered" — a fact
that exists only in the conversation. The helper accepts explicit user decisions and
cannot authenticate a user reference; per the protocol, "the host supplies requests from
actual conversation" and "the CLI never interprets arbitrary prose as approval". Any rule
here (reference must differ, reason must differ, payload must change, reopen must be its
own batch) is arbitrary, defeatable by the same fabricating host, and costs a legitimate
flow: a user who reopens and then re-affirms the identical requirement.

**4. The issue criterion at stake is not violated.** "没有确认来源的旧代码推断不能伪装为
已批准需求" governs legacy inference *without* a confirmation source; such an item is
presented pending by `resume` and needs an explicit decision either way. Here a
confirmation source exists, is retained at revision 1, and is recorded as superseded.
"不捏造回答" is a host obligation the CLI structurally cannot adjudicate.

## Accepted boundary (what the CLI does and does not guarantee)

Guaranteed, verified at `d622402c`:

- A legacy user-turn item included in a local `freeze` without being recorded is refused:
  "Legacy user-turn projection export must be recorded with one confirm decision …"
  (probe `p3`, exit 1).
- Recording that item via `decide confirm` must reuse the original `user_reference` and
  `reason`; anything else exits 1 with no file change, and a second recording is refused.
- Removals: a verified removal refuses `remove`/`confirm`; a freeze-excluded removal needs
  explicit `restore`; an unverified tombstone accepts `remove` without an active revision.

Not guaranteed, and accepted as the host boundary:

- The truthfulness of any `user_reference` or `reason` in a `decide` batch, including the
  claim that a `reopen` happened. The CLI enforces faithfulness to facts recorded in its
  own store, never to facts only the host observed.
- Consequently, a host that fabricates a reconsideration can move a legacy user-turn item
  to a new confirmed revision. The cost it cannot avoid is an auditable record: a revision
  bump, a retained superseded original, and a journal `reopen` decision naming the original
  turn as superseded. That record is the intended remedy, and it is what an independent
  reviewer reads.

Caveat, stated rather than fixed: in the one-batch form the item is never exposed as
pending through a `resume` between the two decisions, so a host reading only `resume`
output sees no reconsideration surface. The journal records both decisions, and batching
several actions the user chose in one turn is explicitly sanctioned ("Explicit batch
approval may cover several named items"), so this is not treated as a defect.

## Verification run

`python3 -m pytest claude/meta-skill/tests/unit/test_legacy_profile_authority.py
test_product_intent_resume.py test_local_reopen_scope.py test_legacy_projection_authority.py
test_product_intent_session.py -q` → **90 passed in 34.30s** on unmodified `d622402c`.
No production file was touched, so no typecheck of changed scripts applies.

## Recommendation

Record A2 as an accepted boundary in the issue-closure evidence, with the two probes
(`reopen`+`confirm` one batch vs. two batches producing identical state) as the reason a
deterministic guard is not defensible. Real-host dialogue quality — that the host only
submits reconsiderations the user actually made — remains owned by the independent host
scenarios, not by this helper.
