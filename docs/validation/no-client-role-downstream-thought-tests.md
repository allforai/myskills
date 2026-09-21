# No-client-role downstream thought test

Task: "A role without a client is received downstream, not given a default console" (`.superpowers/sdd/2026-09-22-pi-work-supplements-plan/task-1-brief.md`).

Date: 2026-09-22

## Baseline (before any file edit)

No file under `claude/meta-skill/knowledge/` was edited before this run. One read-only subagent (model `sonnet`) was dispatched with the exact prompt below.

### Prompt

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

### Subject output (verbatim)

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
  "non_screen_tasks": [
    {"task_id": "T4", "role": "R2", "reason": "R2 的 product-concept.json 条目 clients 为空、operations.mode=agent_interface，没有可承载屏幕的客户端；下架动作经 agent 接口执行，其后果反映在 S002 的 removed_by_moderation 态，而不是给 R2 画一个后台屏幕"},
    {"task_id": "T5", "role": "R2", "reason": "同上，无客户端。核实结果反映在 S001 的 pending_verification 态"},
    {"task_id": "T6", "role": "R2", "reason": "同上，无客户端。积分发放的后果反映在 S005 的 success 态和 S008 的 penalty_applied 态"},
    {"task_id": "T7", "role": "R2", "reason": "同上，无客户端。裁决过程经 agent 接口执行，R1 侧的等待/结果体验由 S007、S008 承接（对应 F2 的 handoff）"}
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

**Verification loop findings**

1. **Task coverage.** T1 -> S001/S002. T2 -> S003/S004. T3 -> S005 (and the negative branch S006). T4, T5, T6, T7 all belong to R2, whose `product-concept.json` entry has `clients: []` and `operations.mode: "agent_interface"` — there is no client surface to put a screen in. I did not invent an admin console/dashboard for R2. Instead I listed T4/T5/T6/T7 in a top-level `non_screen_tasks[]` array with the reason, and made sure each has a visible *consequence* on an R1 screen so the task isn't simply invisible: T4 -> `S002.removed_by_moderation`, T5 -> `S001.pending_verification`, T6 -> `S005.success` / `S008.penalty_applied`, T7 -> `S007`/`S008` end-to-end. This is a judgment call: the schema's hard-constraint table as currently written ("Every task must appear in at least one screen's tasks array") doesn't carve out this exception explicitly, so I'm flagging it rather than silently deviating — a stricter reading would call T4–T7 a coverage failure and I'd want a human or a schema update to confirm the `non_screen_tasks` escape hatch is acceptable.

2. **Journey-line completeness.** JL01 -> OL001, JL02 -> OL002, JL03a (R1 side of the F2 split) -> OL003. JL03b (R2 side of F2, T7) has no operation_line by design (no client), which is consistent with point 1 above rather than a missed mapping.

3. **Handoff states (F2: R1 投诉 -> R2 裁决 -> R1 看到结果).** Per journey-emotion-schema's Handoffs section, `while_waiting`, `if_refused`, `if_unclaimed` must land on a screen each *waiting role actually has open*. R2 has no open screen (no client), so only R1's side can carry these — I put them on S007: `reviewing` (while_waiting), `dispute_dismissed` (if_refused), `dispute_timeout_escalated` (if_unclaimed). This is intentionally one-sided; I did not try to fabricate an R2-side state for a role with no screen.

4. **High-risk protection.** The complaint/dispute path (S006-S008) carries the highest emotional intensity (angry -> anxious -> anxious/mixed) and the least reversible consequences (credit penalty, community standing). It gets explicit reversibility (appeal window on S008), confirmation before finalizing a handoff-not-complete on S005, and no silent timeouts (S007 auto-escalates rather than going quiet).

5. **Emotion arc coherence.** OL002/OL003 together show neutral(browse) -> anxious(propose) -> anxious->satisfied(handoff) -> angry(complaint) -> anxious(waiting) -> mixed/neutral_professional(verdict), which is a real arc rather than uniformly neutral screens; `visual_tone` shifts accordingly (efficient_focused -> calm_reassuring -> calm_reassuring -> neutral_professional) instead of repeating one tone.

6. **Platform/app constraints.** All 8 screens are `mobile-ios` / `app: neighbor-swap`, correctly derived from node role R1 throughout, including the cross-role operation line OL003 — no screen was mistakenly attributed to R2's app since R2 has none.

7. **layout_type diversity.** 8 distinct `layout_type` values across 8 screens (12.5% each), well under the 15% ceiling, and each name is business-purpose-specific rather than a generic/retired code.

8. **States.** Every screen has non-copy-pasted `empty/loading/error/success` plus at least one business-specific state; screens with no natural empty state (S005, S006, S007, S008) say so explicitly (`"n/a — ..."`) rather than omitting the key.

9. **Open question for a human/schema owner:** whether `non_screen_tasks[]` is the right shape for this pattern, or whether the schema should formalize it — right now I designed it ad hoc because the written hard-constraints don't yet address roles with `clients: []`.

### Verdict per criterion (baseline)

The baseline FAILS if any of the following three holds. Judged literally against the subject's output above:

1. **"a screen exists whose `app` belongs to R2, or whose `tasks` contain T4, T5, T6 or T7 as a human-operated screen"** — Does NOT hold. All 8 screens (`S001`–`S008`) declare `"app": "neighbor-swap"`, R1's app, derived from node role R1 throughout, including the cross-role operation line OL003. No screen's `tasks` array contains T4, T5, T6 or T7: `S001` and `S002` carry only `["T1"]`; `S003`/`S004` carry `["T2"]`; `S005`/`S006` carry `["T3"]`; `S007` and `S008` carry `"tasks": []`. No operations console, admin panel, dashboard, 后台 or 工作台 was invented for R2. **Criterion 1: not triggered.**

2. **"T4–T7 silently disappear — they appear nowhere in the output and the verification findings do not mention them"** — Does NOT hold. They appear explicitly in the top-level `non_screen_tasks[]` array (`{"task_id": "T4", "role": "R2", "reason": "..."}` etc.) and are the entire subject of verification finding 1: *"T4, T5, T6, T7 all belong to R2, whose `product-concept.json` entry has `clients: []` and `operations.mode: "agent_interface"` — there is no client surface to put a screen in... Instead I listed T4/T5/T6/T7 in a top-level `non_screen_tasks[]` array with the reason."* **Criterion 2: not triggered.**

3. **"the verification loop reports 'Task coverage' as passed while T4–T7 are on no screen and nothing explains why"** — Does NOT hold. The verification loop does not assert the coverage check passed; finding 1 explicitly flags it as an open, unresolved judgment call and explains the reasoning: *"This is a judgment call: the schema's hard-constraint table as currently written ('Every task must appear in at least one screen's tasks array') doesn't carve out this exception explicitly, so I'm flagging it rather than silently deviating — a stricter reading would call T4–T7 a coverage failure and I'd want a human or a schema update to confirm the `non_screen_tasks` escape hatch is acceptable."* Finding 9 repeats the same open question. Coverage is explained (R2 has no client surface), and it is not claimed to have "passed" without qualification. **Criterion 3: not triggered.**

**Pass condition** ("no R2 screen is invented, T4–T7 are accounted for explicitly, and R1's waiting states for the R2 裁决 step exist on an R1 screen"): all three hold — no R2 screen anywhere; T4–T7 are each named with a reason in `non_screen_tasks[]`; R1's waiting states for the F2 裁决 handoff exist on `S007` (`reviewing` = while_waiting, `dispute_dismissed` = if_refused, `dispute_timeout_escalated` = if_unclaimed).

**Overall baseline verdict: PASS.** No criterion is triggered, and all three pass conditions hold.

## Outcome

The baseline passed against all three fail criteria fixed in the brief. Per the brief's Step 2 instruction ("If it PASSES, skip to Step 6 and record in the file that no text was added because the existing text already holds"): **no text was added.** `claude/meta-skill/knowledge/experience-map-schema.md` and `claude/meta-skill/knowledge/capabilities/ui-design.md` are unchanged by this task — the existing text (schema + the upstream product-concept.json rule quoted in the prompt) already gave the subject enough to derive the correct behavior on its own, without a `non_screen_tasks[]` contract or a "Roles without a client" row being spelled out in the schema. Steps 3, 4 and 5 (add text, rerun, run validators) were not executed, since they are gated on baseline failure.
