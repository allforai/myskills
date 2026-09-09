# Acceptance allocation — root analysis, not an applied repair

Fixed source inspected: `2cc347af`. This records an unresolved design issue;
it does not accept the new-product cell or change its frozen artifacts.

## Evidence

`product_intent.py`'s `plan` operation copies the complete acceptance list from
each referenced confirmed requirement into the node's `acceptance` field and
appends it under `Acceptance:` in the generated brief. `_intent_drift` rejects
any difference from that full list. `_product_contract` separately requires
six responsibilities per requirement (product, experience, technical,
implementation, documentation, verification), allowing reasoned omission only
of experience and technical work. Four are therefore unconditional. These are
different constraints, not one bug.

The independent diagnosis correctly demonstrates that deleting one acceptance
clause from a documentation node is rejected. However, the shared node-spec
template already has a separate `Quality Acceptance` section for the evidence
this node must provide, and the latest repair makes `Effect Verification`
stage-local with a named downstream full-effect owner. Thus equality of the
inherited requirement list alone does not establish that every stage must run
every final product test. The generated unqualified `Acceptance:` heading
still makes that distinction ambiguous, and the real actor did not resolve it.

## Constraints on the next repair

- Preserve the complete user-confirmed acceptance and its revision/provenance;
  do not make per-node deletion a way to reduce product scope.
- Distinguish inherited requirement context from the evidence obligation at
  this node's stage. For example, documentation must accurately describe the
  atomic claim rule and be checked against its implementation; it must not
  claim to have implemented concurrency merely by writing the guide.
- A deferred full-effect obligation needs an explicit downstream owner and
  final coverage. A stage-local pass must not imply product completion.
- Evaluate stage applicability separately. Do not merely allow every stage
  to be omitted by an arbitrary reason string to make this fixture green.
- Re-test through real generated briefs and host behavior. Renaming a heading
  or asserting prompt text is not proof that the planning problem is fixed.

No code change is made here while the planning-gate editor owns
`product_intent.py` and the node template; the next scoped change must be
coordinated after it settles. This issue remains open, as does legacy confirmation question
precision. Original reports are preserved, including their differing findings.

## Recheck after in-flight corrections

The coordinator re-read the current `plan` producer and node-spec template on
2026-09-09. The unqualified generated `Acceptance:` heading remains, while the
template still distinguishes stage-local `Quality Acceptance` and downstream
`Effect Verification`. The next repair must test a generated documentation brief
that inherits a concurrency acceptance requirement: the documentation node must
prove accurate, current documentation without claiming to implement concurrent
behavior; a named implementation/verification owner must still prove the full
product requirement. A second case must reject deleting the inherited criterion
or losing its downstream proof owner. Actual host evaluation must then confirm
the executor follows the distinction; prompt wording tests alone cannot close it.
