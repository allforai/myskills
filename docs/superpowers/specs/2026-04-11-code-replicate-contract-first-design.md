# Design: Contract-First Replication (code-replicate 增强)

**Date:** 2026-04-11  
**Status:** Approved  
**Scope:** code-replicate skill — Phase 1 + 新增 Phase 2.5 + Phase 3 增强

---

## 问题诊断

拥有完整源码，目标清晰，但技术栈复刻完成度依然偏低。根因有三：

1. **上下文容量问题** — 已由任务拆分解决，不是瓶颈
2. **验收基准缺失** — 没有显式的 oracle，生成是盲目的，"完成"是主观的
3. **UI 合约无法静态验证** — UI 的正确性只在运行时可见，跨栈迁移后表现形式本身就变了

核心结论：**复刻完成度低的根本原因是验收标准从未被显式化**。后端缺行为合约，UI 缺交互意图合约。没有 oracle，生成就没有收敛目标。

---

## 设计原则

> 先定标准，再讲执行。

- 验收合约在任何生成之前提取完毕
- 每个生成单元以合约为约束，生成后即时验收
- 跑不起来 = 已知保真度上限，必须在执行前告知用户

---

## 流程变更

### 现有流程

```
Phase 1  预检
Phase 2  结构发现 + 用户确认
Phase 3  生成标准 allforai 产物
Phase 4  验收交付
```

### 新流程

```
Phase 1  预检
  ├── 1.1 参数收集（现有）
  └── 1.2 可运行性评估 ← 新增（门禁）
Phase 2  结构发现 + 用户确认（现有）
Phase 2.5 合约提取 ← 新增
  ├── 后端行为合约
  └── UI 交互意图合约
Phase 3  逐单元生成 + 即时验收 ← 增强
Phase 4  整体验收交付（现有）
```

---

## Phase 1.2：可运行性评估

### 目标

在复刻开始前，确定本次复刻的**保真度上限**，并让用户明确接受。

### 检测项

| 检测项 | 方法 |
|--------|------|
| 源项目能否构建 | 尝试 build 命令；检查依赖是否可解析 |
| 源项目能否运行 | 尝试启动；检查环境变量、DB 连接等前置条件 |
| 目标栈运行环境是否就绪 | 检查目标语言/框架/工具链版本 |

### 保真度上限声明

| 可运行状态 | UI 验收能力 | 保真度上限 |
|-----------|------------|-----------|
| 源 + 目标均可运行，可截图 | 完整运行时验收 | ~100% |
| 可运行，无截图环境 | 结构验收，无视觉对比 | ~70% |
| 源或目标无法运行 | 仅静态合约验收 | ~40% |

### 门禁规则

- 评估结果和保真度上限**必须展示给用户**
- 用户**显式确认**后才进入后续阶段
- 跑不起来不是阻断条件，但用户必须知道缺口在哪

输出：`acceptance-ceiling.json`

```json
{
  "source_runnable": true,
  "target_env_ready": false,
  "screenshot_available": false,
  "fidelity_ceiling": 0.7,
  "known_gaps": ["runtime UI verification", "visual diff"],
  "user_confirmed": false
}
```

---

## Phase 2.5：合约提取

### 目标

从源码中提取**验收合约**，作为整个复刻的 oracle。所有后续生成单元以此为约束。

### 后端行为合约

从 routes / controllers / services 提取：

```json
{
  "contract_id": "BC-001",
  "endpoint": "POST /api/orders",
  "inputs": { "fields": ["user_id", "items[]", "coupon_code"] },
  "outputs": {
    "success": { "status": 201, "body": "order_id" },
    "errors": [
      { "condition": "items empty", "status": 422 },
      { "condition": "coupon expired", "status": 400 }
    ]
  },
  "side_effects": ["inventory.decrement", "notification.send"],
  "cross_module_rules": ["战斗中不能打开背包"]
}
```

**提取重点：**
- 每个接口的完整输入/输出/错误条件
- 副作用（写库、发消息、推通知）
- 跨模块的隐性规则（散落在多个文件中、没有显式断言的约束）

### UI 交互意图合约

从 components / screens / routes 提取**交互意图**，而非组件代码：

```json
{
  "contract_id": "UI-001",
  "screen": "BattleScreen",
  "states": ["loading", "in_battle", "paused", "game_over"],
  "user_actions": [
    { "action": "tap_attack", "precondition": "in_battle", "outcome": "combat_handler.trigger" },
    { "action": "open_inventory", "precondition": "NOT in_battle", "outcome": "inventory_screen" }
  ],
  "transitions": [
    { "from": "in_battle", "trigger": "hp <= 0", "to": "game_over" }
  ],
  "intent": "玩家在战斗中执行攻击和技能，战斗结束时过渡到结算界面"
}
```

**提取重点：**
- 屏幕状态列表（非 UI 组件，是业务状态）
- 用户操作的前置条件和结果
- 状态转换触发器
- 交互意图（一句话描述用户在这个屏幕要完成什么）

**关键原则：提取意图，不提取实现。** 换了技术栈，意图不变；组件代码完全不同。

### 输出

`acceptance-contracts.json`：后端合约 + UI 合约的完整列表，是 Phase 3 的输入约束。

---

## Phase 3 增强：逐单元生成 + 即时验收

### 变更

每个生成单元执行前，从 `acceptance-contracts.json` 取出对应合约作为 acceptance criteria。

```
for each generation_unit:
  1. 取对应合约（BC-xxx 或 UI-xxx）
  2. 生成目标代码
  3. 对照合约验收：
     - 后端：接口签名、错误条件、副作用是否覆盖
     - UI：状态列表、用户操作、转换是否实现
  4. 通过 → 下一单元
     不通过 → 当前单元内修复（最多 3 轮）→ 仍失败 → 标记为 known_gap
```

### known_gap 处理

修复 3 轮仍不通过的合约项，标记为 `known_gap`，写入最终报告。不阻断后续单元，但在 Phase 4 汇总时展示给用户。

---

## 产物清单

| 产物 | 阶段 | 用途 |
|------|------|------|
| `acceptance-ceiling.json` | Phase 1.2 | 保真度上限 + 用户确认 |
| `acceptance-contracts.json` | Phase 2.5 | 验收 oracle |
| `known_gaps.json` | Phase 3 | 未收敛的合约项 |
| `replicate-report.md` | Phase 4 | 整体报告（含 gap 汇总）|

---

## 不在本次范围内

- 自动化测试生成（方向 B）— 跨栈测试迁移代价过高，留作后续
- 视觉快照对比 — 依赖 cr-visual 现有能力，不在本次增强范围
- Phase 2 结构发现的改动 — 现有能力足够，不变
