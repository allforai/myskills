# myskills

**Claude Code + OpenCode** 双平台插件集合，覆盖 **产品设计 → 开发锻造 → QA 验证 → 架构治理** 全链路。

## ✨ 新增：页面交互类型体系 v2（三轴模型）

将 product-design 的交互类型从 8 种（A-H）全量升级为 **37 种 × 三轴模型**，覆盖全平台、全产品类型、全用户属性。

### 三轴模型

| 轴 | 内容 | 说明 |
|---|---|---|
| **第一轴** | 37 种交互类型（8 大分类） | 纯行为契约，不含任何 UI 描述 |
| **第二轴** | 5 平台实现矩阵 | Web 桌面 / Mobile Web / iOS+Android / Windows / TUI |
| **第三轴** | 上下文预设 | 8 种产品类型 × 3 种用户属性 → 高/中/低频类型分布 |

**8 大分类（MG / CT / EC / WK / RT / SB / SY / TU）：**

| 前缀 | 分类 | 典型类型 |
|-----|------|---------|
| MG | 管理/CRUD | 只读列表、CRUD 集群、状态机、审批流、主从详情、树形管理、仪表盘、配置页 |
| CT | 内容消费 | Feed 流、内容阅读、Profile、卡片探索、媒体播放器、相册、搜索、Story |
| EC | 电商交易 | 商品详情、购物车、订单追踪 |
| WK | 协作办公 | IM 对话、频道、文档编辑、画布白板、看板、甘特图、文件管理 |
| RT | 通讯实时 | 通话、直播间、邮件、通知中心 |
| SB | 审核提交 | 审核型提交（提交方视角，与 MG4 审批流互为镜像） |
| SY | 引导系统 | Onboarding 引导、向导多步表单 |
| TU | TUI/CLI | 命令行、交互式菜单、日志流、进度任务流 |

### 行为原语索引（Behavioral Primitives）

交互类型之间共享底层行为单元。**凡共用同一原语的界面，前端实现可共享组件或逻辑。**

18 种原语（`VirtualList` / `InfiniteScroll` / `PullToRefresh` / `SwipeAction` / `DragAndDrop` / `StateMachine` / `AppendOnlyStream` / `RealtimeSync` / `FormWithValidation` / `MultiStepWizard` / `TreeNavigation` / `MediaPlayer` / `BatchSelection` 等）记录在 `product-design-skill/docs/interaction-types.md`，并在 `design-to-spec` 阶段自动消费：

**design-to-spec 新增 Step 2：行为原语识别 → 共享组件规划**
- 汇总项目中所有 `interaction_type`，查原语索引，找出 ≥2 个界面共用的原语
- 在逐页规格生成之前，先输出「共享组件规划表」（YAGNI：只出现 1 次的原语不封装）

### 全链路代号升级

`experience-map.md` / `ui-design.md` / `design-to-spec.md` 全部升级为新编码体系，旧 A-H 代号已清除，不保留向后兼容。

---

## 创新保真 + 状态闭环机制（v3.2.0）

### 创新保真机制

- **experience-map**: 创新界面自动标记（`innovation_screen` + `adversarial_concept_ref`）
- **ui-design**: 创新概念 UI 规格专节
- **task-execute**: core 级别创新任务 → Round 1 优先执行
- **seed-forge**: core 级别创新概念优先灌入

### 状态闭环机制

- **feature-gap**: 孤儿状态/幽灵状态/语义鸿沟检测
- **量化指标**: 状态闭环率 ≥ 95%，幽灵状态 = 0（零容忍）

---

## 30 秒上手

### OpenCode（远程 Git 安装，推荐）

```bash
# 1) 运行远程安装脚本（从 GitHub 克隆）
curl -fsSL https://raw.githubusercontent.com/allforai/myskills/main/install-remote.sh | bash

# 或者手动执行
git clone git@github.com:allforai/myskills.git ~/.opencode/skills/myskills
~/.opencode/skills/myskills/install-remote.sh

# 2) 在任意项目中创建项目配置
mkdir -p your-project/.opencode
cp ~/.opencode/skills/myskills/.opencode.template your-project/.opencode/config.json

# 3) 开始使用
/product-map              # 产品功能地图
/design-to-spec           # 设计转规格
/project-scaffold         # 生成代码脚手架
```

### OpenCode（本地路径安装，开发测试用）

```bash
# 仅建议在本地开发调试时使用
cd /path/to/myskills
./install-opencode.sh
```

### Claude Code（全局插件）

```bash
# 1) 安装四个插件（统一使用 add）
claude plugin add /path/to/myskills/product-design-skill
claude plugin add /path/to/myskills/dev-forge-skill
claude plugin add /path/to/myskills/deadhunt-skill
claude plugin add /path/to/myskills/code-tuner-skill

# 2) 启用插件（~/.claude/settings.json）
# 添加："product-design@myskills": true

# 3) 先做产品建模（建议起手）
/product-map

# 4) 需要全链路时，直接执行
/product-design full
```

---

## 你该从哪个插件开始？

| 你的目标 | 推荐插件 | 第一条命令 |
|---|---|---|
| 梳理产品功能、角色、任务 | product-design | `/product-map` |
| 生成高质量测试数据并验收实现 | dev-forge | `/seed-forge` / `/product-verify` |
| 查死链、CRUD 缺口、幽灵功能 | deadhunt | `/deadhunt` |
| 分析后端架构质量并给重构任务 | code-tuner | `/code-tuner full` |
| 一次跑完整链路 | product-design full 模式 | `/product-design full` |

---

## 四层架构

```
层级        插件              覆盖范围
─────────  ────────────────  ─────────────────────────────────────────────
产品层      product-design    概念→定义→交互→视觉→用例→查漏→剪枝→审计
开发层      dev-forge         种子数据锻造→产品验收（seed-forge / product-verify）
QA 层       deadhunt          死链→CRUD完整性→幽灵功能→字段一致性
架构层      code-tuner        合规→重复→抽象→评分
```

## 插件概览

### product-design (v3.8.0)

8 个技能，核心是先建图再分析：

`product-concept / product-map / journey-emotion / experience-map / interaction-gate / use-case / feature-gap / feature-prune / ui-design / design-audit`

### dev-forge (v2.5.0)

8 个技能，覆盖从设计规格到验收的完整开发链路：

`design-to-spec`（设计转实现规格）→ `project-setup`（环境初始化）→ `project-scaffold`（代码骨架生成）→ `task-execute`（任务执行）→ `e2e-verify`（端到端验证）→ `seed-forge`（种子数据锻造）→ `product-verify`（静态+动态验收）→ `shared-utilities`（公共工具）

### deadhunt (v1.9.0)

死链猎杀 + 流程验证：死链、CRUD 完整性、幽灵功能、字段一致性。

### code-tuner (v1.0.0)

服务端架构分析：合规检查、重复检测、抽象机会、综合评分（0-100）。

---

## 数据合约（.allforai）

所有插件共享 `.allforai/` 作为层间输入/输出：

```
product-design 产出 → .allforai/product-map/
                     .allforai/experience-map/
                     .allforai/use-case/
                     .allforai/feature-gap/
                     .allforai/feature-prune/
                     .allforai/design-audit/

dev-forge 产出     → .allforai/seed-forge/
                     .allforai/product-verify/

deadhunt 产出      → .allforai/deadhunt/
code-tuner 产出    → .allforai/code-tuner/
```

> 建议：先跑 product-design，再跑 dev-forge / deadhunt / code-tuner。

---

## 设计思想

> 用最小的用户能量输入，驱动最大的不确定性消除，同时在每个环节防止已消除的不确定性重新泄漏回来。

### 核心命题：受控熵减

一个产品从模糊想法到可执行规格的过程，本质是一场受控的熵减。想法是高熵的——无数种可能、无数个歧义。每经过一层处理，不确定性减少一些。最终输出的 JSON 规格是低熵的——字段明确、引用可追溯、行为可验证。

整个设计体系在做一件事：**让熵只降不升，防止它在任何环节回流。**

### 三个力学机制

#### 决策经济学 — 用最小代价消除最大不确定性

熵减需要能量，能量就是用户决策。用户的注意力是最稀缺的资源：

- **前置收集** — 在起点一次性批量收集决策，而不是在每个节点零散询问（原则 13）
- **搜索驱动的选择题** — 不问开放题，先调研再出选项，降低决策成本（原则 3）
- **上游消费链** — 已做过的决策自动传播到全链路，绝不重复询问（原则 13 延伸）
- **规模自适应** — 30 个问题逐条确认，300 个问题只确认异常项（原则 6）

> 让用户做尽量少的决策，但每个决策都在正确的时机、以正确的粒度呈现。

#### 信息保真 — 防止熵在流转中回流

决策产生了低熵的结构化数据，但数据在层间流转时会退化——字段丢失、语义漂移、创新被稀释。三道防线对抗退化：

- **事前标记** — 信息产生时打上结构化标签（创新等级、模式标签、频次分级），下游消费时不需要重新理解语义（原则 8、12）
- **事中校验** — 处理过程中持续检查一致性，发现偏移立即标记（原则 7、8）
- **事后审计** — 终审门禁做全链路追溯，确保没有孤儿节点、幽灵引用、语义鸿沟（原则 7、8）

核心约束：**只读不改上游**（原则 11）。发现上游问题时只报告不回退，因为级联修改是熵回流的最大来源。

#### 结构韧性 — 在不完美条件下维持秩序

现实中不可能所有前提都满足。系统不追求完美条件，而是在每个环节设计降级路径：

- 索引不存在 → 回退全量加载（原则 5）
- JSON 损坏 → 自动恢复 .bak（原则 9）
- 搜索失败 → 重试/替代关键词/让用户提供（原则 9）
- 上游不存在 → fallback 到自动检测/询问用户（原则 13）
- 并行冲突 → 分片写入、聚合去重（原则 10）

> 系统的默认状态不是"一切就绪"，而是"随时降级"。

### 统一模型

```
          用户决策（能量输入）
              │
              ▼
    ┌─────────────────────┐
    │   决策经济学         │  ← 最小能量消耗
    │   (少问、批量、传播)  │
    └────────┬────────────┘
             │ 产生低熵数据
             ▼
    ┌─────────────────────┐
    │   信息保真           │  ← 防止熵回流
    │   (标记、校验、审计)  │
    └────────┬────────────┘
             │ 层间传递
             ▼
    ┌─────────────────────┐
    │   结构韧性           │  ← 在缺陷中维持秩序
    │   (降级、恢复、隔离)  │
    └────────┬────────────┘
             │
             ▼
      可追溯、可审计、可执行的规格
```

13 条原则每一条都是这三个机制的具体实例：

| 力学机制 | 对应原则 |
|---------|---------|
| 决策经济学 | 2(用户裁决) 3(选择题) 6(规模自适应) 13(前置收集) |
| 信息保真 | 1(双格式) 4(理论锚定) 7(三维一致性) 8(三时机) 11(只读上游) 12(创新保护) |
| 结构韧性 | 5(两阶段加载) 9(六防御) 10(并行隔离) |

### 总纲：逐层收窄的信心金字塔

```
产品设计 (WHY)  →  开发锻造 (HOW)  →  QA验证 (VALID?)  →  架构治理 (GOOD?)
   最宽泛             逐步具体            行为断言             质量评分
```

每一层只回答自己该回答的问题，不越界。product-design 不碰代码，code-tuner 不评判产品。层间通过 `.allforai/` 目录的 JSON 文件解耦通信。

### 13 条核心设计原则

#### 1. 双格式输出：JSON (机器) + Markdown (人类)

JSON 是完整的可执行规格（每个字段不省略），Markdown 是给人看的摘要。两者职责分明，互不替代。

#### 2. 用户是最终裁决者（ONE-SHOT 确认模型）

系统只提议，不替用户决策。所有关键决策通过 AskUserQuestion 收集，记录到 `*-decisions.json`，带时间戳和理由，不可篡改。resume 时已确认的步骤自动跳过。

#### 3. 搜索驱动的选择题，而非开放式提问

永远不问"你想怎么做？"。先 WebSearch 搜集证据，合成 2-4 个选项（各附依据），让用户选。用户选"其他"则根据输入重新搜索、重新出题。

#### 4. 经典理论锚定 + 实时信号补充

每个技能都有理论锚点（JTBD、Nielsen、WCAG、Clean Architecture...），同时用 WebSearch 获取最近 12-24 个月的行业实践。理论提供稳定性，搜索提供时效性。

#### 5. 两阶段加载：索引 + 按需详情

大产品（400+ 任务）不一次性加载全部数据。先加载轻量索引（~4KB），再根据当前步骤按需加载具体模块。索引不存在时优雅回退到全量加载。

#### 6. 规模自适应交互

| 规模 | 阈值 | 策略 |
|------|------|------|
| 小 | ≤30 | 逐条展示，逐步确认 |
| 中 | 31-80 | 按组摘要，标记问题 |
| 大 | >80 | 脚本生成 + 统计概览 + 仅展示严重问题 |

既不用巨大列表淹没用户，也不在聚合中隐藏问题。

#### 7. 三维一致性校验框架

```
逆向追溯 — 每个下游产物是否有上游源头？
覆盖洪泛 — 每个上游节点是否被下游完整消费？
横向一致性 — 相邻层之间有无矛盾？
```

这个框架不仅用于 design-audit，可泛化到任何多层系统的一致性检查。

#### 8. 三时机植入（事前 / 事中 / 事后）

抽象和模式检测在三个时间点注入：
- **事前**：并行执行前扫描 + 标注（design-pattern / shared-utilities）
- **事中**：执行过程中检查一致性（ui-design pattern check / task-execute abstraction check）
- **事后**：终审门禁验证（design-audit Step 5 / Phase 8 abstraction gate）

#### 9. 防御性六机制

| 机制 | 作用 |
|------|------|
| JSON 加载校验 | 损坏自动恢复 .bak |
| 零结果检测 | 区分"真的零"和"可能出错" |
| 规模自适应 | 不淹没也不隐藏 |
| WebSearch 故障处理 | 重试/替代关键词/让用户提供 |
| 上游过期检测 | 时间戳比较，警告不阻断 |
| 断引用断言 | 标记 BROKEN_REF，继续但报告 |

#### 10. 并行隔离 + 聚合检查点

Phase 4-7 四个 Agent 并行执行，各自写分片文件（`pipeline-decisions-{skill}.json`），互不读写。全部完成后编排器统一聚合、去重、交叉校验。

#### 11. 只读不改上游

后序阶段发现上游问题时**只报告，不回退修改**。由用户决定回哪一层修复。避免级联修改导致的不可预测后果。

#### 12. 创新保护机制

创新功能即使低频也不被自动砍掉：
- **core** → 跳过频次过滤，强制保留
- **defensible** → 需用户确认才能砍
- **experimental** → 正常频次过滤

#### 13. 前置收集，一次执行（Front-load Decisions）

在流程起点（product-concept）一次性收集所有用户偏好和决策（`pipeline_preferences`），后续阶段自动消费这些决策，仅 ERROR 级问题才停顿。减少交互轮次，让流水线尽可能无人值守运行。

## License

MIT
