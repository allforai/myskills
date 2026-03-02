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

## License

MIT
