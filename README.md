# myskills

**Claude Code + OpenCode** 双平台插件集合，覆盖 **产品设计 → 开发锻造 → QA 验证 → 架构治理** 全链路。

## ✨ 新增：创新保真 + 状态闭环机制（v3.2.0）

### 创新保真机制
确保 `product-concept` 阶段定义的创新概念在 downstream 各阶段不被稀释、不误解、不延后：

- **screen-map**: 创新界面自动标记（`innovation_screen` + `adversarial_concept_ref`）
- **ui-design**: 创新概念 UI 规格专节（跨领域参考，如"抖音无限滚动"、"游戏赛季制"）
- **task-execute**: Round 优先级修正（core 级别创新任务 → Round 1 优先执行）
- **use-case**: 创新用例类型（`innovation_mechanism` 专用验证用例）
- **seed-forge**: 创新专用数据链路（core 级别创新概念优先灌入）
- **information-fidelity**: 理论基础（4D+6V+XV 协议）

### 状态闭环机制
确保状态从产生到流转形成完整闭环，不依赖特定行业，通用适用于任何领域：

- **product-concept**: 创新概念状态机定义（初始状态 → 中间状态 → 终止状态）
- **feature-gap**: 状态闭环验证（孤儿状态/幽灵状态/语义鸿沟检测）
- **量化指标**: 状态闭环率 >= 95%，幽灵状态 = 0（零容忍）

**通用性保障**：不预设行业术语（避免"订单"、"支付"等电商绑定），仅验证结构完整性，适用于电商/内容/教育/金融/医疗/SaaS 等任何领域。

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
/full-pipeline
```

---

## 你该从哪个插件开始？

| 你的目标 | 推荐插件 | 第一条命令 |
|---|---|---|
| 梳理产品功能、角色、任务 | product-design | `/product-map` |
| 生成高质量测试数据并验收实现 | dev-forge | `/seed-forge` / `/product-verify` |
| 查死链、CRUD 缺口、幽灵功能 | deadhunt | `/deadhunt` |
| 分析后端架构质量并给重构任务 | code-tuner | `/code-tuner full` |
| 一次跑完整链路 | full-pipeline（在 product-design 内） | `/full-pipeline` |

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

### product-design (v3.1.0)

8 个技能，核心是先建图再分析：

`product-concept / product-map / screen-map / use-case / feature-gap / feature-prune / ui-design / design-audit`

### dev-forge (v1.0.0)

2 个技能：

`seed-forge`（种子数据锻造） + `product-verify`（静态+动态验收）

### deadhunt (v1.9.0)

死链猎杀 + 流程验证：死链、CRUD 完整性、幽灵功能、字段一致性。

### code-tuner (v1.0.0)

服务端架构分析：合规检查、重复检测、抽象机会、综合评分（0-100）。

---

## 数据合约（.allforai）

所有插件共享 `.allforai/` 作为层间输入/输出：

```
product-design 产出 → .allforai/product-map/
                     .allforai/screen-map/
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

> 以经典理论为锚、实时证据为补、用户决策为终、优雅降级为底，通过逐层收窄的信心金字塔，将产品从模糊想法锻造成可追溯、可审计、可执行的工程规格。

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
