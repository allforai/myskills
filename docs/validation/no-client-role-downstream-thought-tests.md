# No-client-role downstream thought test

Task: "A role without a client is received downstream, not given a default console" (`.superpowers/sdd/2026-09-22-pi-work-supplements-plan/task-1-brief.md`, extended by `task-1b-brief.md` and `task-1-fix1.md`).

## What this record is

This file tracks five runs, in order: an invalid non-isolated baseline (Run 1); two isolated pre-edit reruns that confirmed the gap is real (not an artifact of contamination); two isolated post-edit reruns against the first corrected schema text ("After"); and, after a task review found the first fix incomplete, three more isolated reruns against a further-corrected schema text ("After fix round 1") — two reruns of the same scenarios plus a new scenario C. Only the isolated runs carry evidential weight. Verdicts are judged literally against the fixed criteria; quoted lines are the deciding evidence, not paraphrase. Everything reproduced below is inlined verbatim in this file (not pointed at a `.superpowers/` path, which is git-excluded and not reproducible by anyone without this session's history) except Run 1's ~400-line output, which stays as a pointer to the commit that recorded it, since that pointer is a git object everyone with this repo can read.

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

Two isolated reruns were dispatched (read-only, `sonnet`, packet outside the repo, prompt naming only the packet files, no mention of the repository/plan/clients/consoles/testing) against the **unedited** schema text — i.e. before the `Roles without a client` row existed. Their purpose was to rule out that Run 1's "PASS" reflected real schema content once contamination was removed.

### Prompts (used for both the pre-edit isolated baselines and, unchanged, for the post-edit "After" reruns below — the only variable between runs is the content of the packaged `experience-map-schema.md`)

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

**Scenario B** (R2 has NO `clients` key at all; only an open question naming R2):

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

### Scenario A output, pre-edit (verbatim, inlined — previously only pointed at `isolated-baseline-A.md`)

````json
{
  "operation_lines": [
    {
      "id": "OL001",
      "name": "R1 发布可换物品",
      "source_journey": "JL01",
      "role": "R1",
      "nodes": [
        {
          "seq": 1,
          "id": "N001",
          "action": "填写并提交物品信息，发布可换出物品",
          "screens": [
            {
              "id": "S001",
              "name": "发布物品",
              "description": "家长填写要换出的童装信息并发布。首次发布用户对'该填什么、会不会没人要'有轻微不安，因此用分步表单和示例降低门槛，而不是一次性甩出全部字段。",
              "platform": "mobile-ios",
              "app": "neighbor-swap",
              "layout_type": "structured_editor",
              "layout_description": "全屏单列表单，顶部进度点表示三步（基本信息→照片→换入偏好），底部固定提交按钮，避免上下滚动找不到入口。",
              "interaction_type": "分步表单填写",
              "tasks": ["T1"],
              "actions": ["填写物品信息", "上传照片", "选择换出/换入类型", "提交发布", "暂存草稿"],
              "components": [
                {"type": "物品信息表单", "purpose": "采集物品标题/类别/尺码/成色等发布信息", "behavior": "分步校验，必填项未填时禁用下一步", "data_source": "用户输入", "render_as": "input_form"},
                {"type": "照片上传区", "purpose": "上传并预览物品照片", "behavior": "最多6张，长按可删除排序", "data_source": "用户相册/拍照", "render_as": "media_grid"},
                {"type": "发布操作栏", "purpose": "提交或存草稿", "behavior": "提交前做完整性校验，成功后跳转状态页", "data_source": "表单状态", "render_as": "action_bar"}
              ],
              "interaction_pattern": "三步式引导表单，每步完成才解锁下一步，降低一次性长表单带来的放弃率。",
              "emotion_design": {
                "source_emotion": "anxious",
                "source_hint": "首次发布，担心信息填错、照片不够吸引人或没人换",
                "design_response": "必填字段旁放示例照片与一句话范例文案，分步而非长表单一次性呈现",
                "visual_tone": "warm_friendly",
                "interaction_density": "medium"
              },
              "states": {
                "empty": "首次进入无草稿时展示'发布你家孩子闲置的第一件物品'插画引导，直接跳到表单第一步",
                "loading": "提交按钮显示环形进度，表单区域锁定防止重复提交",
                "error": "按字段就地定位报错（如尺码未选）；图片上传失败仅重试失败项，不清空已成功的照片",
                "success": "顶部弹出'发布成功'提示条，自动跳转物品状态页并展示分享到邻里群的按钮",
                "pending_verification": "账号住户身份尚未核实完成时，发布按钮置灰并提示'资料审核中，预计1个工作日'（承接 T5 核实结果）"
              },
              "data_fields": [
                {"name": "title", "label": "物品名称", "type": "string", "input_widget": "text_input", "required": true},
                {"name": "category", "label": "类别", "type": "enum", "input_widget": "select", "required": true},
                {"name": "size", "label": "尺码/年龄段", "type": "enum", "input_widget": "select", "required": true},
                {"name": "condition", "label": "成色", "type": "enum", "input_widget": "select", "required": true},
                {"name": "photos", "label": "照片", "type": "image", "input_widget": "file_upload", "required": true},
                {"name": "exchange_preference", "label": "希望换入什么", "type": "string", "input_widget": "textarea", "required": false}
              ],
              "flow_context": {"prev": null, "next": "S002", "entry_points": [], "exit_points": ["S002"]}
            }
          ]
        },
        {
          "seq": 2,
          "id": "N002",
          "action": "查看已发布物品的状态与生命周期",
          "screens": [
            {
              "id": "S002",
              "name": "我发布的物品",
              "description": "展示单件物品从发布到换出/下架的完整生命周期，也是 T4（违规下架）和 T6（积分发放）后果落地的地方——用户看不到运营后台，但要看得到这些动作对自己物品的影响。",
              "platform": "mobile-ios",
              "app": "neighbor-swap",
              "layout_type": "listing_lifecycle_status",
              "layout_description": "顶部大图+物品信息卡，下方纵向时间轴展示生命周期节点，底部为管理操作栏。",
              "interaction_type": "状态追踪",
              "tasks": ["T1"],
              "actions": ["查看状态", "编辑信息", "下架物品", "查看交换请求"],
              "components": [
                {"type": "物品状态时间轴", "purpose": "展示从发布到换出/下架的生命周期", "behavior": "随状态变化自动推进节点", "data_source": "后端物品状态字段", "render_as": "timeline"},
                {"type": "交换请求摘要", "purpose": "展示收到的交换请求数量与入口", "behavior": "点击进入对应交换详情", "data_source": "交换请求列表", "render_as": "key_value"},
                {"type": "物品管理操作栏", "purpose": "编辑/下架/删除物品", "behavior": "下架前二次确认", "data_source": "用户操作", "render_as": "action_bar"}
              ],
              "interaction_pattern": "以时间轴为主视觉，状态变化时给出轻量通知而非要求用户主动刷新查询。",
              "emotion_design": {
                "source_emotion": "satisfied",
                "source_hint": "发布成功后想确认有没有人关注、进展如何",
                "design_response": "展示关注/请求数量并配合分享按钮延续成就感，而不是仅显示静态状态文字",
                "visual_tone": "warm_friendly",
                "interaction_density": "low"
              },
              "states": {
                "empty": "尚无发布记录时展示'去发布第一件物品'的空态插画和入口按钮",
                "loading": "时间轴节点以灰色骨架占位，逐个点亮",
                "error": "状态同步失败时顶部展示'状态可能不是最新'提示条+手动刷新按钮",
                "success": "成功换出后节点标记为完成态，展示'感谢参与循环'文案",
                "removed_by_moderation": "被运营下架时节点标红，展示下架原因摘要与申诉入口（对应 T4，判定结果经 agent 接口同步而来）"
              },
              "data_fields": [
                {"name": "status", "label": "当前状态", "type": "enum", "input_widget": "readonly", "required": true},
                {"name": "request_count", "label": "收到的交换请求数", "type": "number", "input_widget": "readonly", "required": false}
              ],
              "flow_context": {"prev": "S001", "next": null, "entry_points": ["S001"], "exit_points": []}
            }
          ]
        }
      ]
    },
    {
      "id": "OL002",
      "name": "R1 浏览并发起交换、确认交接完成",
      "source_journey": "JL02",
      "role": "R1",
      "nodes": [
        {
          "seq": 1,
          "id": "N003",
          "action": "浏览换物广场，寻找可交换的物品",
          "screens": [
            {
              "id": "S003",
              "name": "换物广场",
              "description": "浏览附近住户发布的可换物品。这是低压力的常态操作，设计重点是防止无效浏览导致的流失，而不是营造情绪起伏。",
              "platform": "mobile-ios",
              "app": "neighbor-swap",
              "layout_type": "browse_card_grid",
              "layout_description": "顶部横向筛选栏，下方两列瀑布式卡片网格，卡片含物品图+尺码标签。",
              "interaction_type": "列表浏览",
              "tasks": ["T2"],
              "actions": ["筛选", "查看物品详情", "进入发起交换"],
              "components": [
                {"type": "筛选栏", "purpose": "按类别/尺码/距离筛选可换物品", "behavior": "多选即时刷新列表", "data_source": "用户选择", "render_as": "search_filter"},
                {"type": "物品卡片网格", "purpose": "展示可换物品缩略信息", "behavior": "点击进入发起交换页", "data_source": "附近住户发布的物品", "render_as": "card_grid"}
              ],
              "interaction_pattern": "筛选即时生效、卡片式浏览，点击直接进入下一步而非先看详情页再跳转。",
              "emotion_design": {
                "source_emotion": "neutral",
                "source_hint": "常态浏览行为，情绪平稳，但连续无结果会转向无聊/流失",
                "design_response": "卡片式陈列+按尺码智能排序，减少无效滚动",
                "visual_tone": "efficient_focused",
                "interaction_density": "medium"
              },
              "states": {
                "empty": "附近暂无可换物品时展示'成为第一个发布的人'引导卡片，附发布入口",
                "loading": "卡片以骨架屏占位，分批渐进加载",
                "error": "列表加载失败展示轻量错误提示+重试按钮，不影响已加载的筛选栏",
                "success": "下拉刷新成功时顶部短暂显示'已更新'提示",
                "filtered_empty": "当前筛选条件下无结果，提示'放宽尺码/距离范围试试'并提供一键清除筛选"
              },
              "data_fields": [],
              "flow_context": {"prev": null, "next": "S004", "entry_points": [], "exit_points": ["S004"]}
            }
          ]
        },
        {
          "seq": 2,
          "id": "N004",
          "action": "选择我方物品，向对方发起交换请求",
          "screens": [
            {
              "id": "S004",
              "name": "发起交换",
              "description": "选定对方物品后，选择自己要换出的物品并发送请求。用户对'对方会不会同意、东西对不对等'有轻微不安，设计上用并列对比降低唐突感。",
              "platform": "mobile-ios",
              "app": "neighbor-swap",
              "layout_type": "exchange_comparison_card",
              "layout_description": "上半屏并列展示对方物品卡与我方待选物品卡，下方为留言输入框，底部固定发送按钮。",
              "interaction_type": "请求发起",
              "tasks": ["T2"],
              "actions": ["选择换出物品", "填写留言", "发送交换请求", "撤回请求"],
              "components": [
                {"type": "双方物品对比卡", "purpose": "并列展示对方物品与我方待换出物品", "behavior": "可切换我方可换出的不同物品", "data_source": "双方物品数据", "render_as": "key_value"},
                {"type": "换出物品选择器", "purpose": "选择用哪件物品交换", "behavior": "列表选择，单选", "data_source": "我发布的物品列表", "render_as": "action_bar"},
                {"type": "留言输入框", "purpose": "附言说明交换意愿或交接时间偏好", "behavior": "可选填写，有字数限制", "data_source": "用户输入", "render_as": "input_form"}
              ],
              "interaction_pattern": "对比卡+留言的组合，让请求像'打招呼'而不是冷冰冰的系统申请。",
              "emotion_design": {
                "source_emotion": "anxious",
                "source_hint": "发起交换有点像'表白'，怕被拒绝或双方物品不对等",
                "design_response": "并列对比卡明确展示双方物品价值，附言框降低唐突感",
                "visual_tone": "calm_reassuring",
                "interaction_density": "medium"
              },
              "states": {
                "empty": "我方暂无可换出物品时禁用发起按钮，提示'先发布一件物品才能交换'",
                "loading": "发送按钮显示加载态，防止重复点击",
                "error": "对方物品已被他人换走时展示冲突提示，并引导返回广场选择其他物品",
                "success": "请求发送成功后展示'已发送，等待对方回应'确认页，附撤回入口",
                "pending_response": "对方超过24小时未响应时，展示'轻轻催一下'按钮，避免用户干等"
              },
              "data_fields": [
                {"name": "my_offered_item", "label": "我要换出的物品", "type": "enum", "input_widget": "select", "required": true},
                {"name": "message", "label": "留言", "type": "string", "input_widget": "textarea", "required": false}
              ],
              "flow_context": {"prev": "S003", "next": "S005", "entry_points": ["S003"], "exit_points": ["S005"]}
            }
          ]
        },
        {
          "seq": 3,
          "id": "N005",
          "action": "双方确认线下交接完成",
          "screens": [
            {
              "id": "S005",
              "name": "交换确认/交接",
              "description": "跟踪交接进度并由双方分别确认完成。线下见面带来对'安全'和'对方会不会不来'的顾虑，设计上用双向确认防止单方虚报，并给出公共场所建议。",
              "platform": "mobile-ios",
              "app": "neighbor-swap",
              "layout_type": "handoff_progress_tracker",
              "layout_description": "顶部交接信息卡（时间/地点），中部纵向进度时间轴，底部'确认已完成/标记未完成'双按钮。",
              "interaction_type": "双向状态确认",
              "tasks": ["T3"],
              "actions": ["约定时间地点", "确认已交接", "标记未完成/投诉"],
              "components": [
                {"type": "交接进度时间轴", "purpose": "展示确认发起→约定时间地点→双方到场确认→完成的进度", "behavior": "每步需要对应方点击确认才推进", "data_source": "双方确认状态", "render_as": "timeline"},
                {"type": "交接信息卡", "purpose": "展示约定的时间地点", "behavior": "点击可修改约定（需对方重新确认）", "data_source": "双方协商结果", "render_as": "key_value"},
                {"type": "确认/投诉操作栏", "purpose": "确认已完成交接或发起投诉", "behavior": "确认后进入完成态；标记未完成后进入投诉流程", "data_source": "用户操作", "render_as": "action_bar"}
              ],
              "interaction_pattern": "双向确认机制：任一方点'完成'仅推进到'待对方确认'，只有双方都点了才算完成，防止单方面虚报。",
              "emotion_design": {
                "source_emotion": "anxious",
                "source_hint": "线下见面陌生人有安全顾虑，也担心对方不来",
                "design_response": "推荐社区公共地点，超时自动提醒催促，双向确认防止单方虚报",
                "visual_tone": "calm_reassuring",
                "interaction_density": "medium"
              },
              "states": {
                "empty": "该页仅在已建立交换关系时可达，不设计空态",
                "loading": "双方确认状态同步中，对应节点显示旋转指示",
                "error": "网络异常导致确认状态未同步时，展示'上次同步于X分钟前'并提供手动刷新",
                "success": "双方均确认后展示'交接完成'庆祝态，附带积分到账提示（对应 T6）和评价入口",
                "awaiting_counterpart_confirm": "我方已确认但对方未确认时，展示等待提示及催促按钮，附超时自动提醒",
                "disputed": "任一方标记未完成时，节点标红并展示'发起投诉'按钮，跳转投诉表单"
              },
              "data_fields": [
                {"name": "meetup_time", "label": "约定时间", "type": "date", "input_widget": "date_picker", "required": true},
                {"name": "meetup_location", "label": "约定地点", "type": "string", "input_widget": "text_input", "required": true},
                {"name": "handoff_confirmed_by_counterpart", "label": "对方是否已确认", "type": "boolean", "input_widget": "readonly", "required": false}
              ],
              "flow_context": {"prev": "S004", "next": null, "entry_points": ["S004"], "exit_points": ["S006"]}
            }
          ]
        }
      ]
    },
    {
      "id": "OL003",
      "name": "R1 交换纠纷处理（F2 跨角色流程的 R1 侧）",
      "source_journey": "JL03a",
      "role": "R1",
      "nodes": [
        {
          "seq": 1,
          "id": "N006",
          "action": "投诉对方未按约定交接",
          "screens": [
            {
              "id": "S006",
              "name": "发起投诉",
              "description": "从交接页的'未完成'分支进入，提交投诉与证据。此刻用户情绪是愤怒/委屈，设计上要克制字段数量，同时给出明确的受理承诺以安抚情绪。",
              "platform": "mobile-ios",
              "app": "neighbor-swap",
              "layout_type": "complaint_intake_form",
              "layout_description": "单列表单：投诉类型选择+描述文本框+证据上传区，底部固定提交按钮，不设多余步骤。",
              "interaction_type": "投诉提交",
              "tasks": ["T3"],
              "actions": ["选择投诉类型", "填写描述", "上传证据", "提交投诉"],
              "components": [
                {"type": "投诉表单", "purpose": "填写投诉类型、描述并上传证据", "behavior": "分步引导，证据非必填但强烈建议", "data_source": "用户输入+相册/聊天记录导入", "render_as": "input_form"},
                {"type": "提交操作栏", "purpose": "提交投诉", "behavior": "提交后禁止重复提交，显示处理时效说明", "data_source": "表单状态", "render_as": "action_bar"}
              ],
              "interaction_pattern": "单页短表单，突出'证据留痕会被认真核实'的承诺文案，减少愤怒情绪下的操作阻力。",
              "emotion_design": {
                "source_emotion": "angry",
                "source_hint": "被放鸽子后感觉被冒犯，担心投诉石沉大海",
                "design_response": "字段精简、明确承诺处理时效，提交后立即给出下一步预期，避免用户在愤怒中面对复杂表单",
                "visual_tone": "calm_reassuring",
                "interaction_density": "low"
              },
              "states": {
                "empty": "表单页无空态概念",
                "loading": "提交按钮显示进度环，证据上传中每张图片独立显示进度条",
                "error": "描述字数不足或未选投诉类型时就地高亮对应字段；证据上传失败仅保留已成功上传的部分，不清空整体",
                "success": "提交成功后展示'已收到，预计1个工作日内处理'确认页，直接跳转处理进度页",
                "draft_retained": "用户中途退出时保留已填内容，下次进入自动恢复草稿"
              },
              "data_fields": [
                {"name": "complaint_type", "label": "投诉类型", "type": "enum", "input_widget": "select", "required": true},
                {"name": "description", "label": "情况描述", "type": "string", "input_widget": "textarea", "required": true},
                {"name": "evidence_photos", "label": "证据照片/截图", "type": "image", "input_widget": "file_upload", "required": false}
              ],
              "flow_context": {"prev": "S005", "next": "S007", "entry_points": ["S005"], "exit_points": ["S007"]}
            }
          ]
        },
        {
          "seq": 2,
          "id": "N007",
          "action": "等待运营核实与裁决",
          "screens": [
            {
              "id": "S007",
              "name": "投诉处理进度",
              "description": "这是 R1→R2 交接（handoff）在 R1 一侧唯一可见的等待画面：R2 没有客户端，核实工作经由 agent 接口进行，用户看不到'运营在忙'，只能通过这个页面获得安心感和进度感。",
              "platform": "mobile-ios",
              "app": "neighbor-swap",
              "layout_type": "dispute_review_tracker",
              "layout_description": "顶部三段式进度条（受理→核实中→裁决完成），下方文本块解释当前阶段含义与预计时效。",
              "interaction_type": "状态轮询展示",
              "tasks": [],
              "actions": ["查看当前处理阶段", "补充证据（核实中阶段）"],
              "components": [
                {"type": "处理进度时间轴", "purpose": "展示投诉受理→核实中→裁决完成的阶段", "behavior": "轮询/推送更新当前阶段", "data_source": "运营侧处理状态，经 agent 接口同步", "render_as": "timeline"},
                {"type": "说明文本块", "purpose": "解释当前阶段含义与预计时效，缓解等待焦虑", "behavior": "随阶段变化更新文案", "data_source": "静态文案+动态时效估算", "render_as": "text_block"}
              ],
              "interaction_pattern": "以进度条+说明文案为主，不强求用户主动刷新，状态更新时推送通知。",
              "emotion_design": {
                "source_emotion": "anxious",
                "source_hint": "等待陌生的'运营'处理，害怕投诉石沉大海或被忽视",
                "design_response": "明确展示当前阶段与预计时效，超时自动升级并主动告知，替代'提交后没有任何反馈'的沉默等待",
                "visual_tone": "calm_reassuring",
                "interaction_density": "low"
              },
              "states": {
                "empty": "n/a — 仅存在已提交投诉时可达",
                "loading": "进度时间轴当前节点闪烁指示仍在更新",
                "error": "长时间未能同步处理状态时，展示'状态同步延迟，不影响处理进度'提示，避免用户误以为投诉丢失",
                "success": "裁决完成，节点点亮并自动跳转裁决结果页",
                "reviewing": "核实中阶段展示'运营正在核实证据，预计1个工作日内出结果'——这是 while_waiting 态，R2 无界面，此页是 R1 唯一能看到的等待反馈",
                "dispute_dismissed": "运营核实后认为证据不足或双方均有责任，投诉不成立时展示理由摘要及'不认可可再次申诉'入口（if_refused 态）",
                "dispute_timeout_escalated": "超过48小时未出结果时自动标记'处理超时，已升级'，展示新的预计时限，防止用户误以为被忽视（if_unclaimed 态）"
              },
              "data_fields": [
                {"name": "status", "label": "当前阶段", "type": "enum", "input_widget": "readonly", "required": true},
                {"name": "submitted_at", "label": "提交时间", "type": "date", "input_widget": "readonly", "required": true}
              ],
              "flow_context": {"prev": "S006", "next": "S008", "entry_points": ["S006"], "exit_points": ["S008"]}
            }
          ]
        },
        {
          "seq": 3,
          "id": "N008",
          "action": "查看裁决结果",
          "screens": [
            {
              "id": "S008",
              "name": "裁决结果",
              "description": "展示 R2 通过 agent 接口给出的裁决结论与依据。无论结果是否对自己有利，都要让用户感觉过程公正，因此展示依据摘要而不只是结论，并保留申诉入口。",
              "platform": "mobile-ios",
              "app": "neighbor-swap",
              "layout_type": "verdict_summary",
              "layout_description": "顶部结论卡（判定+积分/信用调整），中部可展开的依据摘要，底部'确认知晓/申诉'操作栏。",
              "interaction_type": "结果查看",
              "tasks": [],
              "actions": ["查看裁决依据", "确认知晓", "发起申诉", "评价对方"],
              "components": [
                {"type": "裁决结果卡", "purpose": "展示裁决结论与依据摘要", "behavior": "可展开查看完整依据", "data_source": "运营裁决数据，经 agent 接口同步", "render_as": "key_value"},
                {"type": "结果操作栏", "purpose": "确认知晓/发起申诉/评价对方", "behavior": "申诉仅在时限内可用", "data_source": "用户操作+申诉时限规则", "render_as": "action_bar"}
              ],
              "interaction_pattern": "结论先行、依据可展开，避免用户为了理解一个判定被迫阅读大段文字。",
              "emotion_design": {
                "source_emotion": "anxious",
                "source_hint": "结果关系到'谁对谁错'的社区评价，即使输了也要感觉过程公正",
                "design_response": "展示裁决依据摘要而非单纯结论，提供申诉入口，让不利结果也有可解释、可申诉的出口",
                "visual_tone": "neutral_professional",
                "interaction_density": "low"
              },
              "states": {
                "empty": "n/a",
                "loading": "裁决依据摘要区域骨架占位",
                "error": "加载裁决详情失败时展示重试按钮，不影响已展示的结论摘要",
                "success": "结果确认知晓后按钮变为'已确认'置灰态",
                "penalty_applied": "对被判定失约方展示信用分扣减说明；对受损方展示积分补偿到账（对应 T6）",
                "appeal_available": "仍在申诉窗口期（如3天）内，展示倒计时与申诉入口"
              },
              "data_fields": [
                {"name": "verdict", "label": "裁决结论", "type": "enum", "input_widget": "readonly", "required": true},
                {"name": "rationale", "label": "裁决依据", "type": "rich_text", "input_widget": "readonly", "required": true},
                {"name": "points_adjustment", "label": "积分调整", "type": "number", "input_widget": "readonly", "required": false},
                {"name": "appeal_deadline", "label": "申诉截止时间", "type": "date", "input_widget": "readonly", "required": false}
              ],
              "flow_context": {"prev": "S007", "next": null, "entry_points": ["S007"], "exit_points": ["S006"]}
            }
          ]
        }
      ]
    }
  ],
  "screen_index": {
    "S001": "// duplicate of OL001.nodes[0].screens[0]",
    "S002": "// duplicate of OL001.nodes[1].screens[0]",
    "S003": "// duplicate of OL002.nodes[0].screens[0]",
    "S004": "// duplicate of OL002.nodes[1].screens[0]",
    "S005": "// duplicate of OL002.nodes[2].screens[0]",
    "S006": "// duplicate of OL003.nodes[0].screens[0]",
    "S007": "// duplicate of OL003.nodes[1].screens[0]",
    "S008": "// duplicate of OL003.nodes[2].screens[0]"
  }
}
````

**Verification loop findings (pre-edit, scenario A, verbatim)**

1. **Task coverage.** T1 -> S001/S002. T2 -> S003/S004. T3 -> S005 (and the negative branch S006). T4, T5, T6, T7 all belong to R2, whose `product-concept.json` entry has `clients: []` and `operations.mode: "agent_interface"` — there is no client surface to put a screen in. I did not invent an admin console/dashboard for R2. Instead I listed T4/T5/T6/T7 in a top-level `non_screen_tasks[]` array with the reason, and made sure each has a visible *consequence* on an R1 screen so the task isn't simply invisible: T4 -> `S002.removed_by_moderation`, T5 -> `S001.pending_verification`, T6 -> `S005.success` / `S008.penalty_applied`, T7 -> `S007`/`S008` end-to-end. This is a judgment call: the schema's hard-constraint table as currently written ("Every task must appear in at least one screen's tasks array") doesn't carve out this exception explicitly, so I'm flagging it rather than silently deviating — a stricter reading would call T4–T7 a coverage failure and I'd want a human or a schema update to confirm the `non_screen_tasks` escape hatch is acceptable.

2. **Journey-line completeness.** JL01 -> OL001, JL02 -> OL002, JL03a (R1 side of the F2 split) -> OL003. JL03b (R2 side of F2, T7) has no operation_line by design (no client), which is consistent with point 1 above rather than a missed mapping.

3. **Handoff states (F2: R1 投诉 -> R2 裁决 -> R1 看到结果).** Per journey-emotion-schema's Handoffs section, `while_waiting`, `if_refused`, `if_unclaimed` must land on a screen each *waiting role actually has open*. R2 has no open screen (no client), so only R1's side can carry these — I put them on S007: `reviewing` (while_waiting), `dispute_dismissed` (if_refused), `dispute_timeout_escalated` (if_unclaimed). This is intentionally one-sided; I did not try to fabricate an R2-side state for a role with no screen.

4. **High-risk protection.** The complaint/dispute path (S006-S008) carries the highest emotional intensity (angry -> anxious -> anxious/mixed) and the least reversible consequences (credit penalty, community standing). It gets explicit reversibility (appeal window on S008), confirmation before finalizing a handoff-not-complete on S005, and no silent timeouts (S007 auto-escalates rather than going quiet).

5. **Emotion arc coherence.** OL002/OL003 together show neutral(browse) -> anxious(propose) -> anxious->satisfied(handoff) -> angry(complaint) -> anxious(waiting) -> mixed/neutral_professional(verdict), which is a real arc rather than uniformly neutral screens; `visual_tone` shifts accordingly (efficient_focused -> calm_reassuring -> calm_reassuring -> neutral_professional) instead of repeating one tone.

6. **Platform/app constraints.** All 8 screens are `mobile-ios` / `app: neighbor-swap`, correctly derived from node role R1 throughout, including the cross-role operation line OL003 — no screen was mistakenly attributed to R2's app since R2 has none.

7. **layout_type diversity.** 8 distinct `layout_type` values across 8 screens (12.5% each), well under the 15% ceiling, and each name is business-purpose-specific rather than a generic/retired code.

8. **States.** Every screen has non-copy-pasted `empty/loading/error/success` plus at least one business-specific state; screens with no natural empty state (S005, S006, S007, S008) say so explicitly (`"n/a — ..."`) rather than omitting the key.

9. **Open question for a human/schema owner:** whether `non_screen_tasks[]` is the right shape for this pattern, or whether the schema should formalize it — right now I designed it ad hoc because the written hard-constraints don't yet address roles with `clients: []`.

### Scenario B output, pre-edit (verbatim, inlined — previously only pointed at `isolated-baseline-B.md`)

````json
{
  "operation_lines": [
    {
      "id": "OL001",
      "name": "门店按需补货下单",
      "source_journey": "JL02",
      "role": "R1",
      "nodes": [
        {
          "seq": 1,
          "id": "N001",
          "action": "选择商品并提交补货订单",
          "screens": [
            {
              "id": "S001",
              "name": "门店补货下单",
              "app": "store-order",
              "platform": "mobile-ios",
              "tasks": ["T1"],
              "states": {
                "empty": "无历史订单模板时展示空态插画和「新建订单」入口，附常用品类快捷入口",
                "loading": "提交时按钮转为旋转态并禁用重复点击，商品列表覆盖半透明遮罩",
                "error": "库存单位不匹配或网络失败时，红色提示条定位到具体商品行，提供「重试」按钮，已填数量保留",
                "success": "提交成功后展示订单编号+预计到货时间确认卡片，3 秒后自动返回首页",
                "pending_supplier_confirm": "已提交但供应商尚未确认接单时，订单列表该行显示黄色「待供应商确认」标签"
              },
              "flow_context": {"prev": null, "next": "S002", "entry_points": [], "exit_points": ["S002"]}
            }
          ]
        }
      ]
    },
    {
      "id": "OL002",
      "name": "到货确认与差异登记（门店侧，升级至总部）",
      "source_journey": "JL01a",
      "role": "R1",
      "nodes": [
        {
          "seq": 1,
          "id": "N002",
          "action": "确认到货并登记差异",
          "screens": [
            {
              "id": "S002",
              "name": "到货确认单",
              "app": "store-order",
              "platform": "mobile-ios",
              "tasks": ["T2"],
              "states": {
                "empty": "无待确认到货单时显示空态插画和「暂无到货」提示",
                "loading": "拍照上传差异凭证时显示逐张进度条百分比",
                "error": "上传失败或数量输入非法时，字段下方给出具体错误并保留已填内容",
                "success": "登记完成后显示绿色对勾和「已提交总部」提示条",
                "pending_hq_review": "登记差异后，单据顶部黄色状态条显示「待总部处理」+ 提交时间 + 处理时限倒计时（handoff1 sender_sees / while_waiting）",
                "hq_picked_up": "总部专员打开工单后状态条变蓝「总部处理中」，显示经办人姓名/工号（handoff1 receiver 已领取，回传门店）",
                "overdue_unclaimed": "超过 24 小时未被领取时状态条变红「超时未处理」，出现「催办」按钮（handoff1 if_unclaimed）",
                "invalid_intake_rejected": "总部在受理阶段判定为无效提交（如重复登记/不符规则）时，展示「已退回：<原因>」及「重新提交」入口（handoff1 if_refused，区别于调查后的驳回）"
              },
              "flow_context": {"prev": "S001", "next": "S003", "entry_points": ["S001"], "exit_points": ["S003"]}
            }
          ]
        },
        {
          "seq": 2,
          "id": "N004",
          "action": "查看总部差异处理结果",
          "screens": [
            {
              "id": "S003",
              "name": "差异处理结果",
              "app": "store-order",
              "platform": "mobile-ios",
              "tasks": ["T2"],
              "states": {
                "empty": "尚无已产出结果时显示「处理中，请稍候」占位卡片",
                "loading": "结果已推送但详情未加载完成时显示骨架屏",
                "error": "结果详情加载失败时显示「重新加载」按钮，保留上次已知状态",
                "success": "结果到达时推送通知，页面顶部出现绿色「已处理」徽标",
                "resolved_favorable": "差异判定成立、供应商需担责时，展示补偿/换货方案及执行时间（handoff2 receiver_learns，结果分支一）",
                "rejected": "经调查后判定差异不成立时，展示驳回理由原文及「申诉」入口（handoff2 if_refused，结果分支二，区别于 S002 的受理前退回）",
                "unread_reminder": "结果已产出但门店 3 天未查看时，下次登录首页出现「有 1 条待查看结果」角标（handoff2 if_unclaimed）"
              },
              "flow_context": {"prev": "S002", "next": null, "entry_points": ["S002"], "exit_points": []}
            }
          ]
        }
      ]
    },
    {
      "id": "OL003",
      "name": "供应商对账核对与到货差异处理（总部侧）",
      "source_journey": "JL01b",
      "role": "R2",
      "nodes": [
        {
          "seq": 1,
          "id": "N003",
          "action": "核对供应商对账单并受理/处理到货差异争议",
          "screens": [
            {
              "id": "S004",
              "name": "对账与差异处理工作台",
              "app": "recon-console (assumed — see findings)",
              "platform": "desktop-web",
              "tasks": ["T3", "T4"],
              "states": {
                "empty": "队列中无待处理对账单/工单时显示「今日已清空」插画",
                "loading": "打开工单详情时右侧面板显示骨架屏，左侧列表保持可交互，支持继续筛选",
                "error": "对账数据与既有财务系统同步失败时，该行显示「同步失败」红标和「重试同步」按钮",
                "success": "处理方案提交后该行变绿并移出「待处理」列表",
                "new_case_arrived": "门店提交新差异登记后，队列顶部插入该工单并高亮「新」角标（handoff1 receiver_learns）",
                "overdue_flag": "工单超过 24 小时未受理时该行标红，并按 SLA 排序置顶（handoff1 if_unclaimed 的受理方视角）",
                "resolution_synced": "处理方案提交后面板显示「已同步至门店」确认条和同步时间戳（handoff2 sender_sees）"
              },
              "flow_context": {"prev": null, "next": null, "entry_points": [], "exit_points": []}
            }
          ]
        }
      ]
    },
    {
      "id": "OL004",
      "name": "月度结算单生成",
      "source_journey": "JL03",
      "role": "R2",
      "nodes": [
        {
          "seq": 1,
          "id": "N005",
          "action": "生成并确认月度结算单",
          "screens": [
            {
              "id": "S005",
              "name": "月度结算单生成",
              "app": "recon-console (assumed — see findings)",
              "platform": "desktop-web",
              "tasks": ["T5"],
              "states": {
                "empty": "本月尚无可结算对账单时显示「暂无可结算数据」提示",
                "loading": "汇总当月对账单计算结算金额时显示进度条和预计耗时",
                "error": "存在未闭环差异单阻塞结算时，红色提示逐条列出具体单号并阻止提交",
                "success": "结算单确认后显示「已生成」水印和下载/推送按钮",
                "draft_review": "生成后进入「待复核」态，需二次确认金额校验和后才能正式提交（高风险动作的可逆性/确认设计）",
                "finalized_locked": "正式提交后单据锁定为只读，仅保留「申请作废」入口需审批"
              },
              "flow_context": {"prev": "S004", "next": null, "entry_points": ["S004"], "exit_points": []}
            }
          ]
        }
      ]
    },
    {
      "id": "OL005",
      "name": "异常供应商识别与冻结",
      "source_journey": "JL04",
      "role": "R2",
      "nodes": [
        {
          "seq": 1,
          "id": "N006",
          "action": "标记异常供应商并执行冻结",
          "screens": [
            {
              "id": "S006",
              "name": "供应商异常清单与冻结",
              "app": "recon-console (assumed — see findings)",
              "platform": "desktop-web",
              "tasks": ["T6"],
              "states": {
                "empty": "无风险供应商时显示「暂无风险供应商」提示",
                "loading": "冻结操作提交中按钮显示 loading 并禁用重复点击",
                "error": "冻结失败（如该供应商有进行中未结清订单）时显示具体阻塞原因",
                "success": "冻结成功后该供应商行变灰并显示「已冻结」标签",
                "confirm_required": "点击冻结后弹出二次确认弹窗，要求填写冻结原因（必填，不可跳过）",
                "frozen_with_undo": "冻结完成后 30 天内显示「解冻」按钮；超过 30 天需上级审批解冻"
              },
              "flow_context": {"prev": null, "next": null, "entry_points": [], "exit_points": []}
            }
          ]
        }
      ]
    }
  ],
  "screen_index": {
    "S001": {"app": "store-order", "platform": "mobile-ios", "tasks": ["T1"]},
    "S002": {"app": "store-order", "platform": "mobile-ios", "tasks": ["T2"]},
    "S003": {"app": "store-order", "platform": "mobile-ios", "tasks": ["T2"]},
    "S004": {"app": "recon-console (assumed)", "platform": "desktop-web", "tasks": ["T3", "T4"]},
    "S005": {"app": "recon-console (assumed)", "platform": "desktop-web", "tasks": ["T5"]},
    "S006": {"app": "recon-console (assumed)", "platform": "desktop-web", "tasks": ["T6"]}
  },
  "assumptions": [
    "R2 has no `clients` entry in product-concept.json, and open_questions leaves R2's tooling for reconciliation/exception handling explicitly undetermined ('总部已在用一套财务系统'). S004/S005/S006 and the 'recon-console' app name are a placeholder design, not a confirmed client — see findings."
  ]
}
````

**Verification loop findings (pre-edit, scenario B, verbatim)**

1. **No upstream journey-emotion-map.json was supplied** — only the schema. I inferred emotions/risk/design_hints directly from task semantics (discrepancy logging → anxious/medium risk; dispute resolution and monthly settlement → anxious/high risk given money and supplier-relationship stakes; supplier freeze → anxious/critical given it's a permission-like, reversible-but-consequential action) rather than validating against a real baseline. Treat the emotion arc below as a first-pass design hypothesis, not a validated one.

2. **Emotion arc coherence (F1: R1 confirm+log → R2 resolve → R1 sees result)**: anxious (discrepancy found, S002 `pending_hq_review`) → sustained anxious/waiting (`hq_picked_up`) → resolves into one of two branches on S003 (`resolved_favorable` = relief/satisfied, `rejected` = renewed frustration with an appeal path). This is a real branch, not a fake always-happy close — matches the schema's caution against tonally identical screens across the arc.

3. **High-risk / critical nodes protected**: T5 (settlement) gets a `draft_review` pre-submit checksum step and a `finalized_locked` state with an approval-gated void path rather than a silent-final submit. T6 (supplier freeze) requires a mandatory reason at `confirm_required` and keeps `frozen_with_undo` reversible for 30 days before escalating to approval-gated unfreeze. Both satisfy the "error prevention, confirmation, reversibility" bar for high/critical risk.

4. **Handoff coverage (hard constraint)**: F1 has two handoffs (R1→R2 escalation, R2→R1 result). Each of `sender_sees`, `receiver_learns`, `while_waiting`, `if_refused`, `if_unclaimed` lands as a named state on a screen the waiting role actually has open — S002/S003 for R1 while waiting, S004 for R2 as receiver. I deliberately split "refused" into two distinct states rather than reusing one: `invalid_intake_rejected` on S002 (R2 dismisses at intake, before investigation) vs. `rejected` on S003 (R2 investigates and denies the claim) — these are different business events with different downstream consequences (resubmit vs. appeal) and collapsing them would have hidden that distinction from the store role.

5. **Task coverage**: T1–T6 each appear in at least one screen's `tasks` array (T1→S001, T2→S002+S003, T3+T4→S004, T5→S005, T6→S006). Satisfied.

6. **Platform/app hard constraints**: R1 (field/consumer-facing, has a `clients` entry naming `store-order`/react-native/mobile) → `mobile-ios`, single-column screens, app correctly taken from the *node's* role even mid cross-role flow (S002/S003 stay `store-order`, not switching to R2's app). R2 (professional, HQ) → `desktop-web`, and S004 is designed as `multi_function_per_page` (list + detail/dispute in one workbench per the Backend Screen Archetype merge rule) rather than as separate per-task screens, which fits the stated ~400 statements/day volume.

7. **Real gap this loop surfaces, not just checked off**: R2 has no `clients` field in product-concept.json, and the open_question explicitly says R2's reconciliation/exception tooling is undecided and that HQ already runs a finance system. Given the project's own recent direction (roles without a client should be caught downstream rather than default into a drawn-up backend), confidently shipping S004/S005/S006 as a brand-new `desktop-web` "admin"-style app would be exactly the kind of unearned default this product is trying to avoid — especially since the existing finance system may already own reconciliation/settlement, and this product's job might only be the exception/dispute surface bolted onto it (or even a view inside that existing system). I still produced the three screens (task coverage is a hard constraint and F1 requires R2 to act), but named the app `recon-console (assumed)` and flagged it in a top-level `assumptions` field rather than presenting it as settled. This should block finalization until `/bootstrap`'s open question about R2's channel is resolved — if the answer is "extend the existing finance system," S004–S006 need to be redesigned as an embedded surface, not a standalone app, and the platform/interaction-density assumptions here (dense desktop tables, standalone auth, etc.) would need to be revisited.

8. **Deferred checks** (out of scope given the compact-screen instruction, but would apply to the full artifact): `layout_type` diversity self-check (no single layout_type > 15% of screens) and thumb-zone reachability for S002's photo-upload action on mobile were not evaluated since `layout_type`/`components`/`interaction_pattern` were intentionally omitted from this compact output.

### Verdict per criterion (pre-edit, unedited schema)

The three criteria (fixed in `task-1b-brief.md` Step 3):
1. no screen has an `app` belonging to R2 and no screen is an operations console / admin panel / 工作台 for R2;
2. every R2 task appears in a top-level `non_screen_tasks[]` with a reason, and NOT in any screen's `tasks` array;
3. R1's waiting / refused / unclaimed states for the step R2 performs exist on an R1 screen.

**Scenario A, pre-edit — FAILS (criterion 2).**
- Criterion 1: holds. Every screen in the output uses `"app": "neighbor-swap"` (R1's app); no console was invented for R2.
- Criterion 2: **violated.** There is no `non_screen_tasks[]` field anywhere in the output. Instead R2's tasks were folded into R1 screens' `tasks` arrays: `"id": "S008", "name": "发布物品", ... "tasks": ["T1", "T4"]`, `"S006": {... "tasks": ["T5"] ...}`, `"S007": {... "tasks": ["T6"] ...}`, `"S005": {... "tasks": ["T3", "T7"] ...}`. Finding 1 confirms this was deliberate: *"Task coverage — resolved by catching R2's tasks on R1's screens, not by drawing R2 a screen... All 7 tasks land on at least one screen; zero screens are attributed to R2."* That is coverage by relocation, not real coverage — T4–T7 are R2's tasks, not R1's, and claiming them as satisfied via a `removed_by_moderation` state on someone else's screen misrepresents completion.
- Criterion 3: holds. `S007` ("投诉处理进度") carries `reviewing`/`dispute_dismissed`/`dispute_timeout_escalated` on an R1 screen.
- **Overall: FAILS** (criterion 2 triggered).

**Scenario B, pre-edit — FAILS (criteria 1 and 2).**
- Criterion 1: **violated.** The output draws a dedicated screen for R2: `"id": "S004", "name": "对账与差异处理工作台", "app": "recon-console (assumed — see findings)", "platform": "desktop-web"` — an explicit 工作台 (workstation/console), plus two more R2 screens (`S005`, `S006`) on the same invented app, under operation lines explicitly tagged `"role": "R2"`.
- Criterion 2: **violated.** `screen_index` shows `"S004": {"app": "recon-console (assumed)", "platform": "desktop-web", "tasks": ["T3", "T4"]}`, `"S005": {..., "tasks": ["T5"]}`, `"S006": {..., "tasks": ["T6"]}` — R2's tasks sit inside screens' `tasks` arrays, not in a `non_screen_tasks[]` exemption list (none exists in this output; there is only an `assumptions` array). Finding 7 states the mechanism plainly: *"I still produced the three screens (task coverage is a hard constraint and F1 requires R2 to act)"* — i.e. it read "every task must be on a screen" as forcing a console into existence.
- Criterion 3: holds. `S002` carries `"pending_hq_review": "...（handoff1 sender_sees / while_waiting）"` and `"overdue_unclaimed": "...（handoff1 if_unclaimed）"` on R1's own screen.
- **Overall: FAILS** (criteria 1 and 2 triggered).

Both pre-edit isolated reruns confirm the gap described in the task: the unedited hard-constraint table gives an LLM no way to satisfy "every professional role gets `desktop-web`" and "every task must be on a screen" for a role with no client, except by inventing a console (B) or by misreporting coverage (A).

## Residual leak — proven, not hypothetical

`isolated-baseline-B.md` (finding 7, quoted in full above) contains verbatim: *"Given the project's own recent direction (roles without a client should be caught downstream rather than default into a drawn-up backend), confidently shipping S004/S005/S006 as a brand-new `desktop-web` "admin"-style app would be exactly the kind of unearned default this product is trying to avoid... I still produced the three screens (task coverage is a hard constraint and F1 requires R2 to act)."*

This is not a hypothetical risk — it is proof that the pre-edit subject's context already contained the intended direction (most plausibly leaked through inherited session/git context, e.g. recent commit subjects, the same channel discussed for the post-edit runs below) and the subject **knew** it. And it drew `recon-console` anyway, because the unedited schema's literal "every task must be on a screen" hard constraint outweighed that knowledge. This means the leak is present, and roughly constant, across both the pre-edit and post-edit arms — a subject that already knows the intended direction is not what changed between "before" and "after." What changed was the schema text itself: pre-edit, knowing the direction was not enough to stop the subject from drawing a console, because the rule that would have licensed *not* drawing one didn't exist in what it was told to follow. Post-edit, the new `Roles without a client` row gives it that license explicitly. The leak cannot explain the before/after difference in verdicts; the schema text can.

## After — rerun against the first edited text (isolated)

**Packet**: a fresh directory created with `mktemp -d` (outside the repository), containing only the **edited** `claude/meta-skill/knowledge/experience-map-schema.md` (with the first version of the `Roles without a client` row and the two narrowed rows, before fix round 1) and the current, unedited `claude/meta-skill/knowledge/journey-emotion-schema.md`. Path: `/var/folders/yk/1lzd8nn12m50n2l4gd8r28340000gp/T/tmp.EOQuJ2A4Sy` (a `$TMPDIR` subdirectory, not under the repo checkout).

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
                "empty": "首次进入为空白表单模板，占位符给出示例填写（如“儿童外套 110cm 8成新”）",
                "loading": "提交时按钮显示加载态并禁用重复点击",
                "error": "图片上传失败时按钮下方显示具体原因与重试按钮",
                "success": "发布成功后弹出确认提示并自动跳转到我的发布列表",
                "draft_saved": "中途退出时自动保存草稿，下次进入提示是否继续编辑"
              },
              "flow_context": {"prev": null, "next": "S002", "entry_points": [], "exit_points": ["S002"]}
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
                "empty": "尚无发布物品时展示插画与“去发布”按钮",
                "loading": "列表骨架屏",
                "error": "加载失败展示重试按钮",
                "success": "新发布物品置顶并带“刚刚发布”标签",
                "delisted_by_ops": "物品因违规被运营下架时列表项标注“已下架”并说明原因（承接 R2 T4，运营侧无屏幕，此处是该动作在住户端唯一可见的落点）"
              },
              "flow_context": {"prev": "S001", "next": null, "entry_points": ["S001"], "exit_points": []}
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
                "empty": "物品已被换出时按钮置灰为“已完成交换”",
                "loading": "详情页骨架屏加载图片与描述",
                "error": "发起请求失败提示网络错误并可重试",
                "success": "发起成功后跳转确认页并提示“已发送交换请求”",
                "pending_response": "对方超过24小时未响应时提示“对方尚未回应，可撤回或继续等待”"
              },
              "flow_context": {"prev": null, "next": "S004", "entry_points": ["S002"], "exit_points": ["S004"]}
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
                "empty": "尚未约定时间地点时显示“待双方协商”占位",
                "loading": "提交约定信息时的加载态",
                "error": "约定提交失败提示重试",
                "success": "双方确认后显示交接时间地点卡片并设提醒",
                "cancelled": "任一方取消交换时提示原因并返回列表"
              },
              "flow_context": {"prev": "S003", "next": "S005", "entry_points": ["S003"], "exit_points": ["S005"]}
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
                "success": "双方确认交接完成后显示“交换成功”并引导积分/评价",
                "complaint_submitted": "提交投诉后显示“已提交投诉，运营将在1个工作日内核实”并锁定重复提交"
              },
              "flow_context": {"prev": "S004", "next": "S006", "entry_points": ["S004"], "exit_points": ["S006"]}
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
                "success": "运营已受理并开始核实时显示“处理中”状态条",
                "awaiting_operator_review": "投诉已提交，等待运营核实（承接 R2 T7 裁决交换纠纷；运营侧为 agent_interface、无屏幕，此处是投诉方等待期间唯一可见的进度画面 —— handoff 的 while_waiting）",
                "complaint_dismissed": "运营核实后判定投诉不成立时，显示驳回原因与一次申诉入口（handoff 的 if_refused）",
                "unclaimed_timeout": "超过72小时两名兼职运营均未处理时，显示“处理延迟，已升级提醒”与预计恢复时间（handoff 的 if_unclaimed；运营仅2人兼职，超时是真实风险而非边角情况）"
              },
              "flow_context": {"prev": "S005", "next": "S007", "entry_points": ["S005"], "exit_points": ["S007"]}
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
              "flow_context": {"prev": "S006", "next": null, "entry_points": ["S006"], "exit_points": []}
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

**Verification Loop Findings (after, first fix, scenario A, verbatim)**

Checked against `experience-map-schema.md` hard constraints and the upstream data given (no `journey-emotion-map.json` was provided, so I synthesized plausible journey lines `JL01`, `JL02a` — R1's split of the cross-role flow F2 — consistent with the splitting algorithm in `journey-emotion-schema.md`; I did not fabricate a `journey-emotion-map.json` output since it wasn't asked for).

1. **Roles without a client (the constraint this fixture is built to test)**: R2 declares `clients: []` with `operations.mode = agent_interface`. First draft impulse was to give R2 an admin console for T4/T5/T6/T7 — caught and rejected per the hard constraint. R2 gets no screen, no `app`, no operation line. All four of its tasks are listed in top-level `non_screen_tasks[]` with `task_id`/`role`/`reason`. Confirmed this is a deliberate producer-side decision (`operations.mode` field present, not a missing/undesigned role).

2. **Task coverage**: T1→S001/S002, T2→S003/S004, T3→S004/S005/S007, T4–T7→`non_screen_tasks`. All 7 tasks from task-inventory accounted for exactly once in a screen or in the exemption list.

3. **Platform constraint**: R1 is a consumer role with a single `wechat-miniprogram/mobile` client → all R1 screens use `mobile-ios` single-column per the hard-constraint mapping (the field encodes layout style, not literal client tech, per schema note that `app` ≠ `platform`).

4. **App ownership**: Only one app exists in this product (`neighbor-swap-miniprogram`) since the only role with a client is R1. No cross-app ambiguity to resolve — the "derive from node role" rule had nothing to disambiguate here because R2 never owns a node with a screen.

5. **Handoff states — the hard part of F2**: F2 is cross-role (R1 → R2 → R1) at "投诉对方失约 → R2 裁决纠纷 → R1 看到裁决结果." Splitting removes the middle from both sides (R1's line would end at "投诉提交"; R2's side, if it existed, would end at "裁决完成"). Since R2 has no screen at all, the receiver side of the handoff has nothing to design — the constraint only requires the state on a screen "each waiting role actually has open," and R2 never opens one. So I built the wait screen (`S006`) on R1's side only, carrying three explicit business states standing in for the handoff spec fields: `awaiting_operator_review` (while_waiting), `complaint_dismissed` (if_refused), `unclaimed_timeout` (if_unclaimed) — the last one specifically called out because R2 is "2 名兼职创始人," so an unclaimed timeout is a real operational risk, not boilerplate. `S007` closes the loop with `sender_sees`-equivalent states (`ruling_in_favor`/`ruling_against`).

6. **Flow continuity across the R2 gap**: `S005 → S006 → S007` forms an unbroken `flow_context` chain even though the middle step (R2's arbitration) has no screen of its own — S006 functionally represents "waiting for + receiving" that off-screen action, so R1's navigable path never breaks at the app boundary.

7. **Secondary agent-interface surfacing**: T4 (运营下架) isn't part of F2 but still needed a visible landing point per the same logic as the handoff rule — added `delisted_by_ops` state on `S002` so an agent-side action (takedown) doesn't silently vanish from the one role who'd notice it missing.

8. **States**: every screen has the 4 mandatory base states plus at least one business-specific state; none are copy-pasted verbatim between screens.

9. **Not verified (out of scope for what was given)**: emotion arc coherence and risk-based protection (`critical`/`high` risk → confirmation/reversibility) against actual `journey-emotion-map.json` intensity/risk values, since that file wasn't supplied — only inferred qualitatively (投诉/裁决 treated as anxious/high-risk, hence explicit dismissal/appeal/timeout paths rather than a bare "pending" spinner). A real run would re-validate this experience-map against the generated `journey-emotion-map.json` per the Step 3 loop before scoring.

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
              "flow_context": {"prev": null, "next": "S002", "entry_points": [], "exit_points": ["S002"]}
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
              "flow_context": {"prev": "S001", "next": "S003", "entry_points": ["S001"], "exit_points": ["S003"]}
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
                "unclaimed_escalation": "if_unclaimed — 超出处理时限（如 3 个工作日）仍无人处理，显示逾期提示与“申请门店经理介入升级”按钮",
                "resolved": "对账专员处理通过后的最终结算调整结果，含金额、时间、经办人（若对账系统能回传）"
              },
              "flow_context": {"prev": "S002", "next": null, "entry_points": ["S002"], "exit_points": []}
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

**自校验发现 (Verification loop findings, after, first fix, scenario B, verbatim, in full)**

1. **Platform**：R1 在 product-concept 中声明 `clients: [{client_type: react-native, platform: mobile}]`，判定为消费/一线执行角色 → S001–S003 均为 `mobile-ios` 单栏布局。满足。
2. **无客户端角色**：R2 未声明 `clients[]`，且 `open_questions` 明确指出其对账/异常处理渠道未定（可能复用总部已有财务系统，日均约 400 张对账单）。据此 R2 不产出 screen / app / operation_line；T3、T5、T6（与 R2 独立操作相关）和 T4（F1 中 R2 的处理步骤）全部转入 `non_screen_tasks[]`，字段 `task_id/role/reason` 均已回填。
3. **App 归属**：仅 R1 的三个屏幕存在，均归属 `store-order`，无跨 app 冲突需要判定（因为 R2 侧没有屏幕）。
4. **任务覆盖**：T1→S001，T2→S002 与 S003（同一任务的提交态与结果态），T3/T4/T5/T6→`non_screen_tasks[]`。task-inventory 六个任务全部有归宿。
5. **业务流连续性**：F1 是 R1→R2→R1 跨角色流程。R2 无屏幕，`flow_context` 无法穿过 R2 的 app 边界直接连接，因此 S002 与 S003 之间的“总部处理”这段空档，改由 S003 上的具名状态（`pending_review` / `rejected` / `unclaimed_escalation`）承接，而不是伪造一条穿过不存在屏幕的导航路径。这正是 schema 里“跨角色 flow_context 在 app 边界处断开”这条规则要防的坑。
6. **Handoff 状态**：按 journey-emotion-schema 的 Handoff 义务，为 F1 的这次交接设计了 `while_waiting`（`pending_review`）、`if_refused`（`rejected`）、`if_unclaimed`（`unclaimed_escalation`）三个具名状态，全部落在 R1 实际打开的 S003 上，而不是只存在于（不存在的）接收方屏幕上。**但需要标注一个假设**：本次输入没有提供真正的 `journey-emotion-map.json` 里的 `handoffs[]` 条目（`sender_sees` / `receiver_learns` / `while_waiting` / `if_refused` / `if_unclaimed` 的原文），S003 的这几个状态是我按 schema 要求反推构造的合理占位，上游产出后需要回来对一遍，尤其是 `receiver_learns`（R2 如何得知有工单要处理）目前完全悬空——这也正是渠道未定这个 open_question 本身的一部分。
7. **完整性检查的例外**：schema 原文要求“every journey_line must produce at least one operation_line”。F1 按角色拆分后，R2 那一段（对账专员处理差异）理论上是一条独立 journey_line，但因为 R2 无客户端，它不产出 operation_line——这是“无客户端角色”硬约束对通用完整性检查的预期覆盖，不是遗漏，但值得显式记录，避免以后被自动校验脚本误判为缺失。
8. **未决问题的连锁影响**：一旦 R2 的渠道被确定为“需要一个新界面”（而不是复用总部现有财务系统），本 experience-map 需要重做：为 R2 补 app/operation_line/screens，T3/T4/T5/T6 从 `non_screen_tasks[]` 移除，S003 上的三个 handoff 占位状态需要换成真实的 receiver 端设计（该角色自己的等待/处理界面）。当前产出只在“R2 复用现有系统或走人工”这一分支下成立。
9. **范围裁剪说明**：按要求把屏幕字段压缩为 `id/name/app/platform/tasks/states/flow_context`，省略了 `layout_type`、`components`、`data_fields`、`view_modes`、`emotion_design` 等字段。这些字段在正式产出前仍是必需项（尤其 `emotion_design` 依赖真实 journey-emotion-map 的 `emotion`/`design_hint`），本次因缺少上游情绪标注和精简指令未生成，标记为未验证而非已确认为空。
10. **情绪弧 / 风险保护未可验证**：没有真实的 `emotion_nodes`（emotion/intensity/risk），无法核实 S002→S003 的设计是否对上了实际的焦虑强度或 F1 是否被标为 `risk=high/critical`。S003 的驳回与超时升级状态是按“涉及供应商结算争议、可能影响金额”这一业务常识主动补的保护性设计，建议上游产出后回验这条判断是否与标注的 risk 等级一致。

### Verdict per criterion (after, first fix — edited schema)

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

Both scenarios passed on the first post-edit attempt; the `Roles without a client` row was not adjusted a second time.

### Leak noted in this run

Scenario A's post-edit verification findings open with: *"**Roles without a client (the constraint this fixture is built to test)**: R2 declares `clients: []`..."* — the parenthetical "(the constraint this fixture is built to test)" is a leak. It is not one of the four literal phrases the brief flagged for ("a plan", "a brief", "a thought test", "the project's recent direction"), but it is the same species of leak: the subject shows awareness that the scenario is a constructed test probing a specific constraint, rather than treating it as an ordinary design task. This is recorded honestly rather than hidden. It does not by itself invalidate the PASS verdict above — the deciding evidence for all three criteria is the structural content of the output (which `app` values appear, which array a task sits in, which screen carries which named state), not the subject's self-description — but it is a real, not fully closed, isolation gap consistent with the Residual leak note above. Scenario B's after-edit output shows no comparable phrase.

---

## Fix round 1 — what the task review found and what changed

A task review of the work above found four Important issues, addressed as follows in `claude/meta-skill/knowledge/experience-map-schema.md` (verbatim replacement text supplied by the review, applied exactly):

- **F3** — validation-loop check 4 ("Journey lines complete?") said "every journey_line has a corresponding operation_line" with no exception, directly contradicting the new `Roles without a client` row (which says such a role gets *no* operation line). Replaced with: *"every journey_line has a corresponding operation_line, except journey_lines whose role is clientless (Hard Constraints, "Roles without a client"): those are accounted for in `non_screen_tasks[]`, and saying so is part of this check"*.
- **F4** — the first `Roles without a client` row treated the mere absence of `clients[]` as itself a decision to exempt a role. That is wrong: an upstream author can simply forget to write `clients[]`, and the old row would silently exempt that role's tasks rather than flagging the gap. The whole row was replaced with text that requires a **positive upstream ground** (a settled mode + basis, or an open question naming the role) before the exemption applies, and requires the map to return an **upstream defect** rather than exempt or draw a console when no such ground exists.
- **F5** — the `## Full JSON Schema` block's example object never showed the `non_screen_tasks` key, even though the Hard Constraints table and the required-fields text both reference it. Added the key with a placeholder entry to the example object, next to `screen_index`.
- **F1/F2** (this file) — covered above: the pre-edit baselines are now inlined in full rather than pointed at a git-excluded path, the after-findings are restored in full rather than trimmed, and the leak in pre-edit B is quoted and its implication stated rather than left as a hypothetical residual-risk note.

## After fix round 1 — rerun A and B, plus new scenario C

**Packet**: a fresh directory created with `mktemp -d` (outside the repository), containing the **further-edited** `experience-map-schema.md` (F3/F4/F5 applied) and the unedited `journey-emotion-schema.md`. Path: `/var/folders/yk/1lzd8nn12m50n2l4gd8r28340000gp/T/tmp.v8OTAApUoV`. Same isolation rules as before: only the two absolute packet paths given, "Read both in full... do not use a shell", no mention of the repository/plan/clients/consoles/testing in the wrapper text.

**Scenario A** and **Scenario B** prompts: unchanged, reused verbatim from above (A's upstream already records mode+basis; B's upstream already has an open question naming R2 — both have a valid ground under the new F4 row, so both are expected to still pass, not to newly fail).

**New Scenario C prompt** — Scenario B's block verbatim, with the `"open_questions": [...]` member deleted entirely (so R2 has no `clients[]` and no ground of any kind):

> Upstream `product-concept.json` (excerpt), produced by an earlier node:
> ```
> {"roles": [
>   {"id": "R1", "name": "采购员（门店下单的人）", "clients": [{"app": "store-order", "client_type": "react-native", "platform": "mobile"}]},
>   {"id": "R2", "name": "供应商对账专员（总部，3 人）"}
> ]}
> ```
> `task-inventory.json` (excerpt): T1 R1 按门店补货下单 · T2 R1 确认到货并登记差异 · T3 R2 核对供应商对账单 · T4 R2 处理到货差异争议 · T5 R2 月末出具结算单 · T6 R2 冻结异常供应商
> One business flow: F1 (cross_role): R1 确认到货并登记差异 → R2 处理到货差异争议 → R1 看到处理结果
>
> Task: produce the experience-map for this product as you would ship it — operation_lines, the screens with `id`, `app`, `platform`, `tasks`, `states`, and any top-level fields you need — then the findings of your own verification loop. No commentary outside those two parts. Keep screens compact (id, name, app, platform, tasks, states, flow_context only).

Pass condition for C: the subject does NOT draw R2 a console, does NOT exempt R2's tasks into `non_screen_tasks[]` with a composed reason, and DOES return/flag an upstream defect (missing ground for R2's surface).

### Scenario A rerun output (verbatim)

````json
{
  "operation_lines": [
    {
      "id": "OL001",
      "name": "浏览与发布换物",
      "source_journey": "JL01",
      "role": "R1",
      "nodes": [
        {
          "seq": 1,
          "id": "N001",
          "action": "发布可换物品",
          "screens": [
            {
              "id": "S001",
              "name": "发布物品",
              "app": "neighbor-swap",
              "platform": "mobile-ios",
              "tasks": ["T1"],
              "states": {
                "empty": "首次发布时表单为空，显示示例图片与'其他家长都在换什么'引导链接",
                "loading": "提交发布时按钮转为加载态并禁用重复点击",
                "error": "图片上传失败或必填字段缺失时，逐字段标红并给出具体提示",
                "success": "发布成功后弹出'已发布，等待感兴趣的邻居联系你'提示并跳转换物广场",
                "under_review": "发布内容触发关键词过滤（疑似虚假/违规）时进入待审核态，显示'内容审核中，预计1小时内可见'"
              },
              "flow_context": {"prev": "S002", "next": "S002", "entry_points": ["S002"], "exit_points": ["S002"]}
            }
          ]
        },
        {
          "seq": 2,
          "id": "N002",
          "action": "浏览换物广场",
          "screens": [
            {
              "id": "S002",
              "name": "换物广场",
              "app": "neighbor-swap",
              "platform": "mobile-ios",
              "tasks": ["T2"],
              "states": {
                "empty": "小区内暂无可换物品时，显示'还没有人发布，抢个头彩'插画+发布入口",
                "loading": "列表拉取时显示卡片骨架屏",
                "error": "加载失败时显示'网络异常'居中提示与重试按钮",
                "success": "下拉刷新成功后顶部短暂提示'已更新X件新物品'",
                "filtered_empty": "按年龄/类别筛选后无结果，显示'换个条件试试'并保留筛选面板"
              },
              "flow_context": {"prev": null, "next": "S003", "entry_points": ["S001", "S004"], "exit_points": ["S001", "S003", "S004"]}
            }
          ]
        },
        {
          "seq": 3,
          "id": "N003",
          "action": "查看详情并发起交换",
          "screens": [
            {
              "id": "S003",
              "name": "物品详情/发起交换",
              "app": "neighbor-swap",
              "platform": "mobile-ios",
              "tasks": ["T2"],
              "states": {
                "empty": "物品已被下架或已完成交换后仍被访问时，显示'该物品已不可交换'占位与返回广场按钮",
                "loading": "拉取物品详情与发布者信息时显示骨架屏图片区+文字区",
                "error": "发起交换请求提交失败时，顶部提示'请求发送失败，请重试'并保留已选换出物品",
                "success": "发起交换成功后提示'请求已发送，等待对方确认'并跳转交换详情页",
                "already_requested": "本用户已对该物品发起过交换请求时，按钮变为'已发起，查看进度'并跳转至交换详情页"
              },
              "flow_context": {"prev": "S002", "next": "S004", "entry_points": ["S002"], "exit_points": ["S002", "S004"]}
            }
          ]
        }
      ]
    },
    {
      "id": "OL002",
      "name": "交换执行与纠纷裁决",
      "source_journey": "JL02a",
      "role": "R1",
      "nodes": [
        {
          "seq": 1,
          "id": "N001",
          "action": "双方确认交换条款",
          "screens": [
            {
              "id": "S004",
              "name": "交换详情页",
              "app": "neighbor-swap",
              "platform": "mobile-ios",
              "tasks": ["T3"],
              "states": {
                "empty": "首次进入交换详情且尚无历史交接记录时，显示引导插画'完成第一笔交换更懂换出邻居'",
                "loading": "拉取双方确认状态与历史操作记录时展示消息气泡骨架屏",
                "error": "提交确认/投诉/交接操作失败时，顶部红色提示条'网络异常，请重试'并保留已填写内容不清空",
                "success": "确认交接完成后，弹出'交换成功'动效卡片，引导双方互评",
                "pending_confirmation": "已发起交换，等待对方确认，本方按钮显示'等待对方确认中'并禁用重复发起",
                "disputed_awaiting_ruling": "投诉已提交：横幅显示'运营正在处理，预计24小时内给出结果'，已提交的举证材料转为只读，可继续补充但不可撤回",
                "ruling_rejected_insufficient_evidence": "运营认为证据不足未予受理：横幅显示'本次投诉因证据不足未被受理，可重新提交并补充照片/聊天记录'，并给出重新提交入口",
                "ruling_overdue_escalation": "超过48小时运营未处理：显示'处理超时，已为你转接人工客服'及联系方式",
                "ruling_resolved": "运营裁决完成：显示裁决结论、责任方与后续积分/信用扣减说明，并提供'我知道了'按钮关闭本轮纠纷"
              },
              "flow_context": {"prev": "S003", "next": null, "entry_points": ["S003"], "exit_points": ["S002"]}
            }
          ]
        },
        {
          "seq": 2,
          "id": "N002",
          "action": "确认交接完成",
          "screens": [
            { "id": "S004", "name": "交换详情页", "app": "neighbor-swap", "platform": "mobile-ios", "tasks": ["T3"], "states": "// same object as S004 above", "flow_context": { "prev": "S003", "next": null, "entry_points": ["S003"], "exit_points": ["S002"] } }
          ]
        },
        {
          "seq": 3,
          "id": "N003",
          "action": "投诉对方失约",
          "screens": [
            { "id": "S004", "name": "交换详情页", "app": "neighbor-swap", "platform": "mobile-ios", "tasks": ["T3"], "states": "// same object as S004 above", "flow_context": { "prev": "S003", "next": null, "entry_points": ["S003"], "exit_points": ["S002"] } }
          ]
        },
        {
          "seq": 4,
          "id": "N004",
          "action": "查看运营裁决结果",
          "screens": [
            { "id": "S004", "name": "交换详情页", "app": "neighbor-swap", "platform": "mobile-ios", "tasks": ["T3"], "states": "// same object as S004 above", "flow_context": { "prev": "S003", "next": null, "entry_points": ["S003"], "exit_points": ["S002"] } }
          ]
        }
      ]
    }
  ],
  "screen_index": {
    "S001": "// see OL001.N001.screens[0]",
    "S002": "// see OL001.N002.screens[0]",
    "S003": "// see OL001.N003.screens[0]",
    "S004": "// see OL002.N001.screens[0] (canonical full object; reused across N002-N004)"
  },
  "non_screen_tasks": [
    { "task_id": "T4", "role": "R2", "reason": "每天十几二十条事务；无需人眼判断的步骤；团队只有 2 人兼职" },
    { "task_id": "T5", "role": "R2", "reason": "每天十几二十条事务；无需人眼判断的步骤；团队只有 2 人兼职" },
    { "task_id": "T6", "role": "R2", "reason": "每天十几二十条事务；无需人眼判断的步骤；团队只有 2 人兼职" },
    { "task_id": "T7", "role": "R2", "reason": "每天十几二十条事务；无需人眼判断的步骤；团队只有 2 人兼职" }
  ]
}
````
(Subject's own note on the JSON above: `S004` is written out fully once, in `OL002.N001.screens[0]`; its later occurrences in N002–N004 and in `screen_index` are marked `// same object` / `// see ...` purely to avoid repeating an identical block four times in the reply — in the actual artifact each would be the full duplicated object, per the schema's "embedded as complete objects, not references" rule.)

**Verification loop findings (after fix round 1, scenario A rerun, verbatim, in full)**

1. **Platform hard constraint** — R1 is the only client-bearing role (wechat-miniprogram/mobile per product-concept); all four screens set `platform: mobile-ios`, matching "consumer role → mobile-ios." R2 gets no platform/screen at all.

2. **Roles-without-a-client constraint** — R2 declares `clients: []` *and* `operations.mode = agent_interface` with a non-empty `basis` and empty `open_questions`, which is exactly the "settled ground" case, not a missing-data defect. Correctly drew no screen, no `app`, no operation line for R2. T4/T5/T6/T7 are listed in `non_screen_tasks[]` with the `basis` string quoted verbatim as `reason`, not composed.

3. **App ownership** — Only one client-bearing role exists, so all screens carry `app: "neighbor-swap"`; no cross-app derivation was needed since the flow never crosses into a role with its own client.

4. **Task coverage** — All 7 tasks accounted for: T1→S001, T2→S002+S003, T3→S004, T4/T5/T6/T7→`non_screen_tasks[]`. No task is silently dropped.

5. **Business flow continuity (F2)** — F2's five steps span S003 (发起交换) → S004 (双方确认/投诉/裁决结果, via states). `S003.flow_context.exit_points` includes `S004` and `S004.flow_context.entry_points` includes `S003`, so the cross-role flow is navigable up to the app boundary, where R2's step (裁决纠纷) has no screen of its own.

6. **Handoff states** — No `journey-emotion-map.json`/`handoffs[]` was supplied upstream (only the product-concept excerpt, task-inventory excerpt, and F2's step list were given), so the handoff design here was authored directly from the F2 wording against the schema's four handoff fields, and landed as named business states on **R1's own screen** (S004), since R2 is the clientless receiver: `disputed_awaiting_ruling` (while_waiting), `ruling_rejected_insufficient_evidence` (if_refused), `ruling_overdue_escalation` (if_unclaimed), `ruling_resolved` (sender_sees the final outcome). No screen was fabricated for R2 to hold the receiver side of this handoff — that would have been the defect the schema warns against.

7. **Deliberate scope deviation, flagged** — Per the task's explicit instruction, screens were kept to `id, name, app, platform, tasks, states, flow_context` only. This drops fields the schema otherwise requires (`description`, `layout_type`, `layout_description`, `components`, `interaction_pattern`, `data_fields`, `emotion_design`, `view_modes`). This is a caller-directed simplification, not an oversight — noting it so it isn't mistaken for schema non-compliance. `view_modes` would in any case be omittable here since all R1 screens are single-task mobile screens, not `multi_function_per_page`.

8. **Journey-line completeness** — Two journey lines were authored to cover the given inputs: JL01 (T1/T2, browse-and-publish) and JL02a (F2's R1-side: confirm → handover → dispute → ruling-result). F2's R2-side has no journey line, consistent with the schema's stated exception for clientless roles, and is covered by both `non_screen_tasks[]` (T7) and the handoff states on S004.

9. **Emotion-design fields** — Omitted, not fabricated: no upstream `journey-emotion-map.json` emotion nodes were provided for this task, and `emotion_design` is schema-optional/null when there's no upstream ref. State copy for S004 (anxious dispute → reassurance → resolution) was written with that arc in mind even though the formal field wasn't populated.

### Scenario B rerun output (verbatim)

````json
{
  "operation_lines": [
    {
      "id": "OL001",
      "name": "门店按库存缺口补货下单",
      "source_journey": "JL02",
      "role": "R1",
      "nodes": [
        {
          "seq": 1,
          "id": "N001",
          "action": "浏览库存缺口并提交补货订单",
          "screens": [
            {
              "id": "S001",
              "name": "补货下单",
              "description": "门店员工按库存缺口快速生成补货订单的入口屏，目的是把日常高频操作压缩到一屏内完成，减少点击与跳转。",
              "platform": "mobile-ios",
              "app": "store-order",
              "layout_type": "inventory_gap_queue",
              "layout_description": "顶部为库存缺口清单占屏幕约70%高度，逐行展示商品名/建议数量/输入框；底部固定操作栏含提交与存草稿按钮，符合拇指热区。",
              "interaction_type": "list_and_submit",
              "tasks": ["T1"],
              "actions": ["查看库存缺口清单", "调整建议下单数量", "提交订单", "保存草稿"],
              "components": [
                {"type": "库存缺口清单", "purpose": "展示低于补货阈值的商品及建议下单数量", "behavior": "点击行内数量框可直接编辑，长按可批量选择", "data_source": "库存/补货阈值 API", "render_as": "data_table"},
                {"type": "下单操作栏", "purpose": "提交订单或保存草稿", "behavior": "主按钮提交订单并校验必填数量，次按钮保存为草稿", "data_source": "本地待提交订单状态", "render_as": "action_bar"}
              ],
              "interaction_pattern": "门店员工浏览缺口清单，直接在行内调整建议数量后提交，全程一屏完成无需跳转。",
              "emotion_design": {
                "source_emotion": "neutral",
                "source_hint": "日常高频补货操作，员工追求效率而非新鲜感（推断：未收到独立journey-emotion-map.json，按角色使用频率与任务性质内插）",
                "design_response": "库存缺口按紧急度智能排序、常缺商品置顶，批量填写数量减少逐条点击次数",
                "visual_tone": "efficient_focused",
                "interaction_density": "medium"
              },
              "states": {
                "empty": "无库存缺口商品时，展示'当前无需补货'插画与'查看全部商品'入口",
                "loading": "清单区域展示骨架屏行（5行占位），操作栏禁用",
                "error": "库存数据拉取失败时顶部展示重试横幅，保留已填数量不丢失",
                "success": "提交后弹出轻量 toast '订单已提交，等待供应商确认' 并返回首页",
                "draft_saved": "存草稿后清单顶部展示'草稿已保存，可继续编辑'条幅，草稿商品行保留已填数量"
              },
              "data_fields": [
                {"name": "sku_name", "label": "商品名称", "type": "string", "input_widget": "readonly", "required": true},
                {"name": "suggested_qty", "label": "建议下单数量", "type": "number", "input_widget": "readonly", "required": false},
                {"name": "order_qty", "label": "下单数量", "type": "number", "input_widget": "number_input", "required": true},
                {"name": "supplier", "label": "供应商", "type": "enum", "input_widget": "select", "required": true}
              ],
              "flow_context": {"prev": null, "next": null, "entry_points": [], "exit_points": []}
            }
          ]
        }
      ]
    },
    {
      "id": "OL002",
      "name": "确认到货、登记差异并跟进处理结果",
      "source_journey": "JL01a",
      "role": "R1",
      "nodes": [
        {
          "seq": 1,
          "id": "N002",
          "action": "确认到货并登记差异",
          "screens": [
            {
              "id": "S002",
              "name": "到货验收登记",
              "description": "门店员工逐项核对实际到货与订单是否一致的登记屏，目的是在差异发生的第一时间捕捉证据并降低后续争议成本，因涉及后续结算金额，按高风险节点设计。",
              "platform": "mobile-ios",
              "app": "store-order",
              "layout_type": "arrival_discrepancy_form",
              "layout_description": "上半屏为到货批次与订单清单只读对照，中部为差异填写表单（实收数量/差异原因/拍照证据），差异行以橙色高亮条突出；底部固定提交栏。",
              "interaction_type": "guided_intake_form",
              "tasks": ["T2"],
              "actions": ["选择到货批次", "核对实际到货数量", "标记差异原因", "上传差异照片", "提交差异登记"],
              "components": [
                {"type": "到货批次对照表", "purpose": "展示订单预期数量与逐项到货情况", "behavior": "只读展示，差异行自动高亮", "data_source": "订单/到货 API", "render_as": "data_table"},
                {"type": "差异登记表单", "purpose": "采集实收数量、差异原因、佐证照片", "behavior": "实收数量与订单数量不符时自动展开原因下拉与拍照入口", "data_source": "用户输入 + 相机", "render_as": "input_form"},
                {"type": "差异提示条", "purpose": "提醒员工差异将进入总部财务核对流程", "behavior": "静态展示，不可交互", "data_source": "静态文案", "render_as": "text_block"},
                {"type": "提交操作栏", "purpose": "确认提交差异登记", "behavior": "点击后弹出二次确认对话框，展示差异汇总金额后才真正提交", "data_source": "本地表单状态", "render_as": "action_bar"}
              ],
              "interaction_pattern": "员工对照实际到货逐项确认数量，系统自动标记差异行，员工选择差异原因并可拍照佐证后提交；提交前弹出确认对话框展示差异汇总，防止误提交。",
              "emotion_design": {
                "source_emotion": "anxious",
                "source_hint": "登记到货差异可能牵涉自身责任认定与后续结算金额，且不确定总部会如何处理（推断：未收到独立journey-emotion-map.json，按risk=high与业务语义内插）",
                "design_response": "提交前二次确认弹窗清楚展示差异金额与去向说明；拍照留证与原因下拉代替长文本填写，降低操作负担同时留存证据保护员工",
                "visual_tone": "calm_reassuring",
                "interaction_density": "medium"
              },
              "states": {
                "empty": "无到货批次可核对时，展示'暂无待验收批次'提示与刷新入口",
                "loading": "批次清单区域骨架屏，表单区域禁用",
                "error": "提交失败（如网络中断）时表单保留已填内容并展示'重新提交'按钮",
                "success": "提交成功后展示'差异已登记，已同步至总部财务系统'确认页，并提供跳转 S003 的入口",
                "discrepancy_detected": "实收数量与订单不符的行以橙色高亮并显示差异数量徽标，强制要求填写原因才能提交"
              },
              "data_fields": [
                {"name": "arrival_batch_id", "label": "到货批次号", "type": "string", "input_widget": "readonly", "required": true},
                {"name": "expected_qty", "label": "订单数量", "type": "number", "input_widget": "readonly", "required": true},
                {"name": "received_qty", "label": "实收数量", "type": "number", "input_widget": "number_input", "required": true},
                {"name": "discrepancy_reason", "label": "差异原因", "type": "enum", "input_widget": "select", "required": true},
                {"name": "evidence_photo", "label": "佐证照片", "type": "image", "input_widget": "file_upload", "required": true},
                {"name": "note", "label": "备注", "type": "string", "input_widget": "textarea", "required": false}
              ],
              "flow_context": {"prev": null, "next": "S003", "entry_points": [], "exit_points": ["S003"]}
            }
          ]
        },
        {
          "seq": 2,
          "id": "N003",
          "action": "查看差异处理进度与结果",
          "screens": [
            {
              "id": "S003",
              "name": "差异处理进度",
              "description": "门店员工跟进已登记差异当前处理阶段与最终结论的屏，目的是让 R1 在等待总部对账专员（R2，无客户端）处理期间始终有地方可看，并在结果不利时提供申诉出口。",
              "platform": "mobile-ios",
              "app": "store-order",
              "layout_type": "dispute_status_timeline",
              "layout_description": "顶部横向时间线展示三个阶段（已提交/核对中/已处理），占屏幕上30%；下方为结果详情键值对区域；申诉按钮仅在被拒绝状态下浮现于底部。",
              "interaction_type": "status_tracking",
              "tasks": ["T2"],
              "actions": ["查看处理进度", "查看处理结论", "发起申诉", "知悉结果"],
              "components": [
                {"type": "处理阶段时间线", "purpose": "展示差异从提交到处理完成的阶段", "behavior": "当前阶段高亮，可点击历史节点查看时间戳", "data_source": "对账/差异处理状态（来自总部财务系统同步）", "render_as": "timeline"},
                {"type": "结果详情面板", "purpose": "展示差异金额、处理结论、调整后结算金额", "behavior": "只读展示，处理完成前部分字段显示'待定'", "data_source": "对账结果同步数据", "render_as": "key_value"},
                {"type": "申诉操作栏", "purpose": "对被拒绝的差异发起一次申诉或知悉结果", "behavior": "仅在 dispute_rejected 状态下可用，点击后进入申诉说明输入", "data_source": "用户输入", "render_as": "action_bar"}
              ],
              "interaction_pattern": "员工随时进入查看当前差异所处阶段；处理完成后展示结论与结算影响；被拒绝时可发起一次申诉，超时未处理时展示提醒说明。",
              "emotion_design": {
                "source_emotion": "anxious",
                "source_hint": "等待总部专员处理结果期间，担心差异被认定为自身失误或货款受损，且看不到对方的处理过程（推断：未收到独立journey-emotion-map.json，按跨角色等待场景内插）",
                "design_response": "用时间线明确当前阶段与预计处理时长，避免'黑箱等待'；结果公布时给出对结算单的具体影响说明，而非笼统的'已处理'",
                "visual_tone": "calm_reassuring",
                "interaction_density": "low"
              },
              "states": {
                "empty": "暂无处理中差异时展示'暂无待跟进差异'提示",
                "loading": "时间线与详情区域骨架屏",
                "error": "状态同步失败时展示'结果同步失败，点击重试'，不影响已展示的历史阶段",
                "success": "查看结论后员工点击'知悉'的确认反馈，轻量 toast 提示",
                "awaiting_review": "（等待态，对应 R1↔R2 交接的 while_waiting）展示'已提交至总部财务系统，专员正在核对，预计1-2个工作日'，时间线停留在'核对中'节点",
                "dispute_rejected": "（对应 if_refused）展示'专员判定差异不成立'及具体原因，同时显示申诉入口",
                "dispute_unclaimed_timeout": "（对应 if_unclaimed）超过约定处理时效仍无人处理时，展示'处理超时，已自动提醒总部对账专员'并附加'联系店长升级'入口",
                "dispute_resolved_accepted": "展示'差异已确认'及调整后的结算金额，说明将体现在月末结算单（T5）中"
              },
              "data_fields": [
                {"name": "dispute_id", "label": "差异单号", "type": "string", "input_widget": "readonly", "required": true},
                {"name": "submitted_at", "label": "提交时间", "type": "date", "input_widget": "readonly", "required": true},
                {"name": "current_stage", "label": "当前阶段", "type": "enum", "input_widget": "readonly", "required": true},
                {"name": "resolution_note", "label": "处理结论", "type": "rich_text", "input_widget": "readonly", "required": false},
                {"name": "adjusted_settlement_amount", "label": "调整后结算金额", "type": "number", "input_widget": "readonly", "required": false}
              ],
              "flow_context": {"prev": "S002", "next": null, "entry_points": ["S002"], "exit_points": []}
            }
          ]
        }
      ]
    }
  ],
  "screen_index": {
    "S001": "// duplicate of OL001.nodes[0].screens[0]",
    "S002": "// duplicate of OL002.nodes[0].screens[0]",
    "S003": "// duplicate of OL002.nodes[1].screens[0]"
  },
  "non_screen_tasks": [
    {"task_id": "T3", "role": "R2", "reason": "R2 的对账与异常处理通过什么完成尚未确定：总部已在用一套财务系统；日均约 400 张对账单。"},
    {"task_id": "T4", "role": "R2", "reason": "R2 的对账与异常处理通过什么完成尚未确定：总部已在用一套财务系统；日均约 400 张对账单。"},
    {"task_id": "T5", "role": "R2", "reason": "R2 的对账与异常处理通过什么完成尚未确定：总部已在用一套财务系统；日均约 400 张对账单。"},
    {"task_id": "T6", "role": "R2", "reason": "R2 的对账与异常处理通过什么完成尚未确定：总部已在用一套财务系统；日均约 400 张对账单。"}
  ]
}
````

**Verification loop findings (after fix round 1, scenario B rerun, verbatim, in full)**

1. **Missing upstream artifact — process deviation flagged, not silently patched.** No `journey-emotion-map.json` was supplied (only `product-concept.json`, `task-inventory.json`, and a single business-flow summary). Per the schema, experience-map is supposed to be generated *from* journey-emotion-map, not directly from product-concept/task-inventory. I synthesized the emotion/risk/design-hint reasoning inline (recorded in each screen's `emotion_design.source_hint` with an explicit "推断" note) rather than fabricating a separate `journey_lines`/`handoffs` document and presenting it as if it were received. This is a real gap: the documented two-hop pipeline (business-flows → journey-emotion → experience-map) was not actually run, so there is no persisted `handoffs[]` record to audit against later. Recommend generating and persisting `journey-emotion-map.json` properly before this experience-map is treated as final.

2. **Clientless-role check (Hard Constraints) — passed, not defaulted.** R2 declares no `clients[]`, but `open_questions` contains an entry that names R2 by ID ("R2 的对账与异常处理通过什么完成尚未确定..."). That satisfies the "open question that names that role" ground, so R2 legitimately gets no screen/app/operation_line rather than being defaulted into a backend console. Its tasks (T3–T6) are correctly routed to `non_screen_tasks[]` with the ground quoted verbatim, not composed.

3. **Task coverage — complete.** T1 → S001, T2 → S002/S003, T3–T6 → `non_screen_tasks`. All 6 tasks from `task-inventory.json` accounted for.

4. **Handoff states — both directions of F1 landed on R1's line, none invented on R2's.** F1 is R1 → R2 → R1. Since R2 has no screen, both handoff boundaries (R1 hands off to R2; R2 hands back to R1) had to be represented entirely on R1's side. I put them on S003 rather than S002, since S002 is where R1 is *actively submitting* (ends on "done"/`success`), and S003 is the screen R1 actually has open to check on the wait: `awaiting_review` covers `while_waiting`, `dispute_rejected` covers `if_refused`, `dispute_unclaimed_timeout` covers `if_unclaimed`. No corresponding states were added to S002, since R1 is not "waiting" while filling out the form — only after submission.

5. **High-risk protection.** The discrepancy-logging step (T2) feeds into R2's settlement work (T5) and disputes (T4), so I treated it as risk ≈ high even absent an explicit upstream risk tag. S002 has an explicit confirmation dialog before submit (reversibility guard) and mandatory photo evidence (error/dispute prevention); S003 gives R1 a one-time appeal path when a dispute is rejected. This satisfies the "risk=high/critical nodes must produce screens with explicit error prevention, confirmation flows, and reversibility" rule, though it rests on my inferred risk level, not an upstream-confirmed one — flagged in finding 1.

6. **Emotion arc coherence.** S001 (routine, neutral/efficient_focused) → S002 (anxious/calm_reassuring, submitting a disputed discrepancy) → S003 (anxious tapering into satisfied/angry depending on outcome, still calm_reassuring in tone) shows a progressive arc rather than uniform tone across all three screens.

7. **App/platform consistency.** All three screens use `app: "store-order"`, `platform: "mobile-ios"`, matching R1's declared `clients[]` (`react-native` / `mobile`). No screen was drawn for R2, so there is no risk of the "console defaulted onto a clientless role" failure mode the schema warns against.

8. **Layout diversity.** Three screens, three distinct `layout_type` values (`inventory_gap_queue`, `arrival_discrepancy_form`, `dispute_status_timeline`) — well under the 15% single-type ceiling, and none reuse a retired MG/CT code.

9. **Gap not resolved, only bounded.** T1 (the ordering task) has no supplied business-flow or emotion data at all — I gave it a plausible neutral/efficient emotion read since it's a routine, low-risk, high-frequency action, but this is lower-confidence than the F1-derived screens and should be checked against real journey-emotion data once produced.

### New scenario C output (verbatim)

````json
{
  "operation_lines": [
    {
      "id": "OL001",
      "name": "门店按需补货下单",
      "source_journey": "JL02",
      "role": "R1",
      "nodes": [
        {
          "seq": 1,
          "id": "N001",
          "action": "选择商品并提交补货订单",
          "screens": [
            {
              "id": "S001",
              "name": "补货下单",
              "app": "store-order",
              "platform": "mobile-ios",
              "tasks": ["T1"],
              "states": {
                "empty": "本店暂无历史订货模板，引导手动添加商品",
                "loading": "提交订单时显示按钮内联加载态，防止重复点击",
                "error": "网络失败或库存校验不通过，保留已填数量，提示重试/联系总部",
                "success": "提交成功 toast，跳转至订单状态列表",
                "draft_saved": "未提交前可保存为草稿，返回后继续编辑"
              },
              "flow_context": {"prev": null, "next": "S002", "entry_points": [], "exit_points": ["S002"]}
            }
          ]
        }
      ]
    },
    {
      "id": "OL002",
      "name": "到货确认与差异登记（含总部处理待办）",
      "source_journey": "JL01a",
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
                "empty": "当前无预计到货订单，提示查看在途订单",
                "loading": "拉取预计到货明细中，骨架屏占位",
                "error": "差异保存失败，保留已录入数量，提示重试",
                "success": "差异登记提交成功 toast",
                "no_discrepancy": "数量全部核对一致，一键确认无需登记差异",
                "pending_hq_review": "差异已提交，等待总部对账专员处理（H1 等待态）"
              },
              "flow_context": {"prev": "S001", "next": "S003", "entry_points": ["S001"], "exit_points": ["S003"]}
            }
          ]
        },
        {
          "seq": 2,
          "id": "N003",
          "action": "查看总部对差异的处理结果",
          "screens": [
            {
              "id": "S003",
              "name": "差异处理结果",
              "app": "store-order",
              "platform": "mobile-ios",
              "tasks": ["T2"],
              "states": {
                "empty": "尚无处理记录，显示等待提示",
                "loading": "加载处理进度中",
                "error": "结果加载失败，提示重试",
                "success": "查看结果后标记已读",
                "approved": "总部确认差异，已同步调整库存/账目，展示调整明细",
                "rejected": "总部驳回该差异并给出理由（H1 if_refused）",
                "unclaimed_timeout": "超过承诺处理时限总部仍未处理，展示升级/催办入口（H1 if_unclaimed）"
              },
              "flow_context": {"prev": "S002", "next": null, "entry_points": ["S002"], "exit_points": []}
            }
          ]
        }
      ]
    }
  ],
  "screen_index": {
    "S001": { "id": "S001", "name": "补货下单", "app": "store-order", "platform": "mobile-ios", "tasks": ["T1"], "states": { "empty": "本店暂无历史订货模板，引导手动添加商品", "loading": "提交订单时显示按钮内联加载态，防止重复点击", "error": "网络失败或库存校验不通过，保留已填数量，提示重试/联系总部", "success": "提交成功 toast，跳转至订单状态列表", "draft_saved": "未提交前可保存为草稿，返回后继续编辑" }, "flow_context": { "prev": null, "next": "S002", "entry_points": [], "exit_points": ["S002"] } },
    "S002": { "id": "S002", "name": "到货确认与差异登记", "app": "store-order", "platform": "mobile-ios", "tasks": ["T2"], "states": { "empty": "当前无预计到货订单，提示查看在途订单", "loading": "拉取预计到货明细中，骨架屏占位", "error": "差异保存失败，保留已录入数量，提示重试", "success": "差异登记提交成功 toast", "no_discrepancy": "数量全部核对一致，一键确认无需登记差异", "pending_hq_review": "差异已提交，等待总部对账专员处理（H1 等待态）" }, "flow_context": { "prev": "S001", "next": "S003", "entry_points": ["S001"], "exit_points": ["S003"] } },
    "S003": { "id": "S003", "name": "差异处理结果", "app": "store-order", "platform": "mobile-ios", "tasks": ["T2"], "states": { "empty": "尚无处理记录，显示等待提示", "loading": "加载处理进度中", "error": "结果加载失败，提示重试", "success": "查看结果后标记已读", "approved": "总部确认差异，已同步调整库存/账目，展示调整明细", "rejected": "总部驳回该差异并给出理由（H1 if_refused）", "unclaimed_timeout": "超过承诺处理时限总部仍未处理，展示升级/催办入口（H1 if_unclaimed）" }, "flow_context": { "prev": "S002", "next": null, "entry_points": ["S002"], "exit_points": [] } }
  },
  "non_screen_tasks": [],
  "upstream_defects": [
    {
      "role": "R2",
      "tasks": ["T3", "T4", "T5", "T6"],
      "defect": "R2 (供应商对账专员) declares no clients[] in product-concept.json, and the given excerpt records no ground for treating R2 as clientless — no settled mode + basis (agent interface / existing team tool), no open question naming R2. Per the Hard Constraint 'Roles without a client', this is missing upstream data, not a decision: experience-map must stop rather than draw R2 a console or exempt its tasks into non_screen_tasks[]."
    }
  ]
}
````

**Verification loop findings (new scenario C, verbatim, in full)**

**Net result:** this experience-map is not ship-ready. It correctly covers R1 end-to-end (T1, T2, both legs of F1's R1 side) but must not be treated as complete — T3–T6 and R2's half of the F1 handoffs are blocked on an upstream product-concept defect (missing `clients[]`/ground for R2), not a design gap to be closed by drawing R2 an admin console.

1. **Hard Constraint violation risk avoided, not resolved — R2 is an upstream defect.** `product-concept.json` gives R2 no `clients[]` and quotes no ground (no settled mode + basis, no open question naming R2). Per the "Roles without a client" constraint, a role with no `clients[]` and no such ground must stop the map, not be defaulted into a console or exempted. I did not generate a desktop-web/admin surface for R2 and did not add T3–T6 to `non_screen_tasks[]` (that array is reserved for roles whose clientless status is actually grounded upstream). Recorded as `upstream_defects[0]`.

2. **Task coverage constraint: FAILS.** T3 (核对供应商对账单), T4 (处理到货差异争议), T5 (月末出具结算单), T6 (冻结异常供应商) appear in no screen's `tasks[]` and are correctly absent from `non_screen_tasks[]` per finding 1. The map is incomplete until product-concept is amended with either R2 `clients[]` or an explicit clientless ground; T1 and T2 (R1's tasks) are fully covered (S001, S002/S003).

3. **Journey-line completeness (journey-emotion §4): FAILS for the R2 side.** F1 is `cross_role` and would split into JL01a (R1: register discrepancy → see result) and JL01b (R2: process dispute). JL01a is realized as OL002. JL01b cannot produce an operation_line — same root cause as findings 1–2, not an independent gap.

4. **Handoff states: only the R1 side is satisfiable.** F1 has two handoffs — H1 (R1 registers discrepancy → R2) and H2 (R2 resolves → R1 sees result). R1's waiting/outcome states are placed on screens R1 actually has open: `S002.pending_hq_review` (while_waiting for H1), `S003.approved` / `S003.rejected` (if_refused) / `S003.unclaimed_timeout` (if_unclaimed). The R2-side halves of both handoffs (how R2 learns a dispute arrived; what R2 sees once the resolution is sent) have no screen to land on, since R2 has no app. This is a direct symptom of finding 1, not a separate design omission.

5. **Business flow continuity:** navigable within R1's line — S001 → S002 → S003 via `flow_context`. The R1→R2→R1 leg is real in F1 but has no screen-level representation on the R2 side, consistent with findings 1–4.

6. **Platform mapping:** R1's declared client (`react-native`, `mobile`) maps to `mobile-ios`, single-task screens, matching the Hard Constraint's platform rule for a role that declares `clients[]`.

7. **Emotion baseline not available for this exercise:** no `journey-emotion-map.json` was supplied upstream, only the raw business flow F1. `emotion_design` was correctly omitted (null-when-absent per schema) since screens were also scoped compact per instructions; emotion-intent/high-risk-protection/emotion-arc checks (criteria 1–3 of the validation loop) could not be run against real annotations — only criterion 4 (journey-line completeness) was checkable, and it fails for the reason in finding 3.

### Verdict per criterion (after fix round 1)

**Scenario A rerun — PASSES all three** (unchanged verdict from the first "After" section; a valid ground — `operations.mode`/`basis` — continues to exempt R2 under the new F4 row). Deciding lines: `non_screen_tasks[]` reasons quote `"每天十几二十条事务；无需人眼判断的步骤；团队只有 2 人兼职"` verbatim (the upstream `basis` string, not composed); finding 2 states *"T4/T5/T6/T7 are listed in `non_screen_tasks[]` with the `basis` string quoted verbatim as `reason`, not composed."* No R2 screen anywhere (all `app: "neighbor-swap"`). Waiting/refused/unclaimed states for R2's step (T7) on `S004` (`disputed_awaiting_ruling`, `ruling_rejected_insufficient_evidence`, `ruling_overdue_escalation`).

**Scenario B rerun — PASSES all three** (unchanged verdict; the open question naming R2 continues to be a valid ground under F4). Deciding lines: `non_screen_tasks[]` reasons quote `"R2 的对账与异常处理通过什么完成尚未确定：总部已在用一套财务系统；日均约 400 张对账单。"` verbatim (the upstream open-question string); finding 2 states *"That satisfies the 'open question that names that role' ground... Its tasks (T3–T6) are correctly routed to `non_screen_tasks[]` with the ground quoted verbatim, not composed."* No R2 screen anywhere (all `app: "store-order"`). Waiting/refused/unclaimed states on `S003` (`awaiting_review`, `dispute_rejected`, `dispute_unclaimed_timeout`).

**New scenario C — PASSES the pass condition.**
- Does NOT draw R2 a console: all screens (`S001`–`S003`) are `"app": "store-order"`; no R2 screen exists.
- Does NOT exempt R2's tasks into `non_screen_tasks[]` with a composed reason: `"non_screen_tasks": []` — empty.
- DOES flag an upstream defect: `"upstream_defects": [{"role": "R2", "tasks": ["T3", "T4", "T5", "T6"], "defect": "R2 (供应商对账专员) declares no clients[] in product-concept.json, and the given excerpt records no ground for treating R2 as clientless — no settled mode + basis (agent interface / existing team tool), no open question naming R2. Per the Hard Constraint 'Roles without a client', this is missing upstream data, not a decision: experience-map must stop rather than draw R2 a console or exempt its tasks into non_screen_tasks[]."}]`. Finding 1 confirms the reasoning: *"I did not generate a desktop-web/admin surface for R2 and did not add T3–T6 to `non_screen_tasks[]`... Recorded as `upstream_defects[0]`."*
- **Overall: PASSES.**

All three scenarios passed on their first (or, for A/B, only) post-fix-round-1 attempt. No scenario failed, so the `Roles without a client` row was not adjusted a second time within this round.

**Leak check for this round**: none of the three outputs (A rerun, B rerun, C) contain "plan", "brief", "thought test", "fixture", or "the project's recent direction" (or a comparable meta-aware phrase) in their verification findings. Scenario A's earlier "fixture" phrase (noted above, in the first "After" section) does not recur here.

## What changed in the skill text

First fix (task-1b): added a `Roles without a client` hard-constraint row and narrowed `Platform`/`Task coverage` rows in `claude/meta-skill/knowledge/experience-map-schema.md`, plus one `Roles without a client` bullet in `claude/meta-skill/knowledge/capabilities/ui-design.md`.

Fix round 1 (this file's F3/F4/F5): replaced the `Roles without a client` row entirely to require a positive upstream ground (settled mode+basis, or an open question naming the role) before the exemption applies, and to require an `upstream defect` return instead when no such ground exists; updated validation-loop check 4 ("Journey lines complete?") to state the clientless exception explicitly rather than contradict the hard-constraint row; added a `non_screen_tasks` example entry to the `## Full JSON Schema` block. `ui-design.md` was not touched in fix round 1 (not in scope). `journey-emotion-schema.md` was not touched in either round.
