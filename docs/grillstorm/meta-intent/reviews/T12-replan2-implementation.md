# Revised #12 implementation evidence

Assigned checkout: `/Users/aa/orca/workspaces/myskills/meta-intent-t12`, branch
`j08069099777/meta-intent-t12`. Accepted producer: `3f66d7acc367cdb39ee12ae10827c8d81298ae0a`;
starting documentation HEAD: `88e7becaf30522ef29dd2fa168b62045affcb782`.

Implemented the revised issue and parent version/freshness contract through the
shared copied `evidence_freshness.py` CLI, reconciliation, artifact completion,
readiness, Node-spec input consistency, and both adapters' bootstrap/run paths.
No product-decision semantics, journal authority, Run Policy or ADR3 rules changed.

## Public contract and behavior

`observe` records content-addressed product-source state, selected requirement
content, selected baseline intent payload and scope, observed version, node input contract and
transitive upstream inputs. `read` returns additional input content and durably
adds its dependency, including across rejected publication. `publish` executes
an explicit project verification argv and checks the observation before and after
execution, then records generated-document/evidence content hashes. It rejects
changed inputs, failed verification, missing outputs and corrupt observation IDs.
`check` reports current evidence and execution-readiness status without writing.

`kind: contract` can establish execution readiness without proving completion;
`kind: evidence` binds actual verification and outputs. Direct and transitive
changes invalidate dependent evidence; revalidating a producer does not revive
its consumers' old evidence. Unknown source impact is explicit, unrelated valid
records survive, and a serialized atomic publication preserves parallel records.

Node fields: `source_inputs` (files/directories/globs), `input_dependencies`,
`required_documents`, existing `requirement_refs`, `decision_inputs` and
`hard_blocked_by`. Workflow `generated_outputs` names other generated files.
Source inventory excludes generated data-bus/host files, declared outputs and
dependency/cache directories; explicitly consumed inputs still participate.

Existing workflows without freshness declarations/state retain their legacy gate
behavior until bootstrap onboards them through the documented contract. Updated
bootstrap must declare source inputs for each generated node and publish its
verified contract. A node with declarations but no publication is stale; missing
source declarations are refused by `observe`, not silently treated as empty.
This migration boundary does not retroactively invent provenance for old reports.

## Validation

TDD proceeded one observable slice at a time, first observing each new behavior's
failure and then making that slice pass. Final copied-CLI suite:

`python3 -m pytest claude/meta-skill/tests/unit/test_evidence_freshness.py -q`
— **30 passed** (15 scenarios × Claude/Codex adapter copies).

Scenarios cover SG01 observe A/change B/reject/reverify B, edits during actual
verification, failed verifier exit, direct/transitive source and baseline scope
changes, additional reads across rejected publication, unknown impact, changed
artifact content, retained unrelated branches/baseline revisions, two dirty states
on the same real Git commit, file/glob membership, generated-output convergence,
contract readiness versus completion, parallel publication, and Node-spec parity.
Reconciliation and both completion/readiness gates are exercised as copied CLIs.
The selected-baseline-payload regression uses actual #10 copied
draft/decide/freeze/plan operations before mutating only the frozen intent payload.
The document-convergence verifier executes fixture product code and writes both
required fact documentation and evidence during publication. Baseline version is
retained as provenance; impact compares the selected semantic payload, allowing
an unrelated baseline revision to retain existing evidence.

Focused regression command for freshness/reconciliation/artifacts/readiness:
**55 passed** at the earlier 20-scenario-case checkpoint.

Final full relevant suite:

`python3 -m pytest claude/meta-skill/tests -q`
— **322 passed in 39.58s** after the selected-baseline correction; the final
pre-commit suite also covers the strengthened Git-isolation assertion below.

`node --test 'claude/meta-skill/knowledge/run-engine/tests/**/*.test.js'`
— **55 passed**, including inline-engine synchronization.

`uvx mypy --follow-imports=silent --check-untyped-defs claude/meta-skill/scripts/orchestrator/evidence_freshness.py`
— **success, no issues**. The direct `python3 -m mypy` attempt initially found
no installed mypy module; the available `uvx mypy` runner supplied the checks.

Broader typecheck of the new helper plus artifact, reconciliation, bootstrap and
readiness gates reports **12 errors**: ten existing bootstrap annotations, one
existing readiness nullable-node assignment, and absent PyYAML stubs. The eleven
code errors were reproduced from starting HEAD in temporary baseline files using
`--ignore-missing-imports`; this is not a clean full-validator typecheck.
The reconciliation node-list narrowing was corrected where the new call exposed
its nullable expression. `git diff --check` passes.

An initial pre-commit run exposed inherited `GIT_*` hook variables in the real-Git
fixture. Its accidental local fixture commit was inspected and undone on this
assigned branch, preserving all owned changes and removing the fixture entry;
no integration branch commit was changed. The inherited fixture initialization
also changed shared `core.bare`; the coordinator restored it to `false`.
The local soft reset happened before the coordinator's later no-reset guidance
was received, and no further history rewrite occurred. Fixture Git now strips
those variables and disables only temporary-fixture hooks/signing. The regression
explicitly injects enclosing `GIT_DIR`, `GIT_WORK_TREE` and `GIT_INDEX_FILE`, then
asserts enclosing HEAD, index bytes and shared config bytes are unchanged by the
fixture Git commands. Repository pre-commit hooks remain enabled for the final
candidate commit.

## Limits and remaining ownership

These are deterministic copied-CLI and existing engine tests, not actual Claude
or Codex host-dialogue proof. Input selection and semantic adequacy of the
project-specific verifier remain host responsibilities; a successful arbitrary
command is not by itself evidence that the chosen acceptance criteria are good.
The protocol explicitly requires the real acceptance command and additional-read
registration. There is no background watcher or claim of atomic filesystem
isolation against arbitrary external writers; gates compare current content again.
An abandoned publication lock fails closed and requires coordinator recovery.

Coordinator owns independent two-axis review, integration with #11, and actual-host
validation. No subworkers, push, main merge, installation or issue closure ran.
