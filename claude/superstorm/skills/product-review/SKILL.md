---
name: product-review
argument-hint: [target]
description: Product-thinking critique of a shipped product (missing jobs, broken journeys, competitor positioning); advice only. User-invoked only via /product-review; never invoke it yourself.
---

# product-review — 产品思维审视

> Invoked only by the user as `/product-review [target]`. Claude must not start it on its own.
> Arguments: $ARGUMENTS (the product to review; empty means start at Intake). Follow this skill from Intake. Do not load the cross-exam skill.

This file is the whole protocol. The lenses below are compressed from meta-skill's `product-design-theory.md` and `consumer-maturity-patterns.md`; nothing here requires those files to be installed.

Not cross-exam. Do not read `skills/cross-exam/SKILL.md`, do not write a completion ledger, do not use done/gap/drift/unprovable. If the user has not yet verified the delivery is complete, say once that `/cross-exam` does that and continue with this review.

## Invariants

- **Interactive only.** Invoked unattended or from an autonomous pipeline: refuse and stop.
- **Advice only.** Do not edit the product's source. The only writes are under `docs/product-review/<date>-<slug>/`.
- **No `.allforai/`.** Do not read or write that tree. Do not call meta-skill capabilities. `docs/cross-exam/` is readable input.
- **No 37 interaction types. No token/pixel spec audit.** Commercial UI/interaction is in scope; design-system compliance is not.
- **Do not start grilling.** After the report, tell the user they may `$grill-me` / grilling on that file. Wait.

## Guiding thought

Product-concept 用第一性原理是为了**发明**。这边是**审视已经做出来的东西**，对等思想不是再贴一遍第一性原理，而是：

**进展，不是功能。** 不可再拆的单位是「用户点名的那份工作，有没有让人做成一件可观察的事」。功能在不在、像不像某品类、竞品有没有按钮，都不是起点。

判一条意见之前先能指出：谁、在什么情景、想做成哪件事、你在产品里看到了什么进展或卡死。指不出观察，就只是口味，不要写入报告。

「这类产品都有 X」是惯例，不是缺口。竞品只用来对照**同一份工作**上别人如何让进展发生（ERRC 当比较，不当需求）。怎么打开这个产品由你看完再定，不要带品类检查表。

（思想来源：principled critique — 先问挑战/为谁/何以算成；Cagan/Torres — outcome over output；Ulwick — progress in a circumstance。Nielsen 启发式不是主思想。）

## Questions that apply the thought

For each **job in scope**:

1. **在不在** — 有没有入口去推进这件工作？
2. **走不走得完** — 进展能不能做完，失败或反向有没有路？
3. **该不该有** — 这是核心进展还是装饰？
4. **商业级够不够** — 进展能完成的前提下，陌生人会不会把它当成能卖的产品？

Default extra pass: search live competitors only for how they create the same progress. Unmapped ideas go under "Out of scope".

## Lenses (镜头，不是清单)

原则可以否决镜头之外的情况，也可以否决镜头本身。镜头只回答"往哪看"。镜头没照到东西，不是缺口；照到了东西，仍要过"谁、情景、事、观察"四关才能写。

| Question | Where to look | Lineage |
|---|---|---|
| 2 走不走得完 | 每条路有没有终态；失败有没有恢复路；空态、加载、错误态是不是死路；反向操作（撤销、退出、删除）在不在 | feature-gap journey dimensions |
| 3 该不该有 | Kano：must-be 缺了是 `missing_job`；one-dimensional 弱是 `broken_path` 或 `ui_friction`；attractive 缺了只在竞品对同一份工作做到时才是 `borrow_*`；indifferent 是装饰，不写 | product-concept Kano anchor |
| 4 商业级够不够 | 首次进入有没有被引导；主线是不是功能菜单；核心动作有没有过程反馈；完成后有没有下一步；空态错误态是不是同一套；有没有回来的理由。反面：压缩版后台、概念 demo、功能清单式设计 | consumer-maturity-patterns |
| naming `ui_friction` / `interaction_gap` | 用 Nielsen 十条给**已观察到**的摩擦命名，让 grill 时有共同语言。不用它扫产品 | experience-map Nielsen anchor |

## 0. Intake

Completion: target named; every job in scope written as a triple and read back; run directory decided; user still present.

1. Confirm a human is in the session.
2. Name the product and how to inspect it (repo, running local app, public site). Production write-actions are forbidden; read-only public marketing pages are allowed.
3. Jobs. The user names jobs; you rewrite each into a **triple** and read it back for confirmation:
   `who` / `in what circumstance` / `what observable progress`.
   A wish that stays a wish after one rewrite round ("make search better" with no who or circumstance) is not a job; say which part is missing and let the user supply it once. Still missing → leave it out. No jobs → ask once; still none → stop.
4. Run directory `docs/product-review/<YYYY-MM-DD>-<slug>/`. If `recommendations.md` already exists there, ask once: continue (keep ids, append) or new run (suffix the slug).

## 1. Facts

Completion: evidence limits recorded; prior evidence folded in; every job has evidence for the four questions; competitor notes only for jobs in scope.

**Evidence limits, before opening anything.** Record three facts: can the product run here; is a browser or screenshot tool available; is WebSearch available. These become the report's `Evidence limits` line. Without a browser, every `ui_friction` / `interaction_gap` item carries `evidence: code-only` and says so. Never describe an inspection method you did not use.

**Prior evidence.** If `docs/cross-exam/*/completion-report.md` exists, read the newest one. Its gap list and its 旅程完成度 section are prior evidence: for each gap (`G` id) or journey verdict (`J` id) that blocks a job in scope, list it on the `Prior evidence` line with that job. A journey that cross-exam walked through (`done`) is evidence for 在不在 and 走不走得完 on the matching job; a journey `gap` with its `stuck_kind` is the observation, do not re-probe it. A known gap or blocked journey never becomes an `R` item; items that wait on it write its id in `depends_on` (`G1`, `J1`). Absent → write `Prior evidence: none`.

Find facts yourself (repo, running UI, WebSearch). Do not ask the user for anything look-up-able.

After you see the product, decide what to open and what to compare. Write down that inspection plan in one short paragraph in the report so the review is auditable — not a hidden rubric.

**Competitor sources.** Search only for how a competitor creates the same progress. Grade every source:

| Grade | Source |
|---|---|
| P1 | official docs, specs, standards |
| P2 | research bodies, analyst reports |
| P3 | first-party product-team writing, the product itself |
| P4 | community posts, social media |

P4 supports no item on its own. Record the grade and an adopt/reject reason per competitor note.

## 2. Recommendations

Completion: `recommendations.md` written in the template below. Every item is one grill-able decision.

Each item:

- `id` stable (`R1`…)
- `job` one triple from Jobs in scope, by its label
- `kind`: `missing_job` | `broken_path` | `ui_friction` | `interaction_gap` | `borrow_positioning` | `borrow_feature`
- `depends_on` other `R` ids, cross-exam `G` or `J` ids, or empty
- `recommend`: `adopt` | `defer` for kinds observed in the product; `adopt` | `defer` | `reject` for `borrow_*`
- `tradeoff` one sentence
- `evidence` paths, URLs, or UI observations — not vibes; `code-only` when no browser

Competitor ideas that do not map to a job in scope go to Out of scope, never into the tree.

**Self-check before writing.** An item that fails any line is deleted, not reworded:

- `job` is one of the triples in scope
- `evidence` is an observation (path, URL, screen state, code line), not "this category has X"
- `evidence` provenance matches Evidence limits
- `evidence` shows progress on that job blocked or degraded; "works without it" means delete
- `reject` appears only on `borrow_positioning` / `borrow_feature`; a product-observed kind you would reject was not friction — delete
- the item is not a cross-exam gap restated
- no item rests on a P4 source alone

## 3. Write and stop

Write `docs/product-review/<run>/recommendations.md`:

```markdown
# Product review — <product>

## Jobs in scope
- JOB1 — who: … / circumstance: … / progress: …

## Evidence limits
runs here: yes|no · browser: yes|no · WebSearch: yes|no · consequence: <one clause>

## Prior evidence
docs/cross-exam/<run>/completion-report.md — G1 blocks JOB1; J2 (gap, no_feedback) blocks JOB1; G2, G3 no job in scope | none

## Inspection plan
<one short paragraph: what you chose to open on THIS product and why>

## Decision tree

### R1 — <title>
- job: JOB1
- kind:
- depends_on:
- recommend: adopt | defer | reject
- tradeoff:
- evidence:

<!-- when no item survives the self-check, the tree is exactly: -->
No item survived the self-check.
- JOB1 · 在不在: <observation> · 走不走得完: <observation> · 该不该有: <observation> · 商业级: <observation>

## Competitors (jobs in scope only)
- <name> [P1..P4]: positioning. how it makes the same progress. borrow or reject, why.

## Out of scope
- seen elsewhere, not a job in scope
```

Then stop. One line: this file is upstream for `$grill-me`. Do not grill. Do not implement.
