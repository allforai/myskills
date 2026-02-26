---
name: dev-forge
description: >
  Development forge with two skills: seed-forge (种子数据锻造) and product-verify (产品验收).
  Depends on product-design's .allforai/ output for product-map data.
version: "1.0.0"
---

# Dev Forge — 开发锻造套件

> 基于产品地图，为开发阶段提供种子数据锻造和产品验收能力。

## 前置依赖

本插件依赖 `product-design` 插件生成的 `.allforai/product-map/` 输出。请先运行 `/product-map` 建立产品地图。

## 包含的技能

### 1. seed-forge — 种子数据锻造

> 详见 `${CLAUDE_PLUGIN_ROOT}/skills/seed-forge.md`

按产品地图，生成有业务逻辑、有人物关系、有时间分布的真实感种子数据。

- 角色驱动：按 role-profiles 创建各角色测试用户账号
- 频次决定数量：高频任务多生成，低频少生成（80/20 分布）
- 场景决定关联：按场景链路生成完整数据，时间戳连贯
- 约束决定规则：业务约束在数据中强制体现

```
/seed-forge               # 完整流程（映射→方案→风格→采集→灌入）
/seed-forge plan          # 只设计方案，不灌入
/seed-forge fill          # 加载已有方案，直接采集+灌入
/seed-forge clean         # 清理已灌入的种子数据
```

### 2. product-verify — 产品验收

> 详见 `${CLAUDE_PLUGIN_ROOT}/skills/product-verify.md`

静态扫描代码覆盖率 + 动态 Playwright 验证行为合规性，输出差异任务清单。

- 静态验证：扫描代码，检查 product-map 中定义的任务是否有对应实现
- 动态验证：通过 Playwright 执行关键用户路径，验证行为合规
- 差异报告：输出未覆盖的任务清单和行为偏差

```
/product-verify           # 完整验收（静态+动态）
/product-verify static    # 只做静态扫描
/product-verify dynamic   # 只做动态验证
/product-verify refresh   # 忽略缓存，重新验收
```

## 定位

```
product-design（产品层）  概念→定义→交互→视觉→用例→查漏→剪枝
dev-forge（开发层）       种子数据 + 产品验收 ← 你在这里
deadhunt（QA 层）         死链→CRUD完整性→幽灵功能→字段一致性
code-tuner（架构层）      合规→重复→抽象→评分
```

## 输出

所有产出写入项目根目录的 `.allforai/` 下。

```
your-project/
└── .allforai/
    ├── seed-forge/
    │   ├── model-mapping.json      # 代码实体 ↔ product-map 映射
    │   ├── api-gaps.json           # API 缺口报告
    │   ├── seed-plan.json          # 种子方案（用户/数量/链路/约束）
    │   ├── style-profile.json      # 行业风格
    │   ├── assets-manifest.json    # 素材清单
    │   ├── assets/                 # 下载的图片
    │   ├── forge-log.json          # 灌入日志
    │   └── forge-data.json         # 已创建数据清单
    └── product-verify/
        ├── static-report.json      # 静态扫描结果
        ├── dynamic-report.json     # 动态验证结果
        └── verify-report.md        # 可读报告
```
