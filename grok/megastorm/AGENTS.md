# Grok Megastorm plugin

This plugin targets the official xAI Grok Build CLI. Treat the repository design
and `README.md` conformance table as normative.

- `/megastorm` is an implementation workflow; `/cross-exam` is an explicit,
  audit-only workflow.
- Never treat a headless subprocess as a native independent subagent.
- Never claim `Grok host conformance: verified` from fake CLI tests.
- Phase 1.6 must use the deterministic runner and isolated Git worktrees.
- Effective CLI configuration is security-sensitive; fail closed when it cannot
  be resolved and restricted.

