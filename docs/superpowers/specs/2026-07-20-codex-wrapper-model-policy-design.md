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

1. A host argv with `-m/--model`, or a verified wrapper/profile/config declared
   as model-locked, recommends `inherited`.
2. A direct host invocation with no model signal recommends `tiered`.
3. An opaque wrapper/profile/config whose model behavior cannot be proved has no
   recommendation and requires an explicit Phase 0 choice.

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
guessed. Both executables are canonicalized, fingerprinted, and checked again
before every child launch. The wrapper chain is preserved exactly except for
runner-owned Codex request fields after the boundary.

Wrapper fixed arguments are accepted only from an explicit JSON argv override
or a lossless process snapshot and must not contain prompts, model overrides,
permission bypass, secrets in reports, or another ambiguous subcommand. Unknown
or boundary-less wrappers fail closed. A wrapper that replaces itself with Codex
is naturally treated as a direct Codex invocation.

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
Legacy templates remain explicit compatibility inputs but gain a declared model
policy; `inherited` templates do not require `{model}`, while `tiered` templates
do. Templates remain marked unverified inheritance.

## Policy artifact and resume

Phase 0 writes a versioned artifact containing:

- `model_policy`;
- automatic recommendation and evidence;
- user confirmation marker/time;
- redacted discovered command and command-source kind;
- executable/wrapper fingerprints;
- for `tiered`, the three model mappings;
- for `inherited`, the detected model source (`argv`, `profile`, `config`,
  `wrapper`, or `default`).

The runner requires the artifact for execution. Its canonical fingerprint joins
the task/DAG/prompt/baseline fingerprint. Changing policy, model mappings,
launcher chain, profile/config, or executable fingerprint invalidates affected
work. A resume never silently re-infers policy.

## Failure behavior

- Uncertain model ownership without confirmation: stop before worktrees.
- `inherited` plus a runner-added model flag: construction error.
- `tiered` with missing/placeholder mappings: configuration error.
- Wrapper boundary/identity/fingerprint mismatch: preflight error.
- Wrapper or Codex arguments conflict with runner-owned cwd/output/prompt/session
  fields: strip only known Codex task fields; otherwise fail closed.
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
- Inherited templates omit `{model}`; tiered templates require it.
- Policy artifact confirmation, redaction, fingerprinting, and resume
  invalidation are deterministic.
- Fake Codex E2E covers both policies and proves executor/supervisor commands use
  the frozen policy without further questions.
- A macOS-style PATH fixture containing `python3` but no `python` passes all
  Megastorm-owned commands; static checks reject bare-Python shebangs and commands.
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
