# Pi Work Supplements Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close what the Pi sessions' recent work left open: the "operations role is not a client by default" decision is received downstream instead of being overridden by a default console, one stale test expectation is corrected, and the packages whose behaviour changed since their last bump get new versions.

**Architecture:** Task 1 is test-gated text: a thought test first shows whether the experience-map node invents a console for a role that product-concept left without a client; only if it does is one hard-constraint row (and one ui-design line) added, then the same test is rerun. Task 2 is a one-file correction. Task 3 bumps versions last so it covers everything before it.

**Tech Stack:** Markdown, JSON/YAML manifests, Python 3 + pytest for the manifest and contract checks.

**Spec:** `docs/adr/0010-seams-are-guarded-from-the-receiving-side.md` — criterion 1 ("The receiver verifies … what arrived is what it needs") applied to a product-design seam: product-concept (`claude/meta-skill/knowledge/capabilities/product-concept.md`, Sub-Phase 5 step 5, commit `f355fb47`) decides who is a client; experience-map and ui-design receive that decision.

## Global Constraints

- Work directly on `main`, one commit per task. No worktree, no `git stash` / `checkout` / `reset` / `restore` / `clean`.
- Commit with an explicit pathspec (`git commit -F - -- <paths>`). Never `--no-verify`. The pre-commit hook takes ~40 s.
- End every commit message with exactly `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>` — do not substitute another model name.
- No CI. Do not create anything under `.github/`. Do not push.
- Skills state acceptance criteria, not procedures (owner's rule): new skill text says what a correct output looks like and why, not the steps to produce it.
- Thought-test subjects run on the `sonnet` model, read-only, and are given only the files named in the prompt. The prompt must not contain the words 接缝 / seam / console-is-wrong or any hint of the expected behaviour.
- New versions, exactly: meta-skill `0.22.0` (Codex `0.22.0-codex.1`, Pi `0.22.0-pi.1`); superstorm `0.44.0`; Pi cross-exam `0.22.5-pi.1`.

## Facts established on 2026-09-22

- `f355fb47` added to product-concept Sub-Phase 5 step 5: an operations-side role that resolves to an agent interface or an existing team tool "declares no `clients[]` entry — the surface is a tool contract, not an app"; with no basis for a screen, "declare no client for that role and leave the choice as an open question". Its S12 scenarios tested only the product-concept node's own output.
- Nothing downstream mentions an agent interface, a tool contract, or a role without clients. `claude/meta-skill/knowledge/experience-map-schema.md` Hard Constraints say "consumer role -> `mobile-ios` …; professional role -> `desktop-web` sidebar layout", "Every screen must have `app` field … derived from **node role**", and "Every task from task-inventory.json must appear in at least one screen's `tasks` array". The only readers of `clients[]` (`bootstrap-audits.md`, `concept-acceptance.md`, `capabilities/ui-design.md`) handle the multi-client case only.
- `claude/meta-skill/tests/expected/domain-2-expected.yaml` still lists `feature-prune` (capability deleted in `ada9def8`); its paired prompt `claude/meta-skill/tests/prompts/domain-2.md` no longer mentions it. No script or test reads the expected file.
- Versions: `claude/meta-skill` is `0.21.0` with 11 commits since that bump; `claude/superstorm` is `0.43.0` with 6. Installed plugins resolve by version. `claude/superstorm/scripts/test_package_manifests.py` asserts root marketplace = plugin marketplace = `plugin.json`; `shared/scripts/orchestrator/check_codex_meta_skill_parity.py` asserts the Codex version starts with `<claude bootstrap version>-codex.`. `pi/cross-exam` (`0.22.4-pi.1`) reads `codex/cross-exam-skill/`, whose intake text changed today. `codex/cross-exam-skill/AGENTS.md`'s title version has not tracked content changes since 09-06 and is left alone.
- Not in this plan — only the owner can do it: the real-Pi acceptance run of `/skill:keep-code-simple` recorded as "未做" in `docs/validation/pi-session-model-thought-tests.md`. Its target `/tmp/kcs-acceptance` and the backup `/tmp/kcs-local-edits` still exist today but live under `/tmp`.

---

### Task 1: A role without a client is received downstream, not given a default console

**Files:**
- Create: `docs/validation/no-client-role-downstream-thought-tests.md` (the record: prompts, verbatim outputs, verdicts)
- Modify (only if the baseline fails): `claude/meta-skill/knowledge/experience-map-schema.md` (Hard Constraints table)
- Modify (only if the baseline fails): `claude/meta-skill/knowledge/capabilities/ui-design.md` (the `Multi-client roles` bullet)

**Interfaces:**
- Consumes: product-concept's rule as quoted in Facts.
- Produces: if text is added, the experience-map top-level key `non_screen_tasks[]` with items `{ "task_id": "...", "role": "...", "reason": "..." }`.

- [ ] **Step 1: Run the baseline thought test (no file is edited yet)**

Dispatch one read-only subagent, model `sonnet`, with exactly this prompt:

> You are an executor subagent of the meta-skill plugin in /Users/aa/workspace/myskills, running the experience-map design node for a product. Read-only: do not create or edit any file; return your output as text.
>
> Read these first and follow them as your method:
> - claude/meta-skill/knowledge/experience-map-schema.md
> - claude/meta-skill/knowledge/journey-emotion-schema.md
>
> Upstream `product-concept.json` (excerpt), produced by an earlier node:
> ```json
> {"roles": [
>   {"id": "R1", "name": "家长（换出/换入童装的住户）", "clients": [{"app": "neighbor-swap", "client_type": "wechat-miniprogram", "platform": "mobile"}]},
>   {"id": "R2", "name": "运营（2 名兼职创始人）", "clients": [],
>    "operations": {"mode": "agent_interface", "basis": "每天十几二十条事务；无需人眼判断的步骤；团队只有 2 人兼职", "open_questions": []}}
> ]}
> ```
> `task-inventory.json` (excerpt): T1 R1 发布可换物品 · T2 R1 浏览并发起交换 · T3 R1 确认交接完成 · T4 R2 下架违规或虚假信息 · T5 R2 核实新用户是否本小区住户 · T6 R2 每月发放积分 · T7 R2 裁决交换纠纷
> One business flow: F2 (cross_role): R1 发起交换 → R1 双方确认 → R1 投诉对方失约 → R2 裁决纠纷 → R1 看到裁决结果
>
> Task: produce the experience-map for this product as you would ship it — operation_lines, the screens with `id`, `app`, `platform`, `tasks`, `states`, and any top-level fields you need — then the findings of your own verification loop. No commentary outside those two parts.

- [ ] **Step 2: Judge the baseline against criteria fixed now**

The baseline FAILS (a gap exists) if any of these holds in the subject's output:
1. a screen exists whose `app` belongs to R2, or whose `tasks` contain T4, T5, T6 or T7 as a human-operated screen (an operations console, admin panel, dashboard, 后台, 工作台);
2. T4–T7 silently disappear — they appear nowhere in the output and the verification findings do not mention them;
3. the verification loop reports "Task coverage" as passed while T4–T7 are on no screen and nothing explains why.

It PASSES only if no R2 screen is invented, T4–T7 are accounted for explicitly, and R1's waiting states for the R2 裁决 step exist on an R1 screen.

Write `docs/validation/no-client-role-downstream-thought-tests.md` with: the date, the exact prompt, the subject's output verbatim, and the verdict per criterion. If it PASSES, skip to Step 6 and record in the file that no text was added because the existing text already holds.

- [ ] **Step 3: Add the receiving-side constraint (only if the baseline failed)**

In `claude/meta-skill/knowledge/experience-map-schema.md`, in the `## Hard Constraints` table, replace the row

```
| **Platform** | consumer role -> `mobile-ios` single-column layout; professional role -> `desktop-web` sidebar layout | Physical device differences |
```

with

```
| **Platform** | For a role that declares `clients[]`: consumer role -> `mobile-ios` single-column layout; professional role -> `desktop-web` sidebar layout | Physical device differences |
| **Roles without a client** | A role whose `product-concept.json roles[]` entry declares no `clients[]` — its work runs through an agent interface or a tool the team already uses, or the choice is still an open question for the user — gets no screen, no `app` and no operation line. Its tasks are exempt from Task coverage and are listed instead in top-level `non_screen_tasks[]` (`task_id`, `role`, `reason` carried from product-concept), so nothing downstream can mistake them for forgotten work. Human roles that wait on such a role still get their Handoff states. A console drawn for it is a defect, not a default | product-concept decides who is a client (Sub-Phase 5, producer-side closure check). A node that gives every professional role a desktop console overrides that decision without anyone having made it |
```

and replace the row

```
| **Task coverage** | Every task from task-inventory.json must appear in at least one screen's `tasks` array | Functional completeness |
```

with

```
| **Task coverage** | Every task from task-inventory.json must appear in at least one screen's `tasks` array, or in `non_screen_tasks[]` when its role declares no client | Functional completeness |
```

In `claude/meta-skill/knowledge/capabilities/ui-design.md`, directly after the bullet that begins `- **Multi-client roles**:`, insert:

```
- **Roles without a client**: a role with no `clients[]` has no screens to design — its surface is an agent interface or an existing tool, decided upstream. Do not design an admin panel for it; if experience-map carries `non_screen_tasks[]`, leave those tasks out of the UI spec.
```

- [ ] **Step 4: Rerun the identical prompt (only if Step 3 ran)**

Dispatch a fresh read-only `sonnet` subagent with the exact prompt of Step 1. Judge with the criteria of Step 2. Append the output verbatim and the verdicts to the validation file under a `## After` heading.

If it still fails: do not reword blindly. First check the subject was asked for the artifact where the behaviour lands (it was: the experience-map). Then adjust the new `Roles without a client` row once, rerun once more, and record both. If it fails again, keep the text, record the failure honestly in the validation file, and report DONE_WITH_CONCERNS.

- [ ] **Step 5: Run the validators that cover the edited knowledge files (only if Step 3 ran)**

Run: `python3 claude/meta-skill/scripts/orchestrator/validate_meta_contracts.py && python3 claude/meta-skill/scripts/orchestrator/validate_generalization_boundaries.py && python3 claude/meta-skill/scripts/orchestrator/validate_app_experience_pipeline.py .; echo "exit=$?"`
Expected: `exit=0`.

- [ ] **Step 6: Commit**

```bash
git add docs/validation/no-client-role-downstream-thought-tests.md
git commit -F - -- docs/validation/no-client-role-downstream-thought-tests.md claude/meta-skill/knowledge/experience-map-schema.md claude/meta-skill/knowledge/capabilities/ui-design.md <<'EOF'
feat(meta-skill): 没有客户端的角色在下游被接住，不再默认画一个后台

product-concept（f355fb47）让运营侧角色在走 agent 接口或现成工具时不声明 clients[]，
但下游没有任何东西接这个决定：体验地图的硬约束给每个专业角色一个 desktop-web 后台，
任务覆盖还要求每个任务都落在屏幕上。思维测试记录见 docs/validation/no-client-role-downstream-thought-tests.md；
只在基线测出缺口时才加了这一行硬约束和 ui-design 的一句（ADR-0010：接收方自己接住上游的决定）。

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
EOF
```

(If the baseline passed and no knowledge file changed, the two knowledge paths in the pathspec are simply unchanged; replace the message body's last sentence with `基线已通过，未加任何文字。`.)

---

### Task 2: The domain-2 expectation stops naming a deleted capability

**Files:**
- Modify: `claude/meta-skill/tests/expected/domain-2-expected.yaml`

**Interfaces:**
- Consumes: nothing. Produces: nothing other tasks use.

- [ ] **Step 1: Confirm the pairing**

Run: `grep -c -i "prune" claude/meta-skill/tests/prompts/domain-2.md claude/meta-skill/tests/expected/domain-2-expected.yaml`
Expected: `0` for the prompt, `2` for the expected file. If the prompt count is not 0, stop and report.

- [ ] **Step 2: Remove the capability from the list and its result block**

Replace the line `capabilities: [feature-gap, feature-prune, ui-design]` with `capabilities: [feature-gap, ui-design]`, and delete this block together with the blank line that follows it:

```yaml
  - capability: feature-prune
    assertion_A: PASS
    assertion_B1: PASS
    assertion_B2: N/A
    b1_failures: []
    b2_findings: []
```

- [ ] **Step 3: Verify**

Run: `git grep -n -i "feature-prune\|frequency-tier\|prune-report" -- ':!docs/' ':!**/node_modules/**'; echo "exit=$?"`
Expected: no output, `exit=1`.

Run: `python3 -c "import yaml,sys; d=yaml.safe_load(open('claude/meta-skill/tests/expected/domain-2-expected.yaml')); assert d['capabilities']==['feature-gap','ui-design'] and len(d['results'])==2; print('ok')" 2>/dev/null || python3 - <<'PY'
text = open('claude/meta-skill/tests/expected/domain-2-expected.yaml').read()
assert text.count('- capability:') == 2 and 'prune' not in text
print('ok (no PyYAML; checked as text)')
PY`
Expected: a line starting with `ok`.

- [ ] **Step 4: Commit**

```bash
git commit -F - -- claude/meta-skill/tests/expected/domain-2-expected.yaml <<'EOF'
test(meta-skill): 域-2 的期望文件不再列已删除的 feature-prune

ada9def8 删掉了 feature-prune 能力并改了配对的提示 domain-2.md，期望文件漏了。

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
EOF
```

---

### Task 3: Version bumps for the packages whose behaviour changed

**Files:**
- Modify: `.claude-plugin/marketplace.json` (the `meta-skill` and `superstorm` entries)
- Modify: `claude/meta-skill/.claude-plugin/marketplace.json`, `claude/meta-skill/.claude-plugin/plugin.json`
- Modify: `claude/meta-skill/SKILL.md` (two lines), `claude/meta-skill/skills/bootstrap/SKILL.md` (one line)
- Modify: `codex/meta-skill/SKILL.md` (two lines)
- Modify: `pi/meta-skill/package.json`
- Modify: `claude/superstorm/.claude-plugin/marketplace.json`, `claude/superstorm/.claude-plugin/plugin.json`
- Modify: `pi/cross-exam/package.json`

**Interfaces:**
- Consumes: Tasks 1 and 2 already committed, so the new versions cover them.
- Produces: the exact versions in Global Constraints.

- [ ] **Step 1: See the manifest check pass before touching anything**

Run: `python3 -B -m pytest -q -p no:cacheprovider claude/superstorm/scripts/test_package_manifests.py && python3 -B shared/scripts/orchestrator/check_codex_meta_skill_parity.py >/dev/null; echo "exit=$?"`
Expected: 0 failed, `exit=0`.

- [ ] **Step 2: Apply the replacements (each old string must occur exactly as counted)**

```bash
python3 - <<'PY'
import re, pathlib
def sub(path, old, new, count):
    p = pathlib.Path(path); s = p.read_text()
    assert s.count(old) == count, (path, old, s.count(old))
    p.write_text(s.replace(old, new))
# meta-skill 0.21.0 -> 0.22.0
sub('claude/meta-skill/.claude-plugin/plugin.json',      '"version": "0.21.0"', '"version": "0.22.0"', 1)
sub('claude/meta-skill/.claude-plugin/marketplace.json', '"version": "0.21.0"', '"version": "0.22.0"', 1)
sub('.claude-plugin/marketplace.json',                   '"version": "0.21.0"', '"version": "0.22.0"', 1)
sub('claude/meta-skill/SKILL.md',                        'version: "0.21.0"',   'version: "0.22.0"',   1)
sub('claude/meta-skill/SKILL.md',                        '# Meta-Skill v0.21.0', '# Meta-Skill v0.22.0', 1)
sub('claude/meta-skill/skills/bootstrap/SKILL.md',       'version: "0.21.0"',   'version: "0.22.0"',   1)
sub('codex/meta-skill/SKILL.md',                         'version: "0.21.0-codex.1"', 'version: "0.22.0-codex.1"', 1)
sub('codex/meta-skill/SKILL.md',                         '# Meta-Skill v0.21.0-codex.1', '# Meta-Skill v0.22.0-codex.1', 1)
sub('pi/meta-skill/package.json',                        '"version": "0.21.0-pi.1"', '"version": "0.22.0-pi.1"', 1)
# superstorm 0.43.0 -> 0.44.0
sub('claude/superstorm/.claude-plugin/plugin.json',      '"version": "0.43.0"', '"version": "0.44.0"', 1)
sub('claude/superstorm/.claude-plugin/marketplace.json', '"version": "0.43.0"', '"version": "0.44.0"', 1)
sub('.claude-plugin/marketplace.json',                   '"version": "0.43.0"', '"version": "0.44.0"', 1)
# Pi cross-exam reads codex/cross-exam-skill, whose intake text changed
sub('pi/cross-exam/package.json',                        '"version": "0.22.4-pi.1"', '"version": "0.22.5-pi.1"', 1)
print('ok')
PY
```
Expected: `ok`. An `AssertionError` names the file and string whose count was not what the plan assumed — stop and report it; do not edit by hand around it.

- [ ] **Step 3: Verify nothing still says the old versions, and the checks pass**

Run: `git grep -n '0\.21\.0\|0\.43\.0\|0\.22\.4-pi' -- ':!docs/' ':!**/node_modules/**' ':!*.lock'`
Expected: exactly one line, `codex/cross-exam-skill/AGENTS.md:1:# AGENTS.md — Cross-exam package (Codex, v0.21.0)` — that title has its own history and is deliberately left alone.

Run: `python3 -B -m pytest -q -p no:cacheprovider claude/superstorm/scripts/test_package_manifests.py pi/meta-skill/test_contract.py && python3 -B -m pytest -q -p no:cacheprovider pi/cross-exam codex/meta-skill/test_install.py && python3 -B shared/scripts/orchestrator/check_codex_meta_skill_parity.py >/dev/null && python3 -B shared/scripts/orchestrator/smoke_codex_meta_install.py >/dev/null; echo "exit=$?"`
Expected: 0 failed in both pytest runs, `exit=0`.

- [ ] **Step 4: Commit**

```bash
git commit -F - -- .claude-plugin/marketplace.json claude/meta-skill/.claude-plugin/marketplace.json claude/meta-skill/.claude-plugin/plugin.json claude/meta-skill/SKILL.md claude/meta-skill/skills/bootstrap/SKILL.md codex/meta-skill/SKILL.md pi/meta-skill/package.json claude/superstorm/.claude-plugin/marketplace.json claude/superstorm/.claude-plugin/plugin.json pi/cross-exam/package.json <<'EOF'
bump meta-skill 0.22.0, superstorm 0.44.0, pi cross-exam 0.22.5-pi.1

meta-skill：接缝协议 §F、跨角色交接点、续跑时继承的完成项先过门、旧格式 state-machine.json 退役
（只剩旧格式的目录现在报 retired_bootstrap_format）、run-engine 测试进钩子、运营角色不默认给后台及其下游。
superstorm：cross-exam intake 记 judged_build、报告表头写被评构建、product-review 用它核新鲜度。
Pi cross-exam 读的是 Codex 这一份，intake 文字变了，所以跟着升。已装的插件按版本解析，不升号拿不到这些改动。

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
EOF
```
