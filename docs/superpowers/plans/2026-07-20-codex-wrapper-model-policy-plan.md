# Codex wrapper, model policy, and artifact gateway implementation plan

## Objective

Implement the approved design in
`docs/superpowers/specs/2026-07-20-codex-wrapper-model-policy-design.md` while
preserving existing Codex Megastorm/Cross-exam behavior and macOS `python3`
compatibility.

## Tasks

### 1. Capture RED behavior

- Pressure-test the current skill with a fixed-model wrapper and malicious worker
  artifacts.
- Record wrapper/model, loose output, control-plane, scope, and merge loopholes.
- Do not edit `SKILL.md` until the baseline is captured.

### 2. Model-policy artifact and validation

- Add failing tests for `inherited` and `tiered` policy inference.
- Add strict `locked|unlocked|unknown` source precedence.
- Add Phase 0 confirmation artifact, argv HMAC, executable/config/contract hashes,
  model mappings/source, preview, and resume drift validation.
- Require inherited for unknown ownership; prohibit hidden override.

### 3. Wrapper contract and command construction

- Add direct alias-expanded and contracted wrapper fixtures.
- Implement typed secret placeholders, explicit boundary/arity, replay safety,
  dual executable pins, version checks, and in-memory materialization.
- Implement exact root/exec option partitioning and capability-gated dangerous
  flags under a non-relaxable worker envelope.
- Remove legacy templates from normal verified execution; isolate unsafe
  compatibility behavior.

### 4. Strict result channel

- Freeze executor/supervisor JSON schemas per attempt.
- Use runner-owned `--output-schema` and new attempt-owned
  `--output-last-message` files.
- Reject pre-existing/symlinked/partial/multiple/narrative/identity-mismatched
  results and stdout-only verdicts.
- Replace permissive greedy verdict extraction.

### 5. Artifact contract and frozen control plane

- Add versioned task-contract validation with exact POSIX pathspec/operation
  semantics.
- Enforce control-plane fingerprints, actual Git operations, rename endpoints,
  generated outputs, links, submodules, counts, required outputs, acceptance
  hash, and typed interface verifiers.
- Add `needs_replan` state/event behavior and affected-subgraph invalidation.

### 6. Transactional integration

- Merge onto task-specific candidate refs/worktrees.
- Run post-merge interface/acceptance checks before publication.
- Persist intent, CAS-advance integration only after checks, persist completion,
  then release dependents.
- Test conflicts and crashes at intent/CAS/complete boundaries.

### 7. Skill GREEN/REFACTOR and Python compatibility

- Update skill/playbook/schemas/model examples from observed RED failures.
- Re-run the identical pressure scenario and close remaining loopholes.
- Add scoped static/runtime tests proving Megastorm-owned commands use
  `python3`/`sys.executable`, with a PATH fixture lacking `python`.

### 8. Regression and acceptance

- Run focused host, channel, artifact, runner, Git, cancellation, resume, and
  skill-pressure suites.
- Run all existing Codex Megastorm and Cross-exam tests.
- Perform independent adversarial thought-test acceptance.
- Write a report separating verified contracts from remaining reality gates.
- Commit and push `main` after approval-grade evidence.

