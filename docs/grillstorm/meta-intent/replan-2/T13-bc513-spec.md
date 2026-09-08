# T13 final reporting correction — spec review (bc513f91, base c77323da)

Scope: `git diff c77323da...HEAD`, one commit, HEAD verified
`bc513f918422b616b7e11b4984b7584758c25f16`, diff non-empty (5 files, +128).
Source delta is three literals in `codex/.../flow-template.py:41-43` plus a
3-case parametrised test; the other three files are prior review reports.
Read: GitHub #13 v2 (`ready-for-agent`, no comments), CLAUDE.md, CONTEXT.md,
`codex/meta-skill/AGENTS.md`, ADR-0001/0003, `T13-c773-spec.md`,
`T13-c773-standards.md`. Report-only; nothing touched.

## Verdict

No missing, wrong, or partial requirement work; no scope creep; no new
completion shortcut. c773Standards named exactly `existence_only`,
`not_good_enough`, `quality_failed` as omitted from the Codex reporting set;
exactly those three are added, and nothing else.

## Requirement mapping

#13 同步后共同验收约束: "Claude 与 Codex 的实际入口和生成产物消费同一权威规则."
`BLOCKING_STATUS_VALUES` in `flow-template.py` and `check_artifacts.py` are now
set-identical (0 divergence either way, measured). The three values are already
authoritative in `check_artifacts.py:34-36`, `reconcile_bootstrap_workflow.py:43-45`
and `bootstrap-planning.md:122` ("may not use `existence_only` … `quality_failed`
as a passing state"), so this narrows Codex to the existing rule rather than
adding one — no unrequested restriction.

## Behaviour confirmed independently

- Negatives: current `test_flow.py` against c77323da source → **3 failed, 25
  deselected in 0.03s**, matching the claim.
- Positive control: each case rewrites `status: passed` and asserts
  `artifact_ready` — present inside the same test, passes.
- Whole Codex flow suite at HEAD: **28 passed in 1.27s**.
- Actual gate unchanged: `check_artifacts.py` is not in the diff; only the
  generated flow's local reporting moved. "脚本测试不冒充真实宿主测试" holds —
  copied-CLI runs only, host evidence remains 0/60.
- Qualified Run Policy acceptance intact: `handle_iteration`
  (`flow-template.py:600-602`) writes `accepted_with_gaps` nested in
  `decisions[]`; `artifact_status_error` scans top-level fields only, so accept
  still returns preflight state, unaffected by the new values.

## Observation (pre-existing, non-blocking)

Value parity is now exact, but field parity is not: `flow-template.py`
`STATUS_FIELDS`/`PRODUCTION_GAP_FIELDS` still lack `quality_status`,
`effect_status`, `experience_status`, `visual_quality_status` and five matching
`*_gaps`. So a Codex report using `quality_status: existence_only` — the exact
shape in `test_check_artifacts.py:149` — is still locally silent, though the
authoritative gate blocks it. Pre-existing shape, not a regression from this
delta, and the same duplication class c773Standards logged; recording it, not
expanding scope.
