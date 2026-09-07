# Revised #10 implementation evidence

Implemented only revised issue #10 after coordinator supplied accepted #9 producer
`ea046abc8e0a479d736d332e5e5d15514d3ff294`, integrated at
`54ba9127a07506024700fde12ddd273f3690b963`, and assigned this checkout on
`j08069099777/grillstorm-meta-intent`. Read revised issue, parent #8 source,
CLAUDE/CONTEXT, Codex AGENTS, ADR1–3, implement and TDD instructions first.
Coordinator-owned `replan-2/execution.json` is excluded from the commit.

## Delivered behavior

- Both bootstrap adapters invoke the same interactive copied `product_intent.py`
  protocol at product discussion entry and resume. It accepts explicit structured
  host input and generates observable product/plan outputs; it does not parse
  prompt keywords to invent user consent.
- Drafts distinguish source facts, inferred intent and unknown/user-request intent,
  check source quotes, retain uncertainty, and stay pending. Six product dimensions
  are covered; absent dimensions produce pending gap questions. Host-supplied
  contradiction questions retain dependency IDs.
- Topic decisions support confirm/add/adjust/remove plus question answers, with
  stable IDs, lineage, preserved history, reasons and canonical journal references.
  Empty actions do nothing; invalid batches do not write partial decisions.
  User additions need no code evidence. Discussion leaves product source untouched.
- Explicit scope freeze requires every intent and unanswered question to be included
  or explicitly excluded; dependent unanswered questions block inclusion. Scope
  versions and complete projections are recorded in the existing canonical journal
  and projected into the existing concept-baseline artifact.
- Resume reuses valid recorded choices, exposes only pending topics and invalid
  legacy confirmations, and does not mutate legacy artifacts. Older schema-1.0
  user choices can be reused when goal and rationale match their recorded values;
  the scope decision binds the complete projection without creating a duplicate
  intent decision. Nonmatching/ambiguous legacy material needs missing confirmation.
- The plan operation takes the host's freely chosen graph, binds confirmed intent
  to workflow/Node-spec goals and acceptance, and emits generated files. It checks
  applicable product-through-verification responsibilities without selecting a
  fixed list of Capabilities. The host still supplies a semantically adequate
  graph, domain-specific briefs, suppress decisions and reconciliation metadata.
- All three copied public gates check current frozen scope and journal authority;
  changed product payloads cannot retain readiness. Bootstrap additionally rejects
  Node-spec acceptance/goals that differ from the workflow. Existing local-change
  rules, main Run Policy, ADR3 and 2D/2.5D disclosure remain intact.

## Validation

Primary seam: scripted bootstrap/resume JSON inputs and observable artifacts,
followed by generated copied public CLI gates for both adapters.

Observed red→green cycles:

1. Draft/resume CLI output absent, then provisional topic persistence passed.
2. Four decision operations absent, then history/user-addition scenario passed.
3. Freeze operation absent, then explicit scope/new-product scenarios passed.
4. Plan operation absent (then stale disposable Node-spec found), then complete
   applicable graph generation and public gates passed.
5. Altered Node-spec acceptance incorrectly passed; parity check now rejects it.
6. Existing canonical choice was rejected; exact choice/rationale reuse now passes.
7. Legacy code-derived confirmed label disappeared from resume; it now appears as
   pending without mutating the prior artifact.

Final focused command:
`python3 -m pytest claude/meta-skill/tests/unit/test_product_intent_session.py -q`
— **22 passed**. Covers reconstruction and new-product complete plan paths, four
operations, scope exclusions, unresolved dependencies, no code mutation, invalid
batch preservation, evidence rejection, gaps, canonical reuse, legacy confirmation,
Node-spec parity and product projection drift.

Final full relevant command:
`python3 -m pytest claude/meta-skill/tests -q`
— **264 passed in 27.46s**.

`uvx mypy --follow-imports=silent --check-untyped-defs claude/meta-skill/scripts/orchestrator/product_intent.py`
— **success, no issues in one source file**.

Broader check including `validate_bootstrap.py` reports **11 errors**: missing
PyYAML stubs and ten missing type annotations. The ten annotation errors were
reproduced against the accepted `54ba9127` validator in a temporary file with
missing imports ignored; the only validator code change is the parity field list.
This is not a clean whole-repository or strict typecheck. `git diff --check` passes.

## Limits and remaining ownership

No real Claude/Codex host dialogue or real-host harness was run; scripted JSON
scenarios are deterministic protocol evidence, not semantic host evidence. Source
selection, product inference quality, proactive contradiction discovery and the
semantic adequacy of the freely chosen workflow remain host responsibilities and
need independent host evaluation. The helper does not replace existing full
bootstrap audits, reconciliation, domain suppress validators or unattended Run
Policy; run those at actual project generation as the protocol directs.

Coordinator owns independent two-axis review, integration and any further real-host
validation. No subworkers, push, main merge, install or issue closure was performed.
