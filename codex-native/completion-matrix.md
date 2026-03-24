# Codex Native Completion Matrix

This matrix tracks Codex-native completion by plugin.

Status meanings:

- `Pass`: native entry exists, does not depend on compat for core execution,
  and is not wrapper-only
- `Partial`: native docs exist, but major gaps remain
- `Fail`: no meaningful native implementation exists yet

## Plugin matrix

| Plugin | Native entry exists | Compat dependency removed | Wrapper-only cleared | Status | Notes |
|---|---|---|---|---|---|
| `product-design` | Yes | Yes | Yes | Pass | native entry, main command, playbook, commands, and 9 native sub-skill docs exist |
| `dev-forge` | Yes | Yes | Yes | Pass | native entry, main command, playbook, validation commands, and 4 native skill docs exist |
| `demo-forge` | Yes | Yes | Yes | Pass | native entry, playbook, main command, and 4 native stage docs exist |
| `code-replicate` | Yes | Yes | Yes | Pass | native entry, playbook, main command, and 7 native sub-skill docs exist |
| `code-tuner` | Yes | Yes | Yes | Pass | native entry and native playbook are self-contained for the current workflow scope |
| `ui-forge` | Yes | Yes | Yes | Pass | native entry and native playbook are self-contained for the current workflow scope |

## Repository-level checks

| Check | Status | Notes |
|---|---|---|
| Top-level native index exists | Pass | `codex-native/SKILL.md` exists |
| Native conventions exist | Pass | `codex-native/conventions.md` exists |
| Migration status exists | Pass | `codex-native/migration-status.md` exists |
| Index and status are fully consistent | Pass | top-level index and migration status now agree on plugin existence and progress state |
| Compat retirement ready | Pass | native surface satisfies the retirement criteria and no active compat layer is required |

## Next actions

1. optionally tighten native docs with deeper phase detail where useful
2. keep validating native docs against real usage
