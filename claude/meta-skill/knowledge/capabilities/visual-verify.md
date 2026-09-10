# Visual Verify Capability

> Capability reference for screenshot-based UI comparison between source and target apps.
> Bootstrap may create one or multiple nodes from this capability depending on project complexity.

## Purpose

Capture screenshots of source and target apps, compare per-screen,
identify layout/style/content discrepancies, fix in repair loop.

## Sub-Agent Architecture

- capture agent: screenshot collection (source + target)
- structural agent: layout/style comparison per screen
- data-integrity agent: data content verification
- linkage agent: navigation/link validation
- report agent: scoring + report generation
- repair agent: code fixes for visual discrepancies

## Protocol

1. Capture: source + target screenshots per screen per role
2. Plan: enumerate comparison subtasks
3. Execute: parallel per-screen (structural + data + linkage)
4. reviewer one visual review: inspect captured screenshots and classify visible UI defects
5. Report: aggregate scores
6. Repair loop: fix -> re-capture -> re-compare -> reviewer one review, until a round changes no screen score or a repair regresses another screen

## Boundary: ui-forge vs visual-verify

Both capabilities compare a running UI against a reference and then change code.
The reference is what separates them, and the split is binding:

| | ui-forge | visual-verify |
|---|---|---|
| Reference | `ui-design/ui-design-spec.md` + `tokens.json` | screenshots of a **source app** |
| Needs a source app | No | Yes — without one, skip |
| Question answered | "Does the build match the design we specified?" | "Does the build match the app we are replicating?" |
| In scope to fix | Token values, layout vs spec, component states, visual polish | Layout/style diffs, data-content diffs, navigation/link diffs |
| Out of scope | Data content, navigation targets, link behavior | Polish work with no source-app counterpart |
| Order | Runs first | Runs last (see visual-verify Rules) |

If a project has both a design spec and a source app, both run, in that order,
and neither re-fixes the other's category. A defect ui-forge already closed must
not reappear as a visual-verify repair item; visual-verify reads
`ui-forge/fidelity-assessment.json` to skip them.

If a project has a source app but no design spec, only visual-verify runs.
If it has a design spec but no source app, only ui-forge runs.

## Modes

| Mode | What |
|------|------|
| `full` | capture -> compare -> report -> repair loop |
| `analyze` | capture -> compare -> report (no code changes) |
| `fix` | repair from last report (no re-capture) |

## Rules

1. **Real screenshots only**: No DOM manipulation for state setup. ViewModel calls OK, direct DOM changes forbidden.
2. **Platform adaptation exclusion**: Differences matching stack-mapping.platform_adaptation are not_a_gap.
3. **Multi-role**: role-view-matrix.json triggers per-role comparison.
4. **5-layer validation**: Static page, CRUD states, dynamic effects, API logs, composite milestones.
5. **Data injection tiers**: User interaction > ViewModel call > Network mock > UNREACHABLE.
6. **Pre-condition**: Visual verify runs last — after cr-fidelity + product-verify + testforge all pass, and after ui-forge when that capability is in the workflow.
7. **Encoding**: All output files must use UTF-8. JSON with `ensure_ascii=False`. Scrub GBK mojibake on read-back.
8. **Linkage verify**: If `.allforai/visual-verify/interaction-recordings.json` exists, execute same business flow chains (not just screenshots).
9. **reviewer one review required**: screenshot diff or DOM-derived comparison is not enough. reviewer one must inspect the screenshots and produce a visual review report before the node can pass.
10. **The device axis comes from the code, not from the developer's window**: every screen is captured at every width the code makes different, each capture reads its axes back inside the app, and the gate in "Axes, readback and evidence entries" refuses anything less by name.

## Phases

### Phase A: Screenshot Capture

- Dynamic screens inject minimal test data via ViewModel (not test account presets)
- Source and target both captured; both missing = error; source only missing = CAPTURE_UNAVAILABLE compensation
- Capture per screen per role (from experience-map.json, route-map.json, replicate-config.json)
- Capture per case of the frozen matrix: every screen at every device width, appearance, locale and
  dynamic-type value the inventory carries, each capture reading its axes and width back inside the
  app (see "Axes, readback and evidence entries" below — the inventory, matrix, manifest and entry
  files are that section's)

### Phase B: Task Planning

Explicit comparison task list generated before execution (no direct jump to compare).

### Phase C: Parallel Comparison

Per-screen agents run in parallel:
- Structural: layout hierarchy, element positions, color/typography
- Data integrity: actual data values, empty/loading/error states
- Linkage: navigation targets, action handlers (when interaction-recordings.json present)

### Phase D: Reviewer One

After automated comparison, reviewer one reviews the actual screenshots as images.
This review is a separate gate because pixel diff and selector assertions can miss
obvious product-quality issues such as blank regions, clipped text, unreadable
contrast, modal/keyboard obstruction, wrong visual state, or incoherent responsive
layout.

Reviewer one sees the same screen at every width, appearance and locale the matrix keeps, and
judges each capture against the frozen rules in `visual-baseline.json` — a pinned layout rule gives
the sentence to cite at the wide end (its `ends`), a fluid one the sentence for a column that failed
to stretch. Each finding names the rule, the observation and the originals it points at.

Required outputs:

- `.allforai/visual-verify/screenshot-manifest.json`
- `.allforai/visual-verify/visual-review-1.json`
- `.allforai/visual-verify/visual-review-1.md`

The JSON state must be one of:

- `passed`
- `passed_with_warnings`
- `failed_visual_review`
- `blocked_by_missing_screenshots`
- `blocked_by_unreadable_screenshot`

Any `blocker` or `major` issue in reviewer one review blocks visual-verify pass.

### Phase E: Report + Repair

- Aggregate per-screen scores into composite visual fidelity score
- `full` mode: auto-repair -> re-capture -> re-compare -> reviewer one review until convergence (a round that changes no score, or a repair that regresses another screen, ends it)

## Axes, readback and evidence entries (ADR-0008, #61)

visual-verify captures across the same axes visual acceptance uses, read by the same census and
expanded by the same matrix. The shared package `shared/visual-acceptance` is mirrored into this plugin
as `${CLAUDE_PLUGIN_ROOT}/scripts/visual/` — a fifth engine-style mirror, kept identical by the package's
`sync.py`, sitting beside `scripts/engine/` where its `matrix.py` looks for the evidence engine. The
decision was the whole package rather than reaching `expand_inventory` and the readback functions by
path: an installed plugin holds only its own root, and a copied function drifts the first time the
engine is fixed. The mirror's protocol (`visual/visual-acceptance.md`) and per-platform notes
(`visual/platforms/*.md`: how each axis is read back inside the app) are the reference for what
follows; `${CLAUDE_PLUGIN_ROOT}/scripts/check_visual_evidence.py --run .allforai/visual-verify --node
<node_id>` is the gate. The node copies none of these rules; a rule that is not in the mirror is not a
rule. Nothing here changes who reviews: Reviewer One and the second independent review (ADR-0002/0003)
stay as they are — they now see the same screen at every width the code makes different.

Files under `.allforai/visual-verify/` (the run directory):

| File | What it is |
|---|---|
| `surface-inventory.json` | the inventory in the shared shape: `platform`, `form_factor`, `width_range`, `layout_thresholds`, `locales` / `axis_support`, optional `devices`, `surfaces[]` each with the seven axes |
| `case-matrix.json` | `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/visual/matrix.py surface-inventory.json`, saved verbatim; a row may add only `applicability: not_applicable` with `reason` and `basis` |
| `visual-baseline.json` | the frozen rules the comparison runs against, by category; layout rules are `{rule, pinned: false}` or `{rule, pinned: true, ends}` |
| `screenshot-manifest.json` | `{captures: [...]}` in the shared manifest shape — one capture per kept case, image paths relative to `evidence/` |
| `evidence/<node_id>/…` | the original PNG/JPEG captures |
| `evidence-entries/<node_id>.json` | ledger-shaped entries over the captures (verification-protocol rule 7), written by `capture_evidence.py entry` |
| `visual-review-1.json`, `visual-review-2.json` | the reviewers' reports (ADR-0003 names; reviewer two's when it ran) |

The gate is passed only when every condition below holds; it refuses by name otherwise, and the node's
state is `refused`, `failed_visual_review` or `passed` exactly as the gate says — never as the node says.

- **The inventory expands.** `platform` is declared; a web target declares `form_factor`; `desktop` or
  `both` declares a global `width_range` whose max reaches the desktop floor (1920) unless the window
  is `fixed_window`; `layout_thresholds` carry every width the census read from the code (media
  queries and container queries, framework breakpoints, the main column's `max-width`, `innerWidth`
  branches, sidebar collapse and grid column changes), each with its `path:line`; every axis of every
  surface is a non-empty list of concrete values; a scrollable web surface carries a `scroll-` state
  and a resizable desktop surface a `resize-` state. **The device axis straddles every threshold and
  reaches both ends of the width range** — the developer's window is one value among them, never the
  axis. The engine's matrix rules decide (`页面清单不展开: …` names the rule broken); nothing is sampled
  or capped.
- **Every value the code supports is on the matrix.** `axis_support.<axis>.supported` and
  `locales.supported` come from the census; a value the user declines stays on the record as `declined`
  with their words and time, and every other value appears on that axis of every surface (a compound
  value is one case and proves one value).
- **The frozen matrix is the expansion.** `case-matrix.json` equals the expansion row for row
  (`冻结矩阵与页面清单的展开不一致`).
- **The frozen rules declare what they pin.** Each layout rule is `{rule, pinned: false}` with no width
  literal in its text, or `{rule, pinned: true, ends}` where `ends` names, at the applicable range's min
  and max, the empty area the rule allows as a measurable bound. Otherwise an 820px centered column at
  1920 beside a blank half-screen "matches the rule" and the reviewer has no sentence to cite.
- **Every kept case is captured.** Every case the matrix keeps (not abstracted, not annotated
  not_applicable with reason and basis) has exactly one capture whose seven axes equal the case's; the
  first case without one is refused with its axes (`用例未拍: …`), so the wide end cannot be left out.
- **Every capture reads back.** For each axis the code supports, `readback.<axis>` is the value read
  inside the app — Web: `matchMedia('(prefers-color-scheme: dark)')` plus `data-theme` / `class` for
  appearance, `document.documentElement.lang` for locale, the computed root font size and
  `visualViewport.scale` for dynamic type, `screen.orientation.type` for orientation — and it is one of
  the case's values; `readback.width` is the app's own layout width (`window.innerWidth`) and equals the
  case's effective width; an RTL locale reads back `direction: rtl`. A mismatch is refused by name
  (`<axis> 轴读回值 … 与用例 … 不符`, `width 读回值 … 与用例设备宽度 … 不符`, `… 缺应用内读回值`): a Playwright
  option that did not take effect is not coverage.
- **Web captures say how they were taken.** `capture_mode`, `headless`, `scrollbars`, `scroll_profile`,
  `capture_tool` on every capture; a `scroll-` state accepts only a viewport capture with native
  scrollbars.
- **Images are bound.** `images` exist under `evidence/` and hash to `image_digests`
  (`截图内容摘要不匹配`).
- **Entries judge what was captured.** Each ledger entry names `visual_case_ids` from the matrix and
  `evidence_manifest: "screenshot-manifest.json"`, carries the build every capture it judges carries,
  lists those captures' images, and passes verification-protocol rule 7 (engine shape, author marker
  `{pipeline: "meta-skill/run", node_id, capability: "visual-verify"}`, build against the tree now); every
  capture is judged by some entry (`截图未被任何条目裁决`).
- **Reviewers saw every original.** `visual-review-1.json` exists (`visual-review-2.json` when the second
  reviewer ran); each report's `inspected_images` covers every capture image with matching
  `image_digests` (`reviewer 未检查全部原图`, `reviewer 图片内容绑定不匹配`), `status` is `passed` or
  `findings`, and each finding has a unique `id`, a `severity` (`high | medium | low`, or the node's
  `blocker | major | minor`), the `rule` it cites, an `observation` and the inspected `images` it points
  at. Any `high` / `medium` (`blocker` / `major`) finding from any reviewer fails the node
  (`failed_visual_review`); agreement between reviewers is not required (ADR-0002).

Fixture the gate is tested against (`tests/unit/test_visual_verify_axes.py`): a web desktop inventory
of 1024..1920 with a 1280 threshold, `消息列 820px 居中` pinned with both ends, captures at 1024 / 1280 /
1920 reading their widths back, and a reviewer finding at 1920 citing the rule's wide end — it lands as a
finding. Without the 1920 device the inventory does not expand; with the 1920 capture taken in a 1512
window the capture is refused by its width; with the reviewer not having opened the 1920 image the
report is refused.

## Downstream Consumers

> Bootstrap reads this table to generate Context Pull sections for downstream node-specs.
> `required` = subagent reports error if file missing; `optional` = warning + continue.

| Artifact | Field Path | Consumer Capability | Required | Reason |
|----------|------------|---------------------|----------|--------|
| `.allforai/visual-verify/visual-verify-report.json` | composite visual fidelity score | pipeline-closure-verify | optional | 管道闭合检查读取视觉验证综合分 |
| `.allforai/visual-verify/visual-verify-report.json` | per-screen scores | launch-prep | optional | 上架准备参考视觉还原度是否达标 |
| `.allforai/visual-verify/visual-review-1.json` | state, blocking issues | pipeline-closure-verify | required | 闭环验证必须知道截图是否被 reviewer one 视觉复核通过 |
| `.allforai/visual-verify/screenshot-manifest.json` | screenshot paths, refs | launch-prep | required | 上线前必须保留可追溯截图证据 |
| `.allforai/visual-verify/evidence-entries/<node_id>.json` | entries: build, readback, visual_case_ids | pipeline-closure-verify | required | 闭环验证读取视觉门的账本条目（构建、读回、用例引用），/cross-exam 之后据此采信作者证据 |

## Knowledge References

### Phase-Specific:
- experience-map-schema.md: expected screen inventory for visual comparison
- consumer-maturity-patterns.md: visual maturity evaluation criteria

## Composition Hints

### Skip Entirely
For projects with `architecture_pattern` in `['library-sdk', 'embedded-firmware', 'github-action']` or serverless patterns, CLI tools (including Rust CLI + TUI — terminal output cannot be compared with screenshot diff), pure backend services, or where `ui-design` was skipped: skip visual-verify entirely — no screens to capture.

**Headless guard** (mandatory pre-check): if `.allforai/ui-design/ui-design-spec.md` does not exist, abort with `SKIP_HEADLESS: no UI screens declared` and mark node as skipped. Do NOT attempt to capture screenshots.

### Single Node (default)
For single-platform projects: one visual-verify node captures and compares all screens.

### Split into Multiple Nodes
For multi-platform projects: split per platform (visual-verify-ios, visual-verify-android, visual-verify-web) since each requires different capture tooling.

### Merge with Another Capability
Rarely merged. Visual verification is inherently platform-specific and runs late in the pipeline. Keep separate.
