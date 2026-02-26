# myskills

Claude Code 插件集合，覆盖 产品设计 → 开发锻造 → QA 验证 → 代码架构 全链路。

## 四层架构

```
层级        插件              覆盖范围
─────────  ────────────────  ─────────────────────────────────────────────
产品层      product-design    概念→定义→交互→视觉→用例→查漏→剪枝
开发层      dev-forge         种子数据锻造→产品验收（seed-forge / product-verify）
QA 层       deadhunt          死链→CRUD完整性→幽灵功能→字段一致性
架构层      code-tuner        合规→重复→抽象→评分
```

## 插件说明

### product-design (v3.0.0)

产品设计套件，7 个技能：

| 技能 | 用途 |
|------|------|
| product-concept | 产品概念发现：搜索+选择题引导 |
| product-map | 产品地图：角色、任务、业务流、约束 |
| screen-map | 界面地图：UI 流、异常状态、交互 |
| use-case | 用例集：JSON 机器版 + Markdown 人类版 |
| feature-gap | 功能查漏：缺失功能、不完整旅程 |
| feature-prune | 功能剪枝：CORE / DEFER / CUT 分类 |
| ui-design | UI 设计规格：风格+设计原则→HTML 预览 |

### dev-forge (v1.0.0)

开发锻造套件，2 个技能：

| 技能 | 用途 |
|------|------|
| seed-forge | 种子数据锻造：真实感测试数据 |
| product-verify | 产品验收：静态扫描 + 动态 Playwright 验证 |

### deadhunt (v1.9.0)

死链猎杀 + 流程验证：死链、CRUD 完整性、幽灵功能、跨层字段一致性。

### code-tuner (v1.0.0)

服务端代码架构分析：合规检查、重复检测、抽象分析、综合评分 (0-100)。

## 数据流

所有插件共享 `.allforai/` 目录作为数据合约：

```
product-design 产出 →  .allforai/product-map/   ← dev-forge / deadhunt 消费
                       .allforai/screen-map/
                       .allforai/use-case/
                       .allforai/feature-gap/
                       .allforai/feature-prune/

dev-forge 产出     →  .allforai/seed-forge/
                      .allforai/product-verify/
```

## 安装

```bash
# 安装全部插件
claude plugin add /path/to/myskills/product-design-skill
claude plugin add /path/to/myskills/dev-forge-skill
claude plugin add /path/to/myskills/deadhunt-skill
claude plugin add /path/to/myskills/code-tuner-skill
```

## License

MIT
