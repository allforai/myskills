# Handoff

This mode adapts Matt Pocock's compact handoff contract for Grillstorm's durable,
cross-session and cross-machine runs.

## Modes

### Portable handoff (default)

Write an immutable handoff to:

```text
docs/grillstorm/<goal-slug>/handoffs/<UTC timestamp>.md
```

Record its path in `state.json` as `latest_handoff`. This repository artifact is the default
because a Grillstorm run may continue on another machine.

If a tracker is configured, update the existing program/spec issue or parent ticket with a
short checkpoint containing the handoff path, commit SHA, route, phase, and open gates. Do
not paste the whole handoff into the tracker.

### Local handoff

Use only when the user explicitly requests `handoff local`. Write to the operating system's
temporary directory with owner-only permissions (`0600`). This mode changes sessions on the
same machine and is not cross-machine portable.

## Content

If the user supplied a next-session focus, tailor the handoff to it. Otherwise, describe
the next ready work unit from Grillstorm state.

Do not duplicate content already captured in specs, plans, ADRs, issues, commits, diffs,
task documents, review reports, or the execution report. Point to those durable sources by
path, tracker URL, identifier, or commit instead.

Do not redact project decisions, implementation details, personal project context, or other
information required to resume accurately.

Credential values, private keys, access tokens, and passwords must not enter Git history or
a tracker, even when the repository is private. Record the credential name, expected secret
manager or environment location, validation command, and acquiring authority instead. A
local handoff may preserve an already-present value when the user explicitly requires it.

## Minimal document

```markdown
# Grillstorm handoff: <goal>

## Next-session focus
<user argument or next ready work unit>

## Read order
1. <repository instructions>
2. <state.json>
3. <only the active specs/tasks/reports needed next>

## Current state
- Repository: <remote URL and worktree path>
- Branch/base/checkpoint: <branch and SHAs>
- Run and route: <path and diagnostic|direct|ticketed|program>
- Phase/current work unit: <resume pointer>
- Probe round/audit status: <not-started|round and next probe|audited status>
- Completed proof: <references, not copied evidence>
- Open or reality gates: <references>
- Pre-existing dirty paths to preserve: <paths or none>

## Working-tree transfer
- Grillstorm-owned changes: <checkpoint commit or untransferred paths>
- User-owned/pre-existing changes: <untouched paths>
- Focused checks at checkpoint: <commands and results>

## Decisions not yet reflected elsewhere
<only uncaptured decisions, or none>

## Required environment
<tool versions, credential names and locations, never portable secret values>

## Suggested skills
- `grillstorm`: resume the recorded run from its state.
- <only other genuinely triggered skills>

## Portability
- Repository checkpoint pushed: <yes|no>
- Tracker checkpoint updated: <yes|no|not-configured>
- Portable now: <yes|no>
- Remaining sync gate: <exact action or none>

## Resume instruction
Invoke `$grillstorm resume <repository-relative handoff path>`.
```

## Checkpoint protocol

1. Finish the smallest safe red-green slice when feasible.
2. Stop new dispatch. Wait for active workers to reach supervised integration, or abandon
   their unmerged worktrees and leave those tasks pending.
3. Update `state.json`, task evidence, autonomous decisions, and the execution report.
4. For an execution-phase handoff, create `execution-checkpoint.json` with
   `scripts/portable_checkpoint.py`. Include only tasks whose `grillstorm-confirmed:` or
   `grillstorm-reality-gated:` marker is reachable from the integration commit.
5. Run the available focused checks. Record failures honestly; a checkpoint is not
   completion.
6. Inspect the worktree and separate Grillstorm-owned changes from pre-existing user work.
7. Create a clearly named checkpoint branch/commit containing the integration commit, run
   artifacts, and handoff, unless the launch Git policy forbids checkpoint commits.
8. Push that checkpoint and update the tracker only when the launch contract authorizes
   those external actions.
9. Set `portable now: yes` only after the checkpoint and integration commit are reachable
   from the recorded remote.

```bash
python3 <skill>/scripts/portable_checkpoint.py create \
  --workflow-state docs/grillstorm/<goal>/workflow-state.json \
  --run-state docs/grillstorm/<goal>/state.json \
  --tasks docs/grillstorm/<goal>/tasks/workflow-tasks.json \
  --orchestration docs/grillstorm/<goal>/tasks/orchestration.json \
  --repo <repo-root> --source-host claude \
  --output docs/grillstorm/<goal>/execution-checkpoint.json
```

The target fetches the checkpoint commit, verifies it against the frozen tasks/DAG and Git
markers, then creates a new local controller state, event log, and model policy. Never reuse
the source host's live process, worktree paths, private policy key, or worker fingerprint.

For Codex, pass the checkpoint to a fresh runner state:

```bash
python3 <skill>/scripts/run_layers.py \
  tasks/orchestration.json tasks/workflow-tasks.json \
  ... \
  --portable-checkpoint execution-checkpoint.json \
  --run-state-artifact state.json \
  --state workflow-state.codex.json \
  --events workflow-events.codex.jsonl \
  --report workflow-report.codex.json
```

The same protocol applies in reverse. Claude reconstructs its ready set from the verified
completed IDs and integration commit, then uses its own frozen model mapping.

If checkpoint commits are forbidden or owned changes cannot be transferred safely, record
the exact untransferred paths and set `portable now: no`. Never imply that another machine
can resume code which exists only in the current working tree.

## Boundary rules

- Do not mark a task or run complete because a handoff exists.
- During post-delivery audit, preserve the current sampling frame, next probe, answered
  critique questions, gap families, and child-run pointers.
- Do not make new product decisions while summarizing.
- Do not copy the conversation transcript.
- Never include pre-existing user changes in a checkpoint commit.
- On resume, fetch the recorded remote, verify the checkpoint SHA, inspect the current
  worktree, then trust durable repository artifacts over handoff prose.
- Never claim an in-flight or merely executor-completed task survived a host switch. Only a
  supervised marker reachable from the integration commit is portable completion.
- A tracker checkpoint is a discovery pointer, not the source of truth.
