# Clientless Role — Producer Side Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A role that product-concept decides has no client reaches the experience-map producer as a decision it can read — a named field, carried through the concept baseline and role-profiles — so the receiving-side rule landed on 2026-09-22 fires on the real pipeline, not only when a subject is hand-fed `product-concept.json`.

**Architecture:** One field, `surface`, is added to a role in three places that must agree: product-concept's role contract (where the mode is decided), the fixed `concept-baseline.json` role schema every phase auto-loads (which today forces `app` + `client_type` on every role), and product-analysis's `role-profiles.json` (which the map, journey and experience-map producers read). The experience-map hard-constraint row is then re-keyed from "declares no `clients[]`" to "`surface.mode` is not `screen`", so absence of a key stops meaning anything. Each step is test-gated by an isolated thought test on the artifact the real node actually receives.

**Tech Stack:** Markdown knowledge files, JSON examples, Python 3 + pytest for the validators.

**Spec:** `docs/adr/0010-seams-are-guarded-from-the-receiving-side.md` criterion 2 ("What crosses is checkable … Where only prose can cross, the receiver treats it as a claim"). Background: `docs/validation/no-client-role-downstream-thought-tests.md` §"What is still open" — the three missing producer-side pieces this plan supplies. Upstream rule: `claude/meta-skill/knowledge/capabilities/product-concept.md` Sub-Phase 5 step 5 (commit `f355fb47`).

## Global Constraints

- Work directly on `main`, one commit per task. No worktree, no `git stash` / `checkout` / `reset` / `restore` / `clean`.
- Commit with an explicit pathspec (`git commit -F - -- <paths>`). Never `git add` a tracked file. Never `--no-verify`. The pre-commit hook takes ~40 s and tests the whole tree; another session may hold uncommitted edits — never touch them.
- End every commit message with exactly `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>`.
- No CI. Nothing under `.github/`. Do not push.
- Skills state acceptance criteria, not procedures (owner's rule).
- Thought-test subjects: `sonnet`, read-only, given ONLY a packet of files copied OUTSIDE the repository (`mktemp -d` under `$TMPDIR`), absolute packet paths, "read both in full and NOTHING else — no listing, searching, other files or shell", no repo path, no mention of clients/consoles/surfaces/what is being tested. Record every subject output verbatim.
- Field, exactly (a role object, all three artifacts):
  ```json
  "surface": {
    "mode": "screen | agent_interface | existing_tool | undecided",
    "basis": "<one sentence: what the mode rests on, quoted from the concept's evidence>",
    "open_question": "<present only when mode is undecided: the question left for the user>"
  }
  ```
  `mode: screen` is the only mode under which `clients[]` may be non-empty and the only one that gets screens. `agent_interface` and `existing_tool` declare no `clients[]`. `undecided` declares no `clients[]` and carries `open_question`. A role without `surface` is an upstream defect for every consumer, never a default.

## Facts established on 2026-09-22

- product-concept Sub-Phase 5 step 5 (`product-concept.md:142-151`) decides the mode in prose; the role contract (`:152-196`) has `clients[]`, `feature_parity`, `parity_exceptions[]` and no field for the mode or its ground. Sub-Phase 5's output is `role-profiles.json` + `vpc-per-role.json`; the concept's role list ends in `product-concept.json.roles[]`.
- `concept-baseline.json` (`cross-phase-protocols.md:58-68`) is "fixed", auto-loaded by every phase, and its role entry carries `app` and `client_type` — every role has a client there by construction. It is LLM-extracted from `product-concept.json` + `role-value-map.json` + `product-mechanisms.json` after Phase 1 (`:91-96`). Its Downstream Consumers row (`product-concept.md:474`) lists `experience-map` as a consumer.
- product-analysis (`product-analysis.md:96, :127-128`) produces `role-profiles.json` (`roles[]` with `permissions`, `audience_type` ∈ consumer|admin|operator|system) and `experience-map.json`. `shared/scripts/product-design/_common.py:198-213` loads `role-profiles.json` for the generation scripts. `experience-map-schema.md` is that producer's output schema.
- The receiving side (landed today): `experience-map-schema.md` Hard Constraints row "Roles without a client" keys off "declares no `clients[]` AND the concept records the ground"; validation check 4 exempts clientless roles; `non_screen_tasks[]` is in the schema; `capabilities/ui-design.md:62,69` aligned.
- `bootstrap-audits.md:112-140` Level 3 multi-client parity treats a role with only legacy `client_type` as single-client. No validator in `scripts/orchestrator/` parses `clients` or `client_type`.
- `gen_experience_map.py` (dead, unreferenced) mints a screen per (task, role) with a default app — left alone.

---

### Task 1: product-concept records the surface decision as a field

**Files:**
- Modify: `claude/meta-skill/knowledge/capabilities/product-concept.md` (Sub-Phase 5 step 6's field list; the example block; the Downstream Consumers table)

**Interfaces:**
- Produces: `product-concept.json.roles[].surface` exactly as in Global Constraints; a Downstream Consumers row granting `roles[].surface` to `product-analysis, experience-map, ui-design, product-verify`.

- [ ] **Step 1: Run the producer baseline in isolation (no file edited yet)**

Packet: copy `claude/meta-skill/knowledge/capabilities/product-concept.md` and `claude/meta-skill/knowledge/product-design-theory.md` into a fresh `$TMPDIR` directory. Dispatch one `sonnet` subject:

> You are an executor subagent running the `user-role-definition` node (Sub-Phase 5 of the product-concept capability). Unattended. Your method is defined by exactly two files; read both in full and read NOTHING else — do not list directories, do not search, do not open any other file, do not use a shell:
> - <packet>/product-concept.md
> - <packet>/product-design-theory.md
>
> Upstream summary (use only this):
> - 机会：连锁门店按店补货，店长凭经验报数，总部凭 Excel 汇总，供应商对账靠人工核；漏订与错发每月各十几起。
> - 用户原话（4 位店长、2 位总部采购）："我只想知道该订多少"、"对账单错了我们才发现"、"总部那边有自己的系统"。
> - 团队：3 人，其中 1 人兼做总部采购；总部已在用一套财务系统做付款与对账归档。
> - 运营事实：总部每天要核对约 400 张供应商对账单、处理十几起到货差异争议、月末出结算单、偶尔冻结异常供应商。量级上主要是核对与比对；争议裁定需要人看单据。
>
> Task: produce this product's role definition as the capability file requires — for each role its job, VPC, the producer-side closure check and the client declaration — in the exact JSON shape the file's role contract specifies. Return only the JSON and, after it, at most 8 lines of notes for the orchestrator.

- [ ] **Step 2: Judge the baseline**

FAIL if the operations/HQ role's JSON has no field that names its mode and ground (prose in the notes does not count — the field must be in the role object), or if it receives a `clients[]` entry with a desktop console without a named step someone must look at. Record prompt, output and verdict in `docs/validation/clientless-role-producer-side-thought-tests.md` (new file). The expected result is FAIL: the contract has no such field today. If it passes anyway, still proceed — the field is what makes the decision checkable downstream (ADR-0010 criterion 2), and say so in the record.

- [ ] **Step 3: Add the field to the role contract**

In `claude/meta-skill/knowledge/capabilities/product-concept.md`, in Sub-Phase 5 step 6, directly after the line

```
   - `clients[]`: array of client apps, each with `app` name, `client_type`, `platform`
```

insert

```
   - `surface`: the decision step 5 reached, as data — `{ "mode": "screen | agent_interface | existing_tool | undecided", "basis": "<one sentence: what the mode rests on, quoted from this concept's evidence>", "open_question": "<only when mode is undecided>" }`. `screen` is the only mode under which `clients[]` is non-empty and the only one that gets screens downstream; `agent_interface` and `existing_tool` declare no `clients[]`; `undecided` declares no `clients[]` and carries the question left for the user. Every role carries `surface` — a role without it is an upstream defect for every consumer, not a default to a screen.
```

In the same step's example block, replace the first example object's closing lines

```
     "feature_parity": "partial",
     "parity_exceptions": ["推送通知仅限移动端", "AR 试穿仅限 iOS"]
   }
```

with

```
     "feature_parity": "partial",
     "parity_exceptions": ["推送通知仅限移动端", "AR 试穿仅限 iOS"],
     "surface": { "mode": "screen", "basis": "消费者自己挑选、比价、下单，每一步都要看" }
   }

   // an operations-side role that resolves to an agent interface — no clients[]
   {
     "id": "R3", "name": "运营（2 名兼职）",
     "surface": { "mode": "agent_interface",
                  "basis": "每天十几二十条下架/核实/发积分事务，没有一步需要人眼判断；团队 2 人兼职" }
   }

   // an operations-side role whose channel is still the user's call — no clients[]
   {
     "id": "R2", "name": "供应商对账专员（总部）",
     "surface": { "mode": "undecided",
                  "basis": "总部已在用一套财务系统做付款与对账归档",
                  "open_question": "对账与差异处理是接进现有财务系统，还是另开界面？" }
   }
```

In the Downstream Consumers table, directly after the row that begins `` | `product-concept.json` | `roles[]`, `clients[]` | ui-design, product-verify | ``, insert:

```
| `product-concept.json` | `roles[].surface` | product-analysis, experience-map, ui-design, product-verify | required | 谁有屏幕、谁走 agent 接口、谁还没定，是概念阶段的决定；下游读这个字段，不从 clients[] 有没有去猜 |
```

- [ ] **Step 4: Rerun the identical prompt against the edited file, in a fresh packet**

PASS only if every role object carries `surface` with a valid `mode`, the HQ role's mode is `existing_tool` or `undecided` (not `screen`) with a `basis` that quotes the upstream summary, and an `undecided` role carries `open_question`. Append output and verdict to the record. If it fails, adjust the inserted bullet once, rerun once, record both.

- [ ] **Step 5: Validators, then commit**

Run: `python3 claude/meta-skill/scripts/orchestrator/validate_meta_contracts.py && python3 claude/meta-skill/scripts/orchestrator/validate_generalization_boundaries.py && python3 claude/meta-skill/scripts/orchestrator/validate_app_experience_pipeline.py .; echo "exit=$?"` → `exit=0`.

```bash
git add docs/validation/clientless-role-producer-side-thought-tests.md
git commit -F - -- claude/meta-skill/knowledge/capabilities/product-concept.md docs/validation/clientless-role-producer-side-thought-tests.md <<'EOF'
feat(meta-skill): product-concept 把角色的界面决定写成字段 surface，下游不再从 clients[] 有没有去猜

f355fb47 让运营侧角色走 agent 接口时不声明 clients[]，但决定只留在文字里，没有字段可读。
角色契约新增 surface {mode, basis, open_question}：screen 才有 clients[]，agent_interface /
existing_tool 不声明，undecided 带留给用户的问题；缺 surface 是上游缺陷不是默认。
Downstream Consumers 把它交给 product-analysis / experience-map / ui-design / product-verify。

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
EOF
```

---

### Task 2: The concept baseline and role-profiles can carry a role with no client

**Files:**
- Modify: `claude/meta-skill/knowledge/cross-phase-protocols.md` (§A.1 baseline schema block; §A.4 table row for `roles[].app`)
- Modify: `claude/meta-skill/knowledge/capabilities/product-analysis.md` (the `role-profiles.json` role object in its output schema; the mapping list)

**Interfaces:**
- Consumes: `product-concept.json.roles[].surface` from Task 1.
- Produces: `concept-baseline.json.roles[].surface` (copied verbatim from the concept) with `app` / `client_type` present only when `surface.mode` is `screen`; `role-profiles.json.roles[].surface` (copied verbatim).

- [ ] **Step 1: Edit the baseline schema**

In `claude/meta-skill/knowledge/cross-phase-protocols.md` §A.1, replace

```
  "roles": [
    {
      "id": "R1",
      "name": "role name",
      "app": "website",
      "client_type": "mobile-ios",
      "screen_granularity": "single_task_focus",
      "high_frequency_tasks": ["task1", "task2", "task3"],
      "design_principle": "single-task focus, minimize page transitions"
    }
  ],
```

with

```
  "roles": [
    {
      "id": "R1",
      "name": "role name",
      "surface": { "mode": "screen", "basis": "copied verbatim from product-concept.json roles[].surface" },
      "app": "website",
      "client_type": "mobile-ios",
      "screen_granularity": "single_task_focus",
      "high_frequency_tasks": ["task1", "task2", "task3"],
      "design_principle": "single-task focus, minimize page transitions"
    },
    {
      "id": "R2",
      "name": "operations role with no client",
      "surface": { "mode": "agent_interface", "basis": "copied verbatim" },
      "high_frequency_tasks": ["task4", "task5"]
    }
  ],
```

Directly after the schema's closing ``` fence, insert this paragraph:

```
`roles[].surface` is copied from `product-concept.json` unchanged. `app`, `client_type`, `screen_granularity` and `design_principle` exist only for a role whose `surface.mode` is `screen`; a role in any other mode carries none of them, and a baseline that gives such a role an `app` has invented a client the concept did not decide. A role with no `surface` at all is an extraction defect: the baseline is regenerated, not patched downstream.
```

In §A.4, replace the row

```
| `roles[].app` | role-value-map.json | [B] | all phases | which sub-project code/screens belong to |
```

with

```
| `roles[].surface` | product-concept.json | [B] | all phases | whether this role has screens at all (`mode: screen`), works through an agent interface or an existing tool, or is still the user's open question |
| `roles[].app` | role-value-map.json | [B] | all phases | which sub-project code/screens belong to — present only when `surface.mode` is `screen` |
```

- [ ] **Step 2: Edit role-profiles**

In `claude/meta-skill/knowledge/capabilities/product-analysis.md`, in the `role-profiles.json` role object of the output schema, directly after the line

```
      "audience_type": "<enum: consumer | admin | operator | system>"
```

(add a comma to that line) insert

```
      "surface": "<object — copied verbatim from product-concept.json roles[].surface when the input path is 'from concept' or the concept baseline is present; { mode, basis, open_question? }. A role with no surface here is an upstream defect the map producer returns, not a role that gets screens by default>"
```

In the mapping list near `- app-design roles/personas -> `role-profiles.json.roles[]`.`, directly after that line insert

```
- product-concept `roles[].surface` -> `role-profiles.json.roles[].surface` (verbatim; `experience-map.json` reads it to decide which roles get screens and which tasks go to `non_screen_tasks[]`).
```

- [ ] **Step 3: Validators and the contract tests that read these files**

Run: `python3 claude/meta-skill/scripts/orchestrator/validate_meta_contracts.py && python3 claude/meta-skill/scripts/orchestrator/validate_generalization_boundaries.py; echo "exit=$?"` → `exit=0`.
Run: `python3 -B -m pytest -q -p no:cacheprovider claude/meta-skill/tests/unit/test_validate_bootstrap.py pi/meta-skill/test_contract.py && python3 -B shared/scripts/orchestrator/check_codex_meta_skill_parity.py >/dev/null; echo "exit=$?"` → 0 failed, `exit=0`.

- [ ] **Step 4: Commit**

```bash
git commit -F - -- claude/meta-skill/knowledge/cross-phase-protocols.md claude/meta-skill/knowledge/capabilities/product-analysis.md <<'EOF'
feat(meta-skill): concept-baseline 与 role-profiles 能表达「没有客户端的角色」

基线的固定角色 schema 给每个角色都配 app + client_type，无客户端的角色在那里表达不了，
而体验地图的产出节点读的正是基线。现在两处都原样带 surface；app/client_type 只在
mode 为 screen 时存在；缺 surface 是提取缺陷，重生成基线而不是在下游补。

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
EOF
```

---

### Task 3: The receiving side keys off the field, and the real-pipeline test passes

**Files:**
- Modify: `claude/meta-skill/knowledge/experience-map-schema.md` (the `Roles without a client` row; the `non_screen_tasks` example's `reason` comment)
- Modify: `claude/meta-skill/knowledge/capabilities/ui-design.md` (the `Roles without a client` bullet)
- Modify: `claude/meta-skill/knowledge/bootstrap-audits.md` (Level 3 backward-compatibility sentence)
- Modify: `docs/validation/clientless-role-producer-side-thought-tests.md` (append the pipeline test)

**Interfaces:**
- Consumes: `role-profiles.json.roles[].surface` and `concept-baseline.json.roles[].surface` from Task 2.

- [ ] **Step 1: Re-key the hard-constraint row**

In `claude/meta-skill/knowledge/experience-map-schema.md`, replace the whole `| **Roles without a client** | … |` row with exactly:

```
| **Roles without a client** | A role's `surface.mode` (in `role-profiles.json`, copied from the concept) decides this: `screen` gets screens; `agent_interface`, `existing_tool` and `undecided` get no screen, no `app` and no operation line, and their tasks are listed in top-level `non_screen_tasks[]` (`task_id`, `role`, `reason` — the role's `surface.basis`, and its `open_question` when `undecided`, quoted, never composed here). A role with no `surface` at all is missing upstream data, not a decision: stop and return it as an upstream defect rather than exempting its tasks or drawing it a console. Human roles that wait on such a role still get their Handoff states. A console drawn for a non-`screen` role is a defect, not a default | product-concept decides who is a client (Sub-Phase 5) and records it in `surface`; a node that gives every professional role a desktop console overrides that decision, and a node that exempts a role because a key is absent invents one |
```

In the `## Full JSON Schema` block, replace

```
    {"task_id": "T7", "role": "R2", "reason": "// upstream ground, quoted — only for roles that are clientless per Hard Constraints"}
```

with

```
    {"task_id": "T7", "role": "R2", "reason": "// the role's surface.basis (and open_question when undecided), quoted — only for roles whose surface.mode is not screen"}
```

- [ ] **Step 2: Align ui-design and the audit**

In `claude/meta-skill/knowledge/capabilities/ui-design.md`, replace the bullet that begins `- **Roles without a client**:` with

```
- **Roles without a client**: a role whose `surface.mode` is not `screen` has no screens to design — its surface is an agent interface, an existing tool, or still the user's open question, decided upstream. Do not design an admin panel for it; leave experience-map's `non_screen_tasks[]` out of the UI spec.
```

In `claude/meta-skill/knowledge/bootstrap-audits.md`, replace

```
**Backward compatibility**: if a role has only `client_type` (single client, legacy format),
skip Level 3 for that role — Level 1 and 2 are sufficient.
```

with

```
**Backward compatibility**: if a role has only `client_type` (single client, legacy format),
skip Level 3 for that role — Level 1 and 2 are sufficient. A role whose `surface.mode` is not
`screen` has no clients and no client nodes to check: skip Level 3 for it, and flag any
implementation node that targets it as a client as a planning error.
```

- [ ] **Step 3: The pipeline test — the subject gets what the real node gets**

Packet outside the repo: the edited `experience-map-schema.md`, the current `journey-emotion-schema.md`, and a `role-profiles.json` written by you in the shape Task 2 defines (R1 with `surface.mode: screen` and one client; R2 with `surface: {mode: "undecided", basis: "总部已在用一套财务系统做付款与对账归档", open_question: "对账与差异处理是接进现有财务系统，还是另开界面？"}`, `audience_type: operator`, no `clients`). The subject prompt names the three packet files, forbids everything else, then gives — verbatim — scenario B's `task-inventory.json` line (T1–T6) and flow F1 from `docs/validation/no-client-role-downstream-thought-tests.md`, and the same "Task:" sentence. Do NOT hand it `product-concept.json`: the point is that `role-profiles.json` alone carries the decision.

PASS only if: no screen has R2's app or is a console for R2; T3–T6 are in `non_screen_tasks[]` with `reason` quoting the `basis` and the `open_question`; R1's waiting/refused/unclaimed states for the R2 step exist on an R1 screen. Then a second subject with the SAME packet except R2 has no `surface` at all: PASS only if it returns an upstream defect and neither draws a console nor exempts. Quote deciding lines; append both runs to the record under `## Pipeline test (role-profiles.json only)`.

- [ ] **Step 4: Validators, then commit**

Run: `python3 claude/meta-skill/scripts/orchestrator/validate_meta_contracts.py && python3 claude/meta-skill/scripts/orchestrator/validate_generalization_boundaries.py && python3 claude/meta-skill/scripts/orchestrator/validate_app_experience_pipeline.py .; echo "exit=$?"` → `exit=0`.

```bash
git commit -F - -- claude/meta-skill/knowledge/experience-map-schema.md claude/meta-skill/knowledge/capabilities/ui-design.md claude/meta-skill/knowledge/bootstrap-audits.md docs/validation/clientless-role-producer-side-thought-tests.md <<'EOF'
feat(meta-skill): 体验地图按 surface.mode 判断谁有屏幕，接缝两端对上

接收侧原先靠「没有 clients[] 且上游记了依据」，依据只在文字里；现在读 role-profiles 里
原样带过来的 surface：screen 才有屏幕，其余进 non_screen_tasks[]，reason 引用 basis /
open_question；没有 surface 仍是上游缺陷。ui-design 与 bootstrap-audits 同步。
流水线测试只给被试 role-profiles.json（真实节点读的那份），不再手递 product-concept.json。

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
EOF
```

---

### Task 4: Upgrade note and version

**Files:**
- Modify: `CLAUDE.md` (the `Upgrade impact:` paragraph)
- Modify: the same ten version carriers as the 2026-09-22 bump — `.claude-plugin/marketplace.json`, `claude/meta-skill/.claude-plugin/{marketplace,plugin}.json`, `claude/meta-skill/SKILL.md` (2 lines), `claude/meta-skill/skills/bootstrap/SKILL.md`, `codex/meta-skill/SKILL.md` (2 lines), `pi/meta-skill/package.json`; superstorm and pi/cross-exam are NOT bumped (untouched by this plan)

**Interfaces:** meta-skill `0.22.0` → `0.23.0`, Codex `0.23.0-codex.1`, Pi `0.23.0-pi.1`.

- [ ] **Step 1: Upgrade note**

In `CLAUDE.md`, append to the END of the `Upgrade impact:` paragraph:

` A concept bootstrapped before this has no `roles[].surface`; product-analysis and experience-map treat that as an upstream defect (`missing surface`) rather than giving every role a screen — rerun the concept phase (or add `surface` to each role in `product-concept.json` and regenerate `concept-baseline.json`).`

- [ ] **Step 2: Bump**

```bash
python3 - <<'PY'
import pathlib
def sub(path, old, new, count=1):
    p = pathlib.Path(path); s = p.read_text()
    assert s.count(old) == count, (path, old, s.count(old))
    p.write_text(s.replace(old, new))
sub('claude/meta-skill/.claude-plugin/plugin.json',      '"version": "0.22.0"', '"version": "0.23.0"')
sub('claude/meta-skill/.claude-plugin/marketplace.json', '"version": "0.22.0"', '"version": "0.23.0"')
sub('.claude-plugin/marketplace.json',                   '"version": "0.22.0"', '"version": "0.23.0"')
sub('claude/meta-skill/SKILL.md',                        'version: "0.22.0"',   'version: "0.23.0"')
sub('claude/meta-skill/SKILL.md',                        '# Meta-Skill v0.22.0', '# Meta-Skill v0.23.0')
sub('claude/meta-skill/skills/bootstrap/SKILL.md',       'version: "0.22.0"',   'version: "0.23.0"')
sub('codex/meta-skill/SKILL.md',                         'version: "0.22.0-codex.1"', 'version: "0.23.0-codex.1"')
sub('codex/meta-skill/SKILL.md',                         '# Meta-Skill v0.22.0-codex.1', '# Meta-Skill v0.23.0-codex.1')
sub('pi/meta-skill/package.json',                        '"version": "0.22.0-pi.1"', '"version": "0.23.0-pi.1"')
print('ok')
PY
```

Run: `python3 -B -m pytest -q -p no:cacheprovider claude/superstorm/scripts/test_package_manifests.py pi/meta-skill/test_contract.py && python3 -B shared/scripts/orchestrator/check_codex_meta_skill_parity.py >/dev/null; echo "exit=$?"` → 0 failed, `exit=0`.

- [ ] **Step 3: Commit**

```bash
git commit -F - -- CLAUDE.md .claude-plugin/marketplace.json claude/meta-skill/.claude-plugin/marketplace.json claude/meta-skill/.claude-plugin/plugin.json claude/meta-skill/SKILL.md claude/meta-skill/skills/bootstrap/SKILL.md codex/meta-skill/SKILL.md pi/meta-skill/package.json <<'EOF'
bump meta-skill 0.23.0 — 角色的 surface 字段贯通概念、基线、role-profiles 与体验地图；旧概念缺此字段按上游缺陷处理

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
EOF
```
