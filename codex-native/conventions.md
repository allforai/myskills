# Codex Native Conventions

These rules define what "Codex-native" means in this repository.

## Required properties

- no dependency on Claude frontmatter semantics such as `allowed-tools`
- no dependency on slash-command execution semantics
- no dependency on `${CLAUDE_PLUGIN_ROOT}`
- no instruction that requires Claude-only `AskUserQuestion`, `Task`, or
  `Agent` behavior to make sense

## Interaction rules

- ask the user only when a missing answer would materially corrupt the next
  phase
- otherwise choose the conservative default and state the assumption
- collapse multi-step interactive questionnaires into the minimum blocking set

## Orchestration rules

- describe modes as workflow selectors, not slash commands
- describe phases, prerequisites, outputs, and quality gates explicitly
- describe downgrade behavior explicitly when external tools are unavailable
- prefer deterministic artifact inspection over host-state assumptions

## Source reference rules

- native docs may cite source plugin files as references
- source plugin files are authority for domain intent, not runtime semantics
- native docs must stand on their own even if the source files are not opened

## Completion standard

A workflow is considered Codex-native only when:

1. its main `SKILL.md` explains when to use it without Claude-specific syntax
2. its major commands or sub-skills have standalone native operating rules
3. its prerequisites, outputs, and downgrade paths are explicit
4. a Codex user can execute the workflow without being told to "just follow the
   Claude file"
