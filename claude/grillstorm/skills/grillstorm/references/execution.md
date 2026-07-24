# Autonomous Execution Protocol

Execute only after the route's launch contract is approved. For `direct` and `diagnostic`,
the compact contract lives in `state.json`; for `ticketed` and `program`, it lives in
`launch-contract.md`. Treat the approved behavior, work units, and contract as frozen
inputs. The purpose of this phase is working, reviewed code.

## Resume loop

1. Read `state.json` and the route's execution source:
   - `diagnostic`: symptom/expected-behavior record plus the discovered regression seam;
   - `direct`: the approved spec;
   - `ticketed`: tracker tickets plus the compact catalog when one exists;
   - `program`: `tasks/catalog.md`.
2. Select the first ready work unit in dependency order.
3. Load only its approved spec or issue, relevant interfaces, repository instructions, and
   task document when the route has one.
4. Execute its first pending vertical slice using `implementation-and-diagnosis.md`.
5. Record code/test evidence and state immediately.
6. Run the applicable work-unit gate and both review axes using
   `review-and-validation.md`.
7. Repair findings until the work unit is verified, then expose newly ready work.

For eligible `ticketed` and `program` routes, read `concurrency.md` and dispatch every ready
work unit through its isolated worktree. The approved launch contract authorizes this
internal parallelism unless it explicitly selected sequential execution. `diagnostic` and
`direct` implementation remain sequential.

After all work units verify, run the route's applicable integration, full-suite, two-axis
review, and runtime validation gates. A failure reopens the owning work unit and its
affected dependents; fix and revalidate them before continuing.

## Unforeseen decisions

Do not interrupt the autonomous run for a new design or product decision. Make a recommended
choice with this priority:

1. Preserve approved user-visible behavior and compatibility.
2. Prefer existing repository patterns and domain language.
3. Prefer the smallest scope and fewest new concepts.
4. Prefer reversible choices and additive migrations.
5. Prefer the option with the strongest automated proof.

Append each choice immediately to `autonomous-decisions.md`:

```markdown
## AD-<NN>: <Decision>

- Trigger: <what surfaced>
- Recommendation adopted: <choice>
- Alternatives: <serious alternatives>
- Rationale: <tradeoff>
- Affected artifacts/code: <paths and IDs>
- Revalidation: <checks rerun>
```

Update specs, interfaces, task documents, and dependency edges affected by the decision.
Invalidate and revalidate downstream modules automatically, then continue.

An unavailable credential or authority for a destructive, production, paid, or external
action is not permission to guess. Adopt the safe option: avoid the side effect, complete all
local work, add an exact reality-gate runbook, and continue everything independent. Report
the gate at the end without claiming it passed.

Tool failures, test failures, and ordinary bugs are not decisions; diagnose and repair them.

## No internal fallback

An implementation, adapter, worker, controller, or verifier must not conceal failure by
returning a default/empty value, stale cache, mock result, partial success, alternate
algorithm, weaker model, skipped side effect, or fabricated evidence unless that exact
degraded behavior was approved in the spec. Catching an error is valid only to add context,
clean up, retry the unchanged contract within its budget, or propagate a typed failure.

When the approved path cannot work, fail visibly and preserve the evidence. Repair it,
replan affected artifacts, or create a blocking gap and linked remediation run. The
autonomous recommendation policy chooses among legitimate implementations; it never
authorizes weakening requirements or proof.

## Completion

A work unit is verified only when its production code, tests, applicable gate, runtime
checks, and review repairs have evidence. A run is complete only when every applicable
global gate in `review-and-validation.md` passes, with human-only gates separated from
automated proof.

Generating or updating Markdown files never satisfies an implementation task.
