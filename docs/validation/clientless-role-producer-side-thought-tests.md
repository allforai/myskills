# Producer-side surface thought test

Task: "product-concept records the surface decision as a field" (`.superpowers/sdd/2026-09-22-clientless-role-producer-side-plan/task-1-brief.md`).

## What this record is

Two isolated `sonnet` subject runs, read-only, packet outside the repository, prompt naming
only the packet files (never the repository, this plan, clients, consoles, surfaces, seams,
or what is being tested): a baseline against the **unedited** `product-concept.md`, then an
identical rerun against the **edited** file in a fresh packet. Verdicts are judged literally
against the brief's fixed criteria; quoted lines below are the deciding evidence, not
paraphrase.

## Anchor counts before editing

Verified exactly once each before any edit was made:
- `` `clients[]`: array of client apps, each with `app` name, `client_type`, `platform` `` — 1
- `"parity_exceptions": ["推送通知仅限移动端", "AR 试穿仅限 iOS"]` (example block) — 1
- `` | `product-concept.json` | `roles[]`, `clients[]` | ui-design, product-verify | required | `` (Downstream Consumers table) — 1

## Prompt (identical for both runs; only the packet's `product-concept.md` content changes)

> You are an executor subagent running the `user-role-definition` node (Sub-Phase 5 of the product-concept capability). Unattended. Your method is defined by exactly two files; read both in full and read NOTHING else — do not list directories, do not search, do not open any other file, do not use a shell:
> - \<packet\>/product-concept.md
> - \<packet\>/product-design-theory.md
>
> Upstream summary (use only this):
> - 机会：连锁门店按店补货，店长凭经验报数，总部凭 Excel 汇总，供应商对账靠人工核；漏订与错发每月各十几起。
> - 用户原话（4 位店长、2 位总部采购）："我只想知道该订多少"、"对账单错了我们才发现"、"总部那边有自己的系统"。
> - 团队：3 人，其中 1 人兼做总部采购；总部已在用一套财务系统做付款与对账归档。
> - 运营事实：总部每天要核对约 400 张供应商对账单、处理十几起到货差异争议、月末出结算单、偶尔冻结异常供应商。量级上主要是核对与比对；争议裁定需要人看单据。
>
> Task: produce this product's role definition as the capability file requires — for each role its job, VPC, the producer-side closure check and the client declaration — in the exact JSON shape the file's role contract specifies. Return only the JSON and, after it, at most 8 lines of notes for the orchestrator.

Packet: `claude/meta-skill/knowledge/capabilities/product-concept.md` + `claude/meta-skill/knowledge/product-design-theory.md`, copied into a fresh `$TMPDIR` directory outside the repository (a separate fresh packet for baseline and after-edit runs).

## Baseline run (pre-edit)

### Output (verbatim)

```json
{
  "role_profiles": [
    {
      "id": "R1",
      "name": "店长",
      "evidence_source": "4 位店长访谈原话：'我只想知道该订多少'",
      "jtbd": {
        "job_statement": "当门店进入补货周期、面对多个 SKU 需要下单时，让我不必凭经验判断，就知道每个 SKU 该订多少，从而既不会因少订断货，也不会因多订/错订造成积压或被总部追责。",
        "circumstance": "门店定期补货、下单窗口临近截止",
        "would_exist_without_product": "店长仍要做出订多少的判断——这是他们原本就要完成的事，产品只是替代'凭经验'这一种满足方式"
      },
      "producer_side_closure_check": {
        "consumes": "每个 SKU 的建议补货数量",
        "who_produces": "系统/算法生成建议，不是一个人类角色；建议所依据的门店库存与历史销量数据来自何处，上游材料未交代，记为公开问题，不代入假设",
        "who_operates": "店长本人审核并确认/调整数量后提交下单，由此闭环",
        "client_mode": "screen",
        "screen_basis": "下单是不可逆决策——一旦提交即产生采购与到货成本，店长需对断货/积压结果负责；且需要店长基于本地情境（促销、货架、临期品）做判断调整。体量大或字段多本身不是理由，此处理由专指'不可逆决策+需要人的情境判断'这一条。",
        "reject_as_screen_reason_if_any": null
      },
      "vpc": {
        "jobs": ["决定每个 SKU 的补货数量", "在下单截止前完成下单"],
        "pains": [
          "凭经验报数，容易漏订或错发",
          "订多订少的后果（断货/积压）由店长承担，却缺乏依据支持判断",
          "总部与供应商的对账错误常常事后才发现，店长可能被动卷入纠纷"
        ],
        "gains": [
          "下单时有清楚、可核查的数量依据",
          "减少因判断失误导致的断货或积压",
          "下单后不必担心被动卷入事后追责"
        ],
        "pain_relievers": ["基于可得的库存/销售信息给出补货建议，替代纯经验判断（数据来源待上游确认）"],
        "gain_creators": ["下单前的数量依据留痕，出现纠纷时可追溯店长决策依据"]
      },
      "clients": [
        {
          "app": "store-order-app",
          "client_type": "flutter-mobile",
          "platform": "iOS + Android"
        }
      ],
      "feature_parity": "full",
      "platform_choice_status": "assumption_pending_confirmation — 店长为门店现场角色，移动端是行业惯例默认，未见上游对具体平台/是否已有企业自建 App 的证据，需在 tech-architecture 或 ui-design 阶段与用户确认"
    },
    {
      "id": "R2",
      "name": "总部采购",
      "evidence_source": "2 位总部采购访谈原话：'对账单错了我们才发现'；'总部那边有自己的系统'",
      "jtbd": {
        "job_statement": "当每天要核对约 400 张供应商对账单、处理到货差异争议、月末出结算单时，让我不必逐单人工核对就能知道哪些对得上、哪些对不上，只在真正需要判断的差异和供应商处理上亲自介入，而不是等对账单出错后才发现问题。",
        "circumstance": "日常对账高峰（约 400 张/天）、到货差异争议处理（十几起/月）、月末结算、偶发的供应商异常处理",
        "would_exist_without_product": "核对、裁定差异、出结算单、处理异常供应商都是总部原本就要做的事；产品替代的是'翻 Excel + 人工核对'这种满足方式"
      },
      "producer_side_closure_check": {
        "consumes": "门店订单汇总、订单/到货与供应商对账单的匹配结果、差异清单",
        "who_produces": "系统/算法完成批量匹配；门店订单本身由 R1（店长）在其下单闭环中产生",
        "who_operates": "总部采购人员对匹配不上的差异做裁定、批准月末结算单、决定是否冻结供应商",
        "client_mode": "screen",
        "screen_basis": "差异裁定、结算批准、供应商冻结是不可逆/高风险决策，操作人需要对结果负责，且要看单据做判断——这是名副其实的判断步骤。约 400 张/天的核对体量本身不构成开屏的理由，那部分应由系统自动匹配完成，只把匹配不上的差异呈现给人。",
        "reject_as_screen_reason_if_any": "'400 张/天体量大' 和 '本质是 CRUD/多字段' 均被排除在开 screen 的理由之外，仅供参考，不作为本角色 screen 的依据",
        "existing_tool_note": "总部已有一套财务系统做付款与对账归档；本产品的差异裁定/冻结画面是否并入该系统还是独立新建，上游材料未交代，记为公开问题，留给 tech-architecture/infra-design 阶段与用户确认"
      },
      "vpc": {
        "jobs": [
          "核对每日约 400 张供应商对账单是否与订单/到货一致",
          "裁定到货差异争议（十几起/月）",
          "出具月末结算单",
          "识别并冻结异常供应商"
        ],
        "pains": [
          "人工核对量大（约 400 张/天），错误往往等出问题（如供应商投诉、金额不符）后才被发现",
          "各门店经 Excel 汇总，口径不一致、易出错",
          "总部已有财务系统做付款与对账归档，但缺少前置的自动匹配/核对能力，仍要人工比对",
          "争议裁定依赖人工翻单据，耗时"
        ],
        "gains": [
          "系统提前标出对不上的单据，不必逐张人工核对",
          "把人力集中在真正需要判断的差异和供应商处理上",
          "月末结算数字有底，不靠临时汇总拼凑"
        ],
        "pain_relievers": ["自动匹配订单、到货与供应商对账单，仅把差异项呈现给人工"],
        "gain_creators": ["差异处理与供应商冻结的决策留痕，支持结算与后续追溯"]
      },
      "clients": [
        {
          "app": "hq-reconciliation-console",
          "client_type": "react-spa",
          "platform": "Desktop web"
        }
      ],
      "feature_parity": "full",
      "platform_choice_status": "assumption_pending_confirmation — 总部后台核对/裁定工作按行业惯例默认桌面端，未见上游对具体平台的证据，需在 tech-architecture 或 ui-design 阶段与用户确认"
    }
  ],
  "vpc_per_role": {
    "R1": "见 role_profiles[0].vpc（店长）",
    "R2": "见 role_profiles[1].vpc（总部采购）"
  },
  "open_questions": [
    "店长补货建议所依据的库存/历史销量数据来源未在上游材料中交代，需回到 problem-discovery 或用户确认",
    "供应商是否会直接向产品提交发货/对账信息，尚无访谈证据支持——本轮未声明供应商为客户端角色，避免无据造角色",
    "两个角色的客户端平台（移动端具体形态、桌面端是否已有内部系统可扩展）均为行业惯例假设，非上游证据，待确认",
    "总部差异裁定/冻结画面与既有财务系统的集成方式（并入 vs 独立）未定，留给下游技术设计阶段"
  ]
}
```

Notes for orchestrator (verbatim):

> - Two roles surfaced from evidence only: 店长 (R1, consumer+operator of order suggestions) and 总部采购 (R2, consumer+operator of matching/dispute/settlement/freeze). No supplier role declared — no evidence suppliers touch the product directly.
> - Both roles pass the producer-side closure check into `screen`, not by volume/CRUD (explicitly rejected as a basis) but by an irreversible decision the operator answers for (order submission; discrepancy ruling, settlement approval, supplier freeze) plus a named judgment step.
> - The 400/day statement volume itself is assigned to system/agent matching, not to a human screen — only the flagged exceptions reach R2's client.
> - 4 open questions recorded rather than silently assumed: order-suggestion data source, no supplier client, both client platform choices (mobile/desktop are convention defaults, not evidenced), and whether R2's screen extends the existing finance system or is standalone.
> - `clients[]`/`client_type` values chosen are flagged `assumption_pending_confirmation` per role for downstream tech-architecture/ui-design to confirm with the user rather than silently lock in.

### Verdict: PASS anyway (not the expected FAIL) — recorded per the brief's instruction

The brief's FAIL criteria: *"FAIL if the operations/HQ role's JSON has no field that names its mode and ground (prose in the notes does not count — the field must be in the role object), or if it receives a `clients[]` entry with a desktop console without a named step someone must look at."*

Checking R2 (总部采购, the HQ role) against both clauses:

1. **Field naming mode + ground, in the role object**: R2's role object carries
   `"producer_side_closure_check": { ..., "client_mode": "screen", "screen_basis": "..." , ... }`
   — this is a field in the role object (not prose in the trailing notes), and it names
   both the mode (`"client_mode": "screen"`) and the ground (`"screen_basis": "差异裁定、
   结算批准、供应商冻结是不可逆/高风险决策，操作人需要对结果负责，且要看单据做判断——这是
   名副其实的判断步骤。..."`). This clause does **not** trigger FAIL.

2. **`clients[]` desktop console without a named step**: R2 does receive a `clients[]`
   entry — `{"app": "hq-reconciliation-console", "client_type": "react-spa", "platform":
   "Desktop web"}` — but it comes with a named step someone must look at, quoted from the
   same `screen_basis` line above: *"差异裁定、结算批准、供应商冻结是不可逆/高风险决策...
   且要看单据做判断"*. This clause does **not** trigger FAIL either.

Neither FAIL condition fires, so the literal verdict is **PASS** — the unedited contract
did not FAIL this baseline, contrary to the brief's stated expectation ("the expected result
is FAIL: the contract has no such field today").

**Why this is not evidence against adding the field** (per the brief's own fallback: *"If it
passes anyway, still proceed — the field is what makes the decision checkable downstream
(ADR-0010 criterion 2), and say so in the record"*): the unedited contract has no named,
contract-defined field for this decision. `producer_side_closure_check.client_mode` /
`.screen_basis` are field names this particular strong subject invented on its own, because
the prompt (mirroring the current step 5 prose) explicitly asked it to "produce ... the
producer-side closure check" as part of the output without specifying a schema for it. A
different run, a different model, or a weaker subject has no guarantee of reproducing this
same field name or shape — there is nothing in the contract compelling `client_mode` over
`operations_mode`, `channel`, `surface_decision`, or any other ad hoc name, or compelling the
decision to be structured data at all rather than folded into prose. That is exactly the gap
ADR-0010 criterion 2 names: a decision downstream can check needs a contract-guaranteed field,
not a field a sufficiently capable subject happens to invent this run. Proceeding to Step 3
per the brief.

## After-edit run (post-edit, fresh packet against the edited `product-concept.md`)

### Output (verbatim)

```json
{
  "sub_phase": "user-role-definition",
  "theory_anchors": ["JTBD", "VPC", "Mom Test"],
  "roles": [
    {
      "id": "R1",
      "name": "店长",
      "job": "当到了该给门店补货的时候，我需要知道这次该订多少，这样门店不会因为少订而断货，也不会因为多订/订错被总部追问。",
      "job_evidence": "原话：'我只想知道该订多少'（4 位店长）；现状：'店长凭经验报数'；后果：'漏订与错发每月各十几起'",
      "vpc": {
        "jobs": ["判断本次补货该订多少", "把订货数报给总部"],
        "pains": [
          "凭经验报数，没有依据可核对",
          "漏订导致门店断货，责任落在自己身上",
          "订多/订错导致门店积压或被总部质疑"
        ],
        "gains": ["报数时心里有底", "报错的概率和被追责的风险降低"],
        "pain_relievers": ["基于门店历史出货/消耗给出建议订货量，报数前能看到依据"],
        "gain_creators": ["报数留痕，减少后续总部 Excel 汇总环节的二次核对分歧"]
      },
      "producer_side_closure": {
        "consumes": "该报多少的建议依据（系统产出，非人工角色）",
        "produces": "本店本轮订货数量，供总部采购/对账消费（进入 Excel 汇总与后续对账）",
        "operates": "店长本人报数并对报出的数字负责",
        "note": "店长既是'该订多少'这个问题的消费者，也是订货数据的生产者；下游消费者是 R2。"
      },
      "surface": {
        "mode": "screen",
        "basis": "'我只想知道该订多少'——店长要看着建议订货量做判断、报出数字，且要为漏订/错发的后果负责，这是店长必须亲自过目确认的一步，不是可以交给 agent 静默完成的事务"
      },
      "clients": [
        { "app": "store-order-web", "client_type": "react-spa", "platform": "mobile-web" }
      ],
      "feature_parity": "full",
      "client_confidence_note": "无证据说明店长实际使用的设备/平台；此处按'团队 3 人，其中 1 人兼职'这一团队规模事实，推荐免安装、免维护的移动端 web 作为默认项，需在下一轮结构化确认中让用户选择或推翻。"
    },
    {
      "id": "R2",
      "name": "总部采购/对账人员",
      "job": "每天几百张供应商对账单和门店订货数据到齐时，我需要又快又准地把能对上的核完、把对不上的挑出来处理，这样月末结算单不会出错，异常供应商也不会因为没被发现而继续出问题。",
      "job_evidence": "原话：'对账单错了我们才发现'、'总部那边有自己的系统'；量级事实：'总部每天要核对约 400 张供应商对账单，处理十几起到货差异争议，月末出结算单，偶尔冻结异常供应商'；现状：'总部凭 Excel 汇总'",
      "vpc": {
        "jobs": ["核对约 400 张供应商对账单/天", "裁定十几起到货差异争议", "月末出结算单", "偶尔冻结异常供应商"],
        "pains": [
          "现在靠 Excel 人工汇总核对，出错要等问题发生后才发现",
          "差异争议要靠人工翻单据裁定，耗时且依赖经验",
          "异常供应商的识别没有系统依据，全凭经验"
        ],
        "gains": ["对上的账不用逐张人工核，只处理挑出来的差异", "结算单出错率下降", "异常供应商能更早被发现"],
        "pain_relievers": ["自动匹配 400 张对账单里能对上的部分，只把对不上的交给人裁定", "差异争议时把相关单据证据集中呈现，减少翻找"],
        "gain_creators": ["结算单生成时带核对依据，可追溯", "冻结供应商的决定有据可查，不再纯凭经验"]
      },
      "producer_side_closure": {
        "consumes": "供应商对账单、门店订货/收货数据",
        "produces": "差异裁定结果、月末结算单、供应商冻结决定",
        "operates": "总部采购人员本人（团队 3 人中 1 人兼职），差异裁定和冻结这类步骤需要人看单据、担责任",
        "note": "对账单的生产方是供应商，本产品目前没有证据支持供应商会直接接入任何界面（见 R3）；这一条产消链在供应商一侧仍走现有的人工提交渠道。"
      },
      "surface": {
        "mode": "undecided",
        "basis": "'总部那边有自己的系统'——总部已在用一套财务系统做付款与对账归档，差异裁定/冻结供应商这类需要人看单据、担责任的步骤是否已经、或应该落在这套系统里，现有证据未说清楚",
        "open_question": "差异裁定和冻结供应商这些需要人核实、担责任的步骤，是接进总部现有的财务系统，还是新开一个界面？"
      }
    },
    {
      "id": "R3",
      "name": "供应商",
      "job": "unknown — 本轮访谈只覆盖 4 位店长、2 位总部采购，没有供应商的原话或行为事实",
      "vpc": {
        "status": "insufficient_evidence",
        "note": "按 Mom Test 原则，不能用总部对供应商的转述（如'对账单错了我们才发现'）去推断供应商自己的 Jobs/Pains/Gains；那是总部的痛点，不是供应商的。"
      },
      "producer_side_closure": {
        "consumes": "unknown",
        "produces": "对账单、发货数据（R2 消费的上游数据）",
        "operates": "现状是供应商侧仍走人工核对（'供应商对账靠人工核'），未见证据表明供应商会使用本产品任何界面",
        "note": "识别为 R2 的产出方，但因缺少供应商侧证据，不展开为完整角色定义，转为面向用户的开放问题。"
      },
      "surface": {
        "mode": "undecided",
        "basis": "'供应商对账靠人工核'——现状是人工核对，没有证据显示供应商需要或将会接入本产品的任何界面",
        "open_question": "要不要为供应商开放提交对账单/发货数据的接口，还是维持现状、由总部单方录入？这需要向供应商侧核实后才能决定，本轮访谈未覆盖供应商。"
      }
    }
  ]
}
```

Notes for orchestrator (verbatim):

> - R2 的 surface 直接对应 capability 文件里给出的示例场景（总部已用财务系统做付款与对账归档），按示例判为 undecided，而非因"争议需要人看单据"就默认判 screen——人工判断的必要性不等于渠道已确定。
> - R1 的 client_type/platform 是弱证据推断（仅凭团队规模 3 人），需要在下一轮结构化确认中让用户选择或推翻，不要静默当作已定。
> - R3（供应商）刻意未展开完整 JTBD/VPC，因为访谈样本（4 店长 + 2 总部采购）不含供应商声音；按 Sub-Phase 1 acceptance 的"cause unknown 需点名从哪里能拿到答案"原则处理，而非编造。
> - 两处 open_question 都需要在后续交互轮次中交给用户裁定，不能由本节点替用户拍板。
> - errc/positioning 等下游节点如需要 roles[].surface，可直接读本文件的 surface 字段，不用从 clients[] 有没有去猜。

### Verdict: PASS

The brief's PASS criteria: *"PASS only if every role object carries `surface` with a valid
`mode`, the HQ role's mode is `existing_tool` or `undecided` (not `screen`) with a `basis`
that quotes the upstream summary, and an `undecided` role carries `open_question`."*

- **Every role carries `surface` with a valid mode**: R1 `"surface": {"mode": "screen", ...}`,
  R2 `"surface": {"mode": "undecided", ...}`, R3 `"surface": {"mode": "undecided", ...}`. All
  three modes are members of `screen | agent_interface | existing_tool | undecided`.
- **HQ role's mode is not `screen`, with a basis quoting the upstream summary**: R2 (总部采购/
  对账人员) carries `"mode": "undecided"`, with
  `"basis": "'总部那边有自己的系统'——总部已在用一套财务系统做付款与对账归档，..."` — the quoted
  fragment `总部那边有自己的系统` is copied verbatim from the upstream summary's
  `用户原话（... 2 位总部采购）："...""总部那边有自己的系统""` line.
- **The `undecided` role carries `open_question`**: R2's surface carries
  `"open_question": "差异裁定和冻决供应商这些需要人核实、担责任的步骤，是接进总部现有的财务系统，
  还是新开一个界面？"`; R3's surface likewise carries its own `open_question`.

All three clauses hold. **PASS.** No rerun needed (the brief only calls for a rerun on
failure).

## Leak check

Neither subject's notes mention a plan, a test, a fixture, "the project's recent direction,"
the repository, or this task — no leak in either run. The after-edit subject's note that R2's
surface "直接对应 capability 文件里给出的示例场景" refers to the example block it just read
inside the packet's `product-concept.md` (which is in scope — it was told to read that file
in full), not to any external plan or prior run.

## Pipeline test (role-profiles.json only)

Task: "The receiving side keys off the field, and the real-pipeline test passes"
(`.superpowers/sdd/2026-09-22-clientless-role-producer-side-plan/task-3-brief.md`).

Unlike the two producer-side runs above (which fed `product-concept.md` as method to a
role-definition subject), this test feeds the artifact the real experience-map node actually
receives: the edited `experience-map-schema.md` (post Step 1 of this task), the current
`journey-emotion-schema.md`, and a `role-profiles.json` written for this test in the shape
Task 2's schema defines — `id`, `name`, `permissions`, `audience_type`, `surface`. The subject
is never given `product-concept.json`; the point of the test is that `role-profiles.json`
alone carries the decision downstream. Two isolated `sonnet` subject runs, read-only, each
packet built outside the repository (`mktemp -d` under `$TMPDIR`), prompt naming only the
packet files (never the repository, this plan, clients, consoles, surfaces, seams, or what is
being tested). The two packets are identical except for `role-profiles.json`: Run 1 gives R2 a
full `surface` object (`mode: "undecided"`); Run 2 (control) removes `surface` from R2 entirely.

### Packet `role-profiles.json` — Run 1 (pipeline test)

```json
{
  "roles": [
    {
      "id": "R1",
      "name": "采购员（门店下单的人）",
      "permissions": ["按门店提交补货单", "确认到货并登记差异"],
      "audience_type": "operator",
      "surface": {
        "mode": "screen",
        "basis": "店长凭经验报数，需要逐步填单并核对到货，用 store-order（react-native，mobile）客户端操作"
      }
    },
    {
      "id": "R2",
      "name": "供应商对账专员（总部，3人）",
      "permissions": ["核对供应商对账单", "处理到货差异争议", "月末出具结算单", "冻结异常供应商"],
      "audience_type": "operator",
      "surface": {
        "mode": "undecided",
        "basis": "总部已在用一套财务系统做付款与对账归档",
        "open_question": "对账与差异处理是接进现有财务系统，还是另开界面？"
      }
    }
  ]
}
```

### Packet `role-profiles.json` — Run 2 (control, no `surface` on R2)

```json
{
  "roles": [
    {
      "id": "R1",
      "name": "采购员（门店下单的人）",
      "permissions": ["按门店提交补货单", "确认到货并登记差异"],
      "audience_type": "operator",
      "surface": {
        "mode": "screen",
        "basis": "店长凭经验报数，需要逐步填单并核对到货，用 store-order（react-native，mobile）客户端操作"
      }
    },
    {
      "id": "R2",
      "name": "供应商对账专员（总部，3人）",
      "permissions": ["核对供应商对账单", "处理到货差异争议", "月末出具结算单", "冻结异常供应商"],
      "audience_type": "operator"
    }
  ]
}
```

### Prompt (identical for both runs; only the packaged `role-profiles.json` changes)

> Read these files in full, and read NOTHING else — do not list directories, do not search,
> do not open any other file, do not use a shell:
> - \<packet\>/experience-map-schema.md
> - \<packet\>/journey-emotion-schema.md
> - \<packet\>/role-profiles.json
>
> Follow the first two files as your method. The third file is your role data for this run.
>
> `task-inventory.json` (excerpt): T1 R1 按门店补货下单 · T2 R1 确认到货并登记差异 · T3 R2 核对供应商对账单 · T4 R2 处理到货差异争议 · T5 R2 月末出具结算单 · T6 R2 冻结异常供应商
> One business flow: F1 (cross_role): R1 确认到货并登记差异 → R2 处理到货差异争议 → R1 看到处理结果
>
> Task: produce the experience-map for this product as you would ship it — operation_lines, the screens with `id`, `app`, `platform`, `tasks`, `states`, and any top-level fields you need — then the findings of your own verification loop. No commentary outside those two parts. Keep screens compact (id, name, app, platform, tasks, states, flow_context only).

Packet: `claude/meta-skill/knowledge/experience-map-schema.md` (edited, this task's Step 1) +
`claude/meta-skill/knowledge/journey-emotion-schema.md` (unedited) + the `role-profiles.json`
above, copied into a fresh `$TMPDIR` directory outside the repository (a separate fresh packet
per run).

### Run 1 output (verbatim) — role-profiles.json carries R2's `surface`

```json
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
          "action": "按门店提交补货单",
          "screens": [
            {
              "id": "S001",
              "name": "补货下单",
              "app": "store-order",
              "platform": "mobile-ios",
              "tasks": ["T1"],
              "states": {
                "empty": "尚无本轮补货记录时显示引导插画与「新建补货单」按钮",
                "loading": "门店历史订货基线加载中，显示表单骨架屏",
                "error": "提交失败（网络中断或库存服务异常）时显示具体错误原因、重试按钮与「保存草稿」选项",
                "success": "提交成功后显示确认吐司，并跳转到差异登记入口待用",
                "draft_saved": "草稿保存中/已保存，允许稍后继续编辑再提交"
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
      "name": "到货确认与差异处理跟进（含总部处理等待）",
      "source_journey": "JL02",
      "role": "R1",
      "nodes": [
        {
          "seq": 1,
          "id": "N002",
          "action": "确认到货并登记差异",
          "screens": [
            {
              "id": "S002",
              "name": "到货确认与差异登记",
              "app": "store-order",
              "platform": "mobile-ios",
              "tasks": ["T2"],
              "states": {
                "empty": "尚未扫码/录入到货清单时显示「开始核对到货」引导",
                "loading": "到货清单逐行比对中，显示骨架屏进度",
                "error": "数量/条码校验失败时定位到具体行并给出更正提示",
                "success": "登记完成后显示差异摘要卡片与「提交至总部」反馈",
                "discrepancy_flagged": "已标记数量/质量差异，等待用户确认提交"
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
          "action": "提交后跟进差异处理进度，查看总部处理结果",
          "screens": [
            {
              "id": "S003",
              "name": "差异处理进度",
              "app": "store-order",
              "platform": "mobile-ios",
              "tasks": ["T2"],
              "states": {
                "empty": "无待跟进差异时显示「暂无差异案例」占位说明",
                "loading": "处理状态刷新中，显示进度条骨架",
                "error": "状态同步失败时显示重试按钮与最近一次已知状态（离线缓存）",
                "success": "案例关闭时显示裁定结果与门店确认按钮",
                "pending_review": "已提交，等待总部对账专员处理——显示「审核中」标签与预计处理时限（对应 while_waiting）",
                "disputed_returned": "总部对账专员驳回差异认定、要求补充凭证——显示驳回原因与重新提交入口（对应 if_refused）",
                "unclaimed_timeout": "超过约定时限（如48小时）无人认领——显示升级提醒与「催办」按钮（对应 if_unclaimed）",
                "resolved": "差异已裁定——显示裁定结果、涉及金额/数量调整明细"
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
  "non_screen_tasks": [
    {
      "task_id": "T3",
      "role": "R2",
      "reason": "总部已在用一套财务系统做付款与对账归档 — 对账与差异处理是接进现有财务系统，还是另开界面？"
    },
    {
      "task_id": "T4",
      "role": "R2",
      "reason": "总部已在用一套财务系统做付款与对账归档 — 对账与差异处理是接进现有财务系统，还是另开界面？"
    },
    {
      "task_id": "T5",
      "role": "R2",
      "reason": "总部已在用一套财务系统做付款与对账归档 — 对账与差异处理是接进现有财务系统，还是另开界面？"
    },
    {
      "task_id": "T6",
      "role": "R2",
      "reason": "总部已在用一套财务系统做付款与对账归档 — 对账与差异处理是接进现有财务系统，还是另开界面？"
    }
  ]
}
```

Verification Loop Findings (verbatim):

> 1. **Platform constraint (schema Hard Constraints §Platform)** — R1 declares a client explicitly in `surface.basis` ("store-order（react-native，mobile）客户端"), so S001–S003 are `mobile-ios` / `app: "store-order"`. R2's `surface.mode` is `undecided` (not `screen`), so it correctly gets **no screens, no app, no operation line** — pass.
> 2. **Judgment call flagged, not silently resolved** — R1's `audience_type` is `"operator"`, which under a literal reading of "professional role → desktop-web" could suggest a backend console. I overrode that with the `surface.basis` text, which is the authoritative signal (product-concept already decided the client) — the rule's rationale is explicit that `audience_type`/role labels must not override a recorded `surface` decision. Flagging this as a judgment call rather than a silent default.
> 3. **App ownership** — All three screens carry `app: "store-order"`, derived from node role R1 in both operation lines (no cross-role screen exists to test the "node role, not operation-line role" branch, since R2 never gets a screen) — pass.
> 4. **Task coverage** — T1→S001, T2→S002+S003, T3/T4/T5/T6→`non_screen_tasks[]`. All 6 task-inventory IDs accounted for exactly once or via non-screen exemption — pass.
> 5. **Business flow continuity (F1: R1→R2→R1)** — R1's own leg (submit differences → check outcome) is navigable via `flow_context` S002→S003. The R2 leg intentionally has no `flow_context`/screen, since R2 is clientless — this is the correct outcome per the schema, not a broken link.
> 6. **Handoff states** — Modeled the F1 handoff (R1 hands a discrepancy to R2, then R1 sees the result) entirely on **S003**, the screen the waiting role (R1) actually has open: `pending_review` = while_waiting, `disputed_returned` = if_refused, `unclaimed_timeout` = if_unclaimed, `resolved`/`success` = the return leg. No console was drawn for R2 to hold these instead — pass.
> 7. **Journey-line completeness** — R2's implied journey lines (T3–T6) have no operation_line; this is exactly the exemption the schema allows, and it is recorded in `non_screen_tasks[]` together with the unresolved `open_question` about whether to build inside the existing finance system — pass, but **this is a real open decision, not a resolved one**: T3–T6 have no interface design at all until a human answers it.
> 8. **Gap I'm disclosing rather than papering over**: no actual `journey-emotion-map.json` was provided (only its schema, as method) — I could not run the schema's four-point emotion-arc validation, and I did not fabricate emotion data to fill it. `source_journey` values (`JL01`, `JL02`) are therefore provisional placeholders, not references to a real upstream artifact.
> 9. **Risk/reversibility check** — T2's discrepancy submission is a dispute over goods/money between two orgs, plausibly `risk=high`; S003 gives it explicit protection (retry on sync failure, reversible via `disputed_returned` re-submission path, escalation via `unclaimed_timeout`) even without a formal risk annotation to validate against.

### Verdict: PASS

The brief's PASS criteria: *"PASS only if: no screen has R2's app or is a console for R2;
T3–T6 are in `non_screen_tasks[]` with `reason` quoting the `basis` and the `open_question`;
R1's waiting/refused/unclaimed states for the R2 step exist on an R1 screen."*

- **No screen has R2's app or is a console for R2**: all three screens (`S001`, `S002`, `S003`)
  carry `"app": "store-order"` and sit under role-R1 operation lines; the subject's own finding
  1 states R2 "correctly gets **no screens, no app, no operation line**".
- **T3–T6 in `non_screen_tasks[]` with `reason` quoting `basis` and `open_question`**: all four
  entries carry
  `"reason": "总部已在用一套财务系统做付款与对账归档 — 对账与差异处理是接进现有财务系统，还是
  另开界面？"` — the first clause is `role-profiles.json`'s R2 `surface.basis` verbatim, the
  second is R2 `surface.open_question` verbatim.
- **R1's waiting/refused/unclaimed states for the R2 step exist on an R1 screen**: `S003`
  (app `store-order`, role R1) carries `"pending_review"` (labelled "对应 while_waiting"),
  `"disputed_returned"` ("对应 if_refused"), and `"unclaimed_timeout"` ("对应 if_unclaimed"),
  confirmed by finding 6: *"Modeled the F1 handoff ... entirely on **S003**, the screen the
  waiting role (R1) actually has open ... No console was drawn for R2 to hold these instead."*

All three clauses hold. **PASS.** No rerun needed.

### Run 2 output (verbatim) — control, R2 has no `surface` at all

```json
{
  "operation_lines": [
    {
      "id": "OL001",
      "name": "门店补货下单",
      "source_journey": "JL00",
      "role": "R1",
      "nodes": [
        {
          "seq": 1,
          "id": "N001",
          "action": "选择门店与商品并提交补货单",
          "screens": [
            {
              "id": "S001",
              "name": "补货下单",
              "app": "store-order",
              "platform": "mobile-ios",
              "tasks": ["T1"],
              "states": {
                "empty": "尚无补货草稿，显示空白单据插画 + “新建补货单”入口",
                "loading": "商品与门店库存列表骨架屏加载",
                "error": "提交失败提示网络异常，保留已填数量并可重试",
                "success": "提交成功 toast，返回单据列表并高亮新单",
                "draft_saved": "本地暂存草稿，可关闭 App 后继续编辑"
              },
              "flow_context": {
                "prev": null,
                "next": null,
                "entry_points": [],
                "exit_points": ["S003"]
              }
            }
          ]
        }
      ]
    },
    {
      "id": "OL002",
      "name": "到货确认与差异跟踪（F1・R1 侧）",
      "source_journey": "JL01a",
      "role": "R1",
      "nodes": [
        {
          "seq": 1,
          "id": "N001",
          "action": "确认到货并登记差异",
          "screens": [
            {
              "id": "S003",
              "name": "到货确认登记",
              "app": "store-order",
              "platform": "mobile-ios",
              "tasks": ["T2"],
              "states": {
                "empty": "无待确认到货记录，显示“暂无到货”插画并可返回补货单查看进度",
                "loading": "到货单据骨架屏加载",
                "error": "提交失败提示网络重试，保留已登记差异数量",
                "success": "提交成功 toast，跳转至差异处理结果页",
                "submitted_to_hq": "差异已提交总部对账专员，展示流水号与预计处理时限"
              },
              "flow_context": {
                "prev": "S001",
                "next": "S004",
                "entry_points": ["S001"],
                "exit_points": ["S004"]
              }
            }
          ]
        },
        {
          "seq": 2,
          "id": "N002",
          "action": "查看差异处理结果",
          "screens": [
            {
              "id": "S004",
              "name": "差异处理结果",
              "app": "store-order",
              "platform": "mobile-ios",
              "tasks": ["T2"],
              "states": {
                "empty": "尚无处理记录，显示“等待总部处理”提示",
                "loading": "结果详情骨架屏加载",
                "error": "结果加载失败，提供重试",
                "success": "处理结果明细展示（调整后到货数量、差异原因核定）",
                "processing": "总部专员处理中：展示预计时限与“催办”按钮（handoff while_waiting，等待 R2）",
                "resolved": "差异已按总部核定结果调整，展示明细与确认按钮",
                "rejected": "总部驳回本次登记，展示驳回理由与再次申诉入口（handoff if_refused）",
                "escalated_unclaimed": "超时未处理，自动升级提醒门店并展示升级状态（handoff if_unclaimed）"
              },
              "flow_context": {
                "prev": "S003",
                "next": null,
                "entry_points": ["S003"],
                "exit_points": []
              }
            }
          ]
        }
      ]
    }
  ]
}
```

No screens are produced for T3（核对供应商对账单）、T4（处理到货差异争议）、T5（月末出具结算单）、
T6（冻结异常供应商），and no `non_screen_tasks[]` entry is written for them either.

Verification Loop Findings (verbatim):

> 1. **Blocking defect, not a design decision — R2 has no `surface` field at all.**
>    `role-profiles.json` gives R1 a full `surface` object (`mode: "screen"`, `basis`: the
>    store-order mobile client), but R2's entry stops at `audience_type` — no `surface` key at
>    all. Per the schema's Hard Constraints table: *"A role with no `surface` at all is missing
>    upstream data, not a decision: stop and return it as an upstream defect rather than
>    exempting its tasks or drawing it a console."* I followed that literally: I did not
>    default R2 to a desktop-web admin console (the common backend-role default), and I did
>    not fold T3–T6 into `non_screen_tasks[]` (that array is defined only for roles whose
>    `surface.mode` is a resolved `agent_interface | existing_tool | undecided`, which R2 is
>    not — R2's mode is simply absent). Both moves would have invented a decision that belongs
>    upstream in product-concept.
> 2. **Task coverage constraint is knowingly violated, not silently patched.** T3, T4, T5, T6
>    appear in no screen's `tasks[]` and in no `non_screen_tasks[]` entry. This fails the
>    schema's Task Coverage constraint by design — flagging the gap is the correct behavior
>    here, closing it without upstream data would not be.
> 3. **F1 is only half-built.** ... The R2 half (`JL01b`, task T4) can't be designed at all.
> 4. **Emotion validation loop couldn't run.** No `journey-emotion-map.json` content was
>    provided (only its schema) — I left `emotion_design` off every screen rather than
>    inventing emotions, intensities, or risk levels.
> 5. **Business flow continuity.** Within R1's own screens the chain is intact and navigable:
>    S001 → S003 → S004.
> 6. **Platform.** R1's `surface.basis` names a `react-native, mobile` client (`store-order`),
>    mapped to `mobile-ios` directly from the stated client, not from `audience_type`.
> 7. **Compact-screen instruction, not an omission.** `layout_type`, `components`,
>    `data_fields` etc. were deliberately left out per the "keep screens compact" instruction.
>
> **Net: this experience-map is not shippable as-is.** It's complete and internally consistent
> for R1 (T1, T2, and the R1-visible half of F1's handoffs), but T3/T4/T5/T6 and R2's entire
> surface are an open upstream defect — role-profiles.json needs a `surface` object for R2
> (mode + basis, à la R1's) before OL002 can be finished and before OL003+ ... can be designed
> at all.

### Verdict: PASS

The brief's PASS criteria for the control run: *"PASS only if it returns an upstream defect
and neither draws a console nor exempts."*

- **Returns an upstream defect**: quoting the subject's own finding 1, *"R2 has no `surface`
  field at all ... stop and return it as an upstream defect"*, and its closing line, *"this
  experience-map is not shippable as-is ... T3/T4/T5/T6 and R2's entire surface are an open
  upstream defect"*.
- **Does not draw a console**: quoting the same finding, *"I did not default R2 to a
  desktop-web admin console (the common backend-role default)"* — and indeed no R2 screen,
  app, or operation line appears anywhere in the output.
- **Does not exempt**: quoting the same finding, *"I did not fold T3–T6 into
  `non_screen_tasks[]`"* — and indeed `non_screen_tasks[]` is entirely absent from the output;
  T3–T6 appear in no screen and no exemption list, an openly flagged Task Coverage failure
  (finding 2) rather than a silently accepted gap.

All clauses hold. **PASS.** No rerun needed.

### Leak check

Neither subject's output mentions a plan, a test, a fixture, "the project's recent direction,"
the repository, or this task. Run 1's finding 2 ("judgment call flagged, not silently
resolved") and Run 2's closing summary both read as the subject's own verification-loop
reasoning against the packaged schema text, not as knowledge of an external plan or prior run.
No leak in either run.
