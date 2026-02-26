# dev-forge — 开发锻造套件

**版本：v2.0.0**

Claude Code 插件，从产品设计产物到可运行项目的全流程自动化锻造。理论驱动（Unix Philosophy / Clean Architecture / Worse is Better 等）。

## 30 秒上手

```bash
# 1) 安装
claude plugin add /path/to/dev-forge-skill

# 2) 全流程锻造（推荐）
/project-forge full

# 或分步执行
/project-setup              # 拆子项目 + 选技术栈
/design-to-spec             # 产物 → 需求 + 设计 + 任务
/project-scaffold           # 生成代码骨架 + mock 后端
/seed-forge                 # 造种子数据
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
| 生成项目骨架 + mock 后端 | `/project-scaffold` |
| 造真实感测试数据 | `/seed-forge` |
| 跨端业务 E2E 测试 | `/e2e-verify` |
| 对照产品地图验证实现 | `/product-verify` |

## 前置依赖

本插件依赖 `product-design` 插件生成的 `.allforai/product-map/` 输出。请先运行 `/product-design full` 完成产品设计。

---

## 包含的技能（6 个）

### project-setup — 项目引导
交互式拆分子项目、选择技术栈（16 种模板）、分配模块、配置 monorepo。

### design-to-spec — 设计转规格
产品设计产物 → 按子项目生成 requirements.md + design.md + tasks.md。API-First 策略。

### project-scaffold — 脚手架生成
按技术栈模板生成项目骨架 + Mock 后端（Express），让前端立即可开发。

### e2e-verify — 跨端验证
从 business-flows 推导跨子项目场景，Playwright / Patrol / Detox 自动执行。

### seed-forge — 种子数据锻造
按产品地图生成有业务逻辑、有人物关系、有时间分布的真实感种子数据。

### product-verify — 产品验收
静态扫描代码覆盖率 + 动态 Playwright 验证行为合规性，输出差异任务清单。

---

## 支持的技术栈

| 类型 | 技术栈 |
|------|--------|
| 后端 | NestJS, Spring Boot, Flask, Django, Go Gin, FastAPI, Rails, Laravel |
| Web 前端 | Next.js, Nuxt, Angular, SvelteKit, Vite+React, Vite+Vue |
| 移动端 | React Native (Expo), Flutter |
| Monorepo | pnpm workspace, Turborepo, Nx, 手动管理 |

---

## 理论支撑

每个阶段的决策扎根于经典工程理论。详见 `docs/dev-forge-principles.md`。

核心理论：Unix Philosophy / Conway's Law / Clean Architecture / Hexagonal Architecture / Worse is Better / Tracer Bullet / YAGNI / C4 Model / Test Pyramid / BDD / Contract Testing

---

## License

MIT
