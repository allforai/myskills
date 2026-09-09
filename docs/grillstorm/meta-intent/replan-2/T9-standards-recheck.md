# T9 standards recheck

Reviewed only `git diff ed3313c7b729c4f9575968c08eaec2bfb4312e3e...HEAD` at `ea046abc8e0a479d736d332e5e5d15514d3ff294`: commit `ea046abc fix(meta-skill): reject malformed retained decision inputs (#9)`, two files. The prior standards report was read as historical context; no other review axis was read.

## Documented standards

No hard violations found against `CLAUDE.md`, `CONTEXT.md`, `codex/meta-skill/AGENTS.md`, or ADRs 0001–0003. Tooling-enforced checks were excluded.

The new guard in `claude/meta-skill/scripts/orchestrator/product_intent.py:24` stays in the shared helper, consistent with the Codex adapter's **Shared Asset Strategy** (reuse canonical helpers and tests). It validates artifact shape without prescribing a graph, consistent with ADR 0001's project-specific free planning and placement of cross-node invariants in validators. The delta does not change visual-review policy governed by ADR 0002 as amended by 0003.

## Optional heuristic

- **Low — possible Duplicated Code:** `claude/meta-skill/tests/unit/test_bootstrap_scope.py:29` adds another retained warehouse setup: `retained = {"node_id": "warehouse", ...}`, `workflow["nodes"].append(retained)`, writing `stock.json`, and serializing the node-spec. The same setup already exists at lines 409 and 496; this finding concerns the new repetition, not reopening those historical hunks. Consider a small retained-node fixture helper while keeping malformed-input mutation, host history keys, and recovery assertions explicit. No documented rule requires extraction, and no repository override requires this duplication.

All twelve supplied smell categories were considered; no other actionable heuristic found. HEAD remained pinned and the candidate worktree clean. No tests were run, production files modified, commits created, or subagents used.

Result: zero hard violations, one optional maintainability suggestion; this report makes no spec-acceptance or runtime-correctness claim.
