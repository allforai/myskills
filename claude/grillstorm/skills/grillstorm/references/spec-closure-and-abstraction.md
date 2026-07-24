# Spec Closure And Abstraction

Run this pass after all applicable specs are approved and persisted locally, but before
publishing the final `to-spec` result or generating tickets and execution tasks.

The early reuse radar in `reverse-closure.md` supplies candidates only. Re-evaluate them
against the completed consumer specs here; do not inherit its recommendations blindly.

The pass has a Grill gate followed by two independent critics:

- **Reverse Spec Grill:** trace observable completion backward and actively surface missing
  problems, design decisions, contradictions, exceptional behavior, abstraction questions,
  and proof gaps. Use `prompts/spec-reverse-grill.md`.
- **Closure critic:** trace the goal through behavior, ownership, interfaces, failure modes,
  test seams, runtime observation, and completion evidence.
- **Abstraction critic:** look for existing modules to reuse and repeated/stable concepts
  that justify a new deep module ahead of consumers.

Run the reverse Grill first. Resolve discoverable facts and unambiguous spec repairs
internally. Ask only true product/design decisions, exactly one at a time, with a recommended
answer and tradeoff, and record the result in `reviews/spec-grill.md`.

Only after that gate closes, run the closure and abstraction critics in separate fresh
contexts, concurrently when supported. Critics produce findings only; the orchestrator owns
edits and decisions. Use `prompts/spec-closure-critic.md` and
`prompts/abstraction-critic.md`, resolved relative to the skill root. Keep their inputs and
outputs separate until both finish.

## Closed-loop matrix

Build `reviews/spec-closure.md` with one row per requirement:

```markdown
| Requirement | User outcome | Owner | Inputs/interface | State/failure behavior |
| Test seam | Runtime observation | Completion evidence | Status |
```

Then trace both directions:

1. **Forward:** goal -> requirement -> owner -> interface/data transition -> test seam ->
   runtime observation -> completion evidence.
2. **Backward:** every module, interface, state, seam, and proposed side effect -> requirement
   and user outcome that justify it.

Block on:

- unowned or multiply owned behavior/data;
- requirements without observable proof;
- interfaces without producer, consumer, error semantics, or compatibility policy;
- success paths whose real side effect is not verified;
- failure/degraded/rollback behavior that cannot return to a safe state;
- orphan modules, interfaces, abstractions, or tests with no requirement;
- dependency cycles or a consumer that must know a provider's implementation details;
- duplicated responsibility or invariant enforcement across module boundaries.

## Reuse and abstraction review

Inspect the existing codebase before proposing anything new. Prefer, in order:

1. reuse an existing module as-is;
2. extend an existing deep module without leaking new implementation detail;
3. extract a new module only when the current approved scope supplies evidence.

A new module is justified only when all are true:

- it owns one stable domain concept, policy, state machine, integration boundary, or
  cross-cutting invariant;
- at least two current consumers need the same semantics, or one correctness/security
  invariant needs one authoritative owner;
- it removes duplicated knowledge or reverses an unhealthy dependency direction;
- it can expose a smaller, more stable interface than the complexity it hides;
- it has independent behavioral test seams;
- its lifecycle and data ownership are coherent;
- the approved scope needs it now.

Reject speculative second implementations, generic `utils` buckets, thin pass-through
wrappers, abstraction based only on similar syntax, and modules whose callers still need to
understand their internals.

## Extracting a module

When extraction is justified:

1. Add the module to `program-spec.md` with explicit responsibilities and
   non-responsibilities.
2. Write `modules/<new-module-id>-spec.md`.
3. Assign its data/invariant ownership and dependency direction.
4. Mint or reassign interface IDs and define errors/versioning.
5. Define its behavioral and contract test seams.
6. Update every producer/consumer module spec.
7. Put the new module before consumers in the dependency graph.
8. Invalidate affected approvals and resolve only newly introduced decisions one question
   at a time.
9. Rerun the reverse Spec Grill and both critics over the complete graph.

Increment `spec_revision` and explicitly invalidate affected task, workflow, and launch
revisions whenever extraction or reuse changes the graph.

Do not merely add a future task called "extract shared module." The module boundary,
interface, seam, and consumer migration must be settled in specs before task planning.

If a compact `direct` or `ticketed` route discovers a genuinely independent reusable module
or cross-module interface, promote the route before continuing.

## Exit gate

The pass closes only when:

- the reverse Spec Grill has applied every lens to every global outcome and has no
  unresolved issue or decision;
- every matrix row is closed or explicitly reality-gated;
- backward tracing finds no unjustified artifact;
- reuse candidates have an explicit reuse/extend/extract decision;
- any extracted module is fully specified and precedes its consumers;
- both critics have zero blocking findings after the final revision;
- `program-spec.md`, module specs, domain docs, ADRs, and `state.json` agree.

After any Grill answer, discovery, repair, or critic-driven edit, discard all prior global
verdicts and rerun the reverse Grill plus both critics from the final outcomes. Checking
only the repaired finding is insufficient.

After closure, run the original `to-spec` synthesis without another broad interview,
publish/update the final spec in the configured tracker, and apply `ready-for-agent`. Only
then may `to-tickets` and machine workflow generation begin.
