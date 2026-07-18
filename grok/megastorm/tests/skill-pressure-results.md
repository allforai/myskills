# Grok skill GREEN/REFACTOR results

Independent pressure reruns on 2026-07-18 used the exact RED scenarios recorded
in `skill-pressure-baselines.md`.

## Megastorm: pass

The agent refused to skip Phase -1/0, refused single-context self-approval,
required isolated task worktrees, rejected blind `--yolo`/configuration
inheritance, and refused a class-wide claim without census reconciliation.

The first rerun found two stale direct references in `execution-playbook.md`.
They were changed to the verified Grok command/NDJSON contract and
`schemas/megastorm.md` path.

## Cross-exam: behavioral pass, deterministic loophole closed

The agent hard-stopped when native subagents were unavailable, refused author
self-review and headless substitution, refused evidence-free `done` judgments,
and did not fix audited work.

The rerun found that the initial renderer trusted a self-asserted boolean and
non-empty prober IDs, while evidence admission accepted any non-empty directory.
The renderer and schema were tightened to require:

- a native-dispatch manifest with canonical session attestation;
- entry identity correlation with that manifest;
- a non-empty explicit evidence file list;
- contained, non-empty regular files; and
- a non-empty key observation.

Tests now reject missing/forged dispatch attestations, unmatched prober identity,
placeholder evidence, missing files, empty artifacts, and path escapes.

