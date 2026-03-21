# Phase 2 Stage D — 确认 + 映射

> 展示发现结果 → 用户确认 → 生成跨栈映射。

---

## 2.14 用户确认（AskUserQuestion — 最后一次交互）

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

> **=== Phase 2 结束后不再问任何配置问题 ===**

## 2.15 stack-mapping.json（仅跨栈）

LLM 生成跨栈映射，包含：
- `auto_mapped` — 代码构造映射，每条标注 `compatibility: flexible | exact`
- `abstraction_mapping` — 复用模式映射
- `infrastructure_mapping` — 基础设施映射（cannot_substitute 组件标注精确迁移方案）
- `platform_adaptation` — 跨平台 UX 转换（仅 mobile↔desktop 等交互模型不同时）

同栈时不生成 stack-mapping.json（但其他产物仍然生成）。
