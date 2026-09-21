# No-client-role downstream thought test

Task: "A role without a client is received downstream, not given a default console" (`.superpowers/sdd/2026-09-22-pi-work-supplements-plan/task-1-brief.md`, extended by `task-1b-brief.md`).

## What this record is

This file tracks three runs, in order: an invalid non-isolated baseline (Run 1), two isolated pre-edit reruns that confirmed the gap is real (not an artifact of contamination), and two isolated post-edit reruns against the corrected schema text. Only the isolated runs carry evidential weight. Verdicts are judged literally against three fixed criteria (Step 2/Step 3 of the two briefs); quoted lines are the deciding evidence, not paraphrase.

## Run 1 — invalid (contaminated)

**Why it is invalid**: the subject ran inside the repository (`/Users/aa/workspace/myskills`) rather than against an isolated packet. Its output reproduced the field name `non_screen_tasks[]` with the exact three keys (`task_id`, `role`, `reason`) that the *plan* (not yet applied to the schema at that point) specified for the fix — meaning the subject had, directly or indirectly, read the plan rather than deriving the design from the schema text alone. A "PASS" reached this way proves nothing about whether the schema's existing text actually carries the constraint.

**Original prompt** (verbatim, as dispatched):

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

**Full output**: not reproduced here (it is ~400 lines and its "PASS" carries no evidential weight — see above). See commit `2036c858` for the verbatim subject output and the pre-rewrite verdict text this file used to contain.

## Isolated baselines A and B (pre-edit, confirming the gap is real)

Two isolated reruns were dispatched (read-only, `sonnet`, packet outside the repo, prompt naming only the packet files, no mention of the repository/plan/clients/consoles/testing) against the **unedited** schema text — i.e. before the `Roles without a client` row existed. Their purpose was to rule out that Run 1's "PASS" reflected real schema content once contamination was removed. Their verbatim outputs live at:
- `.superpowers/sdd/2026-09-22-pi-work-supplements-plan/isolated-baseline-A.md`
- `.superpowers/sdd/2026-09-22-pi-work-supplements-plan/isolated-baseline-B.md`

### Prompts (used for both the pre-edit isolated baselines and, unchanged, for the post-edit "After" reruns below — the only variable between the two runs is the content of the packaged `experience-map-schema.md`)

**Scenario A** (R2 has `clients: []` and `operations.mode = agent_interface` — same upstream data as Run 1):

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
> Task: produce the experience-map for this product as you would ship it — operation_lines, the screens with `id`, `app`, `platform`, `tasks`, `states`, and any top-level fields you need — then the findings of your own verification loop. No commentary outside those two parts. Keep screens compact (id, name, app, platform, tasks, states, flow_context only).

**Scenario B** (R2 has NO `clients` key at all; only an open question):

> Upstream `product-concept.json` (excerpt), produced by an earlier node:
> ```
> {"roles": [
>   {"id": "R1", "name": "采购员（门店下单的人）", "clients": [{"app": "store-order", "client_type": "react-native", "platform": "mobile"}]},
>   {"id": "R2", "name": "供应商对账专员（总部，3 人）"}
> ],
>  "open_questions": ["R2 的对账与异常处理通过什么完成尚未确定：总部已在用一套财务系统；日均约 400 张对账单。"]}
> ```
> `task-inventory.json` (excerpt): T1 R1 按门店补货下单 · T2 R1 确认到货并登记差异 · T3 R2 核对供应商对账单 · T4 R2 处理到货差异争议 · T5 R2 月末出具结算单 · T6 R2 冻结异常供应商
> One business flow: F1 (cross_role): R1 确认到货并登记差异 → R2 处理到货差异争议 → R1 看到处理结果
>
> Task: produce the experience-map for this product as you would ship it — operation_lines, the screens with `id`, `app`, `platform`, `tasks`, `states`, and any top-level fields you need — then the findings of your own verification loop. No commentary outside those two parts. Keep screens compact (id, name, app, platform, tasks, states, flow_context only).

### Verdict per criterion (pre-edit, unedited schema)

The three criteria (fixed in `task-1b-brief.md` Step 3):
1. no screen has an `app` belonging to R2 and no screen is an operations console / admin panel / 工作台 for R2;
2. every R2 task appears in a top-level `non_screen_tasks[]` with a reason, and NOT in any screen's `tasks` array;
3. R1's waiting / refused / unclaimed states for the step R2 performs exist on an R1 screen.

**Scenario A, pre-edit — FAILS (criterion 2).**
- Criterion 1: holds. Every screen in the output uses `"app": "neighbor-swap"` (R1's app); no console was invented for R2.
- Criterion 2: **violated.** There is no `non_screen_tasks[]` field anywhere in the output. Instead R2's tasks were folded into R1 screens' `tasks` arrays: `"id": "S008", "name": "发布物品", ... "tasks": ["T1", "T4"]`, `"S006": {... "tasks": ["T5"] ...}`, `"S007": {... "tasks": ["T6"] ...}`, `"S005": {... "tasks": ["T3", "T7"] ...}`. The subject's own verification findings confirm this was deliberate: *"Task coverage — resolved by catching R2's tasks on R1's screens, not by drawing R2 a screen... All 7 tasks land on at least one screen; zero screens are attributed to R2."* That is coverage by relocation, not real coverage — T4–T7 are R2's tasks, not R1's, and claiming them as satisfied via a `removed_by_moderation` state on someone else's screen misrepresents completion.
- Criterion 3: holds. `S004` ("纠纷提交") carries `awaiting_adjudication` / `escalated_to_manual_review` on an R1 screen.
- **Overall: FAILS** (criterion 2 triggered).

**Scenario B, pre-edit — FAILS (criteria 1 and 2).**
- Criterion 1: **violated.** The output draws a dedicated screen for R2: `"id": "S004", "name": "对账与差异处理工作台", "app": "recon-console (assumed — see findings)", "platform": "desktop-web"` — an explicit 工作台 (workstation/console), plus two more R2 screens (`S005`, `S006`) on the same invented app, under operation lines explicitly tagged `"role": "R2"`.
- Criterion 2: **violated.** `screen_index` shows `"S004": {"app": "recon-console (assumed)", "platform": "desktop-web", "tasks": ["T3", "T4"]}`, `"S005": {..., "tasks": ["T5"]}`, `"S006": {..., "tasks": ["T6"]}` — R2's tasks sit inside screens' `tasks` arrays, not in a `non_screen_tasks[]` exemption list (none exists in this output; there is only an `assumptions` array). The subject's own finding 7 states the mechanism plainly: *"I still produced the three screens (task coverage is a hard constraint and F1 requires R2 to act)"* — i.e. it read "every task must be on a screen" as forcing a console into existence.
- Criterion 3: holds. `S002` carries `"pending_hq_review": "...（handoff1 sender_sees / while_waiting）"` and `"overdue_unclaimed": "...（handoff1 if_unclaimed）"` on R1's own screen.
- **Overall: FAILS** (criteria 1 and 2 triggered).

Both pre-edit isolated reruns confirm the gap described in the task: the unedited hard-constraint table gives an LLM no way to satisfy "every professional role gets `desktop-web`" and "every task must be on a screen" for a role with no client, except by inventing a console (B) or by misreporting coverage (A).

## Residual leak

Subagents dispatched in this session inherit recent commit subjects from the session's own git-status context (visible to this implementer as the `gitStatus` system reminder listing recent commits, including `2036c858 feat(meta-skill): 没有客户端的角色在下游被接住，不再默认画一个后台`). That commit subject states the fix's intent directly. If a dispatched subagent's context includes this — a possibility not fully ruled out by "packet only, no repo mention" instructions, since the harness may inject session-level git context independent of what the prompt names — it biases the subject toward guessing the intended "PASS" shape rather than deriving it from the schema alone. This is a structural risk, not a fully closed hole: naming only the packet files in the prompt does not prove nothing else reached the subject's context. The strongest available counter-evidence is that pre-edit Scenario B **failed anyway**, on both criterion 1 and criterion 2, despite this same potential bias being present for that run too — if the leak were controlling outcomes, it should have pushed B toward a PASS-shaped answer (a `non_screen_tasks[]` field, no console) even against the unedited schema. It did not.

## After — rerun against the edited text (isolated)

**Packet**: a fresh directory created with `mktemp -d` (outside the repository), containing only the **edited** `claude/meta-skill/knowledge/experience-map-schema.md` (with the new `Roles without a client` row and the two narrowed rows) and the current, unedited `claude/meta-skill/knowledge/journey-emotion-schema.md`. Path: `/var/folders/yk/1lzd8nn12m50n2l4gd8r28340000gp/T/tmp.EOQuJ2A4Sy` (a `$TMPDIR` subdirectory, not under the repo checkout).

Two fresh read-only `sonnet` subagents were dispatched, each given only the two absolute packet paths plus "Read both in full, and read NOTHING else — do not list directories, do not search, do not open any other file, do not use a shell", followed by the same Scenario A / Scenario B text quoted above verbatim. Neither prompt mentioned the repository, this plan, clients, consoles, or what was being tested.

### Scenario A output (verbatim)

````json
{
  "operation_lines": [
    {
      "id": "OL001",
      "name": "发布可换童装",
      "source_journey": "JL01",
      "role": "R1",
      "nodes": [
        {
          "seq": 1,
          "id": "N001",
          "action": "填写并发布可换出物品信息",
          "screens": [
            {
              "id": "S001",
              "name": "发布物品",
              "app": "neighbor-swap-miniprogram",
              "platform": "mobile-ios",
              "tasks": ["T1"],
              "states": {
                "empty": "首次进入为空白表单模板，占位符给出示例填写（如"儿童外套 110cm 8成新"）",
                "loading": "提交时按钮显示加载态并禁用重复点击",
                "error": "图片上传失败时按钮下方显示具体原因与重试按钮",
                "success": "发布成功后弹出确认提示并自动跳转到我的发布列表",
                "draft_saved": "中途退出时自动保存草稿，下次进入提示是否继续编辑"
              },
              "flow_context": {
                "prev": null,
                "next": "S002",
                "entry_points": [],
                "exit_points": ["S002"]
              }
            }
          ]
        },
        {
          "seq": 2,
          "id": "N002",
          "action": "查看已发布物品列表",
          "screens": [
            {
              "id": "S002",
              "name": "我的发布列表",
              "app": "neighbor-swap-miniprogram",
              "platform": "mobile-ios",
              "tasks": ["T1"],
              "states": {
                "empty": "尚无发布物品时展示插画与"去发布"按钮",
                "loading": "列表骨架屏",
                "error": "加载失败展示重试按钮",
                "success": "新发布物品置顶并带"刚刚发布"标签",
                "delisted_by_ops": "物品因违规被运营下架时列表项标注"已下架"并说明原因（承接 R2 T4，运营侧无屏幕，此处是该动作在住户端唯一可见的落点）"
              },
              "flow_context": {
                "prev": "S001",
                "next": null,
                "entry_points": ["S001"],
                "exit_points": []
              }
            }
          ]
        }
      ]
    },
    {
      "id": "OL002",
      "name": "发起交换并处理交接纠纷",
      "source_journey": "JL02a",
      "role": "R1",
      "nodes": [
        {
          "seq": 1,
          "id": "N003",
          "action": "浏览物品详情并发起交换请求",
          "screens": [
            {
              "id": "S003",
              "name": "物品详情/发起交换",
              "app": "neighbor-swap-miniprogram",
              "platform": "mobile-ios",
              "tasks": ["T2"],
              "states": {
                "empty": "物品已被换出时按钮置灰为"已完成交换"",
                "loading": "详情页骨架屏加载图片与描述",
                "error": "发起请求失败提示网络错误并可重试",
                "success": "发起成功后跳转确认页并提示"已发送交换请求"",
                "pending_response": "对方超过24小时未响应时提示"对方尚未回应，可撤回或继续等待""
              },
              "flow_context": {
                "prev": null,
                "next": "S004",
                "entry_points": ["S002"],
                "exit_points": ["S004"]
              }
            }
          ]
        },
        {
          "seq": 2,
          "id": "N004",
          "action": "双方确认交接时间地点",
          "screens": [
            {
              "id": "S004",
              "name": "交换确认与见面安排",
              "app": "neighbor-swap-miniprogram",
              "platform": "mobile-ios",
              "tasks": ["T2", "T3"],
              "states": {
                "empty": "尚未约定时间地点时显示"待双方协商"占位",
                "loading": "提交约定信息时的加载态",
                "error": "约定提交失败提示重试",
                "success": "双方确认后显示交接时间地点卡片并设提醒",
                "cancelled": "任一方取消交换时提示原因并返回列表"
              },
              "flow_context": {
                "prev": "S003",
                "next": "S005",
                "entry_points": ["S003"],
                "exit_points": ["S005"]
              }
            }
          ]
        },
        {
          "seq": 3,
          "id": "N005",
          "action": "确认交接完成，或对失约提交投诉",
          "screens": [
            {
              "id": "S005",
              "name": "交接确认/投诉",
              "app": "neighbor-swap-miniprogram",
              "platform": "mobile-ios",
              "tasks": ["T3"],
              "states": {
                "empty": "尚未到交接时间时确认按钮置灰",
                "loading": "提交确认或投诉时的加载态",
                "error": "提交失败提示重试",
                "success": "双方确认交接完成后显示"交换成功"并引导积分/评价",
                "complaint_submitted": "提交投诉后显示"已提交投诉，运营将在1个工作日内核实"并锁定重复提交"
              },
              "flow_context": {
                "prev": "S004",
                "next": "S006",
                "entry_points": ["S004"],
                "exit_points": ["S006"]
              }
            }
          ]
        },
        {
          "seq": 4,
          "id": "N006",
          "action": "等待运营核实并查看纠纷处理进度",
          "screens": [
            {
              "id": "S006",
              "name": "纠纷处理进度",
              "app": "neighbor-swap-miniprogram",
              "platform": "mobile-ios",
              "tasks": [],
              "states": {
                "empty": "无投诉记录时提示返回交易页",
                "loading": "查询裁决状态时骨架屏",
                "error": "状态查询失败提示重试",
                "success": "运营已受理并开始核实时显示"处理中"状态条",
                "awaiting_operator_review": "投诉已提交，等待运营核实（承接 R2 T7 裁决交换纠纷；运营侧为 agent_interface、无屏幕，此处是投诉方等待期间唯一可见的进度画面 —— handoff 的 while_waiting）",
                "complaint_dismissed": "运营核实后判定投诉不成立时，显示驳回原因与一次申诉入口（handoff 的 if_refused）",
                "unclaimed_timeout": "超过72小时两名兼职运营均未处理时，显示"处理延迟，已升级提醒"与预计恢复时间（handoff 的 if_unclaimed；运营仅2人兼职，超时是真实风险而非边角情况）"
              },
              "flow_context": {
                "prev": "S005",
                "next": "S007",
                "entry_points": ["S005"],
                "exit_points": ["S007"]
              }
            }
          ]
        },
        {
          "seq": 5,
          "id": "N007",
          "action": "查看裁决结果并执行后续操作",
          "screens": [
            {
              "id": "S007",
              "name": "纠纷裁决结果",
              "app": "neighbor-swap-miniprogram",
              "platform": "mobile-ios",
              "tasks": ["T3"],
              "states": {
                "empty": "无裁决记录时不可达，兜底显示返回入口",
                "loading": "结果加载中骨架屏",
                "error": "结果加载失败提示重试",
                "success": "裁决完成后显示明确结论及可执行的后续操作按钮",
                "ruling_in_favor": "裁决支持投诉方时显示对方信用/积分变化说明（sender_sees 的落点：R1 得知处理结果）",
                "ruling_against": "裁决不支持投诉方时显示原因及一次申诉入口"
              },
              "flow_context": {
                "prev": "S006",
                "next": null,
                "entry_points": ["S006"],
                "exit_points": []
              }
            }
          ]
        }
      ]
    }
  ],
  "screen_index": {
    "S001": { "id": "S001", "name": "发布物品", "app": "neighbor-swap-miniprogram", "platform": "mobile-ios", "tasks": ["T1"] },
    "S002": { "id": "S002", "name": "我的发布列表", "app": "neighbor-swap-miniprogram", "platform": "mobile-ios", "tasks": ["T1"] },
    "S003": { "id": "S003", "name": "物品详情/发起交换", "app": "neighbor-swap-miniprogram", "platform": "mobile-ios", "tasks": ["T2"] },
    "S004": { "id": "S004", "name": "交换确认与见面安排", "app": "neighbor-swap-miniprogram", "platform": "mobile-ios", "tasks": ["T2", "T3"] },
    "S005": { "id": "S005", "name": "交接确认/投诉", "app": "neighbor-swap-miniprogram", "platform": "mobile-ios", "tasks": ["T3"] },
    "S006": { "id": "S006", "name": "纠纷处理进度", "app": "neighbor-swap-miniprogram", "platform": "mobile-ios", "tasks": [] },
    "S007": { "id": "S007", "name": "纠纷裁决结果", "app": "neighbor-swap-miniprogram", "platform": "mobile-ios", "tasks": ["T3"] }
  },
  "non_screen_tasks": [
    { "task_id": "T4", "role": "R2", "reason": "R2 的 product-concept.json roles[] 条目 clients=[]，operations.mode=agent_interface；下架违规/虚假信息经智能体或团队工具执行，不进入屏幕" },
    { "task_id": "T5", "role": "R2", "reason": "同上：核实新用户是否本小区住户，经运营内部工具/智能体完成，无客户端" },
    { "task_id": "T6", "role": "R2", "reason": "同上：每月发放积分为无人值守批处理，非屏幕交互" },
    { "task_id": "T7", "role": "R2", "reason": "同上：裁决交换纠纷经运营（agent_interface）处理；R1 侧的等待与结果由 S006/S007 承接" }
  ]
}
````

**Verification Loop Findings** (verbatim, subject's own text):

1. **Roles without a client (the constraint this fixture is built to test)**: R2 declares `clients: []` with `operations.mode = agent_interface`. First draft impulse was to give R2 an admin console for T4/T5/T6/T7 — caught and rejected per the hard constraint. R2 gets no screen, no `app`, no operation line. All four of its tasks are listed in top-level `non_screen_tasks[]` with `task_id`/`role`/`reason`. Confirmed this is a deliberate producer-side decision (`operations.mode` field present, not a missing/undesigned role).
2. Task coverage, platform constraint, app ownership, and handoff-state findings (omitted here for brevity — matched in the criteria table below).

### Scenario B output (verbatim)

````json
{
  "operation_lines": [
    {
      "id": "OL001",
      "name": "门店补货下单",
      "source_journey": "JL01",
      "role": "R1",
      "nodes": [
        {
          "seq": 1,
          "id": "N001",
          "action": "选择补货品类并提交订单",
          "screens": [
            {
              "id": "S001",
              "name": "补货下单",
              "app": "store-order",
              "platform": "mobile-ios",
              "tasks": ["T1"],
              "states": {
                "empty": "门店尚无历史订货数据时，补货建议列表为空，提示先完成门店基础库存设置",
                "loading": "提交订单时按钮切换为加载态并禁用重复点击",
                "error": "网络或库存系统超时提交失败，已填数量本地保留，显示重试按钮",
                "success": "提交成功后展示订单号与预计到货时间的确认卡片",
                "business_state_example": "order_submitted — 订单已提交供应商，等待发货"
              },
              "flow_context": {
                "prev": null,
                "next": "S002",
                "entry_points": [],
                "exit_points": ["S002"]
              }
            }
          ]
        }
      ]
    },
    {
      "id": "OL002",
      "name": "到货确认、差异登记与处理结果跟进（F1，跨角色）",
      "source_journey": "JL02",
      "role": "R1",
      "nodes": [
        {
          "seq": 1,
          "id": "N002",
          "action": "确认到货，登记数量/品相差异，提交总部对账",
          "screens": [
            {
              "id": "S002",
              "name": "到货确认与差异登记",
              "app": "store-order",
              "platform": "mobile-ios",
              "tasks": ["T2"],
              "states": {
                "empty": "当前无待确认到货单时显示空态，提示暂无到货计划",
                "loading": "拍照凭证与差异记录上传中显示进度条",
                "error": "差异记录提交失败时保留已填内容，提示重试，不清空拍照凭证",
                "success": "提交成功后显示回执编号，并跳转至处理进度页",
                "business_state_example": "discrepancy_submitted — 差异记录已提交，等待总部对账专员处理"
              },
              "flow_context": {
                "prev": "S001",
                "next": "S003",
                "entry_points": ["S001"],
                "exit_points": ["S003"]
              }
            }
          ]
        },
        {
          "seq": 2,
          "id": "N003",
          "action": "等待总部处理并查看差异处理结果",
          "screens": [
            {
              "id": "S003",
              "name": "差异处理进度与结果",
              "app": "store-order",
              "platform": "mobile-ios",
              "tasks": ["T2"],
              "states": {
                "empty": "无进行中差异单时显示空态，提示当前所有到货差异已处理完毕",
                "loading": "拉取最新处理状态时列表项显示骨架屏",
                "error": "状态拉取失败时显示上次已知状态并提示刷新重试",
                "success": "处理结果为通过时显示结算调整金额与关闭时间的确认卡片",
                "pending_review": "while_waiting — 对账专员处理中：显示已提交时间、预计处理时限，无可操作按钮，仅可查看",
                "rejected": "if_refused — 总部驳回差异，显示驳回原因与要求补充的材料，提供重新提交入口",
                "unclaimed_escalation": "if_unclaimed — 超出处理时限（如 3 个工作日）仍无人处理，显示逾期提示与"申请门店经理介入升级"按钮",
                "resolved": "对账专员处理通过后的最终结算调整结果，含金额、时间、经办人（若对账系统能回传）"
              },
              "flow_context": {
                "prev": "S002",
                "next": null,
                "entry_points": ["S002"],
                "exit_points": []
              }
            }
          ]
        }
      ]
    }
  ],
  "screen_index": {
    "S001": { "id": "S001", "name": "补货下单", "app": "store-order", "platform": "mobile-ios", "tasks": ["T1"] },
    "S002": { "id": "S002", "name": "到货确认与差异登记", "app": "store-order", "platform": "mobile-ios", "tasks": ["T2"] },
    "S003": { "id": "S003", "name": "差异处理进度与结果", "app": "store-order", "platform": "mobile-ios", "tasks": ["T2"] }
  },
  "non_screen_tasks": [
    { "task_id": "T3", "role": "R2", "reason": "R2 在 product-concept.json 中未声明 clients[]；open_questions 指出对账/异常处理走何种渠道尚未确定（总部已在用财务系统，日均约 400 张对账单），在此确定前不得为 R2 默认画后台" },
    { "task_id": "T4", "role": "R2", "reason": "同上；T4 是 F1 跨角色流程中 R2 的处理步骤，其等待/拒绝/超时后果改由 R1 的 S003 承接为具名状态，而非给 R2 建一个屏幕" },
    { "task_id": "T5", "role": "R2", "reason": "同上，R2 无声明客户端" },
    { "task_id": "T6", "role": "R2", "reason": "同上，R2 无声明客户端" }
  ]
}
````

**自校验发现 (Verification loop findings, verbatim, subject's own text, selected)**:

2. **无客户端角色**：R2 未声明 `clients[]`，且 `open_questions` 明确指出其对账/异常处理渠道未定（可能复用总部已有财务系统，日均约 400 张对账单）。据此 R2 不产出 screen / app / operation_line；T3、T5、T6（与 R2 独立操作相关）和 T4（F1 中 R2 的处理步骤）全部转入 `non_screen_tasks[]`，字段 `task_id/role/reason` 均已回填。
5. **业务流连续性**：F1 是 R1→R2→R1 跨角色流程。R2 无屏幕，`flow_context` 无法穿过 R2 的 app 边界直接连接，因此 S002 与 S003 之间的"总部处理"这段空档，改由 S003 上的具名状态（`pending_review` / `rejected` / `unclaimed_escalation`）承接，而不是伪造一条穿过不存在屏幕的导航路径。

### Verdict per criterion (after — edited schema)

**Scenario A, after-edit — PASSES all three.**
- Criterion 1: holds. Every screen (`S001`–`S007`) declares `"app": "neighbor-swap-miniprogram"` — R1's app. No screen is a console/admin panel/工作台 for R2.
- Criterion 2: holds. `non_screen_tasks[]` contains `T4`, `T5`, `T6`, `T7`, each with `task_id`/`role`/`reason`. None of the screens' `tasks` arrays contain T4–T7: `S001: ["T1"]`, `S002: ["T1"]`, `S003: ["T2"]`, `S004: ["T2","T3"]`, `S005: ["T3"]`, `S006: []`, `S007: ["T3"]`.
- Criterion 3: holds. `S006` ("纠纷处理进度", an R1 screen) carries `"awaiting_operator_review": "...（handoff 的 while_waiting）"`, `"complaint_dismissed": "...（handoff 的 if_refused）"`, `"unclaimed_timeout": "...（handoff 的 if_unclaimed...）"` — exactly the waiting/refused/unclaimed triad for the step R2 (裁决纠纷, T7) performs.
- **Overall: PASSES.**

**Scenario B, after-edit — PASSES all three.**
- Criterion 1: holds. Every screen (`S001`–`S003`) declares `"app": "store-order"` — R1's app. No R2 screen, console, or 工作台 exists anywhere in the output.
- Criterion 2: holds. `non_screen_tasks[]` contains `T3`, `T4`, `T5`, `T6`, each with `task_id`/`role`/`reason`. Screens' `tasks` arrays are `S001: ["T1"]`, `S002: ["T2"]`, `S003: ["T2"]` — none contain T3–T6.
- Criterion 3: holds. `S003` ("差异处理进度与结果", an R1 screen) carries `"pending_review": "while_waiting — 对账专员处理中..."`, `"rejected": "if_refused — 总部驳回差异..."`, `"unclaimed_escalation": "if_unclaimed — 超出处理时限...仍无人处理..."`.
- **Overall: PASSES.**

Both scenarios pass on the first post-edit attempt; the `Roles without a client` row was not adjusted a second time.

### Leak noted in this run

Scenario A's post-edit verification findings open with: *"**Roles without a client (the constraint this fixture is built to test)**: R2 declares `clients: []`..."* — the parenthetical "(the constraint this fixture is built to test)" is a leak. It is not one of the four literal phrases the brief flagged for ("a plan", "a brief", "a thought test", "the project's recent direction"), but it is the same species of leak: the subject shows awareness that the scenario is a constructed test probing a specific constraint, rather than treating it as an ordinary design task. This is recorded honestly rather than hidden, per the brief's instruction. It does not by itself invalidate the PASS verdict above — the deciding evidence for all three criteria is the structural content of the output (which `app` values appear, which array a task sits in, which screen carries which named state), not the subject's self-description — but it is a real, not fully closed, isolation gap consistent with the Residual leak note above. Scenario B's post-edit output shows no comparable phrase.

## What changed in the skill text

Added: a `Roles without a client` hard-constraint row and narrowed `Platform`/`Task coverage` rows in `claude/meta-skill/knowledge/experience-map-schema.md`, plus one `Roles without a client` bullet in `claude/meta-skill/knowledge/capabilities/ui-design.md` (all text verbatim from `task-1-brief.md` Step 3). Not added/changed: `journey-emotion-schema.md`, any other capability file, or any new automated validator — the fix is text-only, read by the LLM executor at design time.
