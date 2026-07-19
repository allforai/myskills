# Codex wrapper and artifact hardening — GREEN validation

Date: 2026-07-20

## RED pressure baseline

The pre-change pressure test demonstrated that prose output, broad path lists, mutable control
inputs, legacy command templates, and direct integration merges could violate orchestration
constraints. See `codex-wrapper-artifact-red-baseline.md`.

## Adversarial review loop

The first independent post-implementation review rejected the build for five concrete gaps:
supervisor mutation after admission, missing control hashes/non-relaxable sandbox, unconnected
merge-intent recovery, missing Codex version validation, and no candidate-stage artifact replay.
Those findings were treated as failing tests, not waived.

The corrected implementation now:

- schema-binds executor/supervisor results to runner-owned files and ignores diagnostic streams;
- compares executor-reported paths with the real Git diff;
- admits artifacts both before and after supervision, including final content SHA-256 values;
- freezes tracked control inputs and forces a CLI-precedence, worktree-only/no-network sandbox;
- rejects host bypass and additional writable-directory flags;
- replays artifact admission plus acceptance in a candidate worktree before CAS publication;
- recovers durable merge intents before scheduling and releases dependencies only after durable
  merge completion;
- binds the Phase 0 policy to host argv, wrapper/config hashes, executable pins, and Codex version;
- uses `python3`/`sys.executable` only.

## Automated evidence

The full Codex Megastorm plus Cross-exam script suite passes under `python3 -m pytest`; Python
byte-compilation and `git diff --check` also pass. Targeted tests include same-path supervisor
replacement, control-plane mutations, stdout/JSON spoofing, alias/wrapper replay, inherited model
ownership, candidate CAS races/crashes, concurrent stale-baseline candidates, and macOS-style
`python3`-only PATH execution.
