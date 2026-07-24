# AGENTS.md — Cross-exam (Codex port, v0.15.0)

Independent, evidence-backed delivery audit for Codex. Read `SKILL.md` first.
The main session is the examiner; every probe must be a fresh-context sub-agent.
The skill is audit-only and interactive-only. It writes only under the selected
`docs/cross-exam` run directory and never edits the audited delivery.

Run deterministic renderer tests with `python3 -m pytest scripts/ -q`.
