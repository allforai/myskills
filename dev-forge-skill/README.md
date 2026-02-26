# dev-forge — 开发锻造套件

**版本：v1.0.0**

Claude Code 插件，基于产品地图为开发阶段提供种子数据锻造和产品验收能力。

## 前置依赖

本插件依赖 `product-design` 插件生成的 `.allforai/product-map/` 输出。请先运行 `/product-map` 建立产品地图。

---

## 包含的技能

### seed-forge — 种子数据锻造

> 按产品地图，生成有业务逻辑、有人物关系、有时间分布的真实感种子数据。

- **角色驱动**：按 `role-profiles` 创建各角色的测试用户账号
- **频次决定数量**：高频任务多生成数据，低频任务少生成，符合二八分布
- **场景决定关联**：按场景链路生成完整数据（父→子→关联），时间戳连贯，不随机拼凑
- **约束决定规则**：金额上限、审批链、不可逆状态等业务约束在数据中强制体现
- 竞品图片优先，Unsplash/Pexels 兜底；通过 API 灌入，直连数据库清理

### product-verify — 产品验收

> 静态扫描代码覆盖率 + 动态 Playwright 验证行为合规性，输出差异任务清单。

- **静态验证**：扫描代码，检查 product-map 中定义的任务是否有对应实现
- **动态验证**：通过 Playwright 执行关键用户路径，验证行为合规
- **差异报告**：输出未覆盖的任务清单和行为偏差

---

## 安装

```bash
claude plugin add /path/to/dev-forge-skill
```

---

## 使用

```bash
# 种子数据 — 造数据
/seed-forge               # 完整流程（映射→方案→风格→采集→灌入）
/seed-forge plan          # 只设计方案，不灌入
/seed-forge fill          # 加载已有方案，直接采集+灌入
/seed-forge clean         # 清理已灌入的种子数据

# 产品验收 — 验证实现
/product-verify           # 完整验收（静态+动态）
/product-verify static    # 只做静态扫描
/product-verify dynamic   # 只做动态验证
/product-verify refresh   # 忽略缓存，重新验收
```

---

## License

MIT
