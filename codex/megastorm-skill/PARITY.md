# Claude v0.14.0 → Codex capability parity

| Capability | Codex implementation |
|---|---|
| Environment capability probe | `execution-playbook.md` Phase -1 |
| Frozen registry and model tiers | Existing Codex Phase 0 |
| Class-elimination census | `execution-playbook.md` Phase 0.8 |
| Requirement/interface closure | Existing deterministic gates |
| Reality-gate task contract | schemas, prompts, validators |
| Reality-gate DAG passthrough | `scripts/build_task_dag.py` |
| Separate infrastructure/business retries | `scripts/run_layers.py` |
| Ready scheduling and skip chains | `scripts/run_layers.py` |
| Safe task/integration worktrees | `scripts/run_layers.py` |
| Atomic state, fingerprints, JSONL audit | `scripts/run_layers.py` |
| Reality/completeness final accounting | runner report + Phase 2 playbook |
| Independent Cross-exam | `codex/cross-exam-skill/` |
| Evidence renderer and open threads | Cross-exam protocol/scripts |

Claude Workflow APIs, plugin manifests, and slash commands are intentionally replaced by
Codex skills, `codex exec`, Python orchestration, and Codex fresh-context agents.
