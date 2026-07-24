# Upstream Workflow Parity

Grillstorm orchestrates Matt Pocock's small composable skills. It does not reinterpret their
inner disciplines.

## Canonical delivery chain

```text
setup-matt-pocock-skills                       once per repository
  -> grill-with-docs                           every software change
       -> grilling + domain-modeling
  -> to-spec                                   synthesize, do not re-interview
  -> to-tickets                                vertical tracer bullets + blocking edges
  -> implement
       -> tdd at pre-agreed seams
       -> regular focused/type/full checks
       -> code-review: Standards || Spec
       -> commit current branch
```

Grillstorm's only structural extensions are:

- adaptive routing that omits entire original stages when their trigger is absent;
- outcome-first reverse closure and a non-binding early reuse radar;
- top-level decomposition followed by the same grilling loop per module;
- `program-spec.md` plus linked module specs;
- a post-spec reverse Grill, closed-loop, and reusable-module review before final
  publication/ticketing;
- local task closure, reverse Grill, independent global task closure, and deterministic
  workflow simulation;
- a post-ticket/DAG reverse Grill proving the executable projection preserves approved work;
- a catalog and one rich execution document per module;
- route-aware `THINK`/`BUILD`/`VERIFY` roles frozen in the single launch contract;
- worktree-isolated concurrent execution of dependency-ready tasks;
- state/resume across context windows;
- a separately invoked durable `handoff` mode for crossing session and machine boundaries;
- autonomous adoption and logging of recommended unforeseen decisions;
- repair loops that consume the original review findings.

Routing may skip `to-tickets`/catalog for a direct single-module change or use the diagnostic
path for a bug, because the upstream skills are explicitly composable. Routing must never
partially execute or weaken a stage that it does select.

## Non-negotiable stage semantics

### Setup

Configure the issue tracker, triage vocabulary, and domain-doc layout once. Later stages read
that configuration.

### Grill with docs

Ask one decision at a time, recommend an answer, discover facts instead of asking, update
the glossary and sparse ADRs inline, and do no implementation before shared understanding.

### To spec

Do not interview again. Synthesize the approved conversation and codebase understanding,
confirm the highest practical test seams, publish the spec to the configured tracker, and
apply `ready-for-agent`.

### To tickets

Create narrow, complete, demoable vertical slices, each small enough for one fresh context.
Record blocking edges. Quiz granularity and edges before publishing. Publish one tracker
ticket per slice.

Tracker tickets stay concise: outcome, blockers, acceptance criteria, and parent reference.
Do not put volatile file paths or implementation code in tracker tickets. Grillstorm's local
module execution documents may contain expected paths and detailed steps because that is the
explicit long-task extension.

### Implement

Use TDD at the pre-agreed seams. Run typechecking and focused tests regularly, then the full
suite once at the end. Run two-axis code review. Commit owned work to the current branch
after review and repairs.

### TDD

Test public behavior, not implementation details. Work one vertical red-green slice at a
time. Do not batch all tests before implementation. Do not refactor inside the red-green
cycle; refactor during the review/repair stage.

### Code review

Pin one fixed point. Run Standards and Spec reviews in independent contexts, in parallel
when the host supports it. Preserve the two reports separately; do not merge or rerank one
axis against the other.

## Conditional supporting disciplines

Use these only when their trigger exists:

- `research`: an external fact needs primary-source investigation.
- `prototype`: a design question needs a throwaway runnable artifact.
- `codebase-design`: module depth, interface, or seam placement needs design work.
- `diagnosing-bugs`: implementation or a check exposes a hard bug.
- `resolving-merge-conflicts`: an actual merge/rebase conflict occurs.

Do not automatically run unrelated user-invoked alternatives such as `triage`,
`improve-codebase-architecture`, `wayfinder`, or `teach`. They solve different entry
conditions. Grillstorm exposes `handoff` only as a separate context-boundary mode. It
preserves the original compaction, reference-not-duplication, suggested-skill, and next-focus
semantics. Its deliberate long-run adaptation makes the repository handoff the default,
adds checkpoint and tracker pointers, and keeps the original temporary-file behavior as
`handoff local`. It is not inserted as a delivery or completion gate. Grillstorm's
state/catalog layer remains the durable source for long-run continuity.
