# OpenCode Compatibility Guide

Use these rules when adapting existing plugin content for OpenCode.

## Runtime translation

- `AskUserQuestion`: ask the user directly only when blocking information is
  required; otherwise make a reasonable assumption and continue.
- `allowed-tools`: treat as intent hints, not an enforced permission model.
- `$ARGUMENTS`: interpret from the user's natural-language request.
- `Task` / `Agent`: use OpenCode subagents only when explicit delegation makes
  sense.
- Slash commands such as `/product-design full`: represent named workflows, not
  literal OpenCode commands.

## Path translation

- Replace `${CLAUDE_PLUGIN_ROOT}` with repository-relative paths from the
  wrapper skill directory.
- Treat the original plugin directories as the canonical source for detailed
  docs and scripts.

## Safety goals

- Do not move or rename the original plugin directories while compatibility is
  incremental.
- Prefer wrapper skills and documentation over invasive refactors.
- Only extract shared core content after OpenCode wrappers are validated.

