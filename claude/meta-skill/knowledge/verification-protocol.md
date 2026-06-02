# Verification Protocol (epistemic honesty)

**Why this exists:** meta-skill once reported a product at 94.65/100 "launch-ready"
when it was < 30% done — a 3× inflation. The cause: verification read self-reports
and artifact files instead of exercising the real product. This protocol makes
"generated" unable to masquerade as "verified."

## The one rule

> A node counts as **verified** only with REAL external evidence that the behavior
> actually works. No evidence → `verification.method: "none"` → it is `unverified`,
> never counted toward completeness.

## Three states (evidence-derived, computed by `compute_completeness.py`)

- **verified** — real evidence on disk, produced by a verifier ≠ the generator.
- **unverified** — generated, but unproven (the honest default — say so plainly).
- **failed** — blocking findings.

## What counts as REAL evidence (`verification.method`)

| method | evidence_path must contain |
|--------|----------------------------|
| `real-run` | captured output of actually running the built thing (not a description of running it) |
| `real-test` | a test that exercises the **real** path (not a mock/stub) + its passing output |
| `real-api` | a real request/response transcript hitting the running service with real data |
| `db-query` | the real row(s) the action wrote/changed |
| `screenshot` | an image of the working screen with real data (not a mockup/placeholder) |
| `none` | **you did not exercise it** — be honest, do not invent evidence |

## Rules for verify node-specs

1. **Independent.** The verifier MUST NOT be the generator. Self-grading is downgraded
   automatically (`verifier == generated_by` → `unverified`).
2. **Disprove, don't confirm.** Default posture: assume it does NOT work; try to make
   the real flow fail. Only `verified` if it survives.
3. **Exercise reality.** Start the service / launch the app / drive the flow with real
   data. Reading the spec or the diff is NOT verification.
4. **Capture proof to a file** and return `verification: {method, evidence_path, verifier, claim}`.
   `evidence_path` must EXIST on disk (the deterministic gate `check_evidence.py` downgrades
   missing-evidence claims).
5. **No upgrading.** Never raise `method` above what you actually did. "Generated but I
   couldn't run it" is `none`, and that is the correct, honest answer.

## Anti-fabrication: capture, don't author (L1) + reproduce (L2)

Free text is forgeable; a real execution is not. For every command-based method
(`real-run`/`real-test`/`real-api`/`db-query`), **do NOT write the evidence yourself** —
capture it with a tool:

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/capture_evidence.py <evidence_path> -- <the real command>
```

`capture_evidence.py` runs the command and records `{command, exit_code, stdout, stdout_sha256}`
— you choose WHAT to run, the script records what ACTUALLY happened. `check_evidence.py`
downgrades any command-method evidence that is NOT a `capture_evidence/v1` record (free text →
`unverified`). An independent pass then re-runs it:

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/reverify.py <evidence_path>   # must REPRODUCE exit 0
```

A fabricated record (claims exit 0 for a command that really fails) is caught by reverify.
To fake evidence that survives capture + reverify, the command would have to actually pass —
i.e. you'd have to really make it work. That is the point: **make doing it the easy path.**

(`screenshot` is exempt from the capture-record rule — it's an image; its authenticity is
checked by the hollowness detector / human, not by reproduction.)

## Honest boundary

This is defense-in-depth, not un-gameability. Provenance over content: capture (L1) +
reproduction (L2) kill free-text and non-reproducing fabrication; the hollowness detector
(L3, `capabilities/hollowness-detector.md`) checks the command exercises the REAL system (not
a local fake) and hunts hollow code; the transparent two-column report enables human spot-check
sampling (L5). A determined faker who stands up a fake service that really passes can still
fool L1/L2 — that residual is what L3 + human sampling cover. We make the **default path honest**,
fabrication **expensive and reproduction-checkable**, and the report **transparent**.
