# Codex wrapper and model-policy design

## Goal

Make Codex Megastorm preserve the command shape that launched the current Codex
session, including safe alias-expanded or wrapper-owned arguments, without
overriding a host-fixed model. Resolve the behavior once in Phase 0, freeze it in
run metadata, and never ask again during task execution.

## Terminology

- **Shell alias:** expanded by the shell before process creation. The recoverable
  command is the resulting argv, not the alias name.
- **Wrapper:** a still-observable executable/interpreter command that launches
  Codex and may own arguments that are not Codex flags.
- **Host model:** the model selected or fixed by the current launch command,
  profile, configuration, or wrapper.
- **Tiered model:** the existing THINK/VERIFY/BULK mapping supplied by
  `models.json`.

## Model policy

Each run has exactly one frozen `model_policy`:

- `inherited`: preserve the host model behavior and do not append `-m` or
  `--model` to child commands.
- `tiered`: remove any task-conflicting host model flag and append the task's
  confirmed THINK/VERIFY/BULK model.

Automatic recommendation:

1. Resolve model ownership in precedence order: wrapper contract, explicit Codex
   `-m/--model`, selected profile, explicit `-c/--config`, user/project config,
   then Codex default.
2. Each source is classified `locked`, `unlocked`, or `unknown` from evidence.
   A wrapper contract may explicitly declare locked/unlocked ownership; argv is
   locked when a model flag exists; profile/config/default are classified only
   from the pinned Codex version's effective configuration probe plus canonical
   source-file fingerprints.
3. Any higher-precedence `locked` source recommends `inherited`.
4. `tiered` is recommended and permitted only when every effective source is
   positively proven `unlocked` or default-overridable for the pinned CLI.
5. Any `unknown` source permits only `inherited`; the user may confirm inherited
   behavior or stop execution, but cannot confirm an unsafe tiered override.

Phase 0 always displays the discovered redacted command, evidence/reason for the
recommendation, proposed policy, and child-command preview. The user confirms
once. That confirmation is stored in a policy artifact. No task may prompt for
the policy again.

An explicit `inherited` choice is valid even when no model flag is visible; it
means the host/default/wrapper owns model resolution. `tiered` requires all three
real model mappings. No automatic downgrade or fallback is allowed.

## Alias and wrapper command discovery

Ordinary shell aliases need no reconstruction: after expansion, the actual
Codex argv contains their Codex parameters, including Codex `-p/--profile`, and
those safe arguments are normalized and inherited.

Persistent wrappers use this bounded grammar:

```text
<canonical-wrapper> [fixed-wrapper-args] -- <canonical-codex> [codex-host-args]
```

The explicit `--` boundary is mandatory because wrapper argument arity cannot be
guessed. Wrapper replay additionally requires an explicit versioned wrapper
contract supplied beside the JSON argv override. Lossless ancestry discovery may
confirm a known contract but never authorizes an unknown wrapper.

The contract contains:

- canonical wrapper and Codex paths plus pinned content hashes;
- exact fixed wrapper token sequence and option arity;
- explicit Codex child boundary index;
- replay-safety declaration and supported wrapper version;
- model ownership `locked|unlocked|unknown` with evidence;
- secret-bearing token/value positions and approved environment sources;
- forbidden side effects during replay/probe;
- contract schema/version and canonical contract hash.

Both executables and the contract are checked before every child launch. A token,
path, hash, version, or boundary mismatch fails closed.

Wrapper fixed arguments are accepted only from an explicit JSON argv override
plus its matching contract. A lossless process snapshot must match that already
approved contract byte-for-byte. Unknown, boundary-less, side-effectful, or
uncontracted wrappers fail closed. Secret values are replayed only from approved
launch-time environment sources and never serialized into reports or policy
artifacts. A wrapper that replaces itself with Codex is naturally treated as a
direct Codex invocation.

`-p` is never interpreted generically. Before the boundary it belongs to the
wrapper and is preserved only as part of the verified fixed wrapper argv. After
the boundary it means Codex `--profile` and follows the Codex allowlist.

## Command construction

For `tiered`:

```text
<verified launch chain> <root args> exec <safe exec args>
  --ephemeral -m <task-tier-model> -C <worktree>
  --output-last-message <path> <prompt>
```

For `inherited`:

```text
<verified launch chain> <root args> exec <safe exec args>
  --ephemeral -C <worktree>
  --output-last-message <path> <prompt>
```

If the inherited host model is represented by `-m/--model`, it remains exactly
once in the correct Codex argument partition. If model ownership comes from a
profile/config/wrapper, no model flag is synthesized.

The implementation constructs argv arrays and never evaluates a shell string.

### Codex option grammar and placement

The pinned supported Codex CLI grammar is normative:

| Options | Arity | Child placement | Behavior |
|---|---:|---|---|
| `-a/--ask-for-approval` | 1 | before `exec` | inherit |
| `--search` | 0 | before `exec` | inherit |
| `-c/--config`, `--enable`, `--disable`, `-p/--profile`, `--local-provider`, `-s/--sandbox`, `--add-dir` | 1 | after `exec` | inherit, preserve order |
| `--oss`, `--strict-config`, `--dangerously-bypass-approvals-and-sandbox`, `--dangerously-bypass-hook-trust`, `--skip-git-repo-check`, `--ignore-user-config`, `--ignore-rules` | 0 | after `exec` | inherit |
| `-m/--model` | 1 | after `exec` | keep exactly once for `inherited` when argv-owned; strip and replace for `tiered` |
| `-C/--cd`, `-o/--output-last-message`, prompt | 1 | runner-owned | strip host value, append task value |
| `--json`, `--ephemeral`, `--no-alt-screen` | 0 | runner-owned/transport | strip; append canonical form where required |
| `--color`, `--output-schema` | 1 | transport | strip |
| `--image/-i`, `resume`, `--`, stdin prompt `-`, unknown option/subcommand | varies | nowhere | reject |

Split and equals forms are normalized according to this table. Direct and
post-wrapper Codex argv use the identical grammar. Command-shape fixtures are
pinned to the supported Codex CLI version and prove semantic placement.

### Legacy template migration

Legacy templates are removed from normal verified execution. A separately named
unsafe compatibility switch may temporarily run them only with explicit user
authorization. It cannot claim verified isolation/parity and must still enforce
canonical executable/content pinning, protected cwd/output/prompt/session-field
rejection, redaction, and a frozen policy fingerprint. `inherited` compatibility
templates may omit `{model}`; `tiered` templates require it. Recommended docs and
tests do not use the unsafe path.

## Policy artifact and resume

Phase 0 writes a versioned artifact containing:

- `model_policy`;
- automatic recommendation and evidence;
- user confirmation marker/time;
- redacted discovered command and command-source kind;
- executable/wrapper fingerprints;
- an HMAC-SHA256 of the exact unredacted argv using a per-run integrity key stored
  mode `0600` outside reports/events (the raw argv and secret values are never
  persisted);
- canonical paths and content hashes for every model-affecting profile, config,
  requirements, and managed/project/user source;
- wrapper-contract canonical hash and supported wrapper/Codex versions;
- complete effective model-resolution evidence and each source classification;
- for `tiered`, the three model mappings;
- for `inherited`, the detected model source (`argv`, `profile`, `config`,
  `wrapper`, or `default`).

The runner requires the artifact for execution. Its canonical fingerprint joins
the task/DAG/prompt/baseline fingerprint. Changing policy, model mappings,
launcher chain, profile/config, or executable fingerprint invalidates affected
work. Before resume and every child launch it re-probes executable identities,
versions, wrapper contract, exact argv HMAC, model-resolution evidence, and all
source content hashes. Drift invalidates before dispatch. A resume never silently
re-infers policy.

## Untrusted worker artifact gateway

Every executor and supervisor process is an untrusted worker. Exit zero, prose,
self-reported paths, and self-reported acceptance are never sufficient to advance
the DAG.

### Frozen control plane

Before Phase 1.6 the coordinator fingerprints and makes immutable to ordinary
tasks:

- orchestration/DAG and all task-definition files;
- model-policy and model-mapping artifacts;
- Phase 0 registry, wrapper contract, and effective command policy;
- executor/supervisor prompts and schemas;
- Megastorm runner, deterministic gates, state, and event paths;
- acceptance commands and their hashes.

Task worktrees do not contain writable run-state/event files. The coordinator is
their sole writer. Any worker diff touching a control-plane path is rejected
before supervision and never committed or merged.

If a task discovers that the control plane is wrong, its only valid outcome is
`needs_replan` with evidence. The coordinator stops the affected task and its
unstarted downstream subgraph, records the reason, and returns to planning and
independent review. A worker cannot add/remove dependencies, expand its scope,
change models, alter retries, weaken acceptance, or approve its own replan.

### Per-task artifact contract

Each frozen task includes a coordinator-authored contract:

```json
{
  "task_id": "T-auth-01",
  "allowed_paths": ["src/auth/**", "tests/auth/**"],
  "required_outputs": ["src/auth/service.py"],
  "forbidden_paths": ["orchestration.json", ".megastorm/**"],
  "acceptance_cmd_sha256": "...",
  "expected_interfaces": ["api:createSession"],
  "max_files_changed": 12
}
```

The runner derives actual renames, deletions, untracked files, symlink targets,
file count, and interface artifacts from Git/filesystem state. It never trusts an
executor's `touched_paths` report. Path escape, forbidden/control-plane change,
undeclared output, missing required output, excessive file count, or changed
acceptance hash rejects the artifact before the supervisor sees it.

### Strict result channel

Executor and supervisor use versioned JSON envelopes validated against strict
schemas. The parser consumes the declared machine-output channel, not arbitrary
terminal prose or a greedy final `{...}` span. It rejects:

- leading/trailing narrative in the machine result;
- missing, extra-forbidden, or incorrectly typed fields;
- task/run/attempt identity mismatch;
- unknown status/verdict;
- executor claims inconsistent with the actual diff;
- supervisor confirmation without executed acceptance evidence and non-vacuous
  test counts where applicable.

Valid executor terminal outcomes are `complete`, `business_reject`,
`infrastructure_failure`, `needs_replan`, and `reality_gated`. Only the independent
supervisor can return `confirmed` or `rejected`; neither process can mutate DAG
state directly.

### Transactional admission

A task advances the DAG only after all gates succeed:

1. process/transport and strict envelope validation;
2. actual artifact-contract and frozen-control-plane validation;
3. fresh supervisor reruns the frozen acceptance command and inspects the real
   worktree/diff without executor narrative;
4. task commit contains exactly the admitted artifact;
5. CAS merge into the integration ref succeeds;
6. post-merge integration checks validate the affected interfaces and acceptance
   smoke set.

Failure before merge leaves the integration ref unchanged. Failure after a
tentative merge prevents publication and records an escalation/replan event;
dependents are not released until the post-merge event is durable.

## Failure behavior

- Uncertain model ownership without confirmation: stop before worktrees.
- `inherited` plus a runner-added model flag: construction error.
- `tiered` with missing/placeholder mappings: configuration error.
- Wrapper boundary/identity/fingerprint mismatch: preflight error.
- Uncontracted wrapper or model source classified `unknown` with a requested
  `tiered` policy: preflight error.
- Wrapper or Codex arguments conflict with runner-owned cwd/output/prompt/session
  fields: strip only known Codex task fields; otherwise fail closed.
- Worker modifies a frozen control-plane path or violates its artifact contract:
  reject before supervision and preserve the worktree for evidence.
- Worker reports `needs_replan`: stop the affected subgraph, invalidate its
  planning artifacts, and require fresh plan/reverse review before dispatch.
- Unsupported alias reconstruction: show the recoverable argv and explain that
  shell alias names do not survive process creation.

## Python runtime compatibility

macOS support assumes `python3` exists and does not assume a `python` command or
alias. Every executable script keeps `#!/usr/bin/env python3`; documentation,
generated commands, test commands, subprocess launches, and recovery runbooks use
`python3` or the current interpreter from `sys.executable`, never bare `python`.

When one Python script launches another, it prefers `sys.executable` so the child
uses the same virtual environment/interpreter as the runner. User-authored task
`acceptance_cmd` values are not rewritten, but Phase 0 validation warns or rejects
a generated Megastorm command that relies on bare `python` on a host where it is
unavailable.

## Tests

- Direct shell-alias-expanded argv preserves profile/config/feature flags.
- Direct `-m` recommends `inherited` and produces no additional `-m`.
- No model signal recommends `tiered` and uses each tier mapping.
- Profile/config/wrapper ambiguity requires confirmation.
- Wrapper-owned `-p` before `--` and Codex profile `-p` after `--` retain their
  distinct positions.
- Boundary-less, injected, changed, or malicious wrappers fail closed.
- An ancestry-discovered wrapper without a pre-approved matching contract fails
  closed; a matching snapshot/contract succeeds.
- Root/exec option placement fixtures cover every row of the pinned grammar.
- Inherited templates omit `{model}`; tiered templates require it.
- Policy artifact confirmation, redaction, fingerprinting, and resume
  invalidation are deterministic.
- Redaction covers split values, `--key=value`, URL userinfo, environment-expanded
  secrets, wrapper-contract fields, exceptions, metadata, and process displays.
- Fake Codex E2E covers both policies and proves executor/supervisor commands use
  the frozen policy without further questions.
- Adversarial workers attempt to edit the DAG, tasks, models, prompts, state,
  acceptance command, runner, symlink escapes, undeclared files, and excessive
  outputs; every mutation is rejected before merge.
- Strict-channel fixtures cover narrative-wrapped JSON, greedy-brace payloads,
  unknown outcomes, identity mismatch, fake evidence, zero-test acceptance, and
  executor/supervisor disagreement.
- A `needs_replan` fixture proves the affected subgraph stops and cannot resume
  until new independently reviewed fingerprints are supplied.
- Post-merge failure prevents dependent release and publication.
- A macOS-style PATH fixture containing `python3` but no `python` passes all
  Megastorm-owned commands. A scoped repository check covers owned `.py`, shell,
  Markdown, generated commands, and subprocess argv while explicitly excluding
  fixtures and user-authored `acceptance_cmd`; it rejects bare-Python shebangs and
  commands.
- Existing Codex Megastorm and Cross-exam regressions remain green.

## Acceptance criteria

1. A user-started profile/alias command is preserved where process semantics
   make it observable.
2. A host-fixed model is never overwritten by Megastorm.
3. Tiered models remain available when the host does not own model selection.
4. Ambiguity causes one Phase 0 decision, not guessing or per-task prompts.
5. Resume uses the frozen policy and detects command/policy drift.
6. Reports show the redacted effective policy and child-command preview.
7. Installation and execution work on macOS with `python3` and no `python`
   executable.
8. No child Codex process can mutate the control plane or advance the DAG from
   self-reported/unvalidated artifacts.
