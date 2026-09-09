# T15 acceptance-allocation corrections (C3)

Scope: the open issue recorded in `T15-acceptance-allocation-analysis.md`, originating in
`T15-codex-new-product-evaluation.md` §3.4(c)/A5 — every node of the generated plan ends with
the same unqualified `Acceptance:` block, so a documentation node inherits
"For simultaneous claim attempts, only one volunteer holds the claim" with no statement of what
it owes for that criterion at its own stage.

Files changed here, and only these:

- `claude/meta-skill/scripts/orchestrator/product_intent.py` (plan-generated brief + one scoped
  deferral check)
- `claude/meta-skill/knowledge/node-spec-template.md`
- `claude/meta-skill/tests/unit/test_acceptance_allocation.py` (new)
- this report

`check_artifacts.py`, the Node/Codex run drivers, `validate_bootstrap.py`, `bootstrap/SKILL.md`
and the frozen campaign artifacts were **not** touched; other workers own them. No commit, no
change on `main`, no install, no host launch, no remote write. Edits were made with the Claude
Code exact-string edit tool: this checkout has no `apply_patch` binary and the harness exposes no
`apply_patch` tool, so the equivalent exact-match patch tool was used instead.

## What was ambiguous

`plan` copies each referenced confirmed requirement's **complete** acceptance list onto every
consuming node and appends it to the brief. `_intent_drift` rejects any difference from that list,
so per-node deletion is refused — correctly, because deletion is scope loss. What was missing is
the other half: the brief never said that the list is inherited scope rather than this node's
proof obligation. Two different constraints (full inherited acceptance; per-stage evidence) read
as one, so a documentation node could equally conclude "I must implement the claim race" or
"writing the guide satisfies the race criterion". Both are wrong.

## The correction

### 1. The generated brief allocates the obligation (product_intent.py)

The list is unchanged — same statements, same order, still equal to the confirmed requirement, so
`_intent_drift` equality is untouched. Only its heading and a following block changed:

```
Confirmed acceptance (inherited requirement scope, complete and unmodifiable):
- <verbatim confirmed acceptance, complete>

Stage obligation:
- The acceptance above is the complete user-confirmed acceptance ... It is the scope this node
  serves, not a claim that this node proves all of it. Nothing in it may be dropped, reworded or
  narrowed here; acceptance that differs from the confirmed requirement is refused as
  stale_requirement.
- Prove what this node's declared responsibilities (<this node's responsibilities>) can actually
  produce at this stage ... Documentation proves that the documents describe current behavior
  accurately and passes its declared document_verification; writing a guide is not proof that the
  behavior it describes was built.
- Where a statement's full product effect first exists at a later stage, state the stage-local
  proof in Effect Verification and name the node that proves the full effect as
  downstream_effect_owner ... A stage-local pass is not product completion: the nodes holding the
  implementation and verification responsibilities for these requirements still owe the full effect.
```

The responsibility list is per node, so the paragraph is a project- and stage-specific instruction
(`(documentation)` on the docs node, `(product, technical, implementation)` on the build node),
not one universal sentence repeated eight times. It names only mechanisms that already exist:
`responsibilities`, `document_verification`, Quality Acceptance, Effect Verification,
`downstream_effect_owner`, and the existing blocker codes.

### 2. A deferral must keep a holder for the same requirement (product_intent.py)

`validate_bootstrap.validate_effect_stage_ownership` already refuses a `downstream_effect_owner`
that is empty, missing, itself, not downstream, or has no Effect Verification. One loss it cannot
see is a deferral to a node that does not consume the deferring node's confirmed requirements — the
stage-local pass then points at an owner who never inherited the criterion. `validate_scope` now
returns the **existing** `unowned_effect_stage` code for that case, on the same declaration and the
same field. No new schema, no parallel queue, no new universal rule: the check fires only when a
scoped node actually declares a deferral.

Applicability and responsibility coverage are unchanged: `_product_contract` still requires the six
stages per requirement with reasoned omission only of `experience`/`technical`, and
`not_applicable` still rejects anything else. Nothing here lets a stage be dropped for a reason
string.

### 3. The template states the same split (node-spec-template.md)

Three narrow additions: the Scoped requirement contract paragraph now distinguishes the inherited
list from Quality Acceptance's stage evidence and says a documentation node proves accurate current
documentation rather than implementation; Effect Verification records that a scoped node's owner
must consume the same `requirement_refs`; Quality Acceptance records that restating the inherited
list is not a Quality Acceptance.

## Evidence

New: `claude/meta-skill/tests/unit/test_acceptance_allocation.py` — 5 tests × 2 hosts
(`claude`, `codex`; the Codex script tree is a symlink to the Claude one, so both host copies run
the same producer). Each builds a real `new-product` scope through the copied CLI
(draft → decide → freeze → plan), with a claim-race acceptance statement, and a three-stage plan
(`build-claim-flow` → `operator-documentation` → `release-verification`), then runs the copied
public gates on what `plan` wrote.

```
python3 -m pytest claude/meta-skill/tests/unit/test_acceptance_allocation.py -q
10 passed in 6.15s
```

Which tests prove the new behavior, and which guard the preserved behavior — measured by replacing
`product_intent.py` with a byte-identical pre-change copy (reverse of the three hunks) and re-running:

```
4 failed, 6 passed in 5.81s
```

- **New behavior (failed before, pass after)**
  - `test_documentation_node_owes_its_stage_evidence_for_the_inherited_acceptance[claude|codex]` —
    positive docs-stage assignment: the docs node still carries the full inherited list including
    the concurrency criterion, every consuming node carries the identical list (no reallocation),
    and the brief names `(documentation)`, `document_verification`, `downstream_effect_owner`,
    `stale_requirement`, `unowned_effect_stage`; the build and verification nodes name their own
    responsibilities. `validate_bootstrap.py` and `check_decision_inputs.py` exit 0 on the result.
  - `test_a_deferred_full_effect_needs_an_owner_that_carries_the_requirement[claude|codex]` —
    negative: a plan that defers the docs node's full effect to a node consuming only one of the
    six requirements is refused by `plan` itself with `unowned_effect_stage`, and no node-spec is
    written.
- **Preserved behavior (passed before and after — these are the "do not relax" guards)**
  - `test_a_stage_may_not_delete_the_inherited_acceptance_it_cannot_prove[claude|codex]` — deleting
    the concurrency criterion from the documentation node is refused as `stale_requirement`.
  - `test_a_node_spec_may_not_quietly_narrow_the_confirmed_acceptance[claude|codex]` — rewording it
    in the spec is refused on the acceptance mirror.
  - `test_a_deferral_to_a_node_outside_the_plan_is_refused[claude|codex]` — an owner no node
    answers for is still `unowned_effect_stage` at the bootstrap gate.

Repository checks, all after the change:

```
python3 -m pytest claude/meta-skill/tests/unit/test_product_intent_session.py \
                 claude/meta-skill/tests/unit/test_planning_audit_contracts.py -q   → 37 passed
python3 claude/meta-skill/scripts/orchestrator/validate_meta_contracts.py claude/meta-skill        → exit 0
python3 claude/meta-skill/scripts/orchestrator/validate_generalization_boundaries.py claude/meta-skill → exit 0
python3 -m pytest claude/meta-skill/tests/unit -q -p no:randomly                     → 780 passed in 294.44s
```

An earlier randomized full run of the same tree reported `2 failed, 778 passed`, both in
`test_freshness_admission_corrections.py::test_retained_legacy_node_keeps_gate_behavior_without_invented_provenance`,
on the `check_artifacts` freshness measurement fields (`binding_identity`/`binding_kind`). That module
passes standalone (`32 passed`), the deterministic re-run above is fully green, and `check_artifacts.py`
carries +94 uncommitted lines from the worker who owns it — the run overlapped its edit. Nothing in this
change touches a freshness path. Recorded here rather than dropped.

## What this does not prove — still pending

- **Actual host behavior.** These are copied-CLI, generated-project seam tests. The deferral test and
  the three refusal tests are behavioral (the CLI and the gates exit non-zero, and no spec is
  written); the positive docs-stage test is part behavioral (gates exit 0 on the generated project)
  and part assertions on the generated brief's text — which proves the producer allocates the
  obligation per node, not that an executor obeys it. Whether a real host reading this brief
  documents the claim rule instead of claiming to implement it is **not** proven here. Per the
  analysis's own constraint that needs a real host run on a generated documentation node; it is not
  claimed and remains open.
- **Boilerplate acceptance (`C3` in the evaluation's own defect table)** — "The product direction
  explicitly addresses: `<goal text>`" from the gap-question path is a restatement, not a criterion.
  Untouched; it is a separate defect in the same file.
- **A1/A2 from the evaluation** — single-capability routing and pending choices not expressed as
  `decision_mode: "brainstorm"` — are not addressed here and are not affected by this change.
- The frozen `codex/new-product` cell stays unadmitted; nothing under the evidence root was read for
  writing or modified.
