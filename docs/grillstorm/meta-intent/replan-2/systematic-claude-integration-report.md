# Claude host integration — canonical repair-authorization ledger

The remaining consumer half of workstream 3. The Codex driver was already the ledger's
only consumer; the Claude `runEngine` still charged `workflow.json.repair_routes` and read
its budget from a count the load-dag agent summarized out of that file. That temporary
consumer gap is now closed.

Files owned and changed:

- `claude/meta-skill/knowledge/run-engine/engine-core.js`
- `claude/meta-skill/knowledge/run-engine/run-engine.workflow.js` (marker-region mirror)
- `claude/meta-skill/knowledge/run-engine/README.md`
- `claude/meta-skill/knowledge/run-engine/tests/` — `repair-loop.test.js`,
  `safety-wave.test.js`, `declared-loop.test.js`, `real-gate.js`, `fake-agent.js`, and two
  new files, `ledger-double.js` and `ledger-receipts.test.js`
- `claude/meta-skill/knowledge/orchestrator-template.md`

No helper, validator, Codex file or engine outside this list was touched. The wave safety
barrier and every other dirty edit in the tree were preserved.

## Verification

```
node --test 'claude/meta-skill/knowledge/run-engine/tests/**/*.test.js'
```

→ **130 passed** (109 before this task). Focused Node tests only; no Python suite, no
commit, no install, no actual-host launch.

## 1. What replaced what

| removed | replaced by |
|---|---|
| `DAG_SCHEMA.repair_attempts` | nothing — the DAG no longer carries budget at all |
| the `loadDagPrompt` paragraph telling the agent to count `repair_routes[]` | an explicit "Do NOT report repair budgets here" |
| `repairChargePrompt` (append a `repair_routes` entry) | `authorizationPrompt` → `authorize` then `start` |
| engine-side `repairAttempts` arithmetic as the charge | the helper's `charged` map, checked against what was expected |

The engine no longer reads or writes `repair_routes`.

## 2. Executing a Python CLI from an engine with no filesystem

Claude Workflow gives the engine one actuator: an agent. Every ledger operation is
therefore a prompt that runs the canonical helper and returns its stdout verbatim:

```
printf '%s' '<request json>' | python3 .allforai/bootstrap/scripts/repair_authorization.py .
```

`authorizationPrompt` builds that line with the request shell-quoted (`shellQuote`
escapes an embedded `'` as `'\''`, so a repair node id containing a quote cannot split the
command). The prompt forbids inventing, summarizing, correcting, hand-editing or retrying,
and states that a refusal exits non-zero and still prints the verdict that *is* the answer.

Because the verdict arrives through an agent, it is evidence only if it is checked.
`ledgerReceiptError` refuses a verdict that is missing, carries the wrong `status`, names a
different `authorization_id` or `repair_node_id`, or reports the wrong `execution_allowed`.
Any of those is an `invalid_repair_authorization` blocker and nothing executes on it.

## 3. Contracts now enforced

- **Consumption first.** `ledger:consumption` runs before any node. Its `run_id` becomes
  the run identity and its `obligations[].spent` seeds the budget.
- **Initialize only `missing_ledger`.** Any other refusal — `unreadable_ledger`, a foreign
  run, an ambiguous history — stops the run. The engine never asserts a fresh budget; the
  helper reads `workflow.json` itself and refuses zero for a run that already shows
  execution.
- **Unresolved at startup blocks.** A non-empty `unresolved[]` stops the run naming the
  grants, "neither replays nor refunds them".
- **Durable unique identity.** `authorizationId(runId, repairNodeId, priorSpent)` is
  derived from the run, the repair node and each obligation's spend at the moment the
  dispatch was decided — not a clock or a random source. A driver that dies and restarts
  recomputes the *same* id, so the helper sees a replay instead of charging twice; a next
  attempt has a different prior spend and so is a different dispatch. `runIdentity(dag)` is
  likewise derived from the declared graph, so a restart finds its own ledger.
- **Atomic per-QA authorize before execution.** One grant per dispatch covering every
  funded obligation; the receipt must be `authorized` with `execution_allowed: false`, and
  each obligation's `charged` value must be exactly `priorSpent + 1`.
- **First start only.** Execution proceeds only on `started` with `execution_allowed:
  true`. A replayed claim is refused and the repair does not run.
- **Settle only observed execution.** A stage that threw is marked `execution_unknown` and
  never settled. A safety-halted wave returns before the settlement loop, so quarantined
  attempts stay unresolved too.
- Asymmetric budgets, the independent QA delivery measurement, ordinary-failure branch
  isolation and the safety wave barrier are unchanged; new tests pin that they still hold
  under the ledger.

## 4. One rule was deliberately dropped, and why

The old engine required every declared QA node to appear in `repair_attempts` with an
explicit `0`, and stopped the run when one was missing. That rule existed because an agent
summarizing `workflow.json` could silently omit a node, and an omission was
indistinguishable from a zero.

With the canonical ledger the origin is *proved* — `initialize` refuses a workflow that
already shows execution — so an obligation the ledger does not list genuinely has no
history. Absence is trustworthy here only because the document is. The rule is replaced,
not weakened, by two stricter ones: an unreadable/foreign/ambiguous ledger blocks, and an
unresolved grant blocks. `an obligation the trusted ledger does not list has provably spent
nothing` and `runEngine: a ledger that cannot be read at all stops the run before any node`
carry that reasoning in the test file.

## 5. Tests

**Real helper, no mock boundary.** `declared-loop.test.js` builds a temporary project,
copies the shipped `repair_authorization.py` in beside `check_artifacts.py` and
`evidence_freshness.py`, and answers every ledger prompt by actually running that CLI
(`realLedger` in `real-gate.js` parses the request back out of the command line the prompt
built). The prompt encoding, the request round-trip, the receipts and the real
authorize → start → settle state machine are exercised end to end. 13 tests.

**Documented mock boundary.** `ledger-double.js` re-implements only the helper's decisions
for the operations the engine calls, so the L2 suites can drive many waves without a Python
process per call. Its header says it is not the helper and that the real-helper test wins
on any disagreement; one test asserts the double itself refuses a second launch of one
grant, so it cannot quietly diverge on the rule it stands in for.

New (`ledger-receipts.test.js`, 12): a grant receipt naming another dispatch; naming
another repair node; claiming `execution_allowed`; reporting a charge that is not this
attempt; omitting the charge; a launch claim that was never granted; a **replayed** launch
claim (the crash-between-claim-and-work state) proving the repair does not run a second
time and nothing further is charged; the double's own replay refusal; an execution whose
stage threw left unsettled and unresolved; a settled grant recording the observed outcome
with no refund; a forged settlement receipt; and a guard that every ledger label the engine
emits is one the suite answers.

New in `safety-wave.test.js`: `a safety halt leaves the in-flight authorization unresolved,
never settled`, plus an assertion that a halt on a hard QA failure charges no attempt.

New in `repair-loop.test.js`: `authorizationPrompt` runs the canonical helper and forbids
inventing a verdict; shell-quoting of a request containing a quote; `authorizationId`
durability and uniqueness; `ledgerReceiptError` refusal matrix; `only a missing ledger is
initialized`; `an unresolved authorization at startup blocks`; `an unreadable ledger
obligation stops the run`; and `loadDagPrompt no longer claims any authority over the spent
budget` / `DAG_SCHEMA no longer accepts an agent-inferred attempt history`.

**Migrated, not weakened.** Every existing repair-loop assertion kept its meaning; the
charge is now asserted against the ledger's recorded spend and the `repair-authorize:` /
`repair-start:` / `repair-settle:` ordering rather than a `repair-charge:` label — a
stronger check, since it reads the accounting rather than the label that preceded it.

**Mutation check.** Three defects injected and reverted; each was caught:

| injected defect | tests failed |
|---|---|
| a replayed `start` is accepted as a licence to run | 2 |
| an unknown execution is settled anyway | 2 |
| a blocked consumption is read as zero spend | 2 |
| a repair role retains the node's own exhausted obligation | 2 |
| a blocked obligation is still dispatchable in its repair role | 1 |

## 6. Cross-loop role bypass (independent review findings 1 and 2)

The coordinator relayed `systematic-codex-independent-review.md` findings 1 and 2 mid-task
and asked that Claude not permit the same shapes. It did. The Claude expression of the
defect is not the Codex `_pending_state` ordering but the `retained` filter in `runEngine`:
a hard failure was retained — treated as "not a terminal verdict" — whenever the failing
node was the repair node of *any* still-funded loop. A node that repairs loop A and owes an
exhausted QA obligation in loop B was therefore retained, never added to `blockedFailures`,
re-dispatched in its repair role, and its own obligation was satisfied by the verdict it
wrote during a dispatch charged against loop A's budget.

Reproduced first as a failing test (`a repair role never dispatches a node that is an
exhausted obligation elsewhere`), then fixed:

- `unfundedObligation(nodeId)` — true when the node owes a QA obligation of any declared
  loop whose budget is spent or unusable, and the node is not already done.
- `retained` skips such a failure, so it becomes `unhandled`, lands in `blockedFailures`,
  and the run ends `needs_diagnosis` with that node named.
- The `ready` filter also refuses to dispatch an open obligation that is unfunded, in any
  role, so it cannot write its own verdict.
- `authorizedQa.length === 0` is now a blocker rather than a `continue`: a repair attempt
  that reaches the executor without a grant is the unpaid dispatch the ledger exists to
  prevent. With the `ready` filter this is unreachable; it is a stop if that ever changes.

Three regressions cover it: the node is never re-dispatched in its repair role; it never
completes by writing its own verdict and no closure opens behind it; and loop B's repair
node — whose only obligation is exhausted — is never dispatched unpaid and charges nothing.

Finding 3 (halt with `run_safety.py` absent) and finding 4 (blocked accounting killing
independent branches) are Codex-driver locations and were not in scope here. Claude's
equivalents already behave: a missing quarantine receipt is an explicit persistence blocker
(`a missing quarantine receipt is an explicit persistence blocker`), and an ordinary QA
failure blocks only its dependency chain (`ordinary QA failure blocks its dependency chain
but independent work continues`). Neither was re-derived against the review's repros.

## 7. Limits

- **No cross-host parity is demonstrated.** Both hosts now consume the same ledger through
  the same operations, which is the precondition ADR 0004 needs, but nothing here runs the
  shared scenario fixture against both engines. Root still owns proving equivalent business
  outcomes, and per ADR 0004 that needs actual-host acceptance, not these tests.
- **No actual-host run.** Every test drives `runEngine` with a fake or real-CLI agent in
  Node. The Workflow shell was synced and its sync-check passes, but it was not invoked.
- **`adopt_history` and `reconcile` have no engine path**, matching the Codex driver. A run
  whose ledger is missing on a workflow that already executed, or that carries an unresolved
  grant, blocks with a typed message and is recovered by running the helper deliberately.
  That is ADR 0007's accepted trade-off; it means legacy Claude runs that already spent
  `repair_routes` attempts have no automated migration, and their prior spend is not
  visible to the new ledger at all.
- **`runIdentity` is a 32-bit FNV-1a hash of the declared graph.** Collisions across two
  genuinely different plans in the same project are conceivable; the consequence would be a
  second plan resuming the first's budget rather than a reset, and the helper refuses a
  changed identity over an existing ledger either way. A stronger identity would need a
  digest the engine cannot compute without a filesystem.
- **Bootstrap must ship `repair_authorization.py`** into `.allforai/bootstrap/scripts/`.
  Whether the generator copies it was not verified here — the same open item the Codex
  report raised. Without it every ledger prompt returns `invalid` and the run fails closed
  before any node, which is safe but not working.
