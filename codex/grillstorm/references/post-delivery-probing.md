# Post-Delivery Probe And Critique Loop

Run this only after a delivery run has reached its terminal `delivery_status: complete`.
The audit has its own lifecycle and audits the delivered result from the user's perspective;
it never replaces or revokes the earlier completion evidence.

## Sampling frame

Build a complete frame before choosing probes:

- approved outcomes and requirements;
- modules, interfaces, invariants, algorithms, policies, and architectural decisions;
- user journeys and state transitions;
- success, empty, loading, degraded, invalid, denied, partial-failure, timeout,
  cancellation, retry, recovery, stale, concurrent, migration, rollback, and cleanup states;
- external side effects and operational lifecycle;
- test seams, runtime surfaces, startup dependencies, and execution environments.

Use the frozen `requirements-state-registry.json` produced by spec closure as the census.
Every approved requirement and applicable state must be present even when it will not be
sampled in the current round. Missing implementation/evidence discovered by the census is
already a gap candidate; do not hide it behind sampling.

Then use stratified, risk-weighted sampling for depth. Select at least one probe from every applicable
stratum, oversample high-blast-radius boundaries and previously repaired areas, and rotate
samples between rounds. Record the sampling frame, selection rationale, and unsampled
population. A green sample is evidence about that sample, never a completeness claim.

Every probe declares:

```text
probe id
axis: logic-alignment | feature-state-completeness
target requirement/state/invariant/interface
hypothesis
stimulus or inspection action
observation channel
expected evidence
falsifier
result and captured evidence
related-neighborhood keys
```

Logic probes inspect code and frozen documents. Feature/state probes must use the real
medium: browser/DOM/network/screenshot, API request and side effect, CLI invocation/exit
code, public library consumer, database/event trace, or device/external development system.
Static inspection, tests, and a proposed runbook alone cannot pass a feature/state probe.

Every feature probe records a real runtime attempt, integer exit code, and at least one
runtime evidence artifact. A `pass` requires the target to have started. Missing
dependencies, unavailable environments, and failed startup are blocking gaps with captured
failure evidence. The controller must resolve every evidence path beneath the run directory
and recompute its SHA-256; a worker-supplied hash string is not evidence.

## Axis A: Logic alignment

Sample implementation choices that materially shape behavior:

- domain model and terminology;
- ownership and dependency direction;
- algorithm/policy semantics;
- state machine and data lifecycle;
- interface shape and error model;
- reuse/extraction decisions;
- migration, compatibility, recovery, and operational strategy.

For each sample, show the user a compact evidence bundle: intended decision, actual code or
runtime trace, observable consequence, and the most plausible mismatch. Grill whether the
implementation logic matches what the user meant, not merely whether tests pass.

## Axis B: Feature and state completeness

Build a requirement-by-state matrix. Probe behavior details, transitions, feedback, and side
effects across applicable states. Include cross-module and recovery paths, not only isolated
happy paths. Explicitly list cells deferred to a later round; none may remain when the audit
closes.

Report completeness separately:

- `implemented-and-probed`;
- `implemented-evidence-only`;
- `missing`;
- `contradictory`;
- `verification-failed`;
- `not-applicable` with rationale.

Grill whether the delivered behavior feels complete and correct in detail. A feature name
marked implemented is insufficient when loading, empty, error, permission, retry,
concurrency, or recovery behavior is missing or wrong.

## Grill loop

Use `prompts/outcome-critique-grill.md`. Present one evidence bundle and one question per
turn with a recommended judgment and main tradeoff. Do not ask the user for facts that probes
can discover. Persist each answer before continuing.

Classify feedback as:

- `confirmed`: matches intent;
- `gap-seed`: observed or suspected mismatch, including inability to start or execute the
  required runtime;
- `preference`: a newly expressed preference outside the approved goal;

A preference becomes a gap only after the user accepts the scope change.

## Similar-gap expansion

For every gap seed, run `prompts/gap-expander.md` in a fresh `THINK` context. Search:

- the same invariant, policy, algorithm, or state transition;
- sibling consumers/producers of the same interface;
- parallel adapters, commands, screens, endpoints, and modules;
- the same error/retry/permission/recovery pattern;
- duplicated code or tests that may share the defect;
- adjacent and inverse states;
- prior repair sites and weak/missing test seams.

Turn candidates into probes before calling them gaps. Record disproved candidates as well as
confirmed related gaps so later rounds do not repeat work.

## Rounds and saturation

Each round:

1. rotate the sample across both axes;
2. Grill one evidence bundle at a time;
3. expand every new gap seed;
4. probe expansion candidates;
5. update gap families and the remaining sampling frame.

Run at least two rounds. Continue until two consecutive rounds produce no new gap family,
no new blocking member of an existing family, and no unexplored registry cell. Then ask
one final Grill question confirming that the critique has reached practical saturation.
Never claim exhaustive coverage from sampling.

Persist the machine control plane:

- `probes/probe-plan.json`;
- `probes/probe-results.jsonl`;
- `probes/probe-state.json`;
- `gaps/gap-manifest.json`.

Run `scripts/validate_probe_artifacts.py` after each round and before declaring saturation.

## Gap documents and the next cycle

Write `gaps/catalog.md` and one `gaps/<gap-id>.md` per confirmed gap family:

```markdown
# <Gap family>

## Parent delivery
## User-observed mismatch
## Expected versus actual
## Probe evidence
## Related confirmed instances
## Disproved candidates
## Affected requirements/states/interfaces/modules
## Risk and blast radius
## Open decisions
## Recommended next scope
## Acceptance and regression probes
## Source rounds
```

Do not rewrite the completed parent's historical specs/tasks or change its delivery status.
Close the independent audit as `clean` or `gaps`. Missing runtime evidence is a gap. For
confirmed gaps, create a linked remediation delivery run using the gap catalog as discovery
input, route it by actual blast radius, and begin the normal spec/task/execution closure
cycle. Each machine manifest entry records affected requirement/state IDs, recommended
scope, acceptance probes, child delivery run ID, and child state path. Validate it with
`--require-child-links` after child creation. Preserve parent/audit/child pointers in all
states. Every remediation run has its own delivery endpoint and may start a later audit
cycle.
