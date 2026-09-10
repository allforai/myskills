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
6. **Name where the request went.** Runtime evidence (`real-run`/`real-api`/`db-query`/
   `screenshot` of a running app) carries `served_by: {host, process, mock_layers, fixtures?}`
   — the host and process that answered, the mock layers **in effect** (MSW registered,
   json-server / miragejs / nock listening, an explicit stub switch on; `[]` when none), and
   the canned fixture files that could have answered instead. `compute_completeness.py`
   refuses, in cross-exam's words, an entry with a non-empty `mock_layers`
   (`经 mock 层（…）的 runtime 不能判 done`) or whose response is identical to a declared
   fixture (`响应与 fixture 一致（…）的 runtime 不能判 done`); a refused entry is `unverified`.
   Whether the feature is hollow beyond that — success returned without doing the work, a
   screen of placeholder data — is a judgement, and it is `/cross-exam`'s (ADR-0008).
7. **Runtime gates also write ledger-shaped entries.** product-verify, runtime-smoke-verify and
   test-verify write, beside their human reports, `<run>/evidence-entries/<node_id>.json` in
   cross-exam's ledger-entry shape: `medium`, `verdict`, `build` (whole-tree identity from the
   shared engine, host directories excluded and said so in `build_excludes`), `probed_at` with an
   offset, `evidence.dir` under `<run>/evidence/`, `served_by` as in rule 6, `readback` of every
   applied axis, `images` + `image_digests`, and the author marker
   `{pipeline: "meta-skill/run", node_id, capability}`. Record them with
   `capture_evidence.py entry <run> <draft.json> --node <id> --capability <name>` (it adds build,
   probed_at, digests and the marker, and refuses a draft that fails) and check them with
   `check_evidence.py --entries <run> --node <id>`; a gate with a refused, missing or empty entries
   file is not passed. Each capability text states what its entries must satisfy;
   `evidence_freshness` binds the file and every cited evidence file as the node's outputs.

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
checked by the second visual review (ADR-0002) and its `served_by`, not by reproduction.)

## Honest boundary

This is defense-in-depth, not un-gameability. Provenance over content: capture (L1) +
reproduction (L2) kill free-text and non-reproducing fabrication; the `served_by` refusals
(L3, rule 6) keep a command that answered through a mock layer or with a canned fixture from
counting; the transparent two-column report enables human spot-check sampling (L5). A
determined faker who stands up a fake service that really passes, and declares no mock layer,
can still fool L1–L3 — that residual is not `/run`'s to judge: it is what `/cross-exam` covers
afterwards, as a party that did not write the code (ADR-0008), plus human sampling. We make
the **default path honest**, fabrication **expensive and reproduction-checkable**, and the
report **transparent**.
