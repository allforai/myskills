# M4 spec-gap-discipline — task contracts

Design: `docs/superpowers/specs/2026-09-18-spec-gap-discipline-design.md` (requirements R-M4-01..07 and
"Detailed design", units U1–U7). Registry: `docs/superpowers/runs/2026-09-18-product-experience-overhaul/registry.json`.
Branch `product-experience-overhaul`. All commands run from the repo root `/Users/aa/workspace/myskills`.
Paths below are repo-relative; `MS` = `claude/meta-skill`.

Exposes `data:unspecifiedDecisionGap` (T-M4-01) and `data:settingsAudience` (T-M4-03).
Consumes `data:experienceDesignArtifacts` from M1 (T-M4-01, T-M4-02).

## Ground rules for every task

- A task is a contract. The design's unit section is the content brief; this plan states what must be true,
  how it is proven, and the write set. Do not leave the write set. No new files anywhere in M4.
- Append-only. Every M4 edit adds text; none removes, reorders or rewrites an existing sentence, literal,
  frontmatter field or Invocation Contract JSON block. Existing pinned literals must survive verbatim.
- English body text in every edited file (matches the files). No project names (`ink-scent` etc.) in any
  example — `validate_generalization_boundaries.py` and the acceptance commands check this.
- No codex/pi twin writes: `codex/meta-skill/knowledge/defensive-patterns.md` and `codex/.../capabilities/`
  are symlinks to the canonical files; the other touched files have no twins.
- Not touched by M4: `check_artifacts.py`, `validate_skills.py`, `validate_bootstrap.py`,
  `bootstrap-planning.md`, `test_validate_bootstrap.py`, `test_bootstrap_scope.py`, `skills/bootstrap/SKILL.md`,
  `execution-repair-loop/SKILL.md`, `orchestrator-template.md`, `diagnosis.md`, `skills/app-design/PACK.md`,
  `capabilities/app-design.md`, `capabilities/ui-design.md`, any game-side UI spec.
- Baseline measured while planning (2026-09-18): `validate_meta_contracts.py`, `validate_skills.py
  claude/meta-skill/skills`, `validate_generalization_boundaries.py` all exit 0;
  `test_check_artifacts_measurement.py` = 50 passed; every literal pinned below is absent from its target file
  (grep count 0), so each acceptance command fails before its task is done.

## Deviation from the design's implementation order (deliberate)

The design says "U1 first, watch `validate_meta_contracts.py` go red, then U2–U6". In this run other modules
execute concurrently and use `validate_meta_contracts.py` as their own acceptance; a registered pin function
whose literals do not exist yet would turn that shared validator red for every module. So the order is inverted:
prose tasks T-M4-01..06 land first (each proven by exact-literal greps), and the pin function T-M4-08 lands last,
depending on all of them. The red half of the red/green proof moves into T-M4-08's acceptance command as a
negative probe: the new function is called against an empty root (must report 7 missing files) and against a
copy of the tree with one pinned heading removed (must report that exact term). The validator is therefore never
red on the shared branch, and the function is still proven to bite.

## Shared data shapes (the frozen interfaces)

`data:unspecifiedDecisionGap` — one entry of a node artifact's `contract_gaps[]`, five keys, all required:

```json
{
  "kind": "unspecified_user_visible_decision",
  "where": "<file or screen — what needed the decision>",
  "needed_decision": "<the question a design artifact must answer>",
  "blocking_intent_ids": ["<requirement id from the node's requirement_refs[].id>"],
  "suggested_owner_artifact": "<project-relative path present in some upstream node's exit_artifacts>"
}
```

`blocking_intent_ids` may be `[]` (say why in `needed_decision`). When no owner is found,
`suggested_owner_artifact` is the closest `data:experienceDesignArtifacts` path (apps: the four
`.allforai/app-design/...` artifacts of R-M1-04; games: `.allforai/game-design/game-design-doc.json`).

`data:settingsAudience` — the same field names on settings items and service endpoints:

| Field | Values | Required when |
|---|---|---|
| `audience` | `end-user` \| `operator` \| `developer` | every settings item and every service endpoint, exactly one |
| `provisioning` | `build-time` \| `remote-config` \| `deploy-env` | `audience != "end-user"`; absent on `end-user` items |
| `surface` | a topology `surface_id`, or `"none"` | every settings item; for non-`end-user` items only `"none"` or a surface whose `surface_type ∈ {admin_console, operator_console, cli}` |
| `requirement_ref` | confirmed requirement id | only the Pattern J exception: operator-natured content marked `end-user` because a confirmed requirement demands self-hosting |

Settings item: `settings_groups[].items[]` = `{setting_id, label, audience, surface, provisioning?, requirement_ref?}`.
Service endpoint: top-level `service_endpoints[]` = `{endpoint_id, purpose, consumer_surface_refs, audience,
provisioning, requirement_ref?}`; endpoint `audience` means "who supplies this value", default `operator`.

## Task graph

```
T-M4-01 defensive-patterns (Pattern I/J) ──┬─> T-M4-02 node-spec template ──┐
                                           └─> T-M4-06 product-verify ──────┤
T-M4-03 settings + topology spec ──┬─> T-M4-04 program handoff ─────────────┼─> T-M4-08 pin function
                                   └─> T-M4-05 closure QA ──────────────────┘
T-M4-07 check_artifacts characterization test (independent)
```

---

## T-M4-01 — Pattern I (Specification Gap Escalation) and Pattern J (Audience Isolation)

Requirements: R-M4-01, R-M4-02. Design unit U2. `implements: data:unspecifiedDecisionGap`.
`requires: data:experienceDesignArtifacts`.

**Behaviour.** `MS/knowledge/defensive-patterns.md` gains, after Pattern H and a `---` separator, two sections,
each preceded by an explicit anchor line so the short anchors resolve:

```
<a id="pattern-i"></a>
## Pattern I: Specification Gap Escalation
...
<a id="pattern-j"></a>
## Pattern J: Audience Isolation
```

Both use the existing four-part layout with the exact labels `**Trigger condition**:`, `**Protocol**:`,
`**Key principles**:`, `**Example**:`. Patterns A–H are byte-identical afterwards.

- Pattern I states the trigger (implementation/UI node needs a user-visible decision — screen, setting, entry
  point, copy promise, permission request, default value — covered by neither `source_inputs`, the node-spec's
  `## User-visible decisions`, nor upstream design artifacts), the five-step protocol from design U2 (do not
  implement and no placeholder; append the five-key entry above; finish and evidence the covered remainder;
  the non-empty `contract_gaps` failing `check_artifacts.py` is the intended outcome and must not be dodged by
  emptying the field or relabelling as `known_gaps`; routing via the existing diagnosis path — the node whose
  `exit_artifacts` contains `suggested_owner_artifact` is the `suspected_root_node`; no user questions inside
  `/run`), the key principles, and the service-address-input example carrying the JSON entry with
  `suggested_owner_artifact` = `.allforai/app-design/spec/permissions-notifications-settings-spec.json`.
  The "upstream design artifacts" are named by the M1 path contract (`data:experienceDesignArtifacts`); use the
  canonical game path `.allforai/game-design/game-design-doc.json`.
- Pattern J states: exactly one audience per item (`end-user`, `operator` = deploying party, `developer`);
  only `end-user` items on end-user surfaces; the operator/developer list (service endpoints, access
  credentials, vendor keys, model selection, feature flags, environment names) provisioned via `build-time`,
  `remote-config` or `deploy-env`; the single self-hosted exception requiring `requirement_ref`; unlabelled
  audience → Pattern I, never guess; the three-row example table from design U2.

**Test intent.** No unit test exists for this prose. The acceptance pins every literal downstream tasks and
T-M4-08 depend on, proves both new sections carry all four layout labels (counted in the text after the
Pattern I heading, so A–H cannot satisfy it), rejects a project name, and runs the generalization validator.
All pinned literals are absent today, so the command fails before the task.

**Acceptance.**

```bash
F=claude/meta-skill/knowledge/defensive-patterns.md; for t in '<a id="pattern-i"></a>' '## Pattern I: Specification Gap Escalation' '<a id="pattern-j"></a>' '## Pattern J: Audience Isolation' unspecified_user_visible_decision needed_decision blocking_intent_ids suggested_owner_artifact suspected_root_node requirement_ref '`end-user`' '`operator`' '`developer`' build-time remote-config deploy-env '.allforai/app-design/spec/permissions-notifications-settings-spec.json'; do grep -qF -- "$t" "$F" || { echo "missing: $t"; exit 1; }; done && ! grep -qi 'ink-scent' "$F" && python3 -c "t=open('claude/meta-skill/knowledge/defensive-patterns.md',encoding='utf-8').read(); assert t.count('## Pattern H:')==1 and t.index('## Pattern H:')<t.index('## Pattern I: Specification Gap Escalation')<t.index('## Pattern J: Audience Isolation'); tail=t.split('## Pattern I: Specification Gap Escalation')[1]; assert all(tail.count(s)>=2 for s in ('**Trigger condition**:','**Protocol**:','**Key principles**:','**Example**:')), 'four-part layout incomplete'" && python3 claude/meta-skill/scripts/orchestrator/validate_generalization_boundaries.py && python3 claude/meta-skill/scripts/orchestrator/validate_meta_contracts.py
```

Write set: `claude/meta-skill/knowledge/defensive-patterns.md`.

## T-M4-02 — node-spec template: `## User-visible decisions`, Pattern I/J anchors, `contract_gaps` repair target

Requirement: R-M4-05. Design unit U3. `requires: data:experienceDesignArtifacts`. Depends on T-M4-01 (the
anchors it cites must exist).

**Behaviour.** `MS/knowledge/node-spec-template.md` (bootstrap corpus; append-only) gains exactly the four
edits of design U3:
1. after the line-3 sentence, one sentence: nodes that implement a UI must not omit `User-visible decisions`;
2. in the Attention Contract `Repair targets` bullet, one appended sentence: implementation/UI nodes list
   `contract_gaps` as emittable, with `kind: "unspecified_user_visible_decision"` shaped per
   `defensive-patterns.md#pattern-i` (existing enumeration untouched);
3. inside `## Knowledge References`, a paragraph: UI-implementing nodes anchor
   `${CLAUDE_PLUGIN_ROOT}/knowledge/defensive-patterns.md#pattern-i` and `...#pattern-j`, each with two or three
   load-bearing sentences;
4. a new `## User-visible decisions` section between `## Guidance` and `## Exit Artifacts`: applicability
   (non-UI nodes write the single line `Not applicable — no end-user surface`); a table
   `Decision | Kind (screen/setting/entry/copy promise/permission/default) | Source artifact path | Audience`;
   source paths are project-relative upstream design artifact paths (apps: the M1 four); `Audience` copied from
   the settings spec; the table is a closed set — a decision outside it → Pattern I, a non-`end-user` item
   required on an end-user surface → Pattern J, both recorded in `contract_gaps`; bootstrap must not write a
   row it has no source path for.

No deterministic `validate_bootstrap.py` check is added (design A4).

**Test intent.** Greps pin the new literals (all absent today: `User-visible decisions`, `pattern-j`,
`contract_gaps` each count 0); a position check proves the section sits between Guidance and Exit Artifacts;
greps for the existing pinned literals plus `validate_meta_contracts.py` prove nothing was lost from the
bootstrap corpus.

**Acceptance.**

```bash
F=claude/meta-skill/knowledge/node-spec-template.md; for t in '## User-visible decisions' 'defensive-patterns.md#pattern-i' 'defensive-patterns.md#pattern-j' contract_gaps unspecified_user_visible_decision 'Not applicable — no end-user surface' 'Source artifact path' '## Attention Contract' 'Repair targets' '## Effect Verification' '## Quality Acceptance' 'Bootstrap should spend context once' 'execute in pull mode'; do grep -qF -- "$t" "$F" || { echo "missing: $t"; exit 1; }; done && python3 -c "t=open('claude/meta-skill/knowledge/node-spec-template.md',encoding='utf-8').read(); assert t.index('\n## Guidance')<t.index('\n## User-visible decisions')<t.index('\n## Exit Artifacts'); assert t.count('\n## User-visible decisions')==1" && python3 claude/meta-skill/scripts/orchestrator/validate_meta_contracts.py && python3 claude/meta-skill/scripts/orchestrator/validate_generalization_boundaries.py
```

Write set: `claude/meta-skill/knowledge/node-spec-template.md`.

## T-M4-03 — settings spec and topology spec carry `audience` / `provisioning`

Requirement: R-M4-03. Design unit U4. `implements: data:settingsAudience`.

**Behaviour.** Both files keep frontmatter and the Invocation Contract JSON block untouched.

- `MS/skills/app-design/20-spec/permissions-notifications-settings-spec/SKILL.md`:
  Output Contract defines `settings_groups[].items[]` with the four-field table above and cites
  `knowledge/defensive-patterns.md` Pattern J; Automatic Validation rejects: missing `audience`; `audience`
  outside the three values; non-`end-user` item missing `provisioning` or with a value outside the three;
  non-`end-user` item whose `surface` is an end-user surface (allowed: `"none"` or `surface_type` in
  `admin_console`, `operator_console`, `cli`); operator-natured content marked `end-user` without
  `requirement_ref`. Repair routing: undecidable audience → do not guess, `needs_revision`, route to
  job-story-spec / product concept. Completion Conditions: the `FAILED_VALIDATION` sentence also covers "any
  settings item lacks an audience".
- `MS/skills/app-design/20-spec/app-surface-topology-spec/SKILL.md`: Output Contract adds top-level
  `service_endpoints[]` (field always present; pure-client apps write `[]`) with the endpoint shape above;
  Automatic Validation: every surface with a non-empty `backend_dependency` has an endpoint entry; endpoint
  missing `audience`/`provisioning` is rejected; `audience: "end-user"` endpoint requires `requirement_ref`.

**Test intent.** Greps pin the field names and every legal enum value in the file that defines them (settings
spec: all absent today; topology: `service_endpoints`, `provisioning`, `deploy-env`, `requirement_ref` absent).
`validate_skills.py` over the whole tree proves the two SKILL.md files are still structurally valid skills.

**Acceptance.**

```bash
S=claude/meta-skill/skills/app-design/20-spec/permissions-notifications-settings-spec/SKILL.md; T=claude/meta-skill/skills/app-design/20-spec/app-surface-topology-spec/SKILL.md; for t in 'settings_groups[].items[]' setting_id audience end-user operator developer provisioning build-time remote-config deploy-env requirement_ref admin_console operator_console 'Pattern J'; do grep -qF -- "$t" "$S" || { echo "settings missing: $t"; exit 1; }; done && for t in 'service_endpoints' endpoint_id consumer_surface_refs audience provisioning build-time remote-config deploy-env requirement_ref; do grep -qF -- "$t" "$T" || { echo "topology missing: $t"; exit 1; }; done && python3 claude/meta-skill/scripts/orchestrator/validate_skills.py claude/meta-skill/skills && python3 claude/meta-skill/scripts/orchestrator/validate_generalization_boundaries.py
```

Write set: the two SKILL.md files above.

## T-M4-04 — program handoff carries `settings_items[]` and `service_endpoints[]`

Requirement: R-M4-04 (handoff half). Design unit U5. Depends on T-M4-03 (copies its field names verbatim).

**Behaviour.** `MS/skills/app-design/30-generate/program-handoff-generation/SKILL.md`: Output Contract — the
handoff JSON (`.allforai/app-design/handoff/program-development-node-handoff.json`) carries top-level
`settings_items[]` (verbatim `setting_id`, `audience`, `provisioning`, `surface`, `requirement_ref` from
`settings_groups[].items[]`) and `service_endpoints[]` (verbatim from topology); implementation entries
reference those ids in `source_refs`; audience is never rewritten or guessed at handoff; the existing
required-field sentence for implementation entries is unchanged (design A5). Automatic Validation: every
settings item appears in `settings_items[]`; a non-`end-user` item is never assigned as UI work to an entry
on an end-user surface — only as configuration-injection work naming its `provisioning`. Repair routing:
missing `audience`/`provisioning` → permissions-notifications-settings-spec or app-surface-topology-spec.

**Test intent.** Greps pin the carried field names (all absent today) and `validate_skills.py` proves the skill
still validates.

**Acceptance.**

```bash
F=claude/meta-skill/skills/app-design/30-generate/program-handoff-generation/SKILL.md; for t in 'settings_items' 'service_endpoints' setting_id audience provisioning requirement_ref end-user; do grep -qF -- "$t" "$F" || { echo "missing: $t"; exit 1; }; done && python3 claude/meta-skill/scripts/orchestrator/validate_skills.py claude/meta-skill/skills && python3 claude/meta-skill/scripts/orchestrator/validate_generalization_boundaries.py
```

Write set: `claude/meta-skill/skills/app-design/30-generate/program-handoff-generation/SKILL.md`.

## T-M4-05 — closure QA: settings audience closure checks

Requirement: R-M4-04 (QA half). Design unit U5. Depends on T-M4-03.

**Behaviour.** `MS/skills/app-design/40-qa/app-design-closure-qa/SKILL.md`: Automatic Validation gains a
"Settings audience closure" paragraph with two checks; a hit is written to the existing `missing_contracts[]`
and sets `state: "needs_revision"` (no new state value):
- `missing_audience` — any settings item or service endpoint in the settings spec or the handoff lacks `audience`;
- `non_end_user_item_in_screen_spec` — any `audience != "end-user"` item appears in
  `screen-requirements-spec.json` or the UI handoff's end-user surfaces (exception items pass on `requirement_ref`).
Each record is `{code, item_id, artifact, detail}`. Input Contract: one added sentence — the
permissions/settings spec is required reading when settings items exist (the Optional sentence stays where it
is). Repair routing: both codes route to permissions-notifications-settings-spec; the screen-side reference is
removed by the skill that owns screen-requirements.

**Test intent.** The two codes and the record key `item_id` are absent today; greps pin them together with the
existing `missing_contracts` / `needs_revision` they must reuse. `validate_skills.py` proves validity.

**Acceptance.**

```bash
F=claude/meta-skill/skills/app-design/40-qa/app-design-closure-qa/SKILL.md; for t in 'Settings audience closure' missing_audience non_end_user_item_in_screen_spec missing_contracts needs_revision item_id requirement_ref 'screen-requirements-spec.json'; do grep -qF -- "$t" "$F" || { echo "missing: $t"; exit 1; }; done && python3 claude/meta-skill/scripts/orchestrator/validate_skills.py claude/meta-skill/skills && python3 claude/meta-skill/scripts/orchestrator/validate_generalization_boundaries.py
```

Write set: `claude/meta-skill/skills/app-design/40-qa/app-design-closure-qa/SKILL.md`.

## T-M4-06 — product-verify: Audience Leak Check

Requirement: R-M4-06. Design unit U6. Depends on T-M4-01 (cites `#pattern-j`).

**Behaviour.** `MS/knowledge/capabilities/product-verify.md` (codex side follows via directory symlink):
- new `### Audience Leak Check` after `### Multi-Client Feature Parity Verification` and before
  `## Rules (Must Preserve)`: applies to modules with an end-user surface (non-UI follows existing skip
  conditions); dynamically walk every settings/config/account/debug surface reachable by the end-user role,
  including hidden entries, long-press and developer menus; compare each input/toggle with the settings spec's
  `audience`; the criterion is `defensive-patterns.md#pattern-j`. Classification: spec silent on audience (or item
  absent from spec) → `contract_gaps`; spec says non-`end-user` and the build still shows it → `code_gaps`.
  Both entries share one shape `{kind: "audience_leak", where, item, observed_audience, spec_ref, evidence}`
  (`evidence` = screenshot path). Exception items with `requirement_ref` are not leaks, but the referenced
  requirement must be checked to exist. One sentence: the experience-quality critique's `audience_leak` dimension
  uses this section's criterion (M3 points here; M4 edits no M3 file).
- `## Rules (Must Preserve)` gains rule 6 `**Audience isolation**: …`; rules 1–5 unchanged and unreordered.
- `## Knowledge References → Phase-Specific` gains one line for `defensive-patterns.md#pattern-j`.

**Test intent.** Greps pin the heading, entry kind and keys (all absent today); a position check proves
placement; a regex proves rule 6 exists in numbered form; rule 5's text is grepped to prove it survived.

**Acceptance.**

```bash
F=claude/meta-skill/knowledge/capabilities/product-verify.md; for t in '### Audience Leak Check' audience_leak 'defensive-patterns.md#pattern-j' observed_audience spec_ref contract_gaps code_gaps requirement_ref '5. **Screenshot-backed UI acceptance**'; do grep -qF -- "$t" "$F" || { echo "missing: $t"; exit 1; }; done && grep -qE '^6\. \*\*Audience isolation\*\*' "$F" && python3 -c "t=open('claude/meta-skill/knowledge/capabilities/product-verify.md',encoding='utf-8').read(); assert t.index('### Multi-Client Feature Parity Verification')<t.index('### Audience Leak Check')<t.index('## Rules (Must Preserve)')" && python3 claude/meta-skill/scripts/orchestrator/validate_meta_contracts.py && python3 claude/meta-skill/scripts/orchestrator/validate_generalization_boundaries.py
```

Write set: `claude/meta-skill/knowledge/capabilities/product-verify.md`.

## T-M4-07 — characterization test: an `unspecified_user_visible_decision` gap keeps the artifact incomplete

Requirement: R-M4-07 (unit case). Design unit U7. No dependencies. `check_artifacts.py` is NOT modified.

**Behaviour / interface.** `MS/tests/unit/test_check_artifacts_measurement.py` gains, appended at the end with
no change to existing tests or imports, one parametrized function using the file's own helpers
(`project`, `write`, `measure`, `artifact`, `REPORT`):

```python
@pytest.mark.parametrize("flags", [{}, {"allowed_by_production_policy": True}])
def test_an_unspecified_user_visible_decision_gap_keeps_the_artifact_incomplete(tmp_path, flags): ...
```

**Test intent.** With a `status: "completed"` report whose `contract_gaps` holds the five-key
`data:unspecifiedDecisionGap` entry (plus `flags`): `measure()["all_exist"] is False` and
`artifacts[0]["status_error"]["field"] == "contract_gaps"` — for both parameter values, which proves the
allow-flag cannot wave this gap through (the hard-fail branch in `_production_gap_error` returns before
`ALLOWED_PRODUCTION_GAP_FLAGS` is consulted). Control: the same report with `contract_gaps: []` has no
`status_error` (do not assert `all_exist` there — freshness also feeds it in this fixture). This is a
characterization test of existing behaviour and is green on arrival; its job is regression protection. The
executor reports a mutation probe as the red evidence: in a scratch copy (never the repo file), removing
`contract_gaps` from the hard-fail set makes the test fail.

**Acceptance.** Explicit node id (pytest exits 4 if it does not exist), then the whole file (52 items expected:
baseline 50 + 2).

```bash
python3 -m pytest -q "claude/meta-skill/tests/unit/test_check_artifacts_measurement.py::test_an_unspecified_user_visible_decision_gap_keeps_the_artifact_incomplete" && python3 -m pytest -q claude/meta-skill/tests/unit/test_check_artifacts_measurement.py claude/meta-skill/tests/unit/test_check_artifacts.py
```

Write set: `claude/meta-skill/tests/unit/test_check_artifacts_measurement.py`.

## T-M4-08 — `validate_spec_gap_discipline_contract` pins the whole discipline

Requirement: R-M4-07 (pin). Design unit U1. Depends on T-M4-01..06 (see "Deviation" above — registering the
function earlier would turn the shared validator red for other modules).

**Interface.** In `MS/scripts/orchestrator/validate_meta_contracts.py` (hot file — exactly two edits, nothing
else changes):

```python
def validate_spec_gap_discipline_contract(errors: list[str]) -> None: ...
```

placed after `validate_public_entrypoint_surface` and before `main()`, and one registration line at the end of
`main()`'s call sequence, after `validate_public_entrypoint_surface(errors)`.

**Behaviour.** Modelled on `validate_execution_repair_loop_contract`: for each file in the pin table of design
U1 (seven files, literals verbatim from that table), read text and append
`"<file>: missing spec-gap discipline term <term>"` for each absent literal; a missing file appends
`"<file>: missing"` and skips its terms without raising. The function resolves paths from the module global
`ROOT` at call time (no paths captured at import), so it can be probed against another root. No imports added.

**Test intent.** There is no unit-test file for this validator and none is created (design). The acceptance
proves three things: (green) the real tree passes all three validators; (red, file level) against an empty root
the function reports exactly seven `: missing` errors — one per pinned file; (red, term level) against a copy of
the tree with the `## Pattern J: Audience Isolation` heading altered, it reports that exact term with the agreed
message. Greps on the validator source pin registration and the presence of pins for every downstream landing
spot so the table cannot be half-implemented. The executor pastes both the probe output and the green run in
the task report.

**Acceptance.**

```bash
V=claude/meta-skill/scripts/orchestrator/validate_meta_contracts.py; [ "$(grep -c 'validate_spec_gap_discipline_contract(errors' "$V")" -ge 2 ] && for t in 'defensive-patterns.md#pattern-i' '## Pattern I: Specification Gap Escalation' '## User-visible decisions' 'settings_items' 'service_endpoints' 'non_end_user_item_in_screen_spec' 'missing_audience' '### Audience Leak Check' 'defensive-patterns.md#pattern-j' 'missing spec-gap discipline term'; do grep -qF -- "$t" "$V" || { echo "validator lacks pin: $t"; exit 1; }; done && python3 -c "
import sys,tempfile,pathlib,shutil
sys.path.insert(0,'claude/meta-skill/scripts/orchestrator')
import validate_meta_contracts as v
src=pathlib.Path('claude/meta-skill'); tmp=pathlib.Path(tempfile.mkdtemp())
v.ROOT=tmp; e=[]; v.validate_spec_gap_discipline_contract(e)
assert len([x for x in e if x.endswith(': missing')])==7, e
shutil.copytree(src/'knowledge', tmp/'knowledge'); shutil.copytree(src/'skills/app-design', tmp/'skills/app-design')
e=[]; v.validate_spec_gap_discipline_contract(e); assert e==[], e
p=tmp/'knowledge/defensive-patterns.md'; p.write_text(p.read_text(encoding='utf-8').replace('## Pattern J: Audience Isolation','## Pattern J'),encoding='utf-8')
e=[]; v.validate_spec_gap_discipline_contract(e)
assert any('missing spec-gap discipline term' in x and 'Pattern J: Audience Isolation' in x for x in e), e
" && python3 claude/meta-skill/scripts/orchestrator/validate_meta_contracts.py && python3 claude/meta-skill/scripts/orchestrator/validate_skills.py claude/meta-skill/skills && python3 claude/meta-skill/scripts/orchestrator/validate_generalization_boundaries.py
```

Write set: `claude/meta-skill/scripts/orchestrator/validate_meta_contracts.py`.

---

## Requirement coverage

| Requirement | Task(s) |
|---|---|
| R-M4-01 | T-M4-01 |
| R-M4-02 | T-M4-01 |
| R-M4-03 | T-M4-03 |
| R-M4-04 | T-M4-04, T-M4-05 |
| R-M4-05 | T-M4-02 |
| R-M4-06 | T-M4-06 |
| R-M4-07 | T-M4-07 (unit case), T-M4-08 (pin function + `validate_skills.py` still green) |

## Reality-gate pass

No task is reality-gated. Every acceptance is a grep/validator/pytest command runnable headless; M4 adds no
dialogue behaviour that needs a live host session.

## Module-level acceptance (after all eight tasks)

```bash
python3 claude/meta-skill/scripts/orchestrator/validate_meta_contracts.py
python3 claude/meta-skill/scripts/orchestrator/validate_skills.py claude/meta-skill/skills
python3 claude/meta-skill/scripts/orchestrator/validate_generalization_boundaries.py
python3 -m pytest -q claude/meta-skill/tests/unit/test_check_artifacts_measurement.py
python3 -m pytest -q claude/meta-skill/tests/unit/test_check_artifacts.py claude/meta-skill/tests/unit/test_validate_skills.py
```

Never run `pytest pi/meta-skill` or `pytest codex/meta-skill` as directories, and never use the full
`claude/meta-skill/tests/unit` directory as an M4 acceptance (four known pre-existing failures; M5 owns that run).
