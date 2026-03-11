# dev-forge — 开发锻造套件

**版本：v3.0.0**

Claude Code 插件，从产品设计产物到可运行项目的全流程自动化锻造。LLM 驱动的 Forge-Verify-Loop (4D/6V/XV) 闭环架构。

## 30 秒上手

```bash
# 1) 安装
claude plugin add /path/to/dev-forge-skill

# 2) 全流程锻造（推荐）
/project-forge full

# 或分步执行
/project-setup              # 拆子项目 + 选技术栈
/design-to-spec             # 产物 → 需求 + 设计 + 任务
/task-execute               # 按 tasks.md 逐任务执行代码
/e2e-verify                 # 跨端 E2E 验证
/product-verify             # 产品验收
```

## 适用场景

| 场景 | 推荐命令 |
|------|---------|
| 新项目全流程（产品设计 → 代码） | `/project-forge full` |
| 已有项目补缺 | `/project-forge existing` |
| 拆分子项目 + 选技术栈 | `/project-setup` |
| 生成 spec 文档 | `/design-to-spec` |
| 按任务列表执行代码 | `/task-execute` |
| 跨端业务 E2E 测试 | `/e2e-verify` |
| 对照产品地图验证实现 | `/product-verify` |

## 前置依赖

本插件依赖 `product-design` 插件生成的 `.allforai/product-map/` 输出。请先运行 `/product-design full` 完成产品设计。

---

## 包含的技能（5 个）

### project-setup — 项目引导
交互式拆分子项目、选择技术栈、分配模块、配置 monorepo。Conway's Law 6V 架构审计。

### design-to-spec — 设计转规格
FVL：LLM 生成 → 4D/6V 审计 → XV 交叉验证 → 自动修正。API-First 策略，生成 requirements + design + tasks。

### task-execute — 任务执行
R0 项目初始化 → R1-R4 业务实现。增量 XV 审计 + 契约漂移同步 + DevSecOps 左移。支持断点续作。

### e2e-verify — 跨端验证
从 business-flows 推导跨子项目场景，Playwright / Patrol / Detox 自动执行。6V 失败诊断。

### product-verify — 产品验收
静态扫描代码覆盖率 + 动态 Playwright 验证行为合规性，输出差异任务清单。

---

## 理论支撑

每个阶段的决策扎根于经典工程理论 + LLM 闭环验证。详见 `docs/dev-forge-principles.md`。

核心：Forge-Verify-Loop (4D/6V/XV) / Unix Philosophy / Conway's Law / Clean Architecture / Hexagonal Architecture / Worse is Better / Tracer Bullet / YAGNI

---

## License

MIT
