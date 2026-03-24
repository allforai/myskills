# Codex Compat Retirement Criteria

This document records the criteria that were used to determine when
`codex-compat/` could be removed safely.

## Hard exit criteria

All of the following had to be true before `codex-compat/` could be removed.

### 1. Full native plugin coverage

`codex-native/` must have a native entry for each target plugin:

- `product-design`
- `dev-forge`
- `demo-forge`
- `code-replicate`
- `code-tuner`
- `ui-forge`

### 2. Zero compat dependency

No file under `codex-native/` may depend on `codex-compat/` for core execution
logic.

Disallowed examples:

- native `SKILL.md` files pointing to compat playbooks as execution authority
- native command docs that require compat wrappers to explain primary behavior

### 3. No wrapper-only native files

Every native workflow doc in scope must stand on its own.

A native file fails this rule if it effectively says:

- "use the source command as reference"
- "use the original skill as the workflow reference"
- "guidance rather than runtime parity"

without also defining:

- when to use it
- modes
- prerequisites
- outputs
- degradation rules
- final response contract

### 4. Status documents are consistent

The following documents must agree:

- `codex-native/SKILL.md`
- `codex-native/migration-status.md`
- `codex-native/completion-matrix.md`

There must be no mismatch between:

- declared status
- actual directory presence
- actual native readiness

### 5. Reverse validation passes

A reverse validation sweep must find no critical gaps in the target native
surface:

- no missing native paths referenced by the index
- no key workflow still depending on Claude-only runtime semantics
- no key workflow still depending on compat
- no wrapper-only files in the declared native-complete scope

### 6. Artifact compatibility remains intact

Removing `codex-compat/` must not change:

- `.allforai/` artifact locations
- report file locations
- existing Claude/OpenCode source plugin directories

## Recommended transition sequence

1. finish all native plugin entries
2. move remaining execution authority from compat into native
3. run reverse validation
4. update the completion matrix to all-pass where appropriate
5. only then remove `codex-compat/`

## Retirement decision

Use this decision rule:

`codex-compat/` could retire only when `codex-native/` fully replaced it and no
native execution path still pointed back to it.

Current repository state:

- the native surface now satisfies the technical retirement criteria
- `codex-compat/` has been removed from the active Codex path
