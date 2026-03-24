# Runtime Gaps And Degradation Rules

This document records the remaining gaps between the source plugin runtime model
and the current OpenCode compatibility layer.

## Fully translated today

- Root plugin discovery through OpenCode wrapper `SKILL.md` files
- Direct references to source skills, commands, docs, and scripts
- Path translation away from `${CLAUDE_PLUGIN_ROOT}`
- Repository-safe, non-breaking parallel layout

## Partially translated

### Interactive decision systems

Source plugins frequently use `AskUserQuestion` as a structured host feature.
In OpenCode wrappers this becomes:

- ask only when a missing answer blocks progress
- otherwise infer conservatively and continue
- record the assumption in normal output when appropriate

### Slash-command routing

Source examples such as `/product-design full` or `/demo-forge verify` are now
treated as workflow labels rather than executable commands.

### Claude command metadata

Fields such as `allowed-tools` and `$ARGUMENTS` are descriptive only in OpenCode.

## Still host-coupled

### Claude/OpenCode installation flows

- `.claude-plugin/`
- marketplace metadata
- Claude plugin enablement
- OpenCode installer registration

These remain unchanged and are not reimplemented inside OpenCode wrappers.

### MCP-heavy workflows

The source repository expects host-managed tooling for:

- Playwright browser automation
- Stitch UI
- Claude-specific MCP registration flows

OpenCode wrappers can document these requirements, but they cannot claim runtime
parity where the host capability is absent.

### Media and external service pipelines

`demo-forge` and parts of `product-design` rely on external credentials and
service availability. OpenCode wrappers preserve the workflow definition but must
degrade gracefully when those services are not configured.

