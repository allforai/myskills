# Capability: hollowness-detector (retired)

> Status: retired (ADR-0008, #55). Kept as a tombstone so a workflow or node-spec generated
> before retirement resolves this path and reads why it is refused, instead of finding a
> missing file. `validate_bootstrap.py` refuses any workflow or node-spec that names this
> capability, by name; do not plan it, do not suppress-rule around it.

If this file is opened by a node: return `NOT_APPLICABLE`. Do not hunt hollow code, do not
downgrade other nodes, do not write `.allforai/quality/hollowness-report.json`.

## Where the work went

The verdict "is this feature fake" is a judgement the author of the delivery cannot honestly
reach from inside its own pipeline; it belongs to `/cross-exam`, run by the user after the
pipeline, whose prober follows the call path and walks the user's journeys against an oracle.
`fake_success` and `ui_no_data` live there.

Two of the old patterns need no judgement and stay in `/run` as refusals, with cross-exam's
reason strings, so a green-but-hollow node is never counted:

| pattern | what refuses it | reason |
|---------|-----------------|--------|
| `mocked_backend` — the request went through a mock layer (`served_by.mock_layers` non-empty) | `compute_completeness.py`; the evidence-entry gate (#59) | `经 mock 层（…）的 runtime 不能判 done` |
| `stub_handler` — the response is the canned fixture the mock serves (`served_by.fixtures`) | `compute_completeness.py`; the evidence-entry gate (#59) | `响应与 fixture 一致（…）的 runtime 不能判 done` |

The evidence contract these refusals read is in `knowledge/verification-protocol.md`.
