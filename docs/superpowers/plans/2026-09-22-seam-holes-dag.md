# Seam Holes — Execution DAG for the Three 2026-09-22 Plans

Plans (each is self-contained; this file only orders their tasks):

- **A** `2026-09-22-retire-state-machine-format-plan.md` — A1 validators refuse the retired format · A2 delete what only it used · A3 documents
- **B** `2026-09-22-cross-exam-judged-build-plan.md` — B1 engine CLI · B2 both renderers · B3 intake text · B4 /product-review text
- **C** `2026-09-22-inherited-completions-remeasured-plan.md` — C1 run-engine suite gets an invoker · C2 resumed runs re-measure inherited completions

## Dependencies

```
A1 ──► A3            (A3 names the error A1 introduces)
A2                   (independent of A1; after it only to keep one plan's commits together)
B1 ──► B3            (B3 documents B1's command line)
B2 ──► B3, B2 ──► B4 (both quote B2's header lines)
C1 ──► C2            (C2's final hook run exercises the JS suite C1 wires in)
A3 ◄─► C1            same file, different sections of CLAUDE.md — never concurrent
```

No other two tasks touch the same file. Checked pairs that looked close and are disjoint: A2 (`shared/scripts/orchestrator/test_*.py`) vs C1 (`shared/suites/test_suite_coverage.py`); B1 (`claude/meta-skill/scripts/engine/`) vs A1 (`claude/meta-skill/scripts/orchestrator/`); C2 (`cross-phase-protocols.md`) vs everything.

## Why the batch is serial for writers and parallel for readers

Every task commits to one `main` checkout through one git index and one ~35 s pre-commit hook that runs whole-tree suites. Two implementers at once means one task's half-made edit fails the other's hook, and a pathspec commit cannot protect a working tree. The owner's standing rule is no worktrees. So: **one implementer at a time; reviews (read-only, from a diff file) run concurrently with the next implementer.** A fix round is a writer: it waits for the running implementer to finish, and the next dispatch waits for it.

## Order

Interleaved so that a plan's review overlaps another plan's implementation:

| Wave | Implement | Reviewed concurrently |
|---|---|---|
| 1 | A1 | — |
| 2 | B1 | A1 |
| 3 | C1 | B1 |
| 4 | A2 | C1 |
| 5 | B2 | A2 |
| 6 | C2 | B2 |
| 7 | A3 | C2 |
| 8 | B3 | A3 |
| 9 | B4 | B3 |
| 10 | — | B4, then one whole-batch final review |

## Closure self-review applied to the plans (2026-09-22)

- **Mapping** (a rerun upstream ↔ what was built on it): C2 first removed only the failed inherited node; a completed consumer of it stayed done. Fixed in the plan: fixpoint — a completed node with a dependency that is not done is not done, and each removal makes that node's own dependencies askable.
- **Mapping** (two hosts, two texts): B edits Claude and Codex SKILL / schemas / renderer / product-review in pairs; Pi reads the Codex tree. A edits both validators. C restores agreement with the Codex driver, which already measures.
- **Exception**: C1 says "not run" out loud when `node` is missing; B1 exits 1 with a reason and B3 forbids inventing a value; A1 turns a silent pass into a named error. C2 treats a missing or misaddressed gate answer as not passed.
- **Lifecycle**: B — `judged_build` is written once and never rewritten on resume; old reports without the line are handled by B4. A — nothing generates the retired format, so nothing is orphaned by the deletion. C1's probe file and the earlier orphan probe are removed in the same step that creates them.
- **Navigation** (no dead ends): A's error says rerun `/bootstrap`; B4's "新鲜度未核" keeps the existing pointer to rerun `/cross-exam`; C1's message names the missing tool.
- **Config**: `HOOK` and `EXEMPT_PREFIXES` exist in `shared/suites/test_suite_coverage.py`; `sync.py --check` exists; both product-review anchors occur exactly once in each file; a v3 fixture renders today in both renderer suites.
- **Left open on purpose**: Pi's and Codex's own `orchestrator-template.md` keep their Session Resume prose (Codex measures in code; Pi's loop re-reads `check_artifacts.py` each iteration). A visible "pending sync" state for offline actions in the product-design philosophy was not improved by the last thought test.
