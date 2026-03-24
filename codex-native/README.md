# Codex Native Layer

This directory contains a Codex-native adaptation layer for this repository.

Goals:

- preserve the original Claude/OpenCode plugin directories unchanged
- replace thin compatibility wrappers with Codex-native operating contracts
- keep the existing `.allforai/` artifact contract stable
- avoid any shared-core extraction that could disturb Claude-facing paths

Directory rules:

- each plugin gets its own native directory
- each native plugin should include a `SKILL.md`
- complex workflows should include `execution-playbook.md`
- thin commands should be promoted into standalone native workflow documents
- status tracking should live alongside the native layer rather than inside the
  source plugins

Current scope:

- repository-level Codex-native conventions
- native status tracking
- native coverage for all target plugins
- completion and retirement criteria

Non-goals:

- modifying `.claude-plugin/`
- changing existing plugin installation flows
- moving source docs or scripts out of current plugin directories
