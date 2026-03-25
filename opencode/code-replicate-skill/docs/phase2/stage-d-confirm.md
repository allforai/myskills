# Phase 2 Stage D — 确认 + 映射

> 展示发现结果 → 用户确认 → 生成跨栈映射。

---

## 2.14 User Confirmation (Last Interaction)

展示：
- 模块清单 + 技术栈 + 粒度推荐
- infrastructure-profile 中 `migration_risk = critical | high` 的组件
- 通信+加密耦合组件的整体迁移策略
- 第三方服务的目标栈集成方式
- 跨栈映射决策点

收集：
- 模块范围调整
- 映射决策
- 粒度确认
- 基础设施迁移决策

**extend 模式**（`replicate-config.business_direction = "extend"` 时）：
- LLM 额外询问：「目标项目需要哪些源码没有的新能力？」
- 用户回答（如"需要离线下单能力"）→ LLM 将新能力写入 `replicate-config.extensions[]`
- Phase 3 的 extraction-plan.artifacts 除了从源码提取的产物外，额外生成 `extension-spec`（新能力规格）
- cr-fidelity 不验证 extension（新能力不在源码中，无对比基准）— 由 product-verify 验证

> **=== Phase 2 结束后不再问任何配置问题 ===**

## 2.15 stack-mapping.json（仅跨栈）

LLM 生成跨栈映射，包含：
- `auto_mapped` — 代码构造映射，每条标注 `compatibility: flexible | exact`
- `abstraction_mapping` — 复用模式映射
- `infrastructure_mapping` — 基础设施映射（cannot_substitute 组件标注精确迁移方案）
- `platform_adaptation` — 跨平台适配（仅源平台和目标平台交互模型不同时）

**platform_adaptation 指导思想**：复刻 ≠ 像素级复制。复刻 = **业务等价 + 尊重目标平台原生体验**。

LLM 生成 platform_adaptation 时应思考：
- **目标平台的用户期望什么？** — 不是源平台的操作方式搬过来，而是目标平台用户习惯的操作方式
- **目标平台有什么源平台没有的能力？** — 应该利用而非忽略（如桌面端的多窗口、键盘驱动、系统集成）
- **源平台的哪些设计是受限于平台而非业务需求？** — 这些设计在目标平台上不应保留（如移动端的全屏导航是因为屏幕小，不是业务需要）

LLM 自行识别两个平台的差异维度并标注转换规则。不限定维度列表 — 可能是导航模型、操作入口、数据密度、输入方式、系统集成、窗口管理，也可能是项目特有的其他差异。

cr-visual 对比时，符合 platform_adaptation 转换规则的差异不算 gap。

同栈时不生成 stack-mapping.json（但其他产物仍然生成）。
