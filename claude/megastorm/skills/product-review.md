---
name: product-review
description: Product-thinking critique of a shipped or running product. Names missing jobs, broken journeys, commercial UI/interaction gaps, and borrowable competitor positioning. Advice only — never edits product code. Explicitly invoked via /product-review. Same package as cross-exam; different protocol.
disable-model-invocation: true
---

# product-review — 产品思维审视

`$ROOT` = `${CLAUDE_PLUGIN_ROOT}`. This file is the whole protocol.

Not cross-exam. Do not read `skills/cross-exam.md`, do not write a completion ledger, do not use done/gap/drift/unprovable.

## Invariants

- **Interactive only.** Invoked unattended or from an autonomous pipeline: refuse and stop.
- **Advice only.** Do not edit the product's source. The only writes are under `docs/product-review/<date>-<slug>/`.
- **No `.allforai/`.** Do not read or write that tree. Do not call meta-skill capabilities.
- **No 37 interaction types. No token/pixel spec audit.** Commercial UI/interaction is in scope; design-system compliance is not.
- **Do not start grilling.** After the report, tell the user they may `$grill-me` / grilling on that file. Wait.

## Guiding thought

Product-concept 用第一性原理是为了**发明**。这边是**审视已经做出来的东西**，对等思想不是再贴一遍第一性原理，而是：

**进展，不是功能。** 不可再拆的单位是「用户点名的那份工作，有没有让人做成一件可观察的事」。功能在不在、像不像某品类、竞品有没有按钮，都不是起点。

判一条意见之前先能指出：谁、在什么情景、想做成哪件事、你在产品里看到了什么进展或卡死。指不出观察，就只是口味，不要写入报告。

「这类产品都有 X」是惯例，不是缺口。竞品只用来对照**同一份工作**上别人如何让进展发生（ERRC 当比较，不当需求）。怎么打开这个产品由你看完再定，不要带品类检查表。

（思想来源：principled critique — 先问挑战/为谁/何以算成；Cagan/Torres — outcome over output；Ulwick — progress in a circumstance。Nielsen 启发式不是主思想。）

## Questions that apply the thought

For each **user-named job**:

1. **在不在** — 有没有入口去推进这件工作？
2. **走不走得完** — 进展能不能做完，失败或反向有没有路？
3. **该不该有** — 这是核心进展还是装饰？
4. **商业级够不够** — 进展能完成的前提下，陌生人会不会把它当成能卖的产品？

Default extra pass: search live competitors only for how they create the same progress. Unmapped ideas go under "seen, not in scope".

## 0. Intake

Completion: target named, jobs named, run directory created, user still present.

1. Confirm a human is in the session.
2. Name the product and how to inspect it (repo, running local app, public site). Production write-actions are forbidden; read-only public marketing pages are allowed.
3. Ask the user to name the jobs this review is about. No jobs → ask once; still none → stop.
4. Create `docs/product-review/<YYYY-MM-DD>-<slug>/`.

## 1. Facts

Completion: every named job has evidence for the four guiding questions; competitor notes only for those jobs.

Find facts yourself (repo, running UI, WebSearch). Do not ask the user for anything look-up-able.

After you see the product, decide what to open and what to compare. Write down that inspection plan in one short paragraph in the report so the review is auditable — not a hidden rubric.

## 2. Recommendations

Completion: `recommendations.md` written in the template below. Every item is one grill-able decision.

Each item:

- `id` stable (`R1`…)
- `job` one named job
- `kind`: `missing_job` | `broken_path` | `ui_friction` | `interaction_gap` | `borrow_positioning` | `borrow_feature` | `skip`
- `depends_on` other ids or empty
- `recommend`: `adopt` | `defer` | `reject`
- `tradeoff` one sentence
- `evidence` paths, URLs, or UI observations — not vibes

`skip` is for competitor ideas that do not map to a named job.

## 3. Write and stop

Write `docs/product-review/<run>/recommendations.md`:

```markdown
# Product review — <product>

Jobs in scope: …

## Inspection plan
<one short paragraph: what you chose to open on THIS product and why>

## Decision tree

### R1 — <title>
- job:
- kind:
- depends_on:
- recommend: adopt | defer | reject
- tradeoff:
- evidence:

## Competitors (named jobs only)
- <name>: positioning. mapped features. borrow or skip.

## Out of scope
- seen elsewhere, not a named job
```

Then stop. One line: this file is upstream for `$grill-me`. Do not grill. Do not implement.
