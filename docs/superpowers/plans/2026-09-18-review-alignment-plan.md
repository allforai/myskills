# M6 review-alignment — plan

Design: `docs/superpowers/specs/2026-09-18-review-alignment-design.md` (requirements R-M6-01..05, units U1..U4).
Branch `product-experience-overhaul`. All commands run with cwd = repo root.

This module exposes no interface. It consumes four: `data:experienceLensVocabulary`, `data:experienceReviewDoc`
(M3), `data:experienceDirectionIntent` (M2), `data:settingsAudience` (M4). Apart from one new contract test the
module is prose only; behaviour proof of the prose clauses belongs to M5's thought tests (E7, E8), not here.
No task is reality-gated.

## Rules that apply to every task

- **Twin double-write.** `claude/superstorm/skills/product-review/SKILL.md` <-> `codex/cross-exam-skill/product-review.md`
  and `claude/superstorm/skills/cross-exam/SKILL.md` <-> `codex/cross-exam-skill/SKILL.md` are hand-maintained twins;
  both sides change in the same task. New text is verbatim identical on both sides. The product-review twins differ
  today in exactly 12 `diff` lines (`diff A B | grep -c '^[<>]'` = 12: frontmatter, invocation note, the
  `Not cross-exam` sentence, two `/cross-exam` -> `cross-exam` substitutions). That count must still be 12 after every
  task, so new text must not name the cross-exam slash command (write "cross-exam report", never `/cross-exam`).
- `claude/superstorm/knowledge/cross-exam/lenses.md` and `codex/cross-exam-skill/lenses.md` stay byte-identical.
- **R-M6-05 guards (never touch):** `rule_consistency.py`, `rule-consistency.md`, `prompts/rules.md` (either side),
  `schemas.md`, `render_report.py`, `ledger_store.py`, `check_skill_refs.py`, `skills/superstorm/SKILL.md`,
  `pi/cross-exam/`, versions/manifests. No field renamed (`journey_candidates` etc.), no new ledger field, no new
  `$ROOT/...` reference. Each acceptance command re-runs the relevant guard suites
  (baselines: `claude/superstorm/scripts` 255 passed, `codex/cross-exam-skill/scripts` 172 passed,
  `pi/cross-exam/test_contract.py` 7 passed, `check_skill_refs.py` OK) — always as separate pytest invocations.
- Exact wording to insert is in the design's U1–U4 blocks; the literals pinned in each acceptance command are taken
  from those blocks and are absent from the files today.

## Order

`T-M6-01 -> T-M6-02 -> T-M6-04` (same two product-review files, ordered so each diff lands on a known base).
`T-M6-03` and `T-M6-05` are independent of everything else in this module.

---

## T-M6-01 — Lens-name parity: contract test + mapping paragraph (R-M6-01, U1)

**Requires:** `data:experienceLensVocabulary` (M3's `experience-quality-critique/SKILL.md` must exist — it does not
on the design base commit).

**Becomes true.** Both product-review twins carry, after the Lenses table and before `## 0. Intake`, the U1 paragraph
mapping 引导/过程反馈/下一步/状态一致/回来理由 to `onboarding`/`process_feedback`/`next_step`/`state_consistency`/
`return_reason`, and naming `mainline`, `direction_fidelity`, `audience_leak` as outside the five. All five
`<中文名> = `<identifier>`` pairs sit on one line (the test compares the line containing `` `onboarding` ``).
The sentence "nothing here requires those files to be installed" is untouched.

**Test intent (write first, see it fail).** New `shared/scripts/orchestrator/test_experience_lens_parity.py`,
function-style pytest, `ROOT = Path(__file__).resolve().parents[3]`, no fixtures. Contract constants:

```python
LENSES = {"onboarding": "引导", "process_feedback": "过程反馈", "next_step": "下一步",
          "state_consistency": "状态一致", "return_reason": "回来理由"}
GATE   = ROOT / "claude/meta-skill/skills/app-design/40-qa/experience-quality-critique/SKILL.md"
REVIEWS = [ROOT / "claude/superstorm/skills/product-review/SKILL.md",
           ROOT / "codex/cross-exam-skill/product-review.md"]
```

- `test_gate_and_both_reviews_name_every_lens` (parametrized over `[GATE, *REVIEWS]`): file exists and contains each
  identifier in backticks. Missing GATE is a failure, never a skip — a renamed M3 dimension must break this test.
  GATE's formatting is not asserted beyond that.
- `test_reviews_pair_each_identifier_with_its_lens` (over REVIEWS): substring ``f"{zh} = `{ident}`"`` present for all
  five — proves names are paired correctly, not merely present.
- `test_review_twins_carry_the_same_mapping_line`: the line containing `` `onboarding` `` is identical in both twins.

Red state: fails today because neither review names any identifier.

**Acceptance.**
```bash
python3 -m pytest -q shared/scripts/orchestrator/test_experience_lens_parity.py && [ "$(diff claude/superstorm/skills/product-review/SKILL.md codex/cross-exam-skill/product-review.md | grep -c '^[<>]')" = "12" ] && python3 claude/superstorm/scripts/check_skill_refs.py
```
(pytest exits non-zero on a missing file or zero collected tests.)

**Write set:** `shared/scripts/orchestrator/test_experience_lens_parity.py`,
`claude/superstorm/skills/product-review/SKILL.md`, `codex/cross-exam-skill/product-review.md`.

---

## T-M6-02 — product-review adopts the runtime experience review as prior evidence (R-M6-02, U2)

**Requires:** `data:experienceReviewDoc`. **Depends on:** T-M6-01.

**Becomes true** (both twins, four places, wording per design U2):
1. Invariant `No .allforai/`: tail sentence becomes "`docs/cross-exam/` and `docs/experience-review/` are readable
   input." The ban sentences ("Do not read or write that tree. Do not call meta-skill capabilities.") unchanged.
2. A new paragraph headed `Prior evidence — runtime experience review.` follows the existing `Prior evidence`
   paragraph in §1 (which is not rewritten). It states: read `docs/experience-review/runtime.md` if present, never
   `design.md`; its per-lens observations fill the matching `商业级` cells as
   `有|缺 <observation>（runtime review <date>）` without re-checking; uncovered lenses/jobs are observed as usual; open
   must-fix items blocking in-scope jobs go on the `Prior evidence` line by their own id and may be a `depends_on`;
   known must-fix items take no `R` number; staleness discipline identical to the cross-exam report (record date,
   reviewed commit, observed diff; mark stale; do not re-judge; never override that verdict); its evidence limits fold
   into `Evidence limits`; absent -> that source is `none`.
3. §2 `depends_on` definition gains `experience-review must-fix ids`; Self-check line becomes
   `the item is not a cross-exam gap or an experience-review must-fix restated`.
4. §3 template `## Prior evidence` has two source lines, the second being
   `docs/experience-review/runtime.md (<review date>, <reviewed commit>) — <must-fix id> (next_step) blocks JOB1; lens cells adopted: JOB1 引导, 过程反馈 | none`.
   The original `Absent → write \`Prior evidence: none\`` sentence stays.

**Test intent.** No executable behaviour exists; the check pins the literals that carry each of the four clauses in
both twins, asserts the `.allforai/` ban sentence survived, that the old self-check wording is gone, and that the
twins gained no new divergence. Behavioural proof: M5 thought tests.

**Acceptance.**
```bash
for f in claude/superstorm/skills/product-review/SKILL.md codex/cross-exam-skill/product-review.md; do grep -qF '`docs/cross-exam/` and `docs/experience-review/` are readable input' "$f" && grep -qF 'Do not read or write that tree' "$f" && grep -qF 'Prior evidence — runtime experience review' "$f" && grep -qF 'docs/experience-review/runtime.md (<review date>, <reviewed commit>)' "$f" && grep -qF 'lens cells adopted' "$f" && grep -qF 'experience-review must-fix ids' "$f" && grep -qF 'not a cross-exam gap or an experience-review must-fix restated' "$f" && ! grep -qF 'not a cross-exam gap restated' "$f" && grep -qF 'Prior evidence: none' "$f" || exit 1; done && [ "$(diff claude/superstorm/skills/product-review/SKILL.md codex/cross-exam-skill/product-review.md | grep -c '^[<>]')" = "12" ] && python3 -m pytest -q shared/scripts/orchestrator/test_experience_lens_parity.py && python3 claude/superstorm/scripts/check_skill_refs.py
```

**Write set:** `claude/superstorm/skills/product-review/SKILL.md`, `codex/cross-exam-skill/product-review.md`.

---

## T-M6-03 — cross-exam §1b step 1: experience-baseline candidate sources (R-M6-03, U3)

**Requires:** `data:experienceDirectionIntent`. **Depends on:** none.

**Becomes true** (both cross-exam SKILL twins, identical text). In §1b step 1, after the existing parenthesis ending
`task-inventory.json` 存在也读，它只是可选数据源）。 and before 每条候选写成三元组草稿, the design's U3 paragraph is inserted:
two more optional sources of equal standing (present -> read, absent -> not a gap):
`.allforai/product-concept/product-concept.json` `requirements[]` entries with `topic == "experience-direction"` and
`status == "confirmed"` (latest `revision` per id; top-level `who`/`circumstance` used directly, otherwise drafted from
`goal`/`scope`; `progress` from `acceptance`), and `.allforai/app-design/concept/job-story-spec.json`
(`audience_ref` -> who, `situation`/`trigger`/`frequency` -> circumstance, `desired_outcome` -> progress). Candidates
from `auto_decided: true` entries end with “（此方向由模型受托选定）” when shown to the user.
The following "不另派 agent 读代码…" sentence, the census-failure branch and steps 2–4 are untouched. The note is text
inside the candidate sentence — no new field; `schemas.md`, ledger schema, renderer untouched. `experience_proposals[]`
is not read.

**Test intent.** Pins the two source paths, the two filter predicates, the delegation note and the surviving
`task-inventory` sentence in both twins; asserts the lines carrying the new literals are identical across the twins;
then runs both script suites (which include `test_rule_consistency.py` byte comparison), the ref checker and the Pi
contract test as R-M6-05 guards.

**Acceptance.**
```bash
A=claude/superstorm/skills/cross-exam/SKILL.md; B=codex/cross-exam-skill/SKILL.md; for f in "$A" "$B"; do grep -qF 'topic == "experience-direction"' "$f" && grep -qF 'status == "confirmed"' "$f" && grep -qF '.allforai/app-design/concept/job-story-spec.json' "$f" && grep -qF 'auto_decided: true' "$f" && grep -qF '此方向由模型受托选定' "$f" && grep -qF 'task-inventory.json` 存在也读，它只是可选数据源' "$f" || exit 1; done && [ "$(grep -F -e 'experience-direction' -e 'job-story-spec' -e '受托选定' "$A")" = "$(grep -F -e 'experience-direction' -e 'job-story-spec' -e '受托选定' "$B")" ] && python3 -m pytest -q claude/superstorm/scripts && python3 -m pytest -q codex/cross-exam-skill/scripts && python3 claude/superstorm/scripts/check_skill_refs.py && python3 -m pytest -q pi/cross-exam/test_contract.py
```

**Write set:** `claude/superstorm/skills/cross-exam/SKILL.md`, `codex/cross-exam-skill/SKILL.md`.

---

## T-M6-04 — product-review question 4: audience-leak observation point (R-M6-04, U4 part 1)

**Requires:** `data:settingsAudience` (vocabulary only: `end-user` / `operator` / `developer`; no `.allforai/` read).
**Depends on:** T-M6-02.

**Becomes true** (both twins). The Lenses table gains, directly after the `4 商业级够不够` row, the row
`| 4 商业级够不够 · 受众泄漏 | … | meta-skill defensive-patterns Pattern J |` with the design's U4 cell text (one audience
per setting; a non-`end-user` item reachable from the end-user surface is an observation filed under `不够商业级`;
self-hosting products are the exception). The Self-check `claim: 不够商业级` example list gains
`最终用户设置页里要填服务地址或访问凭证`. It is an observation point, not a sixth lens: §1 Completion's five cells and the
template `商业级` row are unchanged.

**Test intent.** Pins the row label, the three-value audience vocabulary, the lineage cell and the self-check example
in both twins; asserts the new row is a table row placed under question 4; re-runs the parity test (the mapping line
from T-M6-01 must survive the table edit) and the twin-divergence count.

**Acceptance.**
```bash
for f in claude/superstorm/skills/product-review/SKILL.md codex/cross-exam-skill/product-review.md; do grep -F '受众泄漏' "$f" | grep -q '^| 4 商业级够不够 · 受众泄漏 |' && grep -F '受众泄漏' "$f" | grep -qF '`end-user` / `operator` / `developer`' && grep -F '受众泄漏' "$f" | grep -qF 'defensive-patterns Pattern J' && grep -F 'claim: 不够商业级' "$f" | grep -qF '最终用户设置页里要填服务地址或访问凭证' || exit 1; done && [ "$(diff claude/superstorm/skills/product-review/SKILL.md codex/cross-exam-skill/product-review.md | grep -c '^[<>]')" = "12" ] && python3 -m pytest -q shared/scripts/orchestrator/test_experience_lens_parity.py && python3 claude/superstorm/scripts/check_skill_refs.py
```

**Write set:** `claude/superstorm/skills/product-review/SKILL.md`, `codex/cross-exam-skill/product-review.md`.

---

## T-M6-05 — cross-exam lenses: audience leak under 细节质量 (R-M6-04, U4 part 2)

**Requires:** `data:settingsAudience`. **Depends on:** none.

**Becomes true.** In both lenses files the `细节质量` row's 泄漏点示例 cell ends with the design's appended clause
(`；最终用户界面里出现部署方/开发者才该碰的配置（服务地址、访问凭证、模型、环境）——规格给设置项标了受众就对受众查，没标就把"这一项是给谁填的"做成问题牌`).
Only that cell changes; the codex twin lives at `codex/cross-exam-skill/lenses.md` (flat layout) and the two files
remain byte-identical.

**Test intent.** The clause must be on the `| 细节质量 ` row (not a new row or prose elsewhere), `cmp` proves the twins
are still byte-identical, and the guard suites prove no existing contract (incl. `pi/cross-exam/test_contract.py`,
which asserts the codex lenses file) moved.

**Acceptance.**
```bash
A=claude/superstorm/knowledge/cross-exam/lenses.md; B=codex/cross-exam-skill/lenses.md; grep -F '这一项是给谁填的' "$A" | grep -q '^| 细节质量 ' && grep -F '这一项是给谁填的' "$A" | grep -qF '部署方/开发者才该碰的配置（服务地址、访问凭证、模型、环境）' && [ "$(grep -c '^| 细节质量 ' "$A")" = "1" ] && cmp "$A" "$B" && python3 -m pytest -q claude/superstorm/scripts && python3 -m pytest -q codex/cross-exam-skill/scripts && python3 claude/superstorm/scripts/check_skill_refs.py && python3 -m pytest -q pi/cross-exam/test_contract.py
```

**Write set:** `claude/superstorm/knowledge/cross-exam/lenses.md`, `codex/cross-exam-skill/lenses.md`.

---

## Requirement coverage

| Requirement | Task |
|---|---|
| R-M6-01 | T-M6-01 |
| R-M6-02 | T-M6-02 |
| R-M6-03 | T-M6-03 |
| R-M6-04 | T-M6-04, T-M6-05 |
| R-M6-05 | guard suites inside every acceptance command; "never touch" list above |
