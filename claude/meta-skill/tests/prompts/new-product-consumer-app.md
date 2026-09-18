# Bootstrap 新产品阶段：消费级语言学习应用

你是 bootstrap skill。在一个空仓库上执行 bootstrap 协议，产出 profile、体验方向决策与 workflow。

## 输入

### 仓库状态

```
./                 # 空仓库：无 .allforai/、无源码、无 package.json / pubspec.yaml / go.mod 等构建清单
```

没有任何已存在的模块、已批准的基线或历史决策日志可供复用。

### 用户请求（逐字）

> 我想做一个给普通人用的语言学习应用，手机端用 Expo，配一个服务端存学习记录和进度。
> 核心是"碎片化时间学习"：等车、排队、睡前几分钟就能学一小段，随时中断随时接上。
> 用户是完全没有语言学习习惯的上班族，不是专业学习者，别做成一个功能表。

## 要读的文件

- `claude/meta-skill/skills/bootstrap/SKILL.md`
- `claude/meta-skill/knowledge/bootstrap-planning.md`
- `claude/meta-skill/knowledge/product-intent-confirmation.md`
- `claude/meta-skill/knowledge/capabilities/product-concept.md`
- `claude/meta-skill/knowledge/capabilities/app-design.md`
- `claude/meta-skill/knowledge/consumer-maturity-patterns.md`
- `claude/meta-skill/knowledge/journey-emotion-schema.md`
- `claude/meta-skill/skills/app-design/40-qa/experience-quality-critique/SKILL.md`

## 执行步骤

### Step 1：判定 profile（SKILL.md Step 1.1-1.6）

从 task_goal、product_vision 与"产品服务谁"判定 `task_route` 与 `experience_priority`。
空仓库没有可逆向的既有实现，路由不得由"缺少产品文档"推导。
`experience_priority.mode` 只写一次，下游节点不得改写；`reason` 一句话说明服务对象。

### Step 2：知识加载（SKILL.md Step 2）

列出本次实际加载的知识文件，路径一律写成 `claude/meta-skill/...` 仓库相对路径。
带界面的产品路由有强制加载项（见 Step 2 第 9 条），不因目标名字没有命中 capability 名而跳过。

### Step 3：体验方向（product-intent-confirmation.md）

在 `experience-direction` 话题上先 `propose` 一轮：给出若干条互斥的方向提案，标注其中一条为推荐并给出 rationale。
然后记录用户这一轮的动作。推荐、默认值、沉默与未作答都不是动作；只有用户自己的 `select`，或用户明确交由模型代定的 `delegate`，
才把方向变成已确认项。不得把自己的推荐当成已确认结果。

### Step 4：规划 workflow（bootstrap-planning.md）

自由规划这个项目需要的节点，不从模板里挑。每个节点记录 `node_id`、`exit_artifacts`、`hard_blocked_by`、`skill_refs`。
设计规格与体验质量评审的产物路径按 `bootstrap-planning.md` 与评审 skill 的落地文本原样写，不要自造路径。
节点 id 由你自己命名——答案键以产物路径与集合谓词核对，不核对节点名，所以不要为了凑某个固定名字而改动图的形状。

### Step 5：无人值守就绪（SKILL.md Step 4 / bootstrap-planning.md）

为需要修复环的质量门各声明一条 `required_repair_loops`，写明 `qa_node_ids`、`repair_node_id`、`closure_node_ids`、`max_attempts`。

## 输出

严格按以下 JSON schema 输出，不添加额外字段：

```json
{
  "profile": {
    "task_route": "local-change|product-reconstruction|new-product",
    "experience_priority": {
      "mode": "consumer|admin|mixed|none",
      "reason": "<one sentence>"
    }
  },
  "loaded_knowledge": ["<repo-relative path>"],
  "experience_direction": {
    "proposed_count": <number>,
    "recommended": <number>,
    "user_action": "select|delegate"
  },
  "workflow": {
    "nodes": [
      {
        "node_id": "<string>",
        "exit_artifacts": ["<artifact path>"],
        "hard_blocked_by": ["<node_id>"],
        "skill_refs": ["<repo-relative path>"]
      }
    ]
  },
  "required_repair_loops": [
    {
      "qa_node_ids": ["<node_id>"],
      "repair_node_id": "<node_id>",
      "closure_node_ids": ["<node_id>"],
      "max_attempts": <number>
    }
  ]
}
```
