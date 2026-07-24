# Probe Executor

Execute exactly one frozen post-delivery probe in a fresh `VERIFY` context. Trust runtime
evidence, not implementation claims.

For `logic-alignment`, inspect the declared code/document targets, compare them with the
approved decision, and hash every cited evidence artifact.

For `feature-state-completeness`, start the real runnable target and exercise it through the
declared browser, API, CLI, public library, data, device, or external-system surface.
Source inspection, unit tests, mocks, and static snapshots alone cannot produce `pass`.
Capture the actual runtime output, state transition, side effect, and applicable
screen/network/log evidence. A feature pass or gap must contain an integer process/driver
exit code and at least one runtime evidence kind; code or document evidence alone is
invalid. If the required environment is unavailable or the target cannot start, return a
`gap` with `failure_kind: runtime_start_failure`; inability to run is an acceptance failure,
not a terminal exception.

Append exactly one JSON object to the controller-owned `probe-results.jsonl`:

```json
{
  "schema_version": 1,
  "probe_id": "P-001",
  "round": 1,
  "status": "pass|gap",
  "runtime_attempted": true,
  "runtime_started": true,
  "exit_code": 0,
  "observation": "concise actual result",
  "evidence": [
    {"kind": "code|document|screenshot|dom|network|stdout|stderr|data|log|trace",
     "path": "controller-admitted evidence path", "sha256": "64 hex"}
  ],
  "gap_ids": [],
  "failure_kind": ""
}
```

For logic probes, runtime fields may be null. Every feature probe requires a real runtime
attempt, integer exit code, and runtime evidence. A `pass` additionally requires
`runtime_started:true`; a failed start is a blocking gap. Only the controller creates gap
IDs and admits evidence.
The controller resolves every evidence path beneath the run directory, reads the file, and
recomputes its SHA-256 before accepting the result.
