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

## Outcome (2026-09-22)

All nine tasks landed on `main`, each with its own task review, then one whole-batch review (Opus) and one fix wave with a scoped re-review.

| Task | Commit | Note |
|---|---|---|
| A1 | `475acd7b` | both validators refuse a directory that holds only the retired format |
| A2 | `95dd8bef` | four files deleted, 1101 lines |
| A3 | `bb7410f5` | five documents |
| B1 | `88ac5bf5` | plan defect found in execution: the entry function had to be private (`_cli`) |
| B2 | `8148a9fe` | both renderers; frozen v2 golden unchanged |
| B3 | `131eb028` | intake text, Claude + Codex |
| B4 | `36b77397` | on top of merged upstream `5f605f69`; thought test passed first try |
| C1 | `bd91761c` | hook measured at 38 s with the node suite |
| C2 | `dde23c9b` | 149/149; repair-loop and budget interaction reviewed: no deadlock, no re-grant |
| fix wave | `89b6baf0` | engine comment no longer claims parity with the Codex driver; hook requires Node >= 21; upgrade note |

### Follow-ups left open on purpose

1. **Terminal-node parity (ADR-0004).** The engine re-measures only inherited completions that a remaining node depends on; the Codex driver measures every node on every pass. A completed terminal node whose artifact was deleted is incomplete on Codex and `complete` on Claude. Closing it costs one gate run (with its validation commands) per completed node on every resume — an owner decision.
2. **Behaviour change to know about.** A QA node whose repair budget was fully spent in an earlier session can now be un-completed and rerun on resume; if it fails again the run ends `needs_diagnosis` where it used to end `complete`.
3. `judged_build.excludes` is recorded but `/product-review`'s prescribed `git status` does not use it; the error direction is toward "stale", never toward "fresh".
4. `identity.py` usage errors exit 1 with plain text, not the JSON `reason` shape the intake text describes.
5. An un-completed node is announced only through `log()`; `transition_log` will show it completed twice with no recorded reason.
6. One test message uses `JSON.stringify(answer)`, which cannot tell `undefined` from `null`.
