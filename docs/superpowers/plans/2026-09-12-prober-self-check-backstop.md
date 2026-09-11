# Prober Self-Check Backstop (#42 residual 3) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stop a verdict from outliving the evidence it was drawn from — an entry judged `done` whose own prober reported a step `stuck` or `could_not` is refused, and where the prober's transcript is on disk its returned statuses must match the ledger's.

**Architecture:** Two layers, weakest assumption first. The ledger already carries `steps[].status` for journey entries, so the first check is purely internal and deterministic: `done` contradicts a `stuck`/`could_not` step in the same entry, no transcript required. The second layer reads the prober's returned JSON out of the transcript `_transcript_reason` already opens and refuses when the ledger's statuses disagree with what the prober actually reported. Both are reasons in the existing refusal path, never new gates.

**Tech Stack:** Python 3, pytest. `claude/superstorm/scripts/render_report.py` and its diverged Codex twin `codex/cross-exam-skill/scripts/render_report.py`; schemas on both platforms.

**Spec:** GitHub issue #42 residual 3, and the recorded decision comment of 2026-09-09 which defines the shape: "the renderer parses the prober's returned JSON from the transcript and refuses an entry judged `done` whose prober reported any step `could_not` / stuck, naming the step."

## Global Constraints

- Residuals 1 and 2 of #42 are **out of scope**: 1 was accepted as-is, 2 shipped as #52. Touch neither.
- Every check returns a Chinese reason string through the existing refusal path; it never raises. Match neighbouring wording (`旅程引用不存在：`, `证据文件写于探测窗口之外`).
- The two renderers have **diverged**; change each on its own and keep each suite's assertions passing unchanged.
- A malformed or unreadable transcript is **not** a refusal — it is the existing "transcript 不可核" note. Absence never convicts.
- Journey entries are the only ones carrying `steps[]`; a non-journey entry is unaffected by both layers.
- Suites run per directory (two `test_render_report.py` files collide): `claude/superstorm/scripts`, `codex/cross-exam-skill/scripts`.
- Never stage `docs/feedback/inbox/`. Commit message via `-F` file; trailer on every commit:
  ```
  Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
  Claude-Session: https://claude.ai/code/session_019P9YwUQfRBh2BhcLJGpXmo
  ```

---

## File Structure

| File | Responsibility |
|---|---|
| `claude/superstorm/scripts/render_report.py` | Both checks, wired into the existing per-entry refusal path beside `_journey_reason` / `_transcript_reason` |
| `claude/superstorm/scripts/test_render_report.py` | Tests at the `render` seam |
| `codex/cross-exam-skill/scripts/render_report.py` | The same two checks, written against that port's own code |
| `codex/cross-exam-skill/scripts/test_render_report.py` | Its own tests |
| `claude/superstorm/knowledge/cross-exam/schemas.md`, `codex/cross-exam-skill/schemas.md` | The contract both checks enforce |

Known anchors (verified on the current tree): `steps[]` entries are `{n, action, observed, status: done|stuck|could_not, evidence}`; `_journey_reason` at ~line 204 already walks `e.get("steps", [])`; `_transcript_reason` at ~line 123 opens `agent_task.output_file` and holds its text in `body`; `_refusal_reason` at ~line 330 is where journey refusals are returned.

---

### Task 1: A verdict cannot outrun its own steps

**Files:**
- Modify: `claude/superstorm/scripts/render_report.py` (new `_step_verdict_reason`, called from `_refusal_reason`)
- Test: `claude/superstorm/scripts/test_render_report.py`

**Interfaces:**
- Consumes: an entry dict with `journey`, `verdict`, and `steps[]` of `{n, action, observed, status, evidence}`.
- Produces: `_step_verdict_reason(e) -> str` — `""` or a reason naming the first contradicting step by its `n` and `status`. Task 2 calls it before its own transcript work.

- [ ] **Step 1: Write the failing test**

Append to `claude/superstorm/scripts/test_render_report.py`, inside the module (top level, beside the other test classes):

```python
class TestStepVerdict(unittest.TestCase):
    """A journey judged done cannot contain a step its own prober marked stuck or could_not."""

    def _journey_entry(self, verdict, statuses):
        e = _entry("旅程能走通吗？", verdict=verdict)
        e["journey"] = "J1"
        e["steps"] = [{"n": i + 1, "action": f"第 {i+1} 步", "observed": "…",
                       "status": s, "evidence": "q01-01.png"} for i, s in enumerate(statuses)]
        if verdict == "gap":
            e["stuck_kind"] = "blocked"
        return e

    def test_done_with_a_stuck_step_is_refused_naming_the_step(self):
        reason = render_report._step_verdict_reason(self._journey_entry("done", ["done", "stuck"]))
        self.assertIn("第 2 步", reason)
        self.assertIn("stuck", reason)

    def test_done_with_a_could_not_step_is_refused(self):
        reason = render_report._step_verdict_reason(self._journey_entry("done", ["could_not"]))
        self.assertIn("could_not", reason)

    def test_done_with_every_step_done_passes(self):
        self.assertEqual(render_report._step_verdict_reason(self._journey_entry("done", ["done", "done"])), "")

    def test_a_gap_may_carry_a_stuck_step(self):
        self.assertEqual(render_report._step_verdict_reason(self._journey_entry("gap", ["done", "stuck"])), "")

    def test_a_non_journey_entry_is_untouched(self):
        e = _entry("普通问题"); e["verdict"] = "done"
        self.assertEqual(render_report._step_verdict_reason(e), "")

    def test_a_malformed_steps_list_is_a_reason_not_a_crash(self):
        e = self._journey_entry("done", ["done"]); e["steps"] = "not a list"
        self.assertIsInstance(render_report._step_verdict_reason(e), str)
        e2 = self._journey_entry("done", ["done"]); e2["steps"] = [{"n": 1}, None]
        self.assertIsInstance(render_report._step_verdict_reason(e2), str)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest -q claude/superstorm/scripts/test_render_report.py -k StepVerdict -v`
Expected: FAIL — `AttributeError: module 'render_report' has no attribute '_step_verdict_reason'`.

- [ ] **Step 3: Implement**

In `render_report.py`, add above `_refusal_reason`:

```python
STEP_FAILURE_STATUSES = ("stuck", "could_not")


def _step_verdict_reason(e):
    """一条旅程判 done，它自己的 steps 里就不能有 stuck / could_not。

    实测官返回的逐步 status 是它当场的观察；把 entry 改成 done 而不动这些 status，
    裁决就跑在了证据前面。这一层只看 entry 自身，不需要 transcript。"""
    if not e.get("journey") or e.get("verdict") != "done":
        return ""
    steps = e.get("steps")
    if steps is None:
        return ""
    if not isinstance(steps, list):
        return "旅程 steps 须是列表"
    for index, step in enumerate(steps):
        if not isinstance(step, dict):
            return f"旅程 steps 第 {index + 1} 项不是对象"
        status = step.get("status")
        if status in STEP_FAILURE_STATUSES:
            return (f"旅程判 done，但第 {step.get('n', index + 1)} 步实测官报 {status}"
                    f"（{step.get('action', '')}）：裁决不能跑在自己的证据前面")
    return ""
```

Then call it inside `_refusal_reason`, immediately after the existing journey checks (the block that returns `旅程引用不存在：` and the `stuck_kind` check), so a journey fault is reported before this one:

```python
    step_reason = _step_verdict_reason(e)
    if step_reason:
        return step_reason
```

- [ ] **Step 4: Run the suite**

Run: `python3 -m pytest -q claude/superstorm/scripts`
Expected: all PASS, including the six new cases and every pre-existing assertion unchanged.

- [ ] **Step 5: Commit**

```bash
cat > /tmp/step1.txt <<'EOF'
cross-exam: a journey judged done cannot contain a step its own prober marked stuck or could_not (#42)

The prober's per-step status is its on-the-spot observation. Editing the
entry to done without touching those statuses puts the verdict ahead of
the evidence it was drawn from. The renderer now refuses such an entry,
naming the step. Internal to the entry; no transcript needed.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_019P9YwUQfRBh2BhcLJGpXmo
EOF
git add claude/superstorm/scripts/render_report.py claude/superstorm/scripts/test_render_report.py
git commit -q -F /tmp/step1.txt
```

---

### Task 2: The ledger's statuses must match what the prober returned

**Files:**
- Modify: `claude/superstorm/scripts/render_report.py` (new `_prober_steps`, `_prober_agreement_reason`; called from `_transcript_reason`)
- Test: `claude/superstorm/scripts/test_render_report.py`

**Interfaces:**
- Consumes: `_step_verdict_reason(e)` from Task 1; the transcript text `body` that `_transcript_reason` already reads from `agent_task.output_file`.
- Produces: `_prober_steps(body) -> list | None` (the prober's returned `steps`, or `None` when the transcript carries no parsable prober JSON) and `_prober_agreement_reason(e, body) -> str`.

- [ ] **Step 1: Write the failing test**

Append to `claude/superstorm/scripts/test_render_report.py`:

```python
class TestProberAgreement(unittest.TestCase):
    """The ledger may not report a step status the prober did not report."""

    PROBER_JSON = json.dumps({
        "steps_taken": ["打开页面"],
        "could_not": [],
        "steps": [{"n": 1, "action": "登录", "observed": "进了", "status": "done", "evidence": "a.png"},
                  {"n": 2, "action": "下单", "observed": "卡在支付", "status": "stuck", "evidence": "b.png"}],
    }, ensure_ascii=False)

    def _entry_with(self, statuses):
        e = _entry("旅程能走通吗？", verdict="done")
        e["journey"] = "J1"
        e["steps"] = [{"n": i + 1, "action": "x", "observed": "y", "status": s, "evidence": "a.png"}
                      for i, s in enumerate(statuses)]
        return e

    def test_a_status_the_prober_never_reported_is_refused(self):
        body = "前言\n" + self.PROBER_JSON + "\n收尾"
        reason = render_report._prober_agreement_reason(self._entry_with(["done", "done"]), body)
        self.assertIn("第 2 步", reason)
        self.assertIn("stuck", reason)

    def test_matching_statuses_pass(self):
        body = self.PROBER_JSON
        self.assertEqual(render_report._prober_agreement_reason(self._entry_with(["done", "stuck"]), body), "")

    def test_a_transcript_without_prober_json_is_not_a_refusal(self):
        self.assertIsNone(render_report._prober_steps("实测官只写了散文，没有 JSON"))
        self.assertEqual(render_report._prober_agreement_reason(self._entry_with(["done"]), "散文"), "")

    def test_the_last_prober_json_wins_when_the_transcript_has_several(self):
        early = json.dumps({"steps": [{"n": 1, "status": "stuck"}]}, ensure_ascii=False)
        late = json.dumps({"steps": [{"n": 1, "status": "done"}]}, ensure_ascii=False)
        steps = render_report._prober_steps(early + "\n改完再返回\n" + late)
        self.assertEqual(steps[0]["status"], "done")

    def test_malformed_prober_json_is_ignored_not_fatal(self):
        self.assertIsNone(render_report._prober_steps('{"steps": [ oops'))
        self.assertEqual(render_report._prober_agreement_reason(self._entry_with(["done"]), '{"steps": [ oops'), "")
```

`json` is already imported at the top of that test file; confirm before adding.

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest -q claude/superstorm/scripts/test_render_report.py -k ProberAgreement -v`
Expected: FAIL — `_prober_agreement_reason` / `_prober_steps` not defined.

- [ ] **Step 3: Implement**

In `render_report.py`, add above `_transcript_reason`:

```python
def _prober_steps(body):
    """实测官返回的 JSON 里的 steps；transcript 里没有可解析的就返回 None。

    自检那条规则只写在 prompt 里（「只改格式与措辞，不改任何 status」），没人核。
    这里把实测官当场返回的 steps 找出来，供台账比对。transcript 允许出现多份（重试、
    自检后重发），以最后一份为准——那是它最终交出的东西。"""
    last = None
    for match in re.finditer(r'\{[^{}]*"steps"\s*:\s*\[', body):
        start = match.start()
        depth = 0
        for index in range(start, len(body)):
            if body[index] == '{':
                depth += 1
            elif body[index] == '}':
                depth -= 1
                if depth == 0:
                    try:
                        candidate = json.loads(body[start:index + 1])
                    except ValueError:
                        break
                    if isinstance(candidate.get("steps"), list):
                        last = candidate["steps"]
                    break
    return last


def _prober_agreement_reason(e, body):
    """台账的逐步 status 必须和实测官返回的一致。实测官没返回可解析的 JSON 就不比——
    缺证不定罪。"""
    if not e.get("journey"):
        return ""
    reported = _prober_steps(body)
    if reported is None:
        return ""
    ledger = e.get("steps")
    if not isinstance(ledger, list):
        return ""
    by_n = {}
    for step in reported:
        if isinstance(step, dict) and step.get("n") is not None:
            by_n[str(step["n"])] = step.get("status")
    for index, step in enumerate(ledger):
        if not isinstance(step, dict):
            continue
        key = str(step.get("n", index + 1))
        if key not in by_n:
            continue
        if step.get("status") != by_n[key]:
            return (f"第 {key} 步台账记 {step.get('status')}，实测官返回的是 {by_n[key]}："
                    f"自检只改格式与措辞，不改 status")
    return ""
```

Then in `_transcript_reason`, after the existing name-or-directory test passes and before it returns the probe-window result, add the comparison (the function already holds `body`):

```python
    agreement = _prober_agreement_reason(e, body)
    if agreement:
        return agreement
```

`re` and `json` are already imported in this module; confirm before adding.

- [ ] **Step 4: Run the suite**

Run: `python3 -m pytest -q claude/superstorm/scripts`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
cat > /tmp/step2.txt <<'EOF'
cross-exam: the ledger's step statuses must match what the prober returned (#42)

The prober's self-check rule — only format and wording, never a status —
lived in the prompt with nothing enforcing it. Where the prober's
transcript is on disk, the renderer now parses the steps it actually
returned and refuses a ledger that reports a different status, naming the
step. A transcript with no parsable prober JSON is not a refusal: absence
never convicts.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_019P9YwUQfRBh2BhcLJGpXmo
EOF
git add claude/superstorm/scripts/render_report.py claude/superstorm/scripts/test_render_report.py
git commit -q -F /tmp/step2.txt
```

---

### Task 3: The Codex port and the written contract

**Files:**
- Modify: `codex/cross-exam-skill/scripts/render_report.py`
- Test: `codex/cross-exam-skill/scripts/test_render_report.py`
- Modify: `claude/superstorm/knowledge/cross-exam/schemas.md`, `codex/cross-exam-skill/schemas.md`

**Interfaces:**
- Consumes: the two functions and their reason strings from Tasks 1–2, reproduced against the Codex port's own code.
- Produces: nothing new.

- [ ] **Step 1: Write the failing tests in the Codex suite**

Append both test classes — `TestStepVerdict` and `TestProberAgreement` — to `codex/cross-exam-skill/scripts/test_render_report.py`, **verbatim from Tasks 1 and 2**, adjusting only the entry-builder helper if that file's `_entry` signature differs (check it first; the two suites have diverged).

- [ ] **Step 2: Run to verify they fail**

Run: `python3 -m pytest -q codex/cross-exam-skill/scripts/test_render_report.py -k "StepVerdict or ProberAgreement" -v`
Expected: FAIL — neither function exists in that port.

- [ ] **Step 3: Implement in the Codex renderer**

Add `STEP_FAILURE_STATUSES`, `_step_verdict_reason`, `_prober_steps` and `_prober_agreement_reason` to `codex/cross-exam-skill/scripts/render_report.py` with the same bodies and the same reason strings as Tasks 1–2. Wire them at that port's equivalents of `_refusal_reason` and `_transcript_reason` — read the file to find them; do not assume the Claude line numbers.

- [ ] **Step 4: Document the contract on both platforms**

In **both** `claude/superstorm/knowledge/cross-exam/schemas.md` and `codex/cross-exam-skill/schemas.md`, find the bullet describing journey `steps[]` (it defines `{n, action, observed, status: done|stuck|could_not, evidence}`) and append:

```markdown
  旅程判 `done` 时 `steps[]` 里不能有 `stuck` / `could_not`，渲染器拒渲并点名那一步——
  裁决不能跑在自己的证据前面。`agent_task.output_file` 在盘时，渲染器另把实测官返回的
  `steps[]` 解析出来与台账逐步比对，status 不一致拒渲：实测官的自检只改格式与措辞，
  不改 status（prober.md）。transcript 里没有可解析的实测官 JSON 就不比——缺证不定罪。
```

- [ ] **Step 5: Run both suites**

Run: `python3 -m pytest -q claude/superstorm/scripts && python3 -m pytest -q codex/cross-exam-skill/scripts`
Expected: both all PASS.

- [ ] **Step 6: Commit**

```bash
cat > /tmp/step3.txt <<'EOF'
cross-exam: the Codex port gets the same two checks, and both schemas state the contract (#42)

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_019P9YwUQfRBh2BhcLJGpXmo
EOF
git add codex/cross-exam-skill/scripts/render_report.py codex/cross-exam-skill/scripts/test_render_report.py claude/superstorm/knowledge/cross-exam/schemas.md codex/cross-exam-skill/schemas.md
git commit -q -F /tmp/step3.txt
```

---

### Task 4: Closure — adversarial check, suites, push, ticket

**Files:** none new.

- [ ] **Step 1: Adversarial thought test**

Dispatch a fresh-context subagent, giving it only: the two renderers, `prompts/prober.md`, both `schemas.md`, and this instruction —

> 你扮演一个想把 gap 改成 done 的盘问官。台账里有一条旅程 entry，实测官报了第 2 步 stuck。逐条试你能想到的改法（改 entry 的 steps status、删掉 steps、删掉 journey 字段、改 n 让它对不上、让 transcript 不可读、在 transcript 后面追加一份伪造的实测官 JSON、把 verdict 改成 drift 而不是 done），用 python 实际验证每条是否被拦，引用拦住它的函数名与理由串。哪条能过就明说。

Record its findings. Anything it gets through that should not pass is fixed here before closing; anything genuinely out of scope (self-reported times, per #52) is noted, not fixed.

- [ ] **Step 2: Full suites and push**

```bash
python3 -m pytest -q claude/superstorm/scripts
python3 -m pytest -q codex/cross-exam-skill/scripts
python3 -m pytest -q shared/evidence-engine
git fetch -q origin && test "$(git log --oneline HEAD..origin/main | wc -l)" = 0 && git push -q origin main
```

- [ ] **Step 3: Close residual 3 on #42**

```bash
gh issue comment 42 --body "Residual 3 is implemented and pushed. Two layers: a journey judged done whose own steps[] carry stuck/could_not is refused by name (no transcript needed); and where the prober's transcript is on disk, its returned steps[] are parsed and compared with the ledger, refusing a status the prober did not report. A transcript with no parsable prober JSON is not a refusal — absence never convicts. Residual 1 was accepted as-is and residual 2 shipped as #52, so all three are now settled; closing."
gh issue close 42 --comment "All three residuals settled: 1 accepted as-is, 2 shipped as #52, 3 implemented (see the comment above)."
```

---

## Self-Review

**Spec coverage.** Residual 3's recorded shape — "the renderer parses the prober's returned JSON from the transcript and refuses an entry judged `done` whose prober reported any step `could_not` / stuck, naming the step" — is Task 2. Task 1 adds the strictly stronger, transcript-free half the decision comment implies but does not name: an entry that contradicts *its own* recorded steps needs no corroboration to be wrong. Both ports and both schemas are Task 3. The noise risk I flagged when deferring ("a prober can get stuck and then succeed") is handled by comparing per-step `n` rather than counting mentions, and by taking the *last* prober JSON in the transcript.

**Placeholder scan.** No TBD. Every code step carries the actual body; every test step the actual test. Task 3 deliberately says "read the file to find them; do not assume the Claude line numbers", because the ports have diverged — that is an instruction, not a gap.

**Type consistency.** `_step_verdict_reason(e) -> str`, `_prober_steps(body) -> list | None`, `_prober_agreement_reason(e, body) -> str` are used with those signatures in Tasks 1–3. `STEP_FAILURE_STATUSES` is the single tuple both layers read. Step identity is `n` throughout, compared as `str(n)` on both sides so an int/str mismatch in a ledger cannot silently skip a step.
