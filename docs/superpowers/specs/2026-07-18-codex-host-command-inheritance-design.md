# Codex host-command inheritance design

## Goal

Megastorm child Codex processes must inherit the actual executable and effective
session-level arguments that launched the current Codex host. The runner must not
silently fall back to a bare `codex` command or impose a different sandbox/profile.

## Scope

This change affects only Codex process discovery and child argv construction.
DAG scheduling, worktrees, retry budgets, Reality Gate, model-tier selection, and
Cross-exam behavior remain unchanged.

## Resolution priority

1. Explicit legacy `--codex-template` when supplied by the caller.
2. `MEGASTORM_CODEX_COMMAND`, encoded as a non-empty JSON array of argv strings.
3. Automatic discovery of the nearest real Codex process in the ancestor chain.
4. Fail preflight with an actionable error. Never use a bare-command fallback.

The default value of `--codex-template` becomes absent so it cannot accidentally
override discovery.

## Discovery

A new focused module, `scripts/host_command.py`, owns discovery, normalization,
redaction, and argv construction.

Starting from the runner parent, discovery walks ancestors and selects the nearest
process whose executable basename is `codex` or whose argv can be unambiguously
identified as Codex CLI. Linux reads NUL-delimited `/proc/<pid>/cmdline`. macOS and
other supported POSIX hosts use a non-shell `ps` query and parse its result with
`shlex.split`. Discovery returns an absolute executable path plus argv.

Aliases are not reconstructed because the shell has already expanded them. When a
wrapper has replaced itself with Codex, the real Codex executable is inherited. If
a wrapper remains as an ancestor, discovery still selects the nearest actual Codex
process rather than replaying the wrapper.

## Command normalization

The discovered argv is separated into executable and session-level arguments.
Megastorm preserves profiles, config overrides, feature flags, sandbox/approval
mode, plugin settings, and other non-conflicting host options.

It removes or replaces child-specific/interactive arguments:

- `exec` or `resume` subcommands and their payload;
- `-m`, `--model`, and `--model=<value>`;
- `-C`, `--cd`, and `--cd=<value>`;
- `-o`, `--output-last-message`, and equals forms;
- prompt payloads and output-stream formatting arguments that conflict with the
  runner's last-message contract.

Unknown option-shaped session arguments are preserved. A positional argument whose
meaning cannot be safely separated from an interactive prompt causes a closed
failure rather than guessing.

The child argv is built as an array:

```text
<absolute executable> exec <preserved session args>
  --ephemeral -m <tier model> -C <task worktree>
  --output-last-message <temporary path> <prompt>
```

No shell string is constructed. The runner passes the array directly to
`subprocess.Popen`.

The current host's sandbox and approval mode win. Megastorm does not inject
`workspace-write` when the parent uses another mode, including
`--dangerously-bypass-approvals-and-sandbox`. Model and cwd remain task-level and
are intentionally replaced.

## Explicit override

`MEGASTORM_CODEX_COMMAND` must decode to a non-empty JSON array of non-empty strings.
Its first element resolves to an executable. Invalid JSON, a scalar value, an empty
array, or non-string members fail preflight.

`--codex-template` remains for compatibility and tests, but it is used only when the
flag is explicitly supplied. Reports mark it as a legacy template whose inheritance
cannot be verified.

## Redaction and reporting

Execution reports record:

- command source: template, environment, Linux procfs, or POSIX process query;
- absolute executable;
- redacted discovered arguments;
- redacted preserved session arguments.

Redaction hides values following or embedded in option names containing `token`,
`secret`, `password`, `api_key`, `apikey`, `authorization`, or `credential`.
Sensitive environment values are never emitted. Raw prompts and output paths are not
included in the command metadata.

## Failure handling

- No reliable Codex ancestor or explicit override: stop before creating worktrees.
- Executable cannot be resolved or executed: infrastructure preflight failure.
- Ambiguous positional argv: stop and identify the unresolved argument.
- Conflicting parameters with a missing value: stop as malformed host argv.
- Unsupported platform without an explicit override: stop and document the override.

No failure path falls back to `codex` from `PATH`.

## Testing

Unit tests cover:

- inheritance of bypass, profile, config, and feature flags;
- replacement of model/cwd/output in split and equals forms;
- preservation of the parent sandbox;
- malformed/ambiguous argv rejection;
- JSON environment override validation;
- redaction of secret-bearing options;
- Linux procfs and macOS/POSIX process-query parsing through injected fixtures;
- paths and arguments containing spaces without shell evaluation.

The runner end-to-end fake-agent test uses an explicit argv override so it remains
independent from the test process ancestry. All existing focused Megastorm and
Cross-exam tests must remain green.

## Completion criteria

- A session launched as `codex --dangerously-bypass-approvals-and-sandbox` produces
  children with the same permission flag.
- A session launched with profile/config/feature settings preserves them.
- Child-specific model, cwd, output, and prompt values are supplied exactly once.
- Discovery failure never invokes a bare `codex`.
- Reports contain useful redacted provenance and no credential material.
- Focused regression tests and static checks pass.
