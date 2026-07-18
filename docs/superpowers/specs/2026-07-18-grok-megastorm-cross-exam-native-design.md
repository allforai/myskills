# Grok Build Megastorm and Cross-exam Native Design

## Goal

Add first-class support for the official xAI Grok Build programming CLI to this
repository. One Grok plugin must expose two independent user-invocable skills:
Megastorm and Cross-exam. The Grok implementation must match the behavioral
contracts already enforced by the Claude and Codex editions while using Grok's
own skills, subagents, headless mode, streaming JSON, configuration, and plugin
discovery conventions.

Parity means equivalent safety, evidence, failure, recovery, and reporting
semantics. It does not mean using the same manifest, commands, process flags, or
orchestration primitives on every host.

## Official Host Contract

The implementation targets the official `grok` Grok Build CLI documented by
xAI, including:

- user-invocable skills exposed as slash commands;
- plugins discovered from project, user, marketplace, configured, or
  `--plugin-dir` roots;
- independent native subagents;
- headless prompts through `-p` / `--single`;
- newline-delimited events from `--output-format streaming-json`;
- `--cwd`, `--no-auto-update`, model selection, and permission modes;
- `grok inspect --json` and `grok plugin validate` for discovery checks.

`grx` is treated as a supported launcher alias or wrapper only when it resolves
to the official Grok Build command surface. The adapter is for the programming
tool, not for calling a Grok model through an unrelated provider.

## Scope and Non-goals

This change adds:

1. A Grok-native plugin with Megastorm and Cross-exam skills.
2. Grok host-command discovery and safe child-command inheritance.
3. A deterministic Phase 1.6 runner backed by fresh headless Grok sessions.
4. Grok-native Cross-exam orchestration using independent subagents.
5. Installation, inspection, protocol-parity, fake-CLI, and regression tests.

It does not:

- automatically run Cross-exam after Megastorm;
- let Cross-exam modify the audited repository;
- silently downgrade or choose a model tier;
- overwrite the user's Grok configuration;
- fall back to a bare `grok` command when host discovery is ambiguous;
- claim a real Grok smoke test on a machine where Grok is not installed and
  authenticated.

## Package Architecture

```text
grok/
└── megastorm/
    ├── plugin metadata compatible with Grok Build
    ├── AGENTS.md
    ├── README.md
    ├── install.sh
    ├── skills/
    │   ├── megastorm/
    │   │   └── SKILL.md
    │   └── cross-exam/
    │       └── SKILL.md
    ├── prompts/
    ├── schemas/
    └── scripts/
        ├── host_command.py
        ├── run_layers.py
        ├── deterministic gates and state helpers
        ├── render_report.py
        └── tests/
```

The concrete metadata filename and fields must follow the current official
Grok/Claude-compatible plugin format. If the installed CLI is available,
`grok plugin validate` is authoritative. The plugin must not depend on the
Codex plugin loader or a Claude-only environment variable.

Both skills live in one installable plugin but remain logically independent.
They exchange data only through documented files. Cross-exam may consume a
Megastorm report or registry, but it also accepts a specification, README,
user-supplied baseline, or an explicitly baseline-free audit.

## Orchestration Model

### Interactive phases

The current interactive Grok session owns Phase -1, Phase 0, and the short
orchestration steps. It probes environmental proof capabilities, front-loads
human decisions, validates the overview, assigns explicit model tiers, and
launches native subagents for Phase 1.1 through Phase 1.5.

The native-subagent stages retain the existing Megastorm contracts:

- independent design and validation;
- closed-loop plan review;
- reverse review and DAG construction;
- explicit task ownership and evidence expectations;
- no acceptance of an executor's self-verdict.

### Deterministic Phase 1.6

Phase 1.6 is controlled by the Python runner rather than conversational
best-effort orchestration. For each dependency-ready task it creates an
isolated worktree, starts an executor in a fresh headless Grok process, then
starts an independent supervisor in another fresh process. The runner alone
controls scheduling, mutexes, retries, durable state, Git integration, and
final task status.

The effective child command is:

```text
<discovered launcher and inherited safe host options>
  --no-auto-update
  --cwd <task-worktree>
  -p <prompt>
  --output-format streaming-json
```

The adapter must avoid duplicated or conflicting prompt, output, cwd, session,
resume, and update flags. Executor and supervisor processes must never share a
session identifier.

## Host-command Discovery and Inheritance

### Resolution order

1. If `MEGASTORM_GROK_COMMAND` is set, parse it as a JSON array of argv tokens.
   Reject strings, empty arrays, non-string tokens, prompt-bearing commands,
   and commands that cannot be identified as official `grok` or `grx` launchers.
2. Otherwise inspect the current process ancestry and recover the nearest
   effective Grok Build invocation, including wrapper/interpreter prefixes.
3. If no trustworthy command can be recovered, fail closed with an actionable
   message. Never synthesize a bare `grok` fallback.

The implementation should use platform-specific process inspection where
needed, with macOS `KERN_PROCARGS2` support and portable `/proc` or process-list
fallbacks where available. Tests inject process data and must not depend on the
test runner actually being launched by Grok.

### Inherited options

Preserve host options whose omission could change the user's intended runtime,
including model/profile/config selection, plugin/config roots, sandbox or
permission mode, and relevant feature flags. Strip interactive-only and
per-request state such as the original prompt, `--cwd`, output format, session
IDs, resume/continue flags, and alternate-screen controls before adding the
runner-owned values.

Launcher prefixes and arguments are preserved. For example, if the current
session was started through a wrapper, the child starts through the same
wrapper with the same safe inherited options.

### Secrets and diagnostics

Raw argv may contain credentials. Diagnostics, state, events, reports, and
exceptions must redact values associated with secret-looking flags and
environment assignments. Tests must cover split and `--key=value` forms.

## Streaming Event Contract

The runner reads stdout as newline-delimited JSON and treats stderr as
diagnostic transport only. It must:

- accept incremental assistant/message chunks and structured tool events;
- assemble the final semantic response without scraping terminal prose;
- preserve useful structured diagnostics and exit status;
- reject malformed JSON, truncated streams, missing terminal completion, empty
  semantic output, and protocol-level errors;
- classify transport/protocol failures as infrastructure failures;
- validate executor and supervisor final envelopes against their schemas;
- reject an unknown supervisor verdict instead of guessing.

The parser should be tolerant of additive event fields but strict about the
minimum event sequence and terminal outcome needed to prove completion.

## Model-tier Contract

THINK, VERIFY, and BULK remain explicit plan-level policy labels. Before Phase
1.6 the user confirms their concrete Grok model mapping. The runner records the
mapping and applies the chosen model flag to each child invocation.

Missing mappings, unavailable models, quota errors, and authentication failures
are surfaced. The runner must not silently select a default, downgrade a tier,
or substitute a different provider.

## Git, Scheduling, and Recovery

The Grok runner inherits the hardened Codex semantics:

- snapshot the user's branch, HEAD, dirty status, and dirty-content fingerprint;
- never stage, commit, stash, clean, reset, or overwrite pre-existing user work;
- create a controlled integration ref/worktree and one task worktree per writer;
- schedule only dependency-ready tasks and enforce resource mutexes;
- compare actual changes with declared `touched_paths`, including renames,
  deletions, untracked files, and repository-escape rejection;
- supervise before committing and merging confirmed task work;
- serialize merges, surface conflicts, and never guess a resolution;
- keep business retry, infrastructure retry, and reality-gated proof distinct;
- transitively skip only after genuine escalation while continuing unrelated
  work;
- terminate process groups on timeout or cancellation;
- publish atomic versioned state and an append-only JSONL event log;
- fingerprint tasks, DAG, prompts, models, and integration baseline on resume;
- invalidate changed tasks and downstream dependents conservatively;
- never merge an already integrated task twice.

Reality-gated tasks get one autonomous acceptance attempt. If implementation is
present but proof requires unavailable hardware, external systems, or human
observation, the runner records the runbook and does not count the outcome as
verified or as a business failure.

## Megastorm Completion Semantics

The Grok skill must implement the parity protocol already defined for Codex:

- Phase -1 capability matrix;
- census-first handling for class-elimination goals;
- explicit evidence obligations and touched paths;
- dependency-ready parallel execution and mutex safety;
- independent executor/supervisor verdicts;
- anti-fake-completion gates;
- reconciliation of census coverage before class-wide completion claims;
- final counts of verified, reality-gated, escalated, and skipped work;
- completeness confidence, DAG warnings, retry history, runbooks, and an
  invitation to invoke Cross-exam independently.

A green task count is insufficient when the original goal asserts exhaustive
coverage.

## Cross-exam Contract

Cross-exam is explicitly invoked, audit-only, generic, evidence-backed, and
interactive. It never fixes findings and never mutates the audited repository.

The examiner must spawn at least one fresh-context native Grok subagent as the
independent prober. If independent subagents are unavailable, the skill refuses
to issue a completeness verdict rather than silently conducting a single-context
self-review.

The workflow is:

1. Resolve and freeze the audit baseline.
2. Build an independent surface census before reading delivery claims deeply.
3. Run targeted deep-dive lenses and a separate census sweep.
4. Store each claim with stable evidence references under the audit directory.
5. Reconcile examiner and prober results.
6. Render verdicts `done`, `gap`, `drift`, or `unprovable`, plus severity,
   rationale, evidence, and `open_threads`.

The renderer rejects invalid verdicts, missing required severity, absent
evidence, path traversal or evidence outside the audit root, and malformed
open-thread records. Claims without valid evidence cannot be rendered as done.

## Installation and Discovery

`grok/megastorm/install.sh` installs the complete plugin into the effective
Grok home, respecting `GROK_HOME` and otherwise using the documented user plugin
directory. It must:

- support a non-mutating dry-run or explicit destination for tests;
- copy/update only this plugin's owned directory;
- avoid editing `config.toml`, marketplace sources, credentials, or unrelated
  plugins;
- fail clearly when the source package is incomplete;
- print the exact `grok inspect` and plugin validation commands for verification.

One installation must make both `/megastorm` and `/cross-exam` discoverable.
Where the CLI is installed, automated checks use `grok inspect --json` and
`grok plugin validate`. Otherwise structural validation and a fake CLI provide
deterministic coverage, and the final report states that real discovery was not
executed.

## Test Strategy

### Host discovery

- actual `grok` and `grx` invocation shapes;
- wrapper/interpreter prefixes and inherited safe flags;
- conflicting runner-owned flag removal;
- invalid override and fail-closed behavior;
- macOS and portable ancestry fixtures;
- secret redaction in command displays, state, events, and errors.

### Streaming protocol

- normal incremental completion;
- tool-event interleaving and additive unknown fields;
- protocol error and non-zero exit;
- malformed line, truncated stream, missing terminal event, and empty result;
- schema-invalid executor output and unknown supervisor verdict.

### Runner and safety

- DAG readiness, mutexes, parallelism limits, and transitive skip;
- worktree isolation and untouched dirty user state;
- touched-path enforcement and merge conflict escalation;
- business versus infrastructure retries and backoff;
- reality-gate ledger and runbook propagation;
- cancellation, atomic state, event log, invalidation, and resume;
- fake Grok CLI end-to-end execution and recovery.

### Cross-exam

- independent-subagent hard gate;
- baseline and census requirements;
- evidence-root containment and stable references;
- verdict/severity/open-thread validation;
- renderer refusal on unsupported completion claims.

### Packaging and parity

- plugin metadata, internal references, install ownership, and discovery layout;
- both skills visible after one test installation;
- protocol matrix across Claude, Codex, and Grok with no unexplained gap;
- all existing Codex Megastorm and Cross-exam regressions remain green.

## Acceptance Criteria

The change is complete only when:

1. One Grok plugin installation exposes both independent skills.
2. Host discovery preserves the real launcher and safe current parameters and
   fails closed when it cannot do so.
3. A fake official-style Grok CLI completes Phase 1.6, exercises supervision,
   and demonstrates interruption/recovery behavior.
4. The user worktree remains byte-for-byte unchanged by isolated test runs.
5. Cross-exam refuses a completeness verdict without an independent subagent.
6. The Grok parity matrix has no unexplained contract gaps.
7. New Grok tests and the existing Codex/Cross-exam suite pass.
8. A thought-test acceptance report challenges happy-path claims with failure,
   adversarial, recovery, evidence, and packaging scenarios.
9. The final report clearly distinguishes deterministic fake-CLI validation
   from any real installed/authenticated Grok smoke test.

## Delivery Sequence

1. Commit this approved design.
2. Obtain independent specification review and resolve every blocker.
3. Write an implementation plan because the repository's usual
   `writing-plans` skill is unavailable in this environment.
4. Implement package, adapter, runner integration, skills, installation, and
   tests in reviewable increments.
5. Run targeted and regression suites, inspect the resulting package, and carry
   out the thought-test acceptance audit.
6. Commit and push the verified result to `origin/main` as explicitly requested.

