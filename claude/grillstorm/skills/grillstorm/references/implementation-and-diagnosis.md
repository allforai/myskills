# Implementation, TDD, And Diagnosis

Implement the approved task documents; do not stop at producing them.

## Test-driven slices

Tests verify observable behavior through approved public seams, not private implementation.
A useful test reads like a capability, survives internal refactors, and derives expected
values from the spec or a known example rather than recomputing the implementation.

For each behavioral slice:

1. Write one focused test at the approved seam.
2. Run it and see the intended behavior fail for the intended reason.
3. Implement only enough production code to make it pass.
4. Run the focused test and relevant type/static check.
5. Continue with the next slice.

Do not write all tests before all implementation. Do not test private methods, internal call
counts, or side-channel state when behavior is available through the public interface.

Mock only system boundaries such as external APIs, time, randomness, or occasionally a
database/filesystem. Prefer a real test database and real internal modules. Use narrow,
operation-specific boundary interfaces instead of one generic fetcher with conditional mocks.

Do not refactor inside the red-green loop. Refactoring belongs to the review/repair stage.

## Non-vacuous proof

An acceptance command is valid only if:

- it exercises the real production path;
- selected tests exist and contain real assertions;
- expected values are independent;
- the command exits nonzero when the required behavior is broken; and
- output shows a nonzero test or assertion count where the runner exposes one.

Existence checks, compilation alone, placeholder snapshots, and zero-test success are not
behavioral proof.

## Failure diagnosis

When implementation or a gate fails, build a tight feedback loop before theorizing:

1. Create or identify one fast command that catches the exact symptom.
2. Reproduce and minimize the failing case.
3. Generate three to five falsifiable, ranked hypotheses.
4. Test one prediction at a time with a debugger or targeted instrumentation.
5. Convert the minimal repro into a regression test at the correct seam.
6. Apply the fix, rerun the minimal and original scenarios, and remove instrumentation.

For nondeterministic bugs, increase the reproduction rate with repetition, fixed seeds,
stress, or controlled timing. If no agent-runnable loop can be built, record attempted
approaches and use the launch contract's escalation or reality-gate policy.

After three distinct failed hypotheses, stop repeating that approach. Record the evidence
and adopt the next recommended safe implementation path or rollback strategy. If no
agent-runnable path exists, convert it to an explicit unclosed/reality gate and continue
independent work. Rephrasing the same theory does not reset the count.

During the autonomous run, write the ranked hypotheses and outcomes into task evidence
instead of interrupting the user. This is the long-run adaptation of the original
non-blocking user checkpoint.

## Per-task completion

A task is verified only when:

- production code is present;
- its behavioral tests went red then green, or a justified non-TDD reason is recorded;
- its acceptance command passes with non-vacuous evidence;
- no placeholder, TODO implementation, fake fallback, or hidden mock supplies the result;
- touched paths and interface changes agree with the approved contract; and
- task evidence is written into the module task document.
