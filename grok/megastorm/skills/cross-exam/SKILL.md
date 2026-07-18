---
name: cross-exam
description: Use when the user explicitly requests an interactive evidence-backed audit of a delivery in official Grok Build.
---

# Cross-exam for Grok Build

Cross-exam is audit-only. It records findings and never fixes them.

## Independence hard gate

Before intake, verify that the current Grok session can dispatch fresh-context
native subagents. Every evidence-bearing observation or judgment candidate must
come from a native prober with stable child-session and attempt identity.

If native dispatch is unavailable, hard-stop before judgments or report
generation. Author self-review is not a degraded mode. A headless Grok process
is not a substitute, even if labeled non-independent.

Prober input contains only the concrete question, target/access envelope,
required states, evidence directory, and neutral context paths. Exclude the
examiner's suspicion, desired verdict, conversation history, and severity.

## Workflow

1. Confirm a local or development/test target and freeze the baseline.
2. Read `$GROK_PLUGIN_ROOT/schemas/cross-exam.md` and
   `$GROK_PLUGIN_ROOT/schemas/cross-exam-lenses.md`.
3. Create `docs/cross-exam/<date>-<target>/`, acquire the versioned run lock,
   and recover stale locks only with explicit user confirmation.
4. Dispatch a fresh census prober before studying delivery claims deeply.
5. Run selected deep-dive cards and, for completeness goals, a separate census
   sweep. Store unselected cards as `open_threads`.
6. Persist raw evidence before ledger entries. Use `done`, `gap`, `drift`, or
   `unprovable`; gaps/drift require severity.
7. Generate the report only with
   `$GROK_PLUGIN_ROOT/scripts/render_report.py`.

Native dispatch writes the session manifest and the trusted Grok host integration
supplies an in-process verifier to the renderer. The examiner cannot supply a
key, command, verifier, or CLI bypass; without the host verifier reporting stops.

Evidence must be non-empty and contained under the run's `evidence/` directory.
Missing proof becomes `unprovable` or a rejected entry, never `done`. Production,
irreversible, shared-data, or undeclared mutations are refused. Authorized
mutating probes require their exact side effect and cleanup plan. Credentials go
only to the authorized prober and never into evidence.

## Red flags

- “I authored it, so I can quickly judge it myself.”
- “A separate headless call is independent enough.”
- “We can issue a scoped report now and disclose missing subagents later.”
- “Fixing an obvious problem while auditing saves time.”

Any red flag means stop; do not render a report.
