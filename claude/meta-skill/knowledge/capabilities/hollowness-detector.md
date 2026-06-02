# Capability: hollowness-detector

**Purpose:** the adversarial half of verification honesty. Hunt code that is GREEN BUT
HOLLOW — compiles / tests pass / report says done, yet the feature does not actually work
for a real user. This is what inflated TeteChat to 94.65% on a < 30% product.

**Trigger:** run during the verification phase, AND as a standalone audit on any codebase
whose completeness is suspect. Independent of the generator.

## What to hunt (the four hollow patterns)

| type | signature | how to confirm |
|------|-----------|----------------|
| `fake_success` | handler/UI returns success without doing the work (e.g. `return ok()` / local optimistic state with no real backend call) | trace the call path: does it reach a real service + real persistence? |
| `mocked_backend` | the "working" feature is wired to a mock/stub/in-memory fake, not the real service | grep for mock/stub/fake/dummy/sample in the production path; check the real endpoint exists and is called |
| `ui_no_data` | screen renders with hardcoded/sample/placeholder data, not real fetched data | find the data source; is it a literal/fixture or a real query? |
| `stub_handler` | endpoint returns 200 with canned/empty data; not implemented | call it for real; compare response to a real implementation's contract |

## Method (adversarial, reality-anchored)

1. Take each node claiming `verified` (or `completed`) and its `evidence`.
2. **Try to falsify the claim.** Follow the real call path from UI/entry → service →
   persistence. If any hop is fake/mock/missing, it is hollow.
3. Check the evidence is **authentic**: a screenshot of real data (not a mockup); a test
   that hits the real path (not a mock); an API transcript with real ids/values.
4. For every hollow finding, **downgrade** the node and record it.

## Output: `.allforai/quality/hollowness-report.json`

```json
{
  "scanned": 152,
  "hollow_nodes": [
    {"node_id": "...", "type": "fake_success", "path": "file:line",
     "evidence": "the call returns ok() without reaching tete-im", "downgrade_to": "unverified"}
  ],
  "authentic_evidence": 41,
  "fabricated_or_missing_evidence": 12
}
```

Downgrades feed back into `compute_completeness.py` (a hollow node is `unverified`, never
counted). Pair with `${CLAUDE_PLUGIN_ROOT}/../knowledge/verification-protocol.md`.
