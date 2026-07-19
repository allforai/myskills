# Codex wrapper/model/artifact RED baseline

Captured on 2026-07-20 before implementation or skill edits.

The existing skill correctly rejected conversational direct merging and required
an exact final JSON object in prose, but the pressure scenario exposed these
unclosed behaviors:

- tier models were always appended even when a wrapper fixed the model;
- no wrapper boundary, argument ownership, contract, or drift check existed;
- orchestration, task, model, prompt, state, and runner files were not explicitly
  frozen against worker edits;
- actual diff did not have a complete operation-aware artifact contract;
- the authoritative acceptance-command hash was not frozen;
- no deterministic `needs_replan` outcome/subgraph invalidation existed;
- supervision happened before merge, with no candidate-ref integration gate;
- permissive implementations could rationalize extracting JSON from prose.

Observed rationalizations included:

- “Phase 0 chose the model, so append `-m` even if the wrapper fixes one.”
- “The wrapper owns `-p`, so preserving it without a grammar is correct.”
- “The JSON is present, so extract it from surrounding prose.”
- “The orchestration/model edits are internal implementation details.”
- “Tests pass, so undeclared generated files are harmless.”
- “The executor improved the acceptance command.”
- “Pre-merge green is sufficient admission.”

GREEN must reject every shortcut through deterministic code, not prompt wording
alone.

