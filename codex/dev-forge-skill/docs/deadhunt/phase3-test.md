## Phase 3: 深度测试

> 通过 Playwright（Web/H5）或 Patrol（Flutter）自动化执行测试。
> 本文档已拆分为子文件，按需加载以节省上下文空间。

### 子文件索引

| 文件 | 内容 | 何时加载 |
|------|------|---------|
| `./docs/deadhunt/phase3/overview.md` | 性能优化策略、5 层分类、分级验证 | 总是加载 |
| `./docs/deadhunt/phase3/404-scanner.md` | 全局 404 监控器 + Layer 1-5 扫描实现 | deep/full 模式 |
| `./docs/deadhunt/phase3/intent-classification.md` | 死链意图判定 (FIX/CLEAN/HIDE/PERM) + 报告汇总 | deep/full 模式 |
| `./docs/deadhunt/phase3/validation.md` | 方向 B 反向验证 + CRUD 闭环 + 数据展示 + 业务流程 + 增量验证 + 稳定性 | deep/full 模式 |
| `./docs/deadhunt/phase3/convergence.md` | 多轮收敛机制（模式学习→交叉验证→扩散搜索） | full 模式 |
| `./docs/deadhunt/phase3/patrol.md` | Patrol 深度测试引擎（Flutter 端） | Flutter 项目 |

### 加载策略

- **quick 模式**: 不加载 Phase 3（仅静态分析）
- **deep/full 模式**: 先加载 `overview.md`，再按需加载其他子文件
- **Flutter 项目**: 额外加载 `patrol.md`
- **incremental 模式**: 加载 `overview.md` + `404-scanner.md`（只验证变更模块）
