## Phase 3: 深度测试

> 通过自动化测试框架对各客户端执行深度测试。
> 使用哪个框架由 LLM 根据项目实际情况决定，本文档已拆分为子文件，按需加载以节省上下文空间。

### 子文件索引

| 文件 | 内容 | 何时加载 |
|------|------|---------|
| `./docs/deadhunt/phase3/overview.md` | 性能优化策略、5 层分类、分级验证 | 总是加载 |
| `./docs/deadhunt/phase3/helper-rules.md` | UI 测试 8 条脆弱层规则 + 截图规则（引擎无关） | 总是加载 |
| `./docs/deadhunt/phase3/404-scanner.md` | 全局 404 监控器 + Layer 1-5 扫描实现 | deep/full 模式 |
| `./docs/deadhunt/phase3/intent-classification.md` | 死链意图判定 (FIX/CLEAN/HIDE/PERM) + 报告汇总 | deep/full 模式 |
| `./docs/deadhunt/phase3/validation.md` | 方向 B 反向验证 + CRUD 闭环 + 数据展示 + 业务流程 + 增量验证 + 稳定性 | deep/full 模式 |
| `./docs/deadhunt/phase3/convergence.md` | 多轮收敛机制（模式学习→交叉验证→扩散搜索） | full 模式 |
| `./docs/deadhunt/phase3/patrol.md` | Patrol 参考示例（Flutter） | 可选，LLM 按需参考 |
| `./docs/deadhunt/phase3/maestro.md` | Maestro 参考示例（RN / Android 原生） | 可选，LLM 按需参考 |
| `./docs/deadhunt/phase3/xcuitest.md` | XCUITest 参考示例（iOS 原生） | 可选，LLM 按需参考 |

### 加载策略

- **quick 模式**: 不加载 Phase 3（仅静态分析）
- **deep/full 模式**: 先加载 `overview.md` + `helper-rules.md`，再按需加载其他子文件
- **incremental 模式**: 加载 `overview.md` + `helper-rules.md` + `404-scanner.md`（只验证变更模块）

### 测试框架选择

LLM 在执行 Phase 3 前，先完成以下判断：

1. 扫描项目，识别每个客户端实际使用的测试框架
2. 按 `helper-rules.md` 的 8 条规则，为该框架生成对应的 helper
3. 若框架属于已有参考示例（Patrol / Maestro / XCUITest），可加载对应文件参考实现模式
4. 若框架不在参考示例中（游戏引擎、桌面 GUI 框架、自定义框架等），按参考示例的结构自行适配，无需额外文档

### 范围边界：跨 module E2E

Phase 3 的 helper 和测试生成均为 **per-module**，只覆盖单个 module 内的 UI 交互。

跨 module 的端到端业务流（如：消费者下单 → 商户接单 → 配送员揽件）不在 Phase 3 范围内，属于 testforge Phase 4 的 E2E 链锻造（`path-b-e2e-chain.md`）负责。

若 Phase 0 检测到项目存在跨 module 业务流（通过 `business-flows.json`），在 Phase 3 报告中标注 `CROSS_MODULE_FLOW_DETECTED`，提示用户在 testforge Phase 4 补充跨 module E2E 链。
