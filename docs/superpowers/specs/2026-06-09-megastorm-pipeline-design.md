# megastorm — 大目标全自治流水线 skill 设计

**日期**: 2026-06-09
**状态**: 设计已收敛,待 spec review
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
  - 判据:`~/.claude/skills/<name>/` 是否存在,或 Skill 列表里是否可见。
- 缺失 → **停下,引导安装**(提示 `/plugin` 安装 superpowers,或克隆/软链对应 skill 目录),
  装好后再继续。**不静默跳过**——缺依赖直接报错指路。

## Phase 0 — 决策全前置(主会话,交互)(§3)

所有人类决策在这里收完。

1. **析现状**:探仓库结构、近期 commit、`docs/`,产出现状摘要。
2. **拆模块**:跑一轮顶层 brainstorming,把目标拆成 M 个模块 + 边界 + 模块间依赖 →
   **用户拍板**模块划分。产出总览 overview.md 的初稿(模块表 + 依赖图)。
3. **逐模块 brainstorming**(顺序、交互):对每个模块调 `brainstorming` skill →
   产出标准 superpowers spec/design 文档,**每份用户批准**。
   - 完成判据:M 份模块 spec 全部落地并经用户确认。
   - 此后到 Phase 2 之间不停,除非升级浮出。

## Phase 1 — 自治流水线(方案 A:逐阶段 Workflow)(§4)

skill 主循环逐阶段调 Workflow,读回结果再决定下一步(model 留在环里,人不在环里)。
官方推荐的"多阶段就跑多个 workflow,一阶段一个"模式;可断点续、可分段查。

### 4.1 Design
Workflow fan-out:每份模块 spec → 一份 design doc(标准 superpowers `-design.md`)。
`pipeline` / `parallel` over modules。

### 4.2 闭环校验(闭环思维)
Workflow 读**全部** spec + design,查**正向闭合**:
- 双向覆盖:每条 spec 需求都有 design 覆盖;每个 design 元素都能追溯回某条 spec。
- 跨模块接口一致(模块 A 暴露的接口 = 模块 B 消费的接口)。
- 无悬挂 / 无孤儿。
- **确定性检查脚本化**(覆盖、接口、孤儿用脚本确定性判定);**产物闭合性交 LLM critic**。
- **自修复环 ≤K 轮(默认 K=3)**:修复 agent 改文档 → 重校验。
  - 能自修的自修;**需要新人类决策 或 K 轮不收敛 → 升级**(skill halt,浮出给人,带证据)。

### 4.3 Plan
Workflow fan-out:每份 design → `writing-plans` → 一份 implementation plan(标准 superpowers plan)。

### 4.4 逆向审查(逆向思维)
Workflow critic 从 plan/design **倒推回 spec**,主动证伪:
- 可行性:plan 的步骤真的能落地吗?有无不可行/缺前置的步骤?
- 隐藏假设、漏掉的边界 / 错误路径。
- 倒着读(从结果反推),而非顺着读一遍。
- 同 §4.2 的**自修复环 + 升级才停**语义。

### 4.5 编排
把所有 plan 的任务摊平成**任务 DAG**:
- 依赖拓扑(任务间先后)。
- 文件触碰分析(哪些任务碰重叠文件)。
- 落机器态(嵌进总览或轻量旁文件,不喧宾夺主)。

### 4.6 并发执行 + 假完成监督(Workflow + Sonnet agent)
按拓扑层 `pipeline` 推进;**同层内碰不同文件的直接并发,碰同文件的进 worktree 隔离再合并**。

每个任务两个角色,**执行者 ≠ 验收者**(对抗式核验,直击"验收撒谎/假完成"):
1. **执行 agent(Sonnet)**:实现任务,跑完自验,声明完成。
2. **验收监督 agent(独立 subagent,对抗立场)**:**不信任执行者自报**——
   - 亲自重跑该任务的验证命令(build/test),看真实退出码与输出;
   - 读真实改动的文件,核对任务验收标准是否**真的**成立;
   - 默认怀疑:证据不足即判**未完成**;
   - schema 强制返回 `{done: bool, evidence: 重跑真实输出, refutation?}`。
   - 只有监督 agent 确认,任务才算 done;**驳回 → 退回重做(软重试 ≤2)→ 仍假完成 → 升级浮出**。

机制 = Workflow 对抗验证 pattern:执行 stage 之后接 verify stage。

失败恢复:软失败重试 ≤2;硬失败 → 升级浮出。

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
- 自修复环轮数上限 K:3
- §4.2 闭环的覆盖/接口/孤儿检查:脚本化(确定性);产物闭合性:LLM critic。

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
