# Review, Repair, And Runtime Validation

Review is a repair gate, not a report-only afterthought.

## Fixed point

Use the starting ref captured in Phase 0 and preserve the list of pre-existing dirty paths.
Review only Grillstorm-owned changes. Never treat a user's earlier edits as this run's work.

## Two review axes

Run Standards and Spec reviews in two independent fresh contexts, concurrently when the host
supports it, so neither axis pollutes the other. If independent contexts are unavailable,
the original code-review gate is not satisfied; record it as an unclosed gate rather than
presenting a main-context self-review as equivalent.

### Standards

Check the complete owned diff against repository instructions, contribution guides, style,
security rules, and architecture conventions. Also inspect these baseline smells:

- mysterious names and duplicated logic;
- feature envy, data clumps, and primitive obsession;
- repeated switches and message chains;
- shotgun surgery and divergent change;
- speculative generality and unnecessary middle layers;
- refused inheritance that should be composition;
- module boundary violations and test coupling to implementation.

Repository standards override generic heuristics. Tool-enforced formatting is not a manual
finding.

### Spec

Trace the diff backward to approved requirements, module specs, interfaces, and acceptance:

- missing or partial requirements;
- behavior that was not requested;
- apparently implemented behavior with incorrect semantics;
- mismatched producer/consumer contracts;
- error, empty, loading, degraded, migration, or compatibility states omitted;
- tests that pass without proving the requirement.

Write findings with severity, file/line evidence, violated source, and required repair.
Preserve the two axis reports separately and do not merge or rerank their findings.
Keep each axis report under 400 words. Aggregate them side by side, then state finding counts
and the worst issue within each axis without choosing one cross-axis winner.

## Repair loop

Blocking findings are `critical`, `high`, or any issue that breaks a requirement, public
contract, data safety, security, or acceptance proof.

1. Write separate `reviews/standards.md` and `reviews/spec.md`.
2. Convert blocking findings into repair entries in the owning module task document.
3. Fix them using the implementation and diagnosis protocol.
4. Rerun affected focused, contract, module, and runtime checks.
5. Rerun both review axes over the updated diff.

Repeat until no blocking findings remain. Low-risk judgment calls may remain only when the
launch contract permits autonomous acceptance; record the rationale.

## Runtime validation

Static tests alone do not prove user-visible delivery. Select the real medium:

- Web: start the app, exercise flows with browser automation, inspect DOM, console, network,
  and relevant loading/empty/error/success states; capture screenshots when visual behavior
  matters.
- API: run real requests against a development instance and verify response plus observable
  side effects.
- CLI: invoke the built command with representative fixtures and verify output, errors, and
  exit codes.
- Library: execute a consumer-level integration example through the public API.
- Mobile/device/external system: use available simulator or development service; otherwise
  follow the approved reality-gate runbook without inventing a pass.

Write `reviews/runtime.md` with the environment, steps, evidence, failures, and repairs.
Never test destructive or paid production behavior without explicit launch authorization.

## Global completion gate

The goal is complete only when:

- every required module is verified;
- every requirement traces to owned code and passing proof;
- every interface has a working producer, consumer, and contract check;
- focused, module, integration, type/static, and full required suites pass;
- standards and spec reviews have no blocking findings;
- user-visible flows pass runtime validation;
- placeholders, dead endpoints, fake success paths, and debug instrumentation are absent;
- reality-gated items are reported separately and never presented as autonomously verified.

The final report must also summarize every entry in `autonomous-decisions.md` and identify
which requirements, interfaces, tasks, code, and checks changed as a result.
