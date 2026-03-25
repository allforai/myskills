# dev-forge — 开发锻造套件

**版本：v5.9.1**

Codex 原生技能，从产品设计产物到可运行项目的全流程自动化锻造。LLM 驱动的 Forge-Verify-Loop (4D/6V/XV) 闭环架构。

## 30 秒上手

```bash
# 1) 安装
bash codex/install.sh

# 2) 全流程锻造（推荐）
project-forge full

# 或分步执行
project-setup              # 拆子项目 + 选技术栈
design-to-spec             # 产物 → 需求 + 设计 + 任务
task-execute               # 按 tasks.md 逐任务执行代码
product-verify             # 产品验收
testforge                  # 测试锻造（全金字塔 + E2E 链）
```

## 适用场景

| 场景 | 推荐工作流 |
|------|---------|
| 新项目全流程（产品设计 → 代码） | `project-forge full` |
| 已有项目补缺 | `project-forge existing` |
| 拆分子项目 + 选技术栈 | `project-setup` |
| 生成 spec 文档 | `design-to-spec` |
| 按任务列表执行代码 | `task-execute` |
| 对照产品地图验证实现 | `product-verify` |
| 测试锻造（审计+补测试+E2E链） | `testforge` |

## 前置依赖

主流程依赖 `product-design` 插件生成的 `.allforai/product-map/` 输出。请先执行 `product-design full` 工作流完成产品设计。

例外：
- `project-forge`
- `project-setup`
- `design-to-spec`
- `product-verify`

这些工作流必须有 `product-map`。

- `testforge`
- `deadhunt`
- `fieldcheck`

这些工作流在缺少 `product-map` 时仍可运行，但只能按降级模式执行，并且必须明确报告覆盖范围下降、上游真值缺失或结论置信度降低。

---

## 包含的技能（7 个 + 1 独立插件）

### project-setup — 项目引导
交互式拆分子项目、选择技术栈、分配模块、配置 monorepo。Conway's Law 6V 架构审计。

### design-to-spec — 设计转规格
FVL：LLM 生成 → 4D/6V 审计 → XV 交叉验证 → 自动修正。API-First 策略，生成 requirements + design + tasks。

### task-execute — 任务执行
R0 项目初始化 → R1-R4 业务实现。增量 XV 审计 + 契约漂移同步 + DevSecOps 左移。支持断点续作。

### product-verify — 产品验收
静态扫描代码覆盖率 + 动态 Playwright 验证行为合规性，输出差异任务清单。

### deadhunt — 死链猎杀 + 完整性验证
猎杀死链、幽灵功能、CRUD 缺口。6 Phase 流水线。

### fieldcheck — 字段一致性检查
检查 UI↔API↔Entity↔DB 四层字段名一致性。

### testforge — 测试锻造
FVL 三维验证发现缺口，覆盖全测试金字塔（unit/component/integration/e2e-chain/mobile）。从 business-flows 推导跨站 E2E 链并生成可执行测试脚本。补测试、修 bug，循环至全绿。

### demo-forge — 演示锻造（独立插件）
生成真实感演示数据，配合富媒体采集+上传，Playwright 验证。

---

## 理论支撑

每个阶段的决策扎根于经典工程理论 + LLM 闭环验证。详见 `docs/dev-forge-principles.md`。

核心：Forge-Verify-Loop (4D/6V/XV) / Unix Philosophy / Conway's Law / Clean Architecture / Hexagonal Architecture / Worse is Better / Tracer Bullet / YAGNI

---

## License

MIT
