# Implementation And Diagnosis Adapter

Load official `tdd` for the red-green loop. On a hard bug, load official `diagnosing-bugs`.
Do not load official `implement`. This file is only Grillstorm execution constraints.

## Coding invariant

Write the primary approved behavior. Do not swallow exceptions, return convenient
zero/empty/default values, reuse stale data, install no-op adapters, silently skip required
side effects, switch algorithms/providers, or make partial work look successful.

If the primary implementation cannot satisfy the contract, keep the failing test, return
`needs_replan`, and repair the plan.

## Non-vacuous proof

An acceptance command is valid only if it exercises the real production path, selected tests
exist with real assertions, expected values are independent, and the command exits nonzero
when the required behavior is broken.

## Secret redaction

Before showing or persisting any diagnostic command, output, request, log, trace, HAR,
payload, or captured artifact, redact API keys, tokens, passwords, cookies, session IDs,
connection strings, signed URLs, authorization headers, and private keys as `<REDACTED>`.
Keep credentials
in environment variables so runnable loops refer to variable names rather than literal values.

## Autonomous diagnosis

During the autonomous run, write ranked hypotheses and outcomes into task evidence. Do not
interrupt the user. Track hypotheses by family (same suspected root cause, however worded).
When the next idea belongs to a family already refuted, that family is exhausted: move to the
next recommended safe path or an explicit reality gate. A genuinely new family is always worth
one attempt — hard bugs are often solved by the fourth or fifth root cause, not the third.
