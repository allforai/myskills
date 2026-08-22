# Review And Runtime Adapter

Load official `code-review` after each verified work unit and at global close. Follow its
two-axis method. This file is not a second review protocol.

## Grillstorm wiring

Review only Grillstorm-owned changes from the Phase 0 starting ref. Write separate
`reviews/standards.md` and `reviews/spec.md`. Convert blocking findings into repair entries,
fix them, rerun affected checks, and rerun official `code-review` until no blocking findings
remain.

Material changes must still reach an authoritative purpose chain and observable outcome.
Additions and deletions need symmetric evidence.

## Runtime validation

Static tests alone do not prove user-visible delivery. Exercise the real medium (web, API,
CLI, library, or device) and write `reviews/runtime.md`. Never test destructive or paid
production behavior without launch authorization.

## Global completion gate

Complete only when required modules are verified, requirements trace to owned code and
passing proof, official review axes have no blocking findings, runtime validation passed,
and `autonomous-decisions.md` is summarized.
