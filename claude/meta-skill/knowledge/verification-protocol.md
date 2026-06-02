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

## Honest boundary

The deterministic gate ensures evidence **exists and is the right type** — it cannot
stop a determined agent that **fabricates** evidence. The hollowness detector
(`capabilities/hollowness-detector.md`) checks evidence authenticity + hunts hollow code;
the two-column report stays transparent for human spot-checks. We do not claim
un-gameability — we make the **default path honest** and lying **catchable**.
