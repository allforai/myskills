# Auditor Enrichment Steps — design-to-spec

> This file is loaded by the Auditor Agent AFTER validation (auditor-validate.md) completes.
> Auditor's second job: read validated tasks.md → supplement quality sub-tasks.
> This is a SEPARATE agent call from validation — fresh attention for enrichment.

---

### Auditor 第二职责：注意力分离补充（审查完 V9-V12 后执行）

> Decomposer 只生成平铺的功能任务（B0-B5）。Auditor 审查后，**主动补充**质量子任务。
> 这比让 Decomposer 自己分离更可靠——Auditor 是独立 Agent，有全新注意力，且已读完全部产出。

**Auditor 补充流程**：

1. **异常加固子任务**（后端 B2 任务）：
   对每个 _Risk: HIGH/MEDIUM_ 的 B2 任务，Auditor 评估：
   - 该端点有哪些 Decomposer 未覆盖的异常场景？（边界/并发/降级/状态非法）
   - 有 → 生成 `B2.HARDEN.{seq}` 子任务，含具体异常清单
   - 无 → 跳过

2. **体验 DNA 子任务**（前端 B3 任务，experience-dna.json 存在时）：
   读取 design.md 的 `_DIFF:` 标注 + experience-dna.json，
   为每个 core/defensible DIFF 生成 `B3.DNA.{seq}` 子任务：
   ```
   - [ ] B3.DNA.{seq} [{sub-project}] [DNA-CRITICAL] {DIFF.name}
     - Component: {visual_contract.component}
     - Placement: {visual_contract.placement}
     - Spec: {visual_contract.spec}
     - Behavior: {visual_contract.behavior}
     - Must NOT: {visual_contract.must_not}
     - _DNA: DIFF-{id}_
     - _Risk: HIGH_
   ```

3. **其他质量维度子任务**（Auditor 自主判断）：
   Auditor 扫描 B3 主任务，识别缺失的质量维度并补充。常见维度（非穷举）：
   | 维度 | 子任务 Round 名 | 触发条件 |
   |------|---------------|---------|
   | 四态（empty/error） | B3.POLISH.{seq} | 页面规格有 states 但主任务只覆盖 loaded |
   | 国际化 | B3.i18n.{seq} | 前端子项目有 i18n 配置 |
   | 无障碍 | B3.a11y.{seq} | 项目要求 a11y |
   | 性能 | B3.PERF.{seq} | 页面有长列表/大图/复杂计算 |
   Auditor 可按项目特点创建新维度（如离线同步、动效等），不限于此表。

4. **测试任务细化**（所有子项目）：
   - 每个 B2 _Acceptance_ 条件 → 确保有对应的 B5 测试断言
   - 每个 B2.HARDEN 异常 → 生成 B5.HARDEN 测试
   - 每个 B3.DNA spec → 生成 B5.DNA 行为测试
   - 粗粒度的 B5 模块测试保留（覆盖集成场景），细粒度断言作为补充

5. **补充后重检**：
   新增的子任务也需要通过 V9-V12 验证（确保子任务本身的质量）。
   这在 Auditor 的验证循环内自然完成（最多 3 轮）。

---

### V11 验收条件完整性（B2 任务强制）

> V9 回答"有没有对应的任务"，V10 回答"数据从哪来"，V11 回答"任务有没有可执行的验收标准"。
> 没有验收条件的任务 = 没有完成标准 = Phase 5 验收时才发现「代码有但行为不对」。

**V11.1 存在性检查**：每个 B2 任务是否有 `_Acceptance_` 字段？缺失 → `TASK_ACCEPTANCE_MISSING`（CRITICAL）
**V11.2 粒度检查**：验收条件数量是否达到 `_Risk_` 级别要求？不达标 → `TASK_ACCEPTANCE_INSUFFICIENT`（WARNING）
**V11.3 可执行性检查**：每条验收条件是否包含可验证断言（HTTP 方法 + 路径 → 状态码 / 响应字段 / 副作用）？模糊描述 → `TASK_ACCEPTANCE_INSUFFICIENT`（WARNING）

**修正方式**：
- `TASK_ACCEPTANCE_MISSING` → 基于 task-inventory 的 main_flow / exceptions / rules 自动生成 `_Acceptance_` 条件
- `TASK_ACCEPTANCE_INSUFFICIENT` → 补充缺失的异常路径 / 边界条件
- `TASK_DIFF_MISSING`（core）→ CRITICAL — 在对应前端子项目 tasks.md 补充 B3 任务，实现 DIFF 视觉契约指定的组件
- `TASK_DIFF_MISSING`（defensible）→ WARNING — 记录但不阻塞
- `TASK_DIFF_UNDERSPECIFIED` → WARNING — 补充 DIFF 的完整 visual_contract 规格到任务描述中（从 experience-dna.json 复制 spec+behavior+must_not）
- `TASK_API_GAP` → 在 tasks.md 中补充缺失的 B2 端点任务（遵循端点级原子性规则）
- `TASK_COVERAGE_CRITICAL` → 从 task-inventory.json 推导缺失的端点，补充 B2 + B3 + B5 任务
- `TASK_PROVENANCE_CRITICAL` → 补充行为上报端点（B2）+ 前端上报组件（B3）
- `TASK_DATA_GAP` → 补充 B1 定义任务
- `TASK_UX_GAP` → 补充 B3 页面任务
- 修正后回到小循环 A 重检（最多 3 次内循环）

---

### 小循环 B: XV 交叉审查（OpenRouter 可用时执行，否则跳过）

向专家模型发送：
```
{task-inventory.json 摘要} + {tasks.md 任务列表} + {小循环 A 审计结果}
要求：
1. 检查是否有产品功能在任务列表中完全缺失
2. 检查 B2 任务粒度是否合理（是否有 controller 级别的粗粒度任务）
3. 检查任务间依赖是否合理
输出：CONFIRM | REJECT(缺失列表) | SUGGEST(优化建议)
```

REJECT → 按缺失列表补充任务 → 重检
SUGGEST → 记录建议，不阻塞

---

### 小循环 C: 闭环审计

对 tasks.md 中每个模块/功能域检查 6 类闭环：

| 闭环类型 | 任务层审计问题 | 不通过标记 |
|---------|-------------|----------|
| 配置闭环 | 有 config_items 的功能是否有 B2 配置端点任务？ | `TASK_CLOSURE_CONFIG` |
| 监控闭环 | 有 audit 的功能是否有 B2 审计中间件任务？ | `TASK_CLOSURE_MONITOR` |
| 异常闭环 | 有 exceptions 的功能是否在 B2 任务的实现要点中提到？ | `TASK_CLOSURE_EXCEPTION` |
| 生命周期闭环 | 有状态机的实体是否有完整的状态变更端点任务？ | `TASK_CLOSURE_LIFECYCLE` |
| 映射闭环 | 有关联关系的实体是否有级联操作任务？ | `TASK_CLOSURE_MAPPING` |
| 导航闭环 | 每个前端页面是否有路由守卫 + 404 + 回退任务？layout 组件（header/footer/sidebar）中的链接目标是否在 pages/ 有对应页面任务？ | `TASK_CLOSURE_NAVIGATION` |
| 数据溯源闭环 | 返回聚合/统计数据的 GET 端点，其数据源是否有对应的写入端点/任务？（V10 的任务层投影） | `TASK_CLOSURE_PROVENANCE` |

修正 → 回到小循环 C 重检

---

### 退出条件

- V9 Coverage CRITICAL = 0（所有 CORE 产品任务有对应 B2 任务）
- V10 Provenance CRITICAL = 0（所有聚合数据有可追溯的写入路径）
- V11 Acceptance MISSING = 0（所有 B2 任务有验收条件）
- 4D 无 GAP（或已修复）
- 闭环无 CRITICAL 缺失
- V12 DIFF CRITICAL = 0（所有 core 级体验差异化契约在前端页面中有对应实现任务）
- Auditor 补充完成：HIGH risk 任务的子任务已补充，Acceptance 测试已派生

**大循环 3 轮后仍有问题** → 记录为已知问题到 `pipeline-decisions.json`，输出警告，继续（不停）

→ 输出进度: 「Step 4.3 验证 ✓ V9:{X}% V10:{Y}% V11:{Z}% V12 DNA:{W}% | 补充: HARDEN:{H} DNA:{D} POLISH:{P} 测试:{T} | gaps:{N} fixed | XV:{status}」
