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
process whose resolved executable basename is exactly `codex`. Linux reads the
executable from `/proc/<pid>/exe` and NUL-delimited argv from
`/proc/<pid>/cmdline`; both must describe the same live PID before and after the
read. macOS uses native `sysctl(KERN_PROCARGS2)` through `ctypes`, retaining
NUL-delimited argument boundaries. `ps` is never used because its rendered output
can be truncated or lose quoting.

Argv text alone cannot establish process identity. A process exit, PID reuse/start
token change, unreadable executable, empty argv, kernel-buffer truncation, or
executable/argv disagreement fails closed. Unsupported platforms require an
explicit override.

Linux reads `/proc/<pid>/stat` field 22 before and after the exe/cmdline reads and
requires the start ticks to match. macOS reads `proc_pidinfo(PROC_PIDTBSDINFO)`
start seconds/microseconds before and after `KERN_PROCARGS2` and requires both the
start token and parent PID to match. The ancestor walker similarly rechecks each
parent link before advancing, so PID reuse cannot splice a different process into
the discovered chain.

Aliases are not reconstructed because the shell has already expanded them. When a
wrapper has replaced itself with Codex, the real Codex executable is inherited. If
a wrapper remains as an ancestor, discovery still selects the nearest actual Codex
process rather than replaying the wrapper.

## Command normalization

The discovered argv is separated into executable and session-level arguments.
Normalization uses a versioned allowlist with explicit arity. V1 inheritable
zero-value flags are `--oss`, `--strict-config`,
`--dangerously-bypass-approvals-and-sandbox`,
`--dangerously-bypass-hook-trust`, `--skip-git-repo-check`,
`--ignore-user-config`, and `--ignore-rules`. V1 inheritable one-value options are
`-c/--config`, `--enable`, `--disable`, `-p/--profile`, `--local-provider`,
`-s/--sandbox`, and `--add-dir`. Root-only `-a/--ask-for-approval` is also
inheritable with one value, and root-only `--search` is inheritable with zero
values. Repeated options preserve order. Split and equals
forms are accepted where supported. Unknown options fail closed because their arity
cannot be inferred safely.

The normalized command has two option partitions. Root-only approval arguments are
emitted before `exec`; options accepted by `codex exec` are emitted after it:

```text
<executable> <root options> exec <exec options> <Megastorm task options> <prompt>
```

It removes or replaces child-specific/interactive arguments:

- an `exec` subcommand and its single prompt payload; every `resume` form is rejected;
- `-m`, `--model`, and `--model=<value>`;
- `-C`, `--cd`, and `--cd=<value>`;
- `-o`, `--output-last-message`, and equals forms;
- `--json`, `--no-alt-screen` (zero values), `--color` (one value), `--output-schema` (one value),
  and an inherited `--ephemeral` are recognized and removed; Megastorm appends one
  canonical `--ephemeral` and owns its output contract. Split and equals forms of
  the recognized one-value options are accepted;
- `--image`, interactive-only modes, `--`, stdin prompt `-`, and non-`exec`
  subcommands fail closed rather than being partially inherited;
- prompt payloads and output-stream formatting arguments that conflict with the
  runner's last-message contract.

For a normal interactive host command, no positional is allowed after option
parsing because it is an initial prompt. For an ancestor already running `exec`,
the parser consumes the same v1 grammar, removes exactly one final prompt, and
rejects `exec resume`, extra positionals, `--`, or `-`. `resume` and every other
subcommand are rejected.

The child argv is built as an array:

```text
<absolute executable> <preserved root args> exec <preserved exec args>
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
Its first element is resolved once with `shutil.which` when not absolute, then
replaced by its canonical absolute path; its basename must be `codex`. Invalid JSON, a scalar value, an empty
array, or non-string members fail preflight.

`--codex-template` remains for compatibility and tests, but it is used only when the
flag is explicitly supplied. Its legacy syntax is parsed once with `shlex.split` and
requires `{model}`, `{cwd}`, and `{out}` placeholders; the prompt is appended as one
argv element and no shell is invoked. The first token is canonicalized to an absolute
executable. Templates are trusted overrides and are not normalized as inherited host
commands. Reports mark them `legacy-template/unverified-inheritance`. Neither an
environment override nor template executes a bare executable through PATH.

## Redaction and reporting

Execution reports record:

- command source: `legacy-template`, `environment`, `linux-procfs`, or
  `macos-kern-procargs2`;
- absolute executable;
- redacted discovered arguments;
- redacted preserved session arguments.

Redaction hides values following or embedded in option names containing `token`,
`secret`, `password`, `api_key`, `apikey`, `authorization`, or `credential`. It also
parses `-c/--config` assignments and redacts when any dotted key segment is sensitive,
redacts URI userinfo, and replaces values exactly matching sensitive environment
values. A structured config value that cannot be parsed is entirely redacted.
Sensitive environment values are never emitted. Raw prompts and output paths are not
included in the command metadata.

## Failure handling

- No reliable Codex ancestor or explicit override: stop before creating worktrees.
- Executable cannot be resolved or executed: infrastructure preflight failure.
- Unknown option, ambiguous positional, `--`, stdin prompt, unsupported subcommand,
  or malformed option arity: stop and identify only its non-sensitive option name.
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
- Linux `/proc/<pid>/exe` plus cmdline agreement and macOS `KERN_PROCARGS2`
  parsing through injected binary fixtures;
- process exit/PID-reuse races, truncated buffers, spoofed argv identity, and
  executable disagreement;
- allowlisted option placement/arity, repeated options, unknown options, `--`, stdin
  prompt, `exec resume`, and unsupported subcommands;
- canonicalization/rejection of bare executable overrides and templates;
- structured config and credential-bearing URL redaction;
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
