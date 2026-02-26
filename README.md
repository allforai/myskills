# myskills

Claude Code 插件集合，覆盖 **产品设计 → 开发锻造 → QA 验证 → 架构治理** 全链路。

## 30 秒上手

```bash
# 1) 安装四个插件（统一使用 add）
claude plugin add /path/to/myskills/product-design-skill
claude plugin add /path/to/myskills/dev-forge-skill
claude plugin add /path/to/myskills/deadhunt-skill
claude plugin add /path/to/myskills/code-tuner-skill

# 2) 先做产品建模（建议起手）
/product-map

# 3) 需要全链路时，直接执行
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
