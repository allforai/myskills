# megastorm — 大目标全自治流水线 skill 设计

**日期**: 2026-06-09
**状态**: 设计已收敛,spec review 通过(2 轮,✅ Approved)
**类型**: 新 skill(独立小插件,源码在 myskills repo,全局命令调用)

## 目标

提供一个 skill / 全局命令 `/megastorm <目标>`,把 superpowers 的 `brainstorming` /
`writing-plans` / `executing-plans` 串成一条流水线,承接**比单次 brainstorming 更大的目标**:

> 给一个目标 → 分析现状 → 拆成 M 个模块 → 逐模块 brainstorming 出多份 spec →
> Workflow 生成 design → 闭环思维校验全部文档 → Workflow 生成 plan →
> 逆向思维审核全部 spec/design/plan → 都通过后编排任务 → Workflow(Sonnet)并发执行直到完成。

**核心不变式**:`决策全前置 → 自治 → 自修复环 + 升级才停`。
所有人类交互集中在最前面;一旦进入自治阶段,除非校验不收敛/需要新决策才浮出给人,中途不停。

**与 bootstrap/run 的关系**:无关。这是独立的新 skill,完全走 superpowers 的
spec/design/plan 词汇与产物风格,不碰 meta-skill 的 node-spec / `.allforai` 机制。

## 非目标(YAGNI)

- 不替代、不演进现有 `/bootstrap` + `/run` 引擎。两套并存。
- 不发明新的产物命名规范;模块级 spec/design/plan 一律复用 superpowers 各 skill 的原生格式。
- 自治阶段不做"假设+静默续跑";凡需要新人类决策一律升级浮出(见 §4 校验语义)。

## §0 原语映射(Primitives)— 每个阶段到底调什么

把抽象词钉到真实工具,避免"Workflow / pipeline / parallel"被当成未定义术语:

- **"Workflow" = Claude Code 内置的 Workflow 工具**(多 agent 编排原语),不是要新造的引擎。真实算子:
  - `agent(prompt, {schema, model, isolation, label, phase})` — 派一个 subagent;`schema` 强制结构化返回。
  - `pipeline(items, stage1, stage2, …)` — 每个 item 独立流过各 stage,无 barrier。
  - `parallel(thunks)` — 并发 + barrier。
  - Workflow **只能由主会话(我)调用**;用户敲 `/megastorm` 即显式 opt-in,我在主循环里调它。
- **交互式 skill 只在主会话跑,绝不塞进 Workflow agent**(这是本设计最关键的边界):
  - `superpowers:brainstorming`、`superpowers:writing-plans` 是**强交互、要用户拍板**的,
    无法在 headless 的 Workflow `agent()` 里阻塞等人。
  - 因此 **Phase 0** 的 brainstorming 由**主会话用 Skill 工具**逐模块交互调用(人在环)。
  - **Phase 1** 的 design / plan 由 **Workflow `agent()` subagent** 完成,其 prompt
    **内联 brainstorming / writing-plans 的方法论**(不去调那两个交互 skill 本身),
    产出标准格式的 `-design.md` / plan。这就是"自治、人不在环"与"交互 skill"之间的硬边界。
  - `superpowers:executing-plans` 的纪律(逐任务实现 + 自验)同样以**方法论内联**进 Phase 1.6
    的执行 agent prompt,而非整体调用该交互 skill。
- **每阶段原语对照**:

  | 阶段 | 原语 | 形态 |
  |------|------|------|
  | Phase -1 预检 | Skill 注册表查询 | 主会话 |
  | Phase 0 拆模块 / 逐模块 spec | `Skill: superpowers:brainstorming` | 主会话,交互 |
  | Phase 1.1 Design | Workflow `pipeline`/`parallel` + `agent`(内联 brainstorming 方法论) | 自治 |
  | Phase 1.2 闭环校验 | 确定性脚本 + Workflow `agent`(LLM critic) | 自治 |
  | Phase 1.3 Plan | Workflow `agent`(内联 writing-plans 方法论) | 自治 |
  | Phase 1.4 逆向审查 | Workflow `agent`(critic) | 自治 |
  | Phase 1.5 编排 | 确定性脚本(读 plan 的 `touched_paths` 字段建 DAG) | 自治 |
  | Phase 1.6 并发执行 + 监督 | Workflow `pipeline`(执行 stage → 验收 stage),`isolation:'worktree'` 按需 | 自治 |

- **模型策略(省 token)**:
  - **规划/思考类全用默认模型**(继承主会话 = Opus):Phase 0 brainstorming、Phase 1.1 design、
    1.2 闭环 critic、1.3 plan、1.4 逆向 critic —— 这些是高价值推理,值 Opus。
  - **写代码执行 plan 的 task 用 Sonnet**(`agent(..., {model:'sonnet'})`):Phase 1.6 的**执行 agent**
    是大量、机械的实现工作,用 Sonnet 省 token。
  - **假完成监督 agent 保留默认模型(Opus)**:对抗式验收是信任根,不为省 token 牺牲核验严谨度。

## 形态与打包(§1)

- **源码**放 myskills repo:`claude/megastorm/`
  - `.claude-plugin/plugin.json` + `marketplace.json`(插件 + 市场清单)
  - `skills/megastorm.md`(主 skill,流水线编排指令)
  - `commands/megastorm.md`(`/megastorm` 命令入口)
- **全局调用**:`install.sh` 把 `/megastorm` 命令安装到 `~/.claude/`(形态对标 `/brainstorming`),
  任何项目里 `/megastorm <目标>` 都能显式启动。
- **触发方式**:重型、烧 token,**只显式触发**(用户敲 `/megastorm`),不靠 model 描述自动触发。
- **依赖**:全局 superpowers 的 `brainstorming` / `writing-plans` / `executing-plans`。

## Phase -1 — 预检(§2)

启动第一步,**早失败**:

- 检测 `brainstorming`(及 `writing-plans`、`executing-plans`)是否已安装。
  - **判据:Skill 注册表里是否出现命名空间名** `superpowers:brainstorming` /
    `superpowers:writing-plans` / `superpowers:executing-plans`(它们作为 superpowers 插件分发,
    实际落在 `~/.claude/plugins/cache/.../superpowers/<ver>/skills/`,**不是**裸的 `~/.claude/skills/<name>/`)。
  - **不要硬编码路径判断**——路径会因 superpowers 版本而变,硬编码会在已安装时误报"缺失"导致假安装循环。
    以会话内可见的 Skill 列表(`superpowers:*`)为准。
- 缺失 → **停下,引导安装**(提示 `/plugin` 安装 superpowers marketplace),装好后再继续。
  **不静默跳过**——缺依赖直接报错指路。

## Phase 0 — 决策全前置(主会话,交互)(§3)

所有人类决策在这里收完。

1. **析现状**:探仓库结构、近期 commit、`docs/`,产出现状摘要。
2. **拆模块**:跑一轮顶层 brainstorming,把目标拆成 M 个模块 + 边界 + 模块间依赖 →
   **用户拍板**模块划分。产出总览 overview.md 的初稿(模块表 + 依赖图)。
3. **逐模块 brainstorming**(顺序、交互):对每个模块调 `brainstorming` skill →
   产出标准 superpowers spec/design 文档,**每份用户批准**。
   - 完成判据:M 份模块 spec 全部落地并经用户确认。
   - 此后到 Phase 2 之间不停,除非升级浮出。

**"新人类决策"判定规则(Phase 0/1 边界的硬测试)**:自治阶段每当涌现一个问题,用此规则分流——
- **算"新人类决策" → 升级浮出**:任何会改变 ① 模块边界、② 对外/跨模块公开接口、
  ③ 用户可见的范围或行为 的问题。
- **算"自治可决" → 自行决定 + 记入假设台账,不停**:纯内部实现选择(命名、文件组织、
  局部算法、私有数据结构等),不影响上述三者。
这条规则把"决策全前置"落到可执行:Phase 0 收的就是会动①②③的决策;Phase 1 只允许动内部。

## Phase 1 — 自治流水线(方案 A:逐阶段 Workflow)(§4)

skill 主循环逐阶段调 Workflow,读回结果再决定下一步(model 留在环里,人不在环里)。
官方推荐的"多阶段就跑多个 workflow,一阶段一个"模式;可断点续、可分段查。

**升级契约(§4.2 / §4.4 共用)**:自治 stage 里需要浮出时,Workflow `agent` 用 schema 强制返回
`{status: "ok" | "escalate", reason?, evidence?}`。Workflow 脚本把任一 `escalate` 结果收集进返回值;
**主会话(skill)读到 workflow 返回里含 escalate → 立即 halt,把 reason+evidence 渲染给用户**,
等用户决策后再续跑(或携新决策重跑该 stage)。这样"升级才停"不是口号:停的主体是主会话,
不是 headless agent 自己问人。

### 4.1 Design
Workflow `pipeline`/`parallel` over modules:每份模块 spec → 一份 design doc(标准 superpowers `-design.md`)。
design agent 用**默认模型(Opus)**,prompt 内联 brainstorming 的方法论。

### 4.2 闭环校验(闭环思维)
Workflow 读**全部** spec + design,查**正向闭合**:
- 双向覆盖:每条 spec 需求都有 design 覆盖;每个 design 元素都能追溯回某条 spec。
- 跨模块接口一致(模块 A 暴露的接口 = 模块 B 消费的接口)。
- 无悬挂 / 无孤儿。
- **确定性检查脚本化**(覆盖、接口、孤儿用脚本确定性判定);**产物闭合性交 LLM critic**。
- **自修复环 ≤K 轮(默认 K=3)**:修复 agent 改文档 → 重校验。
  - 能自修的自修;**需要新人类决策 或 K 轮不收敛 → 升级**(skill halt,浮出给人,带证据)。

### 4.3 Plan
Workflow fan-out:每份 design → 一份 implementation plan(标准 superpowers plan)。
plan agent 用**默认模型(Opus)**,prompt 内联 writing-plans 方法论。
**plan 产物硬约束**:每个 task 必须带两个机器可读字段——
- `touched_paths: [...]`(本 task 预计改/建的文件路径,供 §4.5 建文件触碰图);
- `acceptance_cmd: "..."`(本 task 的机器可校验验收命令,如 `pytest tests/x.py`、`npm run build`,
  退出码 0 即过),供 §4.6 监督 agent 客观核验。
没有这两个字段的 plan 视为不合格,退回 plan agent 补全。

### 4.4 逆向审查(逆向思维)
Workflow critic 从 plan/design **倒推回 spec**,主动证伪:
- 可行性:plan 的步骤真的能落地吗?有无不可行/缺前置的步骤?
- 隐藏假设、漏掉的边界 / 错误路径。
- 倒着读(从结果反推),而非顺着读一遍。
- 同 §4.2 的**自修复环 + 升级才停**语义。

### 4.5 编排(确定性脚本)
把所有 plan 的任务摊平成**任务 DAG**——**全确定性,不靠 LLM 猜**:
- **文件触碰图**:直接读每个 task 的 `touched_paths` 字段(§4.3 已强制产出);两个 task 的
  `touched_paths` 集合相交 = 碰同文件。无需解析散文,故确定性可单测。
- **依赖拓扑**:task 间显式 `depends_on` + "写后读"推导(task B 的 `touched_paths` 被 task A 写过 → A 先)。
  - **同路径互写消歧**:两个 task 都写同一 path 且无 `depends_on` 时(互写,非读后写),
    按 plan 内声明顺序串行,并 WARN 提示——不并发该对,避免 DAG 层序歧义。
- Kahn 拓扑分层 + 环检测(复用 orchestrator 风格的确定性 BLOCK)。
- 落机器态(嵌进总览或轻量 `orchestration.json`,不喧宾夺主)。

### 4.6 并发执行 + 假完成监督(Workflow + Sonnet agent)
按拓扑层 `pipeline` 推进;**同层内碰不同文件的直接并发,碰同文件的进 worktree 隔离再合并**。

每个任务两个角色,**执行者 ≠ 验收者**(对抗式核验,直击"验收撒谎/假完成"):
1. **执行 agent(Sonnet,省 token)**:实现任务,跑完自验,声明完成。
2. **验收监督 agent(独立 subagent,默认模型 Opus,对抗立场)**:**不信任执行者自报**——
   - **独立 fresh context**(不喂执行者的会话/自报,只给 task 定义 + `acceptance_cmd` + 仓库现状),
     杜绝"读自报不考验运行现实"(本仓库记录的头号缺陷)。
   - **客观判据 = 亲自重跑 `acceptance_cmd`**(§4.3 plan 已为每个 task 钉死该命令);
     **退出码 0 且关键断言命中才算过**,而非"看起来完成"。
   - 再读真实 diff,核对改动确实对应 task 意图(防"跑过了但改错地方")。
   - 默认怀疑:重跑失败 / 无 `acceptance_cmd` / 证据不足 → 一律判**未完成**。
   - schema 强制返回 `{done: bool, rerun_exit_code: int, evidence: 重跑真实 stdout/stderr, refutation?}`。
   - 只有监督 agent `done:true` 才算 done;**驳回 → 退回执行 agent 重做 → 仍假完成 →
     升级浮出(走 §4 共用升级契约)**。

机制 = Workflow 对抗验证 pattern:`pipeline(tasks, 执行 stage, 验收 stage)`,执行后立刻接验收。
并发安全(§4.5):同层碰不同文件直接并发;碰同文件的执行 stage 用 `agent(..., {isolation:'worktree'})`
隔离,验收过后合并回主工作树。

失败恢复:**每个 task 一个软重试预算 ≤2**(执行/验收驳回共用这一个预算,非各自 2 个);
预算耗尽 / 合并冲突无法自解 = 硬失败 → 升级浮出。

## Phase 2 — 报告(§5)

总览 overview.md 收尾 + 终结报告:
- 自治阶段自行做出的假设台账;
- 所有升级点 + 处置;
- 已完成 / 已**独立验收**清单(区分"声称完成"与"监督确认");
- learning 抽取。

## 产物布局 —— superpowers 原生(§6)

一份**总览** + 其余全是标准 superpowers 文档。

```
docs/superpowers/specs/
├── YYYY-MM-DD-<goal>-overview.md     # 总览(唯一人读入口):目标、现状、模块拆分、依赖图、
│                                     #   各模块 spec/design/plan 链接、流水线状态、升级记录、假设台账
├── YYYY-MM-DD-<module-a>-design.md   # 每模块 brainstorming 产出 = 标准 superpowers spec/design
├── YYYY-MM-DD-<module-b>-design.md
└── ...
docs/superpowers/plans/
├── YYYY-MM-DD-<module-a>-plan.md     # writing-plans 标准产出
├── YYYY-MM-DD-<module-b>-plan.md
└── ...
```

- 总览 = 贯穿全程的索引,人读唯一入口。
- 模块级 spec/design/plan 完全用 superpowers 各 skill 原生格式与命名。
- 编排 DAG / 文件触碰图作为机器态最小化(嵌总览或轻量旁文件)。

## 两种"思维"的精确语义(§7)

- **闭环思维**(§4.2):正向闭合 —— 双向覆盖(spec↔design)、接口一致、无孤儿。
  确定性能查的脚本化,产物闭合性交 LLM critic。
- **逆向思维**(§4.4):反向可行性 —— 从结果倒推、主动证伪、找缺失,而非顺读一遍。

## 默认值

- skill 名:`megastorm`
- 自修复环轮数上限 K:3(**每个校验 stage 各自 3 轮**,§4.2 与 §4.4 不共用预算)
- §4.2 闭环的覆盖/接口/孤儿检查:脚本化(确定性);产物闭合性:LLM critic。
- 模型:规划/思考/校验/验收 = 默认模型(Opus);**仅 Phase 1.6 执行 agent = Sonnet**。

## 流程总览

```
/megastorm <目标>
  └─ Phase -1 预检(brainstorming 等是否安装,缺则引导安装)
  └─ Phase 0 决策全前置(交互):析现状 → 拆模块(用户拍板)→ 逐模块 brainstorming(逐份批准)
  └─ Phase 1 自治(逐阶段 Workflow,人不在环):
        Design → 闭环校验(自修复≤K/升级)→ Plan → 逆向审查(自修复≤K/升级)
        → 编排任务 DAG → 并发执行(执行 agent + 假完成监督 agent,worktree 按需隔离)
  └─ Phase 2 报告(假设台账、升级点、独立验收清单、learning)
```
