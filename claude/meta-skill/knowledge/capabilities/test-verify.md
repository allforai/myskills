# Test Verify Capability

> Capability reference for test verification (smoke, test vectors, protocol compat).
> Bootstrap may create one or multiple nodes from this capability depending on project complexity.

## Purpose

Run test suites against translated code. Entry point is a passing compile-verify
(R1 build). Covers runtime smoke, functional test vectors, and protocol compatibility.

## Protocol

1. Run test command(s)
2. Capture results (pass/fail counts, error details)
3. On failure: categorize (logic error vs missing mock vs integration issue)
4. Feed failures back to translate or compile-verify as appropriate

## Verification Layers (from cr-fidelity)

| Layer | Name | What | How |
|-------|------|------|-----|
| R1 | Build | Code compiles | Build command (handled by compile-verify node — prerequisite) |
| R2 | Smoke | App starts | Launch + health check endpoint |
| R3 | Test vectors | Known input→output | Execute extracted test vectors against target |
| R4 | Protocol compat | Custom protocol behavior | Protocol-specific test suite (only if discovery flagged custom protocols) |

Composite score = static * 0.5 + runtime * 0.5. R1 failure = everything fails.

### Adaptive Dimension Selection

LLM evaluates which layers apply per project before running tests.
Outputs `verification_reasoning[]` in test-verify-report.json:

```json
{
  "verification_reasoning": [
    {
      "layer": "R2",
      "applicable": true,
      "reasoning": "Project has HTTP server with /health endpoint. Smoke check is trivial and high-value.",
      "risk_if_skipped": "medium"
    },
    {
      "layer": "R4",
      "applicable": false,
      "reasoning": "No custom protocols detected during discovery. Standard HTTP/REST only.",
      "risk_if_skipped": "low"
    }
  ]
}
```

No silent skips — every layer must appear in reasoning, either `applicable: true` or `applicable: false` with justification.

## Failure Routing

| Failure Type | Root Cause | Route To |
|-------------|------------|----------|
| App won't start (R2) | Missing config, port conflict, env var | compile-verify or node-spec fix |
| Test vector mismatch (R3) | Logic divergence from source | translate node — intent_rebuild for affected component |
| Mock resolution error | Test harness not adapted for target platform | translate node — test file fix |
| Protocol incompatibility (R4) | Custom protocol not faithfully reproduced | translate node — protocol_spec driven rebuild |

## Pass Threshold

Bootstrap sets `min_pass_rate` per layer (default: R2 = 100%, R3 = 90%, R4 = 100%).
If actual rate < threshold → trigger fix loop (max 3 cycles).
If not resolved → surface as UPSTREAM_DEFECT with per-layer breakdown.

## Rules

1. **Test commands from node-spec**: Bootstrap generates them per platform and test framework.
2. **R1 (build) is prerequisite**: Do not run tests if compile-verify has not passed.
3. **Adaptive dimensions**: LLM evaluates which verification layers apply per project — not all projects need R4.
4. **No silent skip**: Each verification layer must be explicitly evaluated with reasoning before being excluded.
5. **Failure routing before retry**: Classify failure type before retrying — prevents misdirected fixes.
6. **Score persistence**: Write composite score to test-verify-report.json for downstream nodes (visual-verify, tune) to reference.

## Composition Hints

### Single Node (default)
For small-to-medium projects: one test-verify node runs all verification layers (R2-R4) sequentially.

### Split into Multiple Nodes
For large projects: split per test layer (test-verify-unit, test-verify-integration, test-verify-e2e) to isolate failure domains and allow parallel execution.

### Merge with Another Capability
For very simple projects (single platform, no custom protocols): merge compile-verify + test-verify into a single build-and-test node.
