# M1 design-routing — implementation plan

Design: `docs/superpowers/specs/2026-09-18-design-routing-design.md` (requirements R-M1-01..09, units U1–U9).
Branch `product-experience-overhaul`. Canonical tree `claude/meta-skill/`; `codex/` and `pi/` trees are
symlinks for every file touched here, and no hand-maintained twin is edited (owned by M5).
All commands run with cwd = repository root. The executor does not run git mutations.

## Ground rules for every task

- A task is a contract. The design's "Units" section holds the exact wording and tables; this plan states
  what must be true, how it is proven, and the complete write set. Do not leave the write set.
- Follow the design's **Spec corrections** (13 read sites, canonical game doc path plus the `design/`
  variant, findings/rendered function pair, `not_applicable` at `workflow.json` top level, the
  `test_bootstrap_scope.py::project()` fixture line).
- Shared hot files (`validate_bootstrap.py`, `validate_meta_contracts.py`, `bootstrap-planning.md`,
  `test_validate_bootstrap.py`, `test_bootstrap_scope.py`, `skills/bootstrap/SKILL.md`) get additive,
  localized edits only, exactly one M1 task each. Never remove or reword an existing pinned literal, never
  renumber existing list items or Musts.
- Do not touch `product_intent.py`, `validate_unattended_readiness.py`,
  `validate_game_creative_pipeline.py`, or any real file under `codex/` or `pi/`.
- Invariant owned by this module (acceptance grep #4): under `claude/meta-skill/knowledge/`, in every file
  whose name does not contain `bootstrap`, any line mentioning `experience_priority` also contains the
  literal `experience_priority.mode`. T-M1-04 and T-M1-05 write new sentences that fall under it.
- Known pre-existing failures (4, in `test_decision_gate` / `test_evidence_freshness`) are not in any
  acceptance command here and must not be "fixed".
- No task is reality-gated: everything is proven by pytest, validators or pinned literals.

## Task graph

```
T-M1-01 (validator + tests) ──► T-M1-04 (planning law, artifact contract)
T-M1-02 (SKILL.md schema + load clause) ─┐
T-M1-03 (13 read sites)                  ├─► T-M1-07 (contract pins + module closure)
T-M1-04, T-M1-05 (app-design), T-M1-06 ──┘
```

T-M1-01, 02, 03, 05, 06 have no intra-module dependency and are file-disjoint.

---

## T-M1-01 — `validate_experience_design_coverage` with its unit tests (U7 + U9; R-M1-07, R-M1-09)

Implements `api:validateExperienceDesignCoverage`.

**Behaviour.** `scripts/orchestrator/validate_bootstrap.py` exposes

```python
def experience_design_coverage_findings(bdir) -> list[dict]   # typed findings, same shape as effect_stage_ownership_findings
def validate_experience_design_coverage(bdir) -> list[str]    # _rendered(...) wrapper
def _ui_implementation_nodes(workflow, specs_dir, profile) -> list[dict]   # name is fixed: M3 calls it
```

with the four blocker codes `missing_experience_priority`, `missing_experience_design_node`,
`implementation_not_blocked_by_experience_design`, `experience_not_applicable_on_ui_product`.
Decision order, constants (`PRODUCT_ROUTES`, `EXPERIENCE_PRIORITY_MODES`, `APP_EXPERIENCE_DESIGN_ARTIFACTS`
with exactly the four app paths, `GAME_EXPERIENCE_DESIGN_DOC_PATHS` with both game paths, UI term tuples)
and placement are as design U7 steps 1–9. Key properties:

- never raises; missing/unparseable/non-dict profile or workflow → `[]`;
- `task_route` outside `new-product`/`product-reconstruction` → `[]` (covers `local-change` and legacy profiles);
- invalid/missing `experience_priority` (non-dict, illegal `mode`, empty `reason`) → only
  `missing_experience_priority`, short-circuit;
- `mode == "none"` → `[]`; `admin` is subject only to the `not_applicable.experience` check;
- UI implementation nodes are identified solely via `_ui_implementation_nodes`, built on the existing
  `_matching_nodes` plus profile module roles — no new heuristic, no bare `"ui"`/`"expo"` terms;
- artifact match accepts a monorepo prefix (`endswith("/" + path)`); a node that itself produces the artifact
  is not required to depend on itself; a transitive `hard_blocked_by` path to any one producer per required
  artifact group suffices; each message ends with `RETURN_TO_BOOTSTRAP`.

Registration: one line in `main()` directly after `validate_app_design_flow`, both public names in
`__all__`, appended as the last term of the `structural_gate_blockers` return, one line in the module
docstring's check list. The bootstrap copy list is not changed.

**Test intent (write first, see them fail).** In `tests/unit/test_validate_bootstrap.py`, appended after
`test_app_design_flow_passes_…`, using the file's existing `_bootstrap_dir` / `_base_node` / `_write` style,
a fixture helper named `_experience_project` (name fixed: M3 reuses it) and a subprocess helper that loads
`validate_bootstrap` from `<host>/meta-skill/scripts/orchestrator` (subprocess, because
`module_isolation.load` caches by realpath and would make host parametrization vacuous). All eight
behaviour tests are parametrized over `HOSTS = ["claude", "codex"]`, names exactly as the design's U9 table:

| Test | Asserts | Why it proves the behaviour |
|---|---|---|
| `…passes_with_design_node_blocking_ui_implementation` | baseline graph, `consumer` → `[]` | no false positive on the intended shape |
| `…rejects_missing_experience_priority` (3 shapes) | only that code | short-circuit and A1 (`reason` required) |
| `…rejects_workflow_without_design_node` | code present, messages name the user-flow and screen-requirements paths | the ink-scent incident is refused |
| `…rejects_ui_implementation_not_blocked_by_design` | only the unblocked node reported with correct `node_id`; a transitively blocked sibling is not | transitive closure is honoured |
| `…rejects_experience_not_applicable_on_ui_product` | code present under `mode=admin` | check applies to every non-`none` mode |
| `…ignores_local_change`, `…ignores_mode_none` | `[]` | non-trigger routes stay silent |
| `…game_accepts_either_design_doc_path` | both game paths pass, none → `missing_experience_design_node` | spec correction 2 |

Two in-process wiring tests (no host param): `test_experience_coverage_is_a_structural_gate_blocker`
(`structural_gate_blockers` code set contains `missing_experience_design_node`, proving `/run`-boundary
reachability) and `test_app_design_flow_fixtures_raise_no_experience_findings` (existing profile-less
app-design fixtures yield `[]`).

`tests/unit/test_bootstrap_scope.py::project()` gains exactly one profile line,
`"experience_priority": {"mode": "none", "reason": "Headless order-service fixture; no end-user interface"}`;
without it the shared product-route fixture fails all gates with `missing_experience_priority`
(design spec correction 6). No assertion anywhere is weakened.

**Write set.** `claude/meta-skill/scripts/orchestrator/validate_bootstrap.py`,
`claude/meta-skill/tests/unit/test_validate_bootstrap.py`, `claude/meta-skill/tests/unit/test_bootstrap_scope.py`.

**Acceptance** (collection guards make zero-test passes impossible; the second pytest run is the regression
set from the design):

```bash
CO="$(python3 -m pytest --co -q claude/meta-skill/tests/unit/test_validate_bootstrap.py)"; \
echo "$CO" | grep -q 'test_experience_coverage_rejects_workflow_without_design_node\[codex\]' && \
echo "$CO" | grep -q 'test_experience_coverage_passes_with_design_node_blocking_ui_implementation\[claude\]' && \
echo "$CO" | grep -q 'test_experience_coverage_is_a_structural_gate_blocker' && \
echo "$CO" | grep -q 'test_app_design_flow_fixtures_raise_no_experience_findings' && \
test "$(echo "$CO" | grep -c 'test_experience_coverage_')" -ge 19 && \
python3 -m pytest -q claude/meta-skill/tests/unit/test_validate_bootstrap.py && \
python3 -m pytest -q claude/meta-skill/tests/unit/test_validate_unattended_readiness.py claude/meta-skill/tests/unit/test_bootstrap_scope.py claude/meta-skill/tests/unit/test_product_intent_session.py claude/meta-skill/tests/unit/test_acceptance_allocation.py claude/meta-skill/tests/unit/test_legacy_projection_authority.py claude/meta-skill/tests/unit/test_legacy_profile_authority.py claude/meta-skill/tests/unit/test_intent_review_corrections.py claude/meta-skill/tests/unit/test_product_intent_resume.py claude/meta-skill/tests/unit/test_product_retained_scope.py claude/meta-skill/tests/unit/test_planning_audit_contracts.py
```

(19 = 8 host-parametrized tests × 2 hosts, with the 3-shape and 2-path tests contributing more, plus 1
un-parametrized `test_experience_coverage_is_a_structural_gate_blocker`; the floor is deliberately conservative.)

Depends on: none.

---

## T-M1-02 — bootstrap skill: `experience_priority` schema/producer and the forced design-knowledge load (U1 + U3; R-M1-01, R-M1-03)

Implements `data:experiencePriority`.

**Behaviour.** In `skills/bootstrap/SKILL.md`:

- Step 1.6 profile JSON block carries, right after `"architecture_pattern"`, the line
  `"experience_priority": {"mode": "consumer | admin | mixed | none", "reason": "<one sentence: who the product serves and why this mode>"},`
- a `**experience_priority**` paragraph after the block (before the `bootstrap-profile.json vs discovery
  source-summary.json` quote): bootstrap is the sole producer; downstream reads
  `bootstrap-profile.json` `experience_priority.mode` and never reclassifies; criteria for the four modes;
  `none` only for `cli`, `library-sdk`, `embedded-firmware` or pure backend/API; judged by who the product
  serves, not the stack; games are `consumer`; `reason` mandatory; `local-change` may omit the field.
- Step 1.2 ends with `Classify experience_priority (see 1.6) from task_goal, product_vision and who the product serves.`
- Step 2: items 1–8 and `Capabilities are REFERENCE material, not a node menu.` unchanged and un-renumbered;
  item 1 gains the pointer sentence `Product routes with an interface also load item 9 regardless of goal names.`;
  new item 9 exactly as design U3 (condition `experience_priority.mode != none` on `new-product` /
  `product-reconstruction`; loads `knowledge/capabilities/product-concept.md`,
  `knowledge/consumer-maturity-patterns.md`, `knowledge/journey-emotion-schema.md`, and
  `knowledge/capabilities/app-design.md` or `knowledge/capabilities/game-design.md`; closes with
  `This loads method, not a fixed node list.`), path prefix style consistent with the section.

The literals checked below are the ones T-M1-07 pins; write them verbatim.

**Test intent.** No unit test reads this prose. Proof is the pinned literals (all absent at baseline —
`experience_priority` occurs 0 times in the file today) plus `validate_skills.py` (frontmatter/structure
intact) and `validate_meta_contracts.py` (no existing pinned literal lost).

**Write set.** `claude/meta-skill/skills/bootstrap/SKILL.md`.

**Acceptance**

```bash
F=claude/meta-skill/skills/bootstrap/SKILL.md; \
grep -qF '"mode": "consumer | admin | mixed | none"' $F && \
grep -qF 'Classify experience_priority (see 1.6)' $F && \
grep -qF 'experience_priority.mode != none' $F && \
grep -qF 'knowledge/capabilities/product-concept.md' $F && \
grep -qF 'knowledge/consumer-maturity-patterns.md' $F && \
grep -qF 'knowledge/journey-emotion-schema.md' $F && \
grep -qF 'knowledge/capabilities/app-design.md' $F && \
grep -qF 'knowledge/capabilities/game-design.md' $F && \
grep -qF 'Product routes with an interface also load item 9' $F && \
grep -qF 'This loads method, not a fixed node list.' $F && \
grep -qF 'Capabilities are REFERENCE material, not a node menu.' $F && \
python3 claude/meta-skill/scripts/orchestrator/validate_skills.py claude/meta-skill/skills && \
python3 claude/meta-skill/scripts/orchestrator/validate_meta_contracts.py
```

Depends on: none.

---

## T-M1-03 — unify the 13 `experience_priority` read sites (U2; R-M1-02)

**Behaviour.** Every read site in `knowledge/` reads `bootstrap-profile.json` `experience_priority.mode`.
Apply the design's U2 table line by line and change nothing else: 8 lines are rewritten, 5 already
comply (`experience-map-schema.md:371` only gains `, read from \`bootstrap-profile.json\``;
`consumer-maturity-patterns.md:9` gains the `bootstrap-profile.json` qualifier). In particular:
the `experience_priority` row is deleted from the source-summary field table in `product-analysis.md`
and replaced by the sentence beginning `Experience classification is not a source-summary field:` before the
"Archetype fallback rule" paragraph; `generate-artifacts.md` no longer claims to generate the field;
`design-audit-dimensions.md` no longer says `product-map.json` contains it.

**Test intent.** The module invariant grep (prints 8 lines at baseline → must print nothing) plus positive
literals for the rewritten sentences and the absence of the two false producer/source claims.

**Write set.** `claude/meta-skill/knowledge/consumer-maturity-patterns.md`,
`claude/meta-skill/knowledge/experience-map-schema.md`,
`claude/meta-skill/knowledge/design-audit-dimensions.md`,
`claude/meta-skill/knowledge/capabilities/product-analysis.md`,
`claude/meta-skill/knowledge/capabilities/generate-artifacts.md`,
`claude/meta-skill/knowledge/capabilities/translate.md`,
`claude/meta-skill/knowledge/capabilities/feature-gap.md`.

**Acceptance**

```bash
K=claude/meta-skill/knowledge; \
test -z "$(grep -rn 'experience_priority' $K | grep -v 'experience_priority.mode' | grep -v bootstrap)" && \
grep -qF 'Experience classification is not a source-summary field' $K/capabilities/product-analysis.md && \
grep -qF 'carried unchanged (never reclassified)' $K/capabilities/product-analysis.md && \
grep -qF '`bootstrap-profile.json` `experience_priority.mode` is `consumer` or `mixed`' $K/design-audit-dimensions.md && \
! grep -qF '`product-map.json` contains `experience_priority`' $K/design-audit-dimensions.md && \
! grep -qF 'experience_priority' $K/capabilities/generate-artifacts.md && \
grep -qF '`protection_level`, `audience_type`, `render_as` fields generated' $K/capabilities/generate-artifacts.md && \
grep -qF 'When `bootstrap-profile.json` `experience_priority.mode = consumer`' $K/consumer-maturity-patterns.md && \
grep -qF 'experience_priority.mode' $K/capabilities/translate.md && \
grep -qF 'experience_priority.mode' $K/capabilities/feature-gap.md && \
grep -F 'experience_priority.mode' $K/experience-map-schema.md | grep -qF 'bootstrap-profile.json' && \
python3 claude/meta-skill/scripts/orchestrator/validate_meta_contracts.py
```

Depends on: none.

---

## T-M1-04 — planning law: experience design is never omitted; artifact-path contract (U4; R-M1-04)

Implements `data:experienceDesignArtifacts`.

**Behaviour.** `knowledge/bootstrap-planning.md` `## Free planning` gains one appended list item (existing
five items and all Musts untouched) with the design U4 wording: "Smallest" never means omitting experience
design; on product routes with `experience_priority.mode` `consumer`/`mixed` the workflow contains node(s)
whose `exit_artifacts` produce the experience design artifacts and every interface-implementing node is
directly or transitively `hard_blocked_by` them; the contract is the artifact path, not the node name; the
four app paths; the canonical game path `.allforai/game-design/game-design-doc.json` with
`.allforai/game-design/design/game-design-doc.json` accepted as the same artifact; names the two refusing
codes. `knowledge/product-intent-confirmation.md` `plan` operation gains, after the `not_applicable may
explain …` sentence, one sentence (single line, so it satisfies the T-M1-03 invariant) stating that
`not_applicable.experience` is legal only when `bootstrap-profile.json` `experience_priority.mode` is `none`,
otherwise refused as `experience_not_applicable_on_ui_product`.

**Test intent.** The contract is "text and validator define the same path set". The acceptance imports
T-M1-01's constants and asserts every path in `APP_EXPERIENCE_DESIGN_ARTIFACTS` and
`GAME_EXPERIENCE_DESIGN_DOC_PATHS` appears verbatim in `bootstrap-planning.md`, and that the app tuple is
exactly the four registry paths — so drift on either side fails. Literal greps cover the law sentence, the
two codes, and the `not_applicable` rule; the invariant grep is re-run because this task adds an
`experience_priority` line to a non-bootstrap knowledge file.

**Write set.** `claude/meta-skill/knowledge/bootstrap-planning.md`,
`claude/meta-skill/knowledge/product-intent-confirmation.md`.

**Acceptance**

```bash
K=claude/meta-skill/knowledge; \
python3 -c "
import sys, pathlib
sys.path.insert(0, 'claude/meta-skill/scripts/orchestrator')
import validate_bootstrap as vb
text = pathlib.Path('claude/meta-skill/knowledge/bootstrap-planning.md').read_text(encoding='utf-8')
app = tuple(vb.APP_EXPERIENCE_DESIGN_ARTIFACTS)
assert app == ('.allforai/app-design/concept/job-story-spec.json', '.allforai/app-design/spec/user-flow-spec.json', '.allforai/app-design/spec/screen-requirements-spec.json', '.allforai/app-design/spec/permissions-notifications-settings-spec.json'), app
paths = app + tuple(vb.GAME_EXPERIENCE_DESIGN_DOC_PATHS)
assert len(paths) == 6
missing = [p for p in paths if p not in text]
assert not missing, missing
" && \
grep -qF 'never means omitting experience design' $K/bootstrap-planning.md && \
grep -qF 'missing_experience_design_node' $K/bootstrap-planning.md && \
grep -qF 'implementation_not_blocked_by_experience_design' $K/bootstrap-planning.md && \
grep -qF 'the contract is the artifact path' $K/bootstrap-planning.md && \
grep -F 'not_applicable.experience' $K/product-intent-confirmation.md | grep -F 'experience_priority.mode' | grep -qF 'experience_not_applicable_on_ui_product' && \
test -z "$(grep -n 'experience_priority' $K/product-intent-confirmation.md | grep -v 'experience_priority.mode')" && \
python3 claude/meta-skill/scripts/orchestrator/validate_meta_contracts.py
```

Depends on: T-M1-01 (imports its constants).

---

## T-M1-05 — app-design runs unattended: `human_gate` out, Phase A `decision_inputs` in (U5; R-M1-05)

**Behaviour.** `knowledge/capabilities/app-design.md`: the line-5 note is replaced by the design U5 sentence
(direction choices are Phase A decisions; `decision_mode: "brainstorm"` + `decision_inputs`; no node carries
`human_gate: true`; nothing waits for approval at run time). The `## Human Gate Protocol` section is replaced
in place by `## Decision Inputs` (Phase A collects direction choices into
`.allforai/app-design/decision-<id>.json` wired to consumers' `decision_inputs`; `/run` nodes only read
them; no `.allforai/app-design/approval-records.json` is written and no `approval_record_path` is set; the
legacy concept-drift read in the bootstrap skill is left alone). "Merge all approved design JSONs" becomes
"Merge all selected design JSONs". The `Discipline Owner` column stays. `tests/prompts/domain-codex.md`
line 37's last question is replaced by the design's sentence so reviewers no longer demand the removed
section. `SKILL.md`, `validate_approval_records`, `validate_app_design_flow` are not touched. If a new line
mentions `experience_priority`, it must contain `experience_priority.mode`.

**Test intent.** Absence of the section heading and of the "requires approval" note, presence of the
replacement heading and mechanism literals, the prompt no longer asking for the section; the existing
app-design-flow unit tests still pass (the deterministic app-design checks are unaffected).

**Write set.** `claude/meta-skill/knowledge/capabilities/app-design.md`,
`claude/meta-skill/tests/prompts/domain-codex.md`.

**Acceptance**

```bash
A=claude/meta-skill/knowledge/capabilities/app-design.md; P=claude/meta-skill/tests/prompts/domain-codex.md; \
! grep -qF '## Human Gate Protocol' $A && \
! grep -qF 'requires `discipline_owner` approval' $A && \
! grep -qF 'Merge all approved design JSONs' $A && \
grep -qF '## Decision Inputs' $A && \
grep -qF 'decision_mode: "brainstorm"' $A && \
grep -qF 'decision_inputs' $A && \
grep -qF 'No node carries `human_gate: true`' $A && \
grep -qF 'Merge all selected design JSONs' $A && \
grep -qF 'Discipline Owner' $A && \
! grep -qF 'Human Gate Protocol 节是否引用' $P && \
grep -qF '是否已无 Human Gate Protocol 节' $P && \
test -z "$(grep -n 'experience_priority' $A | grep -v 'experience_priority.mode')" && \
python3 claude/meta-skill/scripts/orchestrator/validate_meta_contracts.py && \
python3 -m pytest --co -q claude/meta-skill/tests/unit/test_validate_bootstrap.py | grep -q 'test_app_design_flow_passes' && \
python3 -m pytest -q claude/meta-skill/tests/unit/test_validate_bootstrap.py -k test_app_design_flow
```

Depends on: none.

---

## T-M1-06 — §3.5.0b App Design Coverage Check (U6; R-M1-06)

**Behaviour.** `knowledge/bootstrap-audits.md`: the §3.5 Trigger sentence routes three ways —
`has_product_concept` false and game → §3.5.0; false, non-game and `experience_priority.mode != none` →
§3.5.0b; otherwise → Step 3.4. A new heading
`#### 3.5.0b App Design Coverage Check (interface products without product-concept.json)` sits after the end
of §3.5.0 and before `#### 3.5.1`, with a lead paragraph (coverage is judged against the experience design
artifact nodes and their node-specs, not a feature list), a three-column table
(System Concern / Trigger Condition / Check) with these seven System Concern rows —
`First entry & onboarding`, `Main line, not a feature grid`, `In-progress feedback of the core loop`,
`What happens after completion`, `Empty / loading / error / success states`, `Reason to return`,
`Settings audience` — and a closing paragraph: unlike §3.5.0, a gap on an interface product is **blocking**,
not a note; repair by widening an existing experience design node-spec or adding a design node that UI
implementation nodes are `hard_blocked_by`, re-run the check, do not enter Step 3.4 until clean; a changed
node set is re-confirmed under the Phase A "Post-confirmation plan delta" rule. The Settings-audience row
only requires the check to exist (the field contract `data:settingsAudience` belongs to M4). Write the file
in its existing language (English).

**Test intent.** Pinned literals: the heading (the one T-M1-07 pins), the trigger condition, all seven row
labels, the word "blocking", and ordering (3.5.0b heading appears before the 3.5.1 heading).

**Write set.** `claude/meta-skill/knowledge/bootstrap-audits.md`.

**Acceptance**

```bash
F=claude/meta-skill/knowledge/bootstrap-audits.md; \
grep -qF '#### 3.5.0b App Design Coverage Check' $F && \
grep -qF 'experience_priority.mode != none' $F && \
grep -qF 'App Design Coverage Check** (§3.5.0b)' $F && \
grep -qF 'First entry & onboarding' $F && \
grep -qF 'Main line, not a feature grid' $F && \
grep -qF 'In-progress feedback of the core loop' $F && \
grep -qF 'What happens after completion' $F && \
grep -qF 'Empty / loading / error / success states' $F && \
grep -qF 'Reason to return' $F && \
grep -qF 'Settings audience' $F && \
grep -qiF 'blocking' $F && \
test "$(grep -n '^#### 3.5.0b' $F | head -1 | cut -d: -f1)" -lt "$(grep -n '^#### 3.5.1' $F | head -1 | cut -d: -f1)" && \
python3 claude/meta-skill/scripts/orchestrator/validate_meta_contracts.py
```

Depends on: none.

---

## T-M1-07 — pin the routing contract in `validate_meta_contracts.py`; module closure (U8; R-M1-08)

**Behaviour.** `scripts/orchestrator/validate_meta_contracts.py` gains

```python
def validate_experience_routing_contract(errors: list[str]) -> None
```

placed after `validate_execution_repair_loop_contract` and modelled on it. Against `_bootstrap_text()` it
requires these nine literals, appending `f"bootstrap.md: missing experience routing term {term}"` for each
absent one: `experience_priority`, `"mode": "consumer | admin | mixed | none"`,
`experience_priority.mode != none`, `knowledge/capabilities/product-concept.md`,
`knowledge/consumer-maturity-patterns.md`, `knowledge/journey-emotion-schema.md`,
`knowledge/capabilities/app-design.md`, `knowledge/capabilities/game-design.md`,
`3.5.0b App Design Coverage Check`. `main()` calls it right after
`validate_execution_repair_loop_contract(errors)`. No existing pin is removed or altered. If a literal does
not match the text written by T-M1-02/T-M1-06, the pin list here is the contract — report the mismatch
rather than loosening the pin (those files are outside this write set).

**Test intent.** There is no unit-test file for this validator, so acceptance proves both directions
directly: (a) with the real corpus the validator exits 0 (texts from T-M1-02/06 are present and verbatim);
(b) with `_bootstrap_text` stubbed to an empty string the new function reports exactly nine
`missing experience routing term` errors — so it cannot be a no-op; (c) `main()` source calls it.
As the module's last task it also runs the design's remaining acceptance commands (`validate_skills.py`,
invariant grep #4) over the finished module.

**Write set.** `claude/meta-skill/scripts/orchestrator/validate_meta_contracts.py`.

**Acceptance**

```bash
python3 claude/meta-skill/scripts/orchestrator/validate_meta_contracts.py && \
python3 -c "
import sys, inspect
sys.path.insert(0, 'claude/meta-skill/scripts/orchestrator')
import validate_meta_contracts as m
assert 'validate_experience_routing_contract(errors)' in inspect.getsource(m.main)
real = []
m.validate_experience_routing_contract(real)
assert real == [], real
m._bootstrap_text = lambda: ''
errs = []
m.validate_experience_routing_contract(errs)
hits = [e for e in errs if 'missing experience routing term' in e]
assert len(hits) == 9, errs
assert any('3.5.0b App Design Coverage Check' in e for e in hits)
assert any('consumer | admin | mixed | none' in e for e in hits)
" && \
python3 claude/meta-skill/scripts/orchestrator/validate_skills.py claude/meta-skill/skills && \
test -z "$(grep -rn 'experience_priority' claude/meta-skill/knowledge | grep -v 'experience_priority.mode' | grep -v bootstrap)"
```

Depends on: T-M1-02, T-M1-03, T-M1-04, T-M1-05, T-M1-06.

---

## Requirement and interface coverage

| Requirement | Task |
|---|---|
| R-M1-01, R-M1-03 | T-M1-02 |
| R-M1-02 | T-M1-03 |
| R-M1-04 | T-M1-04 |
| R-M1-05 | T-M1-05 |
| R-M1-06 | T-M1-06 |
| R-M1-07, R-M1-09 | T-M1-01 |
| R-M1-08 | T-M1-07 |

| Exposed interface | Implemented by |
|---|---|
| `api:validateExperienceDesignCoverage` | T-M1-01 |
| `data:experiencePriority` | T-M1-02 |
| `data:experienceDesignArtifacts` | T-M1-04 |

Consumes: none. Reality-gated tasks: none.

## Notes for the orchestrator

- T-M1-01 keeps test and implementation in one task on purpose: a "red tests only" task has no acceptance
  command that exits 0, and both files are cross-module hot files that should be visited once. The executor
  still works test-first inside the task.
- Consequence to carry into M5 release notes (from the design): already-bootstrapped product-route projects
  get `missing_experience_priority` at their next `/run` until `/bootstrap` is re-run.
