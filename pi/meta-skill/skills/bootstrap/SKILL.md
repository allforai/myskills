---
name: bootstrap
description: >
  Analyze the target project and generate its .allforai/ workflow (product concept,
  experience map, art, game design, verify nodes) plus a project-local /skill:run.
  User-invoked only via /skill:bootstrap or /skill:meta-skill; never invoke it yourself.
---

# Bootstrap Protocol — Pi Adapter

用户显式调用 `/skill:bootstrap [path]` 才运行。空参数表示当前目录。
先完整读取本文件，再读取 canonical bootstrap，并只应用下列替换。

## Canonical Source

包根目录是本文件上两级（含 `package.json` 的 `pi/meta-skill/`）。按这个顺序解析 canonical meta-skill 根：

1. `<package-root>/../../claude/meta-skill/`（myskills 源码布局）
2. `<package-root>/canonical/`（可选的独立快照）

两者都不存在则停止，说明需要从 myskills 源码安装，或放入 `canonical/` 快照。不要猜路径，也不要把 Claude 插件树链进 `~/.pi/agent/skills/`。

读完 `<canonical-root>/skills/bootstrap/SKILL.md` 全文，执行该协议，同时应用下面的 Pi 替换。
canonical 里的 `${CLAUDE_PLUGIN_ROOT}` 一律解析为 `<canonical-root>`。
本适配里的 `./scripts/`、`./mcp-ai-gateway/`、`../knowledge/` 相对包根目录解析。

Pi 没有 `AskUserQuestion`。阻塞性信息用纯文本问；不要发明答案，也不要用 Codex 的 assume-and-declare 代替同意。

## Required Pi Substitutions

### 1. Generated run entry

当 canonical 说：

- 读 `knowledge/orchestrator-template.md`
- 写 `.claude/commands/run.md`
- `mkdir -p .claude/commands`

改为：

- 读 `<package-root>/knowledge/orchestrator-template.md`（Pi 模板，不是 Claude/Codex 那份）
- 写目标项目 `.pi/skills/run/SKILL.md`
- `mkdir -p .pi/skills/run`

不要写 `.claude/commands/run.md`、`.codex/commands/run.md` 或 `.allforai/codex/flow.py`。
不要调用 Claude Workflow JS。共享合约仍是 `.allforai/bootstrap/workflow.json` 和复制过去的 orchestrator 脚本。

### 2. User invocation

当 canonical 让用户跑 `/run [goal]`，改为在目标项目调用 `/skill:run [goal]`。
没有 goal 时沿用 `.allforai/bootstrap/bootstrap-profile.json` 里捕获的任务目标。
完成摘要里把这条命令写清楚。

canonical 的后续用户步骤不变：`workflow.json.user_steps` 仍是
`["/cross-exam", "/product-review"]`（CLI / library-sdk 被 suppress 时为 `[]`）。
它们不是节点，也不要派发。摘要里按列表打印。`/cross-exam` 在已安装 `myskills-cross-exam` 时对应 `/skill:cross-exam`（没有独立子代理则该项会拒跑）。`/product-review` 尚未移植到 Pi，说明要在 Claude/Codex 上调用。不要假装已经跑过。

### 3. Plugin-root runtime copies

项目本地 helper 仍复制到目标项目，运行时只引用项目内路径。从 `<package-root>/scripts/`
（指向 Claude 树的符号链接）和 `<canonical-root>/knowledge/` 复制，至少包括 canonical Step 6.2 的集合：

- `scripts/orchestrator/check_artifacts.py`
- `scripts/orchestrator/product_intent.py`
- `scripts/orchestrator/evidence_freshness.py`
- `scripts/orchestrator/repair_authorization.py`
- `scripts/orchestrator/run_safety.py`
- `scripts/check_decision_inputs.py`
- `scripts/orchestrator/validate_bootstrap.py`
- `scripts/orchestrator/expand_game_2d_production.py`
- `scripts/orchestrator/reconcile_bootstrap_workflow.py`
- `scripts/orchestrator/validate_unattended_readiness.py`
- `scripts/orchestrator/render_approval_dashboard.py`
- `scripts/orchestrator/serve_approval.py`
- `scripts/orchestrator/apply_approval_action.py`
- `scripts/orchestrator/record_meta_skill_feedback.py`
- `scripts/orchestrator/record_run_event.py`
- `scripts/orchestrator/summarize_run_log.py`
- `knowledge/input-freshness.md`
- `knowledge/diagnosis.md`
- `knowledge/learning-protocol.md`
- `knowledge/feedback-protocol.md`
- 若发出 product inference：项目本地 `check_product_summary.py`

重建时保留已有的 `repair-authorizations.json` 和 `safety-quarantine.json`。
不要把 Pi 专用文件写进共享 `.allforai/bootstrap/` 树。若将来有 Pi 专用 helper，写到 `.allforai/pi/`。

### 4. Task capture and intent

在生成任何 bootstrap 产物之前捕获本次 `task_goal`。调用消息里已经清楚就用它；否则先问一个简短问题。
不要让 `/skill:run` 成为目标第一次出现的地方。写入 `.allforai/bootstrap/bootstrap-profile.json`。
`task_route` / `task_scope` 和需求合约以 `<canonical-root>/knowledge/bootstrap-planning.md` 为准。
缺文档不会自动变成全量重建；代码推断不能确认意图。

产品重建和新产品走 canonical `knowledge/product-intent-confirmation.md` 交互协议，包括 resume、journal 决策、scope 冻结和计划投影。使用复制后的 `product_intent.py`。沉默或中断不是批准。

Step 3.4 节点列表确认在 Pi 上也是临时的：审计之后对节点集或 `hard_blocked_by` 的改动，要在 Phase A 三透镜门之前作为相对已确认列表的 delta 再出示。把出示过的图和用户答复写入
`.allforai/bootstrap/plan-confirmation.json`，决定记入
`.allforai/bootstrap/plan-confirmation-journal.json`。计划或运行选择不要写入产品决策 journal。

### 5. Canonical graph and node-specs

写 `.allforai/bootstrap/workflow.json`。`state-machine.json` 是已退役的格式：只剩它而没有 `workflow.json` 的目录会被校验器以 `retired_bootstrap_format` 拒绝，重跑 bootstrap 即可。
node-specs 仍是运行时合约，并标准化为 `## Spec` / `## Design` / `## Task`。
每个节点至少有一个位于 `.allforai/bootstrap/` 下的完成产物。`docs/bootstrap/` 不是完成面。

### 6. Gates before offering run

复制 helper 之后，对生成项目运行 bootstrap、decision-inputs、unattended-readiness 三道共享门。
决策输入或 DAG 结构透镜不是 OK、或 node-spec 审计未过时，不得把 `/skill:run` 说成可执行。

### 7. 体验方向与体验质量门

canonical 这部分在 Pi 上照常执行，只有提问方式不同。

1. 按 canonical Step 1.6 把 `experience_priority {mode, reason}` 写进
   `.allforai/bootstrap/bootstrap-profile.json`。Pi 上 bootstrap 同样是这个字段的唯一生产者，
   下游节点只读它，不重新分类、不改写。
2. `task_route` 是 `new-product` 或 `product-reconstruction` 且 `experience_priority.mode != none` 时，
   无论 goal 名字是否匹配，都加载 `<canonical-root>/knowledge/capabilities/product-concept.md`、
   `<canonical-root>/knowledge/consumer-maturity-patterns.md`、
   `<canonical-root>/knowledge/journey-emotion-schema.md`，以及
   `<canonical-root>/knowledge/capabilities/app-design.md`（`is_game_project = false`）
   或 `<canonical-root>/knowledge/capabilities/game-design.md`（`is_game_project = true`）。
3. `experience-direction` 话题先 `propose` 再谈：用纯文本逐条列出 2–3 条方向并标明推荐的哪一条，
   然后等用户回复。用户挑了哪条就记 `select`；用户在那一轮明说"你定"才记 `delegate`，
   批次的 `user_reference` 写那条真实的用户发言，不是推荐本身、也不是展示提案的那一轮。
   assume-and-declare 产生不了 `select`，也产生不了 `delegate`；推荐和展示的默认值不是动作，
   沉默、中断、没有回复都不是委托。同一轮里刚 `propose` 出来的提案还不算当前提案轮：
   `select` 和 `delegate` 回应的必须是用户已经看过的那一轮，所以开出提案的这一轮到"列出方向、
   话题待定"为止；用户在还没有任何提案时就说"你定"，回应是开一轮提案，不是替他记 `delegate`。
   协议出处是
   `<canonical-root>/knowledge/product-intent-confirmation.md`，动作用复制后的 `product_intent.py` 记录。
4. 按 `<canonical-root>/knowledge/bootstrap-planning.md`（Must #9 与游戏路线的同一条）规划 design 与
   runtime 两道体验质量门节点：design 门在任何 UI 实现节点之前，runtime 门在最后一个 UI/产品验证/视觉 QA 之后，
   收尾与验收节点 `hard_blocked_by` runtime 那道门；两道门各自在
   `unattended-run-readiness-spec.json.required_repair_loops` 里有修复回路。
   把 `/skill:run` 说成可执行之前，第 6 节那三道共享门必须通过。

## Validation

生成后确认：

- `.allforai/bootstrap/bootstrap-profile.json` 有非空任务目标
- `.allforai/bootstrap/workflow.json` 存在
- `.allforai/bootstrap/node-specs/*.md` 存在
- `.pi/skills/run/SKILL.md` 存在，且 frontmatter `name: run`
- `.allforai/bootstrap/scripts/` 与 `protocols/` 已复制
- 没有新写 `.claude/commands/run.md`、`.codex/commands/run.md` 或 `.allforai/codex/flow.py`
- `workflow.json` 里每个节点都有至少一个根在 `.allforai/bootstrap/` 的 `exit_artifact`

## Completion

阻塞时报告具体缺口，不要打印成功文案，也不要把 `/skill:run` 标成 ready。
成功时列出写入的文件，并告诉用户下一步是 `/skill:run [目标]`。
