# Code Replicate For Codex Native

This document defines the Codex-native entry contract for repository
reverse-engineering.

## When to use

Use this workflow when the user wants to:

- reconstruct product and architecture artifacts from an existing codebase
- prepare an existing system for downstream forge workflows
- analyze a codebase at `interface`, `functional`, `architecture`, or `exact`
  fidelity

## Inputs

- source path or remote repository URL
- desired fidelity level
- optional project type and scope

## Native execution rules

- treat source discovery as phase-driven work, not a slash command
- prefer inference over unnecessary questioning
- keep the source repository read-only by default
- produce artifacts rather than only prose summaries

## Core outputs

- `.allforai/code-replicate/replicate-config.json`
- `.allforai/code-replicate/discovery-profile.json`
- `.allforai/code-replicate/source-summary.json`
- `.allforai/code-replicate/replicate-report.md`
- any generated downstream `.allforai/product-map/`, `.allforai/experience-map/`,
  and `.allforai/use-case/` artifacts
