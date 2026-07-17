# Codex Megastorm + Cross-exam parity acceptance

## Result

The Codex-native Megastorm protocol is aligned to the Claude v0.14.0 capability
surface, Cross-exam is available as an independent skill, and the runner's normal
execution path no longer writes or commits through the user's checked-out worktree.

Focused result: **117 passed**.

## Automated evidence

Command:

```text
python3 -m pytest codex/megastorm-skill/scripts codex/cross-exam-skill/scripts -q
```

Additional gates:

```text
python3 -m py_compile codex/megastorm-skill/scripts/*.py codex/cross-exam-skill/scripts/*.py
bash -n codex/install.sh
git diff --check
```

All focused gates passed.

## Thought-test matrix

| Adversarial scenario | Expected invariant | Evidence/result |
|---|---|---|
| User starts from a dirty worktree | Existing branch/index/files remain untouched | End-to-end fake-agent test proves the draft remains only in the user tree and output only in the retained integration ref |
| Two same-file tasks are ready together | Original mutex survives universal worktree isolation | Thought test found an overwrite bug; fixed by retaining multi-task mutex groups plus singleton isolation markers; regression test passes |
| Executor changes an undeclared path | Task cannot silently merge | Actual Git diff is compared with `touched_paths`; path escape/out-of-scope tests pass |
| Crash after confirmed merge but before state snapshot | Resume must not execute/merge the task twice | Confirmation marker commits recover `done`/`reality_gated` state from integration history; recovery test passes |
| State belongs to different tasks/prompts/models | Stale confirmation is refused | Input fingerprint mismatch exits before reuse |
| Codex process/network fails | Infrastructure noise must not consume business retries | Separate infrastructure counter test passes; process groups have timeout, TERM, then KILL |
| Reality-gate environment is absent | Implementation merges, proof stays pending, dependents continue | Verdict routing and dependency-satisfaction tests pass; report separates reality gates |
| Human later rejects a reality gate | Old report cannot remain authoritative | Resolution script marks report superseded and invalidates the task plus downstream confirmations |
| Goal says “eliminate every X” after a grep audit | Green task count cannot claim class elimination | Playbook requires census; runner defaults report to `Completeness unverified` unless census artifact is declared |
| Agent sees unrelated ambient credentials | Unapproved secrets are not inherited | Minimal environment test excludes an injected secret; explicit `--allow-env` is required |
| Cross-exam lacks fresh-context agents | It must refuse instead of self-review | Skill hard gate explicitly requires `spawn_agent` + `wait_agent` and forbids fallback |
| Prober returns oral judgment/no evidence | Renderer must exclude it from counts | Missing/empty/outside evidence and invalid verdict tests pass |
| Gap has no valid severity | It must not enter gap statistics | Renderer rejects invalid severity; regression test passes |
| Examiner crashes or PID is reused | Active run cannot be silently taken over | PID + process-start lock, explicit stale takeover, archive, and tests are present |
| Unselected question cards disappear | Unexamined risk remains visible | Stable `open_threads` are persisted and rendered outside completion counts |

## Parity accounting

The parity map is maintained in `codex/megastorm-skill/PARITY.md`. Host-specific
Claude Workflow calls, manifests, and slash commands are intentionally not copied;
Codex uses skills, `codex exec`, Python orchestration, and fresh-context agents.

## Honest limitations

- A repository-root `python3 -m pytest -q` cannot collect on the current Python 3.9
  environment because unrelated existing suites use Python 3.10 union annotations and
  duplicate top-level test module names. The focused changed-scope suite is isolated and
  green; the root collection failure was not caused or modified by this change.
- Workspace-write sandboxing cannot prove that every arbitrary command lacks remote side
  effects. Megastorm therefore requires Phase 0 capability authorization, strips ambient
  secrets by default, and must refuse unattended work when the host cannot enforce the
  requested boundary.
- Cross-exam itself was not auto-run against this delivery: its protocol is explicitly
  interactive-only and requires the user to choose facets/questions. This acceptance is the
  requested thought-test review, not a fabricated Cross-exam report.
