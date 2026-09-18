# M3 experience-gate — task contracts

Design: `docs/superpowers/specs/2026-09-18-experience-gate-design.md` (requirements R-M3-01 … R-M3-11 and
`## Detailed design`, units U1–U7). Registry: `docs/superpowers/runs/2026-09-18-product-experience-overhaul/registry.json`.
Branch `product-experience-overhaul`. All commands run with cwd = repo root. Paths below are repo-relative;
`CMS` abbreviates `claude/meta-skill` in prose only (never in commands).

A task here is a contract: what must be true, how the failing test proves it, the exact acceptance command, and the
complete write set. The design's Detailed design section is the authority for every literal (field names, blocker
codes, section headings, pinned strings). Where this plan and the design disagree, the design wins; report the
disagreement instead of improvising.

## Module-wide rules

- Canonical tree only. `codex/meta-skill/{scripts,tests,knowledge/capabilities}` and `pi/meta-skill/…` follow by symlink.
  Do not edit any hand-maintained twin (`codex/meta-skill/knowledge/flow-template.py` carries its own
  `PRODUCTION_GAP_FIELDS`; its parity belongs to M5, not here).
- Never run `pytest codex/meta-skill` or `pytest pi/meta-skill` as directories. Never use the whole
  `claude/meta-skill/tests/unit` directory as an acceptance (four known pre-existing failures, ~6 min).
- Do not touch: `skills/game-creative/**`, `knowledge/capabilities/game-design.md`, `validate_game_creative_pipeline.py`,
  `validate_unattended_readiness.py`, `reconcile_bootstrap_workflow.py`, `skills/bootstrap/SKILL.md`.
- Every edit to a shared hot file is additive and localized (one task per hot file): `validate_bootstrap.py`,
  `test_validate_bootstrap.py`, `check_artifacts.py`, `bootstrap-planning.md`, `validate_meta_contracts.py`.
  No existing pinned literal in `validate_meta_contracts.py` is removed or reworded.
- No node id, capability or skill name introduced here may contain `product-review` or `cross-exam`
  (`verdict_entry_planned_as_node`).
- M1 invariant that M3 must keep true: every line under `claude/meta-skill/knowledge` (outside files whose name contains
  `bootstrap`) that mentions `experience_priority` contains the literal `experience_priority.mode` on the same line.
- No git mutation by executors; the orchestrator commits.
- **Cross-module ordering is explicit.** The scheduler is dependency-ready, not module-ordered: interface edges
  (`requires` → `implements`) only reach the *early* upstream tasks (T-M1-01/02/04, T-M2-04, T-M4-01/03). They do not
  reach the upstream tasks M3 really stands on — T-M1-03 (the same-line `experience_priority.mode` invariant that three
  M3 acceptances grep), T-M1-05 (Human Gate removal in `app-design.md`), T-M2-01…10 (live edits to `product_intent.py`
  and the suites M3's regression commands run), T-M4-04/05/08 (skill JSON blocks and `validate_meta_contracts.py`
  being edited while M3 runs those validators). Therefore T-M3-02, T-M3-04, T-M3-05 and T-M3-08 carry `depends_on`
  entries for the upstream sink tasks **T-M1-07, T-M2-10, T-M4-07, T-M4-08** (each sink transitively covers its whole
  module). This realises the overview's order M1 → (M2 ∥ M4) → M3 in the DAG. T-M3-01 stays free (tmp_path tests only).
  These foreign ids are stable; if an upstream plan renumbers its sink, update these four entries.

## Interface ownership

| Exposed interface | Proved consumable by |
|---|---|
| `data:experienceCritiqueReport` | T-M3-02 |
| `data:experienceReviewDoc` | T-M3-02 |
| `data:experienceLensVocabulary` | T-M3-02 |
| `api:validateExperienceGateFlow` | T-M3-05 |

Consumed: `data:experiencePriority`, `data:experienceDesignArtifacts` (M1); `data:experienceDirectionIntent` (M2);
`data:settingsAudience`, `data:unspecifiedDecisionGap` (M4). T-M3-05 additionally requires
`api:validateExperienceDesignCoverage` (M1): design U3 trigger 3 forbids a second UI-implementation-node heuristic and
mandates reuse of the helper M1 lands together with that function. The name is from the frozen registry; the module
manifest's `consumes` list omitted it, the design text did not.

## Requirement coverage

| Requirement | Tasks |
|---|---|
| R-M3-01, R-M3-02, R-M3-03, R-M3-04, R-M3-10 | T-M3-02 |
| R-M3-05 | T-M3-02 (PACK), T-M3-03 (capability) |
| R-M3-06 | T-M3-03, T-M3-07, T-M3-08 |
| R-M3-07 | T-M3-04, T-M3-06, T-M3-07 |
| R-M3-08 | T-M3-05 |
| R-M3-09 | T-M3-01, T-M3-09, T-M3-10 |
| R-M3-11 | T-M3-01, T-M3-04, T-M3-05, T-M3-06 |

## Dependency sketch

```
T01 ──► T02 ──► T03
         │ └──► T07 ─┐
         │      T08 ─┼─► T09 ─┐
T04 ─────┼───────────┘        ├─► T10
T05 ──► T06 ──────────────────┘
```

T02, T04, T05 and T08 additionally wait for the upstream sinks T-M1-07, T-M2-10, T-M4-07, T-M4-08 (see Module-wide
rules). No task is reality-gated: every acceptance is a deterministic test, validator run or literal check.

---

## T-M3-01 — Source-wiring validator `validate_app_experience_pipeline.py` with its unit test

**Implements (requirement):** R-M3-09 (validator), R-M3-11 (its test). Design U4 first bullet, U7 second bullet.

**Behaviour.** A new script mirrors `validate_game_creative_pipeline.py` section by section (same private helpers,
same `main(argv)` with `repo_root` defaulting to `.`, exit 1 and one error per stderr line on failure).

```python
def validate_app_experience_pipeline(repo_root: str) -> list[str]
```

- Required files: `claude/meta-skill/skills/app-design/PACK.md` and
  `claude/meta-skill/skills/app-design/40-qa/experience-quality-critique/SKILL.md`; when either is missing, report only
  the missing file(s) and return.
- Every `skills/app-design/**/SKILL.md` must appear in PACK by canonical path; error text
  `app-design/PACK.md: missing canonical child path skills/<ref>`.
- `REQUIRED_PARENT_TERMS` and `REQUIRED_CRITIQUE_TERMS` exactly as enumerated in design U4; a missing term yields an
  error containing `missing required term <term>`.
- `BOOTSTRAP_CORPUS` = `skills/bootstrap/SKILL.md`, `knowledge/bootstrap-planning.md`,
  `knowledge/capabilities/app-design.md` (written with the `claude/meta-skill/` prefix, missing files skipped). The corpus
  must contain `skills/app-design/40-qa/experience-quality-critique/SKILL.md`; the error for an unwired corpus **starts
  with** `bootstrap corpus:` (T-M3-02's test filters on this prefix — it is part of the contract).

**Test intent (write first).** `test_validate_app_experience_pipeline.py` mirrors
`test_validate_game_creative_pipeline.py` with a `_minimal_repo(tmp_path)` fixture that lists every required term
line by line. Three cases, with these exact names (the acceptance counts the `test_validate_app_experience_pipeline_`
prefix; the game file it mirrors has only the first two, the third is new here) —
`test_validate_app_experience_pipeline_accepts_minimal_graph`,
`test_validate_app_experience_pipeline_rejects_unlisted_child`,
`test_validate_app_experience_pipeline_rejects_missing_term`: the minimal graph yields `[]` (proves the term lists are satisfiable and nothing beyond
them is demanded); an extra child `SKILL.md` absent from PACK yields `missing canonical child path` (proves the
child-listing rule); deleting `audience_leak` from the critique fixture yields `missing required term audience_leak`
(proves the lens vocabulary is actually pinned). The tests run on `tmp_path`, so they pass before the real skill exists.

**Write set:** `claude/meta-skill/scripts/orchestrator/validate_app_experience_pipeline.py` (create),
`claude/meta-skill/tests/unit/test_validate_app_experience_pipeline.py` (create).

**Acceptance:**

```bash
python3 -m py_compile claude/meta-skill/scripts/orchestrator/validate_app_experience_pipeline.py && [ "$(python3 -m pytest claude/meta-skill/tests/unit/test_validate_app_experience_pipeline.py --co -q | grep -c 'test_validate_app_experience_pipeline_')" -ge 3 ] && python3 -m pytest -q claude/meta-skill/tests/unit/test_validate_app_experience_pipeline.py claude/meta-skill/tests/unit/test_validate_game_creative_pipeline.py
```

**Depends on:** none.

---

## T-M3-02 — Child skill `experience-quality-critique` and its PACK registration

**Implements (interfaces):** `data:experienceCritiqueReport`, `data:experienceReviewDoc`, `data:experienceLensVocabulary`.
**Requirements:** R-M3-01, R-M3-02, R-M3-03, R-M3-04, R-M3-10, R-M3-05 (PACK half). Design U1 and U2 first bullet.
**Requires:** `data:experiencePriority`, `data:experienceDesignArtifacts`, `data:experienceDirectionIntent`,
`data:settingsAudience`, `data:unspecifiedDecisionGap` — the Input Contract names their real paths, fields and values;
read the landed M1/M2/M4 files and use their vocabulary verbatim (no synonyms for `audience`, `provisioning`,
`unspecified_user_visible_decision`, `topic == "experience-direction"`, `auto_decided`).

**Behaviour.**
- `SKILL.md` exists with frontmatter `name: app-design-40-qa-experience-quality-critique` and the twelve sections of
  design U1, aligned section-for-section with `skills/game-creative/40-qa/creative-quality-critique/SKILL.md`.
- The Output Contract json block is the design's schema verbatim in shape (`data:experienceCritiqueReport`): stage gates
  live under `gates{}`, elements are `finding_id`s; `design` may only fill `must_fix_before_implementation`, `runtime`
  only `must_fix_before_release`; `runtime` mirrors each must-fix into `experience_gaps[]`; `lenses.*` carries
  `有|缺|未查` plus `confidence`, never a numeric score. Every json fence in the file is parseable JSON
  (enumerations are written inside string values; no comments inside blocks).
- Invocation Contract block: `skill: "app-design/experience-quality-critique"`, modes `design` and `runtime`,
  `output_root: ".allforai/app-design/qa"`, all paths starting with `.allforai/`.
- Lenses section (`data:experienceLensVocabulary`): the eight identifiers, each at least once as backticked inline
  code, first occurrences in this order — `onboarding`, `process_feedback`, `next_step`, `state_consistency`,
  `return_reason`, `mainline`, `direction_fidelity`, `audience_leak`. The first five are declared same-name/same-meaning
  as the five lenses of `/product-review` question 4. `audience_leak` cites defensive-patterns Pattern J and the
  product-verify "audience leak" check rather than restating criteria. Anti-pattern contrast cites
  `consumer-maturity-patterns.md` §B. Taste filter: a finding whose `observation` cannot fill all four fields is not written.
- Reviewer Independence (R-M3-04): fresh-context reviewer, reads only listed artifacts and evidence, must not read the
  authoring node's reasoning; `reviewer.authored_reviewed_artifacts: true` forces `FAILED_VALIDATION`.
- Judgment Rules: pure `llm_judgment` never enters `must_fix_*`; `must_fix_*` accepts only `contract_defect`, or
  `evidence_based_critique` with `confidence >= 0.8` and concrete `evidence_refs`.
- Review Doc (`data:experienceReviewDoc`): `docs/experience-review/<stage>.md`, overwrite-latest, fixed headings in order
  `# 体验评审 — <stage>`, `## 结论`, `## Must-fix`, `## 各镜头观察`, `## 证据限制`, self-sufficient sentences
  (the reader does not open `.allforai/`).
- Purpose states this is an in-run self-correction gate, not the delivery verdict, and that it neither calls nor is
  named after the post-run verdict entries.
- `PACK.md`: Current Children row, canonical invocation path, new `## Judgment Types` and `## Shared Outputs` sections
  after `## Boundary`, frontmatter description suffix — all as worded in design U2.

**Test intent (write first).** New `test_experience_quality_critique_skill.py` reads the real files from the repo
checkout and asserts: (a) `validate_app_experience_pipeline(<repo root>)`, with errors starting `bootstrap corpus:`
filtered out, is `[]` — proves PACK lists every child and both files carry every pinned term, independently of when the
planning text lands; (b) inside the `## Lenses` section the eight backticked identifiers all occur and their first
occurrences are in registry order — this is exactly the substring form M6's parity test searches, so passing here means
the vocabulary is consumable; (c) every ```` ```json ```` fence parses, one parsed block has `gates` with exactly the
three gate keys and a `findings[0]` carrying `observation` with `who/circumstance/task/observed`, and one has
`skill == "app-design/experience-quality-critique"` — proves the report contract is machine-readable; (d) the four
review-doc headings and `docs/experience-review/` appear — proves the review-doc contract is stated where M6 reads it;
(e) the file contains neither `/cross-exam` nor `/product-review` inside any json fence `skill`/node-id value.
All five fail today because the file does not exist.

**Write set:** `claude/meta-skill/skills/app-design/40-qa/experience-quality-critique/SKILL.md` (create),
`claude/meta-skill/skills/app-design/PACK.md` (edit), `claude/meta-skill/tests/unit/test_experience_quality_critique_skill.py` (create).

**Acceptance:**

```bash
python3 -m pytest -q claude/meta-skill/tests/unit/test_experience_quality_critique_skill.py claude/meta-skill/tests/unit/test_validate_skills.py && python3 claude/meta-skill/scripts/orchestrator/validate_skills.py claude/meta-skill/skills
```

**Depends on:** T-M3-01; upstream sinks T-M1-07, T-M2-10, T-M4-07, T-M4-08 (its acceptance runs `validate_skills.py`
over skill files M4 edits, and the Input Contract quotes landed M1/M2/M4 vocabulary).

---

## T-M3-03 — Register the critique nodes in `capabilities/app-design.md`

**Requirements:** R-M3-05 (capability half), R-M3-06 (placement constraint). Design U2 second bullet, U6 placement paragraph.
**Requires:** `data:experiencePriority` (M1 has already removed the Human Gate section from this file and owns its
`## Decision Inputs` section; do not touch either).

**Behaviour.** Canonical Node Registry gains `experience-critique-design` (owner `independent-reviewer`) and
`experience-design-repair` (owner `lead-ux`) rows **before** the `app-design-finalize` row, with the outputs and
blocked-by cells of design U2. The sentence after "Required nodes" states they are mandatory when
`experience_priority.mode` is `consumer` or `mixed` (rule in `bootstrap-planning.md` Must #9) and absent for
`none`/`admin`. Sub-Skill Mapping gains three rows (`experience-critique-design` mode `design`,
`experience-design-repair`, `experience-critique-runtime` mode `runtime`) and the note that the runtime node is not an
app-design stage node: its capability must not be `app-design`, it sits after the last UI/product-verify/visual QA.
The new rows and notes contain no `human_gate` and no `decision_mode`. `APP_DESIGN_REQUIRED_NODES` in
`validate_bootstrap.py` is not extended.

**Test intent.** Prose registration; the checks are the orphan rule of `validate_skills.py` (slug reachable from a
capability mapping), the exact node ids, row order relative to `app-design-finalize`, absence of `human_gate` on the new
lines, the M1 same-line invariant, and `validate_meta_contracts.py` still green (no accidental `capability: "<new>"`).
The id greps fail today.

**Write set:** `claude/meta-skill/knowledge/capabilities/app-design.md`.

**Acceptance:**

```bash
F=claude/meta-skill/knowledge/capabilities/app-design.md && grep -q 'experience-critique-design' $F && grep -q 'experience-design-repair' $F && grep -q 'experience-critique-runtime' $F && grep -q 'app-design/40-qa/experience-quality-critique' $F && python3 -c 'import sys; t=open(sys.argv[1],encoding="utf-8").read(); assert t.index("| `experience-critique-design` |") < t.index("| `experience-design-repair` |") < t.index("| `app-design-finalize` |")' $F && ! grep -E 'experience-critique|experience-design-repair' $F | grep -qE 'human_gate|decision_mode' && ! grep -rn 'experience_priority' claude/meta-skill/knowledge | grep -v 'experience_priority.mode' | grep -v bootstrap | grep -q . && python3 claude/meta-skill/scripts/orchestrator/validate_skills.py claude/meta-skill/skills && python3 claude/meta-skill/scripts/orchestrator/validate_meta_contracts.py
```

**Depends on:** T-M3-02.

---

## T-M3-04 — `check_artifacts`: non-empty `must_fix_*` means the artifact is not complete

**Requirements:** R-M3-07 (deterministic half), R-M3-11. Design U5 and U7 third bullet, Spec correction 3.

**Behaviour.** `MUST_FIX_GATE_FIELDS = ("must_fix_before_implementation", "must_fix_before_release")`; both appended
to `PRODUCTION_GAP_FIELDS` and to the hard-fail set inside `_production_gap_error`. For these two fields only, when the
top-level value is empty and `data["gates"]` is a dict, the value is read from `gates.<field>`. The returned
`status_error` keeps `field` = the field name and the existing `reason` sentence. Behaviour for every other field is
unchanged byte for byte. Hard fail precedes the allow-flag check, so no production policy can wave it through.
Intended consequence: a game `creative-quality-critique.json` with non-empty `gates.must_fix_before_release` now also
fails. `must_fix_before_art_gen` / `must_fix_before_frontend` stay out. `reconcile_bootstrap_workflow.GAP_FIELDS` unchanged.

**Test intent (write first, in `test_check_artifacts.py` next to `test_quality_gaps_are_not_complete`).**
- `test_must_fix_before_implementation_in_gates_is_not_complete` and `test_must_fix_before_release_in_gates_is_not_complete`:
  artifact with the list under `gates{}` → not complete, `status_error["field"]` equals the field name. These are the
  cases that fail today and that a naive "add the name to the tuple" fix would still fail — they prove the nested read.
- `test_top_level_must_fix_is_not_complete`: same at top level.
- `test_empty_must_fix_gates_are_complete`: both must-fix lists `[]` under `gates{}` while
  `gates.recommended_iterations` is non-empty → complete, no `status_error`. Proves advice does not block.

**Write set:** `claude/meta-skill/scripts/orchestrator/check_artifacts.py`, `claude/meta-skill/tests/unit/test_check_artifacts.py`.

**Acceptance:**

```bash
[ "$(python3 -m pytest claude/meta-skill/tests/unit/test_check_artifacts.py --co -q | grep -c 'must_fix')" -ge 4 ] && python3 -m pytest -q claude/meta-skill/tests/unit/test_check_artifacts.py claude/meta-skill/tests/unit/test_check_artifacts_measurement.py
```

**Depends on:** upstream sinks T-M1-07, T-M2-10, T-M4-07, T-M4-08 (T-M4-07 edits
`test_check_artifacts_measurement.py`, which this acceptance runs).

---

## T-M3-05 — `validate_experience_gate_flow` in `validate_bootstrap.py`, registered at all three entry points

**Implements (interface):** `api:validateExperienceGateFlow`. **Requirements:** R-M3-08, R-M3-11. Design U3, U7 first bullet.
**Requires:** `data:experiencePriority`, `data:experienceDesignArtifacts`, `api:validateExperienceDesignCoverage`
(M1's `_ui_implementation_nodes(workflow, specs_dir, profile)` and M1's UI-implementation-node fixture in the test file).

**Behaviour.**

```python
EXPERIENCE_GATE_PRODUCT_ROUTES = ("new-product", "product-reconstruction")
EXPERIENCE_GATE_MODES = ("consumer", "mixed")
APP_EXPERIENCE_CRITIQUE = "experience-quality-critique"
GAME_CREATIVE_CRITIQUE = "creative-quality-critique"
EXPERIENCE_GATE_CLOSURE_CAPABILITIES = ("concept-acceptance", "pipeline-closure-verify")

def experience_gate_flow_findings(bdir: str) -> list   # typed [{code, message, node_id?}] via _structural
def validate_experience_gate_flow(bdir: str) -> list   # _rendered(experience_gate_flow_findings(bdir))
```

- Trigger, node classification (by `exit_artifacts` path, never by node id or capability; app stage by file-name
  suffix; game "post-implementation" by graph position), and the four blocker codes are exactly the design U3 tables:
  `missing_experience_gate`, `implementation_not_blocked_by_design_critique`,
  `closure_not_blocked_by_experience_gate`, `experience_gate_without_repair_loop`. These four strings are the legal set;
  they are defined in this file and nowhere else.
- The UI implementation node set comes from M1's `_ui_implementation_nodes`. If M1 inlined that logic, first extract it
  under that exact name with zero behaviour change (M1's tests untouched and green), then reuse it. No second heuristic.
- Pure, read-only, never raises: missing/unparseable/mis-shaped inputs return `[]`; cycles are absorbed by `_downstream_of`.
- Registered in `main()` (cross-node group, after the `validate_app_design_flow` call), in `__all__` (both names), and
  appended to the `structural_gate_blockers` return expression (docstring gains half a sentence).
- Missing or legacy flat-string `experience_priority` does not trigger (old projects are not retro-blocked here; absence
  is M1's code). `admin` and `none` do not trigger.

**Test intent (write first; appended section in `test_validate_bootstrap.py`, no host parametrization).**
A private helper `_experience_gate_project(tmp_path, *, game=False, mode="consumer", route="new-product", nodes=None,
loops=None)` writes profile, workflow, minimal node-specs and readiness spec and produces a **passing** graph by
default; each rejection case removes exactly one edge/node/loop so the asserted code is attributable to that one
defect. Assertions read `code` from `experience_gate_flow_findings`. The fourteen cases of design U7 are all required
(names contain `experience_gate`): app passes; game passes; app without critique node (and single-stage variant naming
the missing stage); game without creative critique; implementation not blocked by design critique; closure not blocked
(app); closure not blocked (game with only the pre-implementation critique); critique outside repair loop (plus
readiness-spec-missing variant); not triggered for `mode == none`; for `local-change`; without `experience_priority`;
reader node that only mentions the skill is not a gate; `structural_gate_blockers(project_root)` surfaces the same
code (proves the `/run`-boundary registration); malformed profile / non-list `nodes` return `[]` without raising.
UI implementation nodes reuse M1's fixture so both modules agree on what such a node is.

Regression: the three product-route suites below must stay green with the new gate registered. If a consumer-mode
fixture trips this gate, the fixture text contains UI wording — fix the fixture wording; never loosen the trigger
(design Assumption 11).

**Write set:** `claude/meta-skill/scripts/orchestrator/validate_bootstrap.py`, `claude/meta-skill/tests/unit/test_validate_bootstrap.py`.

**Acceptance:**

```bash
python3 -m py_compile claude/meta-skill/scripts/orchestrator/validate_bootstrap.py && python3 -c 'import sys; sys.path.insert(0,"claude/meta-skill/scripts/orchestrator"); import validate_bootstrap as v; assert {"validate_experience_gate_flow","experience_gate_flow_findings"} <= set(v.__all__); assert callable(v._ui_implementation_nodes)' && [ "$(python3 -m pytest claude/meta-skill/tests/unit/test_validate_bootstrap.py --co -q | grep -c 'experience_gate')" -ge 14 ] && python3 -m pytest -q claude/meta-skill/tests/unit/test_validate_bootstrap.py claude/meta-skill/tests/unit/test_validate_unattended_readiness.py claude/meta-skill/tests/unit/test_bootstrap_scope.py claude/meta-skill/tests/unit/test_product_intent_session.py claude/meta-skill/tests/unit/test_acceptance_allocation.py
```

**Depends on:** upstream sinks T-M1-07, T-M2-10, T-M4-07, T-M4-08 (the regression suites in this acceptance execute
`product_intent.py` and `test_product_intent_session.py`, both under edit until T-M2-10), plus `requires`.

---

## T-M3-06 — Readiness gate accepts the Must #9 repair-loop shape, and the new gate bites at the `/run` boundary

**Requirements:** R-M3-07 (loop declaration), R-M3-11. Design U7 fourth bullet. `validate_unattended_readiness.py` is **not** edited.
**Requires:** `data:experiencePriority`, `data:experienceDesignArtifacts`.

**Why two tests, not one.** `validate_unattended_readiness` also calls `product_intent.validate_scope`. As soon as the
profile carries `task_route: new-product`, `status == "ready"` needs the whole product contract (`task_goal`,
`task_scope`, frozen intents, `requirement_refs`, confirmed plan, and after M2 a confirmed `experience-direction`
intent). A "minimal" product-route fixture in this file can never be `ready`; the full product-route pass is M5's
`test_designed_and_gated_workflow_passes_every_public_gate`. Every existing fixture in this file is profile-less for
that reason. So the two claims are proved separately:

**Behaviour / test intent.** Two new tests reusing `_write`, `_minimal_project` and `_repair_loop`:

1. `test_unattended_readiness_accepts_experience_gate_repair_loops` — **profile-less** graph (no
   `bootstrap-profile.json`, like `_project_with_repair_loop`) with the Must #9 shape: experience design node → design
   critique (`exit_artifacts` ending `experience-quality-critique-design.json`) → design repair → a node waiting for
   both (the design loop's closure, directly `hard_blocked_by` QA and repair) → UI implementation → runtime critique
   (`…-runtime.json`) → implementation repair → closure node directly `hard_blocked_by` runtime critique and repair.
   Two declared loops. Use neutral capabilities (`qa`, `implement`) and ids outside `APP_DESIGN_REQUIRED_NODES` so
   `validate_app_design_flow` has nothing to say; the experience design node's `exit_artifacts` already cover M1's
   user-flow and screen-requirements paths so the same graph serves test 2. Assert `report["blockers"] == []`. Proves the loop shape Must #9 prescribes is accepted by the
   existing readiness gate and by `repair_loop_declaration_findings` (closure directly blocked by QA and repair,
   bounded budget).
2. `test_unattended_readiness_reports_experience_gate_at_run_boundary` — the same graph plus a profile
   `{task_route: "new-product", experience_priority: {mode: "consumer", reason: …}}` and node-specs whose wording makes
   M1's `_ui_implementation_nodes` recognise the UI implementation node (reuse the wording of M1's fixture in
   `test_validate_bootstrap.py`). Do **not** assert `status`: scope blockers such as `invalid_scope` are expected and
   are not this test's subject. Assert on the set of blocker codes only: with both loops declared it contains no code
   starting `experience_gate`, no `missing_experience_gate`, no `implementation_not_blocked_by_design_critique`, no
   `closure_not_blocked_by_experience_gate` and no `missing_experience_design_node`; after dropping the runtime loop
   from the spec it contains `experience_gate_without_repair_loop`; after removing the runtime critique node it
   contains `missing_experience_gate`. Without this second test the first would pass on a fixture that never reached
   M3's gate; with it, the registration in `structural_gate_blockers` is proved from the real `/run` entry.

**Write set:** `claude/meta-skill/tests/unit/test_validate_unattended_readiness.py`.

**Acceptance:**

```bash
python3 -m pytest -q "claude/meta-skill/tests/unit/test_validate_unattended_readiness.py::test_unattended_readiness_accepts_experience_gate_repair_loops" "claude/meta-skill/tests/unit/test_validate_unattended_readiness.py::test_unattended_readiness_reports_experience_gate_at_run_boundary" && python3 -m pytest -q claude/meta-skill/tests/unit/test_validate_unattended_readiness.py
```

**Depends on:** T-M3-05.

---

## T-M3-07 — Planning law Must #9 in `bootstrap-planning.md`

**Requirements:** R-M3-06, R-M3-07 (routing prose), R-M3-04, R-M3-10 (node-spec obligations). Design U6 first two bullets.
**Requires:** `data:experiencePriority` (uses `experience_priority.mode`, always with `.mode`).

**Behaviour.** A ninth item is appended after Must 8, same single-paragraph style, headed
`**Experience quality gate (products with UI).**`. Content checklist is design U6 (scope: non-game product routes with
mode `consumer`/`mixed`; `stage: "design"` before any UI implementation node and `stage: "runtime"` after the last
UI/product-verify/visual QA; both nodes' `exit_artifacts` — the `.json`, same-name `.html` and
`docs/experience-review/design.md` / `runtime.md`; fresh-context reviewer that does not read the author's reasoning;
closure nodes `hard_blocked_by` the runtime critique; non-empty `must_fix_before_implementation` /
`must_fix_before_release` fail the artifact via `check_artifacts.py`; one declared loop per critique node in
`unattended-run-readiness-spec.json.required_repair_loops` with the design/runtime routing, `experience_gaps`, Must #2
budget, Run Policy on exhaustion, no questions during the run; placement: design critique and design repair use
`capability: app-design` before `app-design-finalize`, runtime critique must not, suggested `quality-checks`; node ids
never contain the post-run verdict entry names; closing sentence: games are covered by item 8 and both are enforced by
`validate_experience_gate_flow`). Must 8's text is unchanged. The paragraph must not contain the quoted form
`capability: "<name>"` for any name without a capability file.

**Test intent.** Prose; the check is the exact literals T-M3-09 will pin, the unchanged Must 8 heading, the real-repo
run of `validate_app_experience_pipeline.py` (exit 0 requires the corpus to cite the skill path — this task or T-M3-03
supplies it, and everything else it checks was delivered by T-M3-02), and `validate_meta_contracts.py` staying green.
The literal greps fail today.

**Write set:** `claude/meta-skill/knowledge/bootstrap-planning.md`.

**Acceptance:**

```bash
F=claude/meta-skill/knowledge/bootstrap-planning.md && grep -qF '9. **Experience quality gate (products with UI).**' $F && grep -qF '8. **Creative quality gate (game projects).**' $F && grep -qF 'skills/app-design/40-qa/experience-quality-critique/SKILL.md' $F && grep -qF 'experience-quality-critique-design.json' $F && grep -qF 'experience-quality-critique-runtime.json' $F && grep -qF 'must_fix_before_implementation' $F && grep -qF 'must_fix_before_release' $F && grep -qF 'docs/experience-review/' $F && grep -qF 'required_repair_loops' $F && grep -qF 'experience_gaps' $F && grep -qF 'validate_experience_gate_flow' $F && grep -qF 'experience_priority.mode' $F && python3 claude/meta-skill/scripts/orchestrator/validate_app_experience_pipeline.py . && python3 claude/meta-skill/scripts/orchestrator/validate_meta_contracts.py
```

**Depends on:** T-M3-01, T-M3-02.

---

## T-M3-08 — Suppress rule and `concept-acceptance` prerequisite

**Requirements:** R-M3-06. Design U6 third and fourth bullets.
**Requires:** `data:experiencePriority`.

**Behaviour.** `suppress-rules.md` table gains the row
`| \`experience_priority.mode = none\` | experience quality gate (Must #9) nodes | no end-user UI to judge; the summary states the exemption |`
(`admin` is "not applicable", not suppressed — no row). `concept-acceptance.md` `## Prerequisite` gains a closing
paragraph: the node is `hard_blocked_by` the creative/experience critique — for games the post-implementation
`creative-quality-critique` (Must #8), for apps with UI the runtime-stage `experience-quality-critique` (Must #9); while
`must_fix_*` is non-empty the critique node is incomplete and this gate does not start; the critique judges quality and
routes repair, this gate still only checks coverage and does not score (ADR-0008 unchanged).

**Test intent.** Prose; checks are the exact suppress literal, both skill names in `concept-acceptance.md` (neither is
there today: current count 0), the M1 same-line invariant, and `validate_meta_contracts.py` green (suppress-rules is in
its bootstrap corpus).

**Write set:** `claude/meta-skill/knowledge/suppress-rules.md`, `claude/meta-skill/knowledge/capabilities/concept-acceptance.md`.

**Acceptance:**

```bash
grep -qF 'experience_priority.mode = none' claude/meta-skill/knowledge/suppress-rules.md && grep -qF 'Must #9' claude/meta-skill/knowledge/suppress-rules.md && grep -qF 'creative-quality-critique' claude/meta-skill/knowledge/capabilities/concept-acceptance.md && grep -qF 'experience-quality-critique' claude/meta-skill/knowledge/capabilities/concept-acceptance.md && grep -qF 'hard_blocked_by' claude/meta-skill/knowledge/capabilities/concept-acceptance.md && ! grep -rn 'experience_priority' claude/meta-skill/knowledge | grep -v 'experience_priority.mode' | grep -v bootstrap | grep -q . && python3 claude/meta-skill/scripts/orchestrator/validate_meta_contracts.py
```

**Depends on:** upstream sinks T-M1-07, T-M2-10, T-M4-07, T-M4-08 (T-M1-03 establishes the same-line invariant this
acceptance greps; without the edge this task is ready as soon as T-M1-02 is, i.e. possibly while T-M1-03 is mid-edit).

---

## T-M3-09 — Pin the gate contract in `validate_meta_contracts.py`

**Requirements:** R-M3-09 (third sentence). Design U4 last bullet.

**Behaviour.** New `validate_experience_gate_contract(errors: list[str]) -> None`, modelled on
`validate_execution_repair_loop_contract`, registered as the last call in `main()`. Pins, additively:
- in `_bootstrap_text()`: `Experience quality gate (products with UI)`,
  `skills/app-design/40-qa/experience-quality-critique/SKILL.md`, `experience-quality-critique-design.json`,
  `experience-quality-critique-runtime.json`, `must_fix_before_implementation`, `must_fix_before_release`,
  `docs/experience-review/`, `experience_priority.mode = none`;
- in `knowledge/capabilities/concept-acceptance.md`: `creative-quality-critique` and `experience-quality-critique`;
- in `skills/app-design/PACK.md`: `experience-quality-critique`.
A missing file is reported as an error, not raised. No existing function or pinned literal changes.

**Test intent.** There is no unit test file for this validator in the repo, so the proof is behavioural and two-sided:
with the real tree the full validator exits 0 (the pins are satisfied by T-M3-02/07/08); with `_bootstrap_text`
replaced by an empty string the new function alone reports at least eight errors (one per bootstrap literal) — proves
the pins bite and that the function was not written as a no-op. The registration check requires the name to occur at
least twice as a call/def with `errors`.

**Write set:** `claude/meta-skill/scripts/orchestrator/validate_meta_contracts.py`.

**Acceptance:**

```bash
[ "$(grep -c 'validate_experience_gate_contract(errors' claude/meta-skill/scripts/orchestrator/validate_meta_contracts.py)" -ge 2 ] && python3 -c 'import sys; sys.path.insert(0,"claude/meta-skill/scripts/orchestrator"); import validate_meta_contracts as m; m._bootstrap_text=lambda: ""; e=[]; m.validate_experience_gate_contract(e); assert len(e) >= 8, e' && python3 claude/meta-skill/scripts/orchestrator/validate_meta_contracts.py
```

**Depends on:** T-M3-02, T-M3-07, T-M3-08.

---

## T-M3-10 — Pre-commit wiring and module acceptance

**Requirements:** R-M3-09 (hook), module acceptance of the design. Design U4 second bullet, "验收命令".
**Requires:** `data:experienceDirectionIntent` (the regression run includes M2's `test_experience_direction.py`, whose
consumer-mode fixtures must still pass all three gates with the new structural gate registered),
`data:settingsAudience`, `data:unspecifiedDecisionGap` (M4's edits to the same validators/knowledge are in the tree when
the full validator set runs).

**Behaviour.** `.githooks/pre-commit` gains exactly one line,
`python3 claude/meta-skill/scripts/orchestrator/validate_app_experience_pipeline.py .`, directly after the existing
`validate_game_creative_pipeline.py .` line (which stays single and unchanged — design Spec correction 1). Then the
whole module acceptance runs green. If a regression suite fails because a fixture now trips the experience gate, apply
design Assumption 11 (fix fixture wording in the owning test only after confirming the cause); do not alter trigger
conditions. Any such fix outside this write set is an escalation, not a silent edit.

**Test intent.** The hook line count is exactly 1 for each pipeline validator and the hook still parses; every
validator exits 0 on the real tree; every M3-touched and M1/M2 regression suite passes; the M1 same-line invariant holds.

**Write set:** `.githooks/pre-commit`.

**Acceptance:**

```bash
bash -n .githooks/pre-commit && [ "$(grep -c 'validate_app_experience_pipeline.py \.' .githooks/pre-commit)" -eq 1 ] && [ "$(grep -c 'validate_game_creative_pipeline.py \.' .githooks/pre-commit)" -eq 1 ] && python3 -m py_compile claude/meta-skill/scripts/orchestrator/*.py && python3 claude/meta-skill/scripts/orchestrator/validate_app_experience_pipeline.py . && python3 claude/meta-skill/scripts/orchestrator/validate_game_creative_pipeline.py . && python3 claude/meta-skill/scripts/orchestrator/validate_skills.py claude/meta-skill/skills && python3 claude/meta-skill/scripts/orchestrator/validate_meta_contracts.py && ! grep -rn 'experience_priority' claude/meta-skill/knowledge | grep -v 'experience_priority.mode' | grep -v bootstrap | grep -q . && python3 -m pytest -q claude/meta-skill/tests/unit/test_validate_bootstrap.py claude/meta-skill/tests/unit/test_validate_app_experience_pipeline.py claude/meta-skill/tests/unit/test_experience_quality_critique_skill.py claude/meta-skill/tests/unit/test_validate_game_creative_pipeline.py claude/meta-skill/tests/unit/test_check_artifacts.py claude/meta-skill/tests/unit/test_check_artifacts_measurement.py claude/meta-skill/tests/unit/test_validate_unattended_readiness.py claude/meta-skill/tests/unit/test_validate_skills.py claude/meta-skill/tests/unit/test_experience_direction.py claude/meta-skill/tests/unit/test_bootstrap_scope.py claude/meta-skill/tests/unit/test_product_intent_session.py claude/meta-skill/tests/unit/test_acceptance_allocation.py
```

**Depends on:** T-M3-03, T-M3-04, T-M3-06, T-M3-09.

---

## Notes for the orchestrator

- One file beyond the design's touch list is created: `claude/meta-skill/tests/unit/test_experience_quality_critique_skill.py`
  (T-M3-02). It turns the three data-interface contracts of the skill file into a real test instead of a grep chain,
  and it is distinct from M6's `test_experience_lens_parity.py`.
- T-M3-05 `requires` `api:validateExperienceDesignCoverage` although the M3 manifest's `consumes` omits it; see
  "Interface ownership".
- T-M3-02/04/05/08 carry foreign `depends_on` ids (T-M1-07, T-M2-10, T-M4-07, T-M4-08). `build_task_dag.py` resolves
  `depends_on` over the combined task list, so they are valid only when all six task files are fed to it together.
- Known consequence outside M3's write set: `codex/meta-skill/knowledge/flow-template.py` keeps its own
  `PRODUCTION_GAP_FIELDS` and does not learn the two `must_fix_*` fields here (M5 parity).
