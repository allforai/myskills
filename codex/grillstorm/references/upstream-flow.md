# Upstream Workflow Parity

Grillstorm orchestrates Matt Pocock's official skills. It does not reinterpret their
inner disciplines, and it does not vendor a second copy of them.

## Canonical delivery chain

```text
setup-matt-pocock-skills                       once per repository
  -> grill-with-docs                           every software change
       -> grilling + domain-modeling
  -> to-spec                                   official synthesis; may confirm seams
  -> to-tickets                                official slices; may quiz granularity
  -> Grillstorm execution                      never official implement
       -> official tdd at pre-agreed seams
       -> regular focused/type/full checks
       -> official code-review: Standards || Spec
       -> commit owned work under the launch Git policy
```

Grillstorm's only structural extensions are:

- adaptive routing that omits entire official stages when their trigger is absent;
- outcome-first reverse closure and a non-binding early reuse radar;
- top-level official grilling followed by the same official loop per module;
- `program-spec.md` plus linked module specs as local durable copies;
- a post-spec reverse Grill, closed-loop, and reusable-module review before or after
  official publication;
- local task closure, reverse Grill, independent global task closure, and deterministic
  workflow simulation;
- a post-ticket/DAG reverse Grill proving the executable projection preserves approved work;
- a catalog and one rich execution document per module;
- route-aware `THINK`/`BUILD`/`VERIFY` roles frozen in the single launch contract;
- worktree-isolated concurrent execution of dependency-ready tasks;
- state/resume across context windows;
- a separately invoked durable `handoff` mode for crossing session and machine boundaries;
- autonomous adoption and logging of recommended unforeseen decisions after launch;
- repair loops that consume official `code-review` findings.
- a post-delivery probe-sampling and user critique loop that produces linked gap runs.

Routing may skip `to-tickets`/catalog for a direct single-module change or use the diagnostic
path for a bug, because the official skills are explicitly composable. Routing must never
partially execute or weaken a stage that it does select.

## Stage ownership

### Setup

Load official `setup-matt-pocock-skills`. Later stages read `docs/agents/`.

### Grill with docs

Load official `grill-with-docs` or `grilling` plus `domain-modeling`. Official questions are
allowed. Do no implementation before that official stage exits.

### To spec

Load official `to-spec`. Do not interview again except for questions that skill itself asks,
including seam confirmation. Publish to the configured tracker and apply `ready-for-agent`.
Keep a local copy under `docs/grillstorm/<goal-slug>/`.

### To tickets

Load official `to-tickets`. Allow its granularity quiz. Publish one tracker ticket per
slice. Grillstorm's local module execution documents may add paths, interfaces, and
acceptance commands because that is the long-task extension official tickets omit.

### Execution

Do not load official `implement`. Read `execution.md` and, when eligible, `concurrency.md`.
Inside each work unit, load official `tdd`. After the unit is coded, load official
`code-review`. On a hard bug, load official `diagnosing-bugs`.

## Conditional official disciplines

Load the official skill only when its trigger exists:

- `research`
- `prototype`
- `codebase-design`
- `diagnosing-bugs`
- `resolving-merge-conflicts`

Do not automatically run unrelated official skills such as `triage`,
`improve-codebase-architecture`, `wayfinder`, or `teach`. Grillstorm `handoff` remains a
separate context-boundary mode, not a delivery gate.
