### Phase 4: Verify & Handoff

**Step 4a** — `cr_validate.py` 结构校验 + **内循环修复**
- 检查项：必填字段完整、ID 引用有效、role_id/flow_id 存在、schema 合规
- 不通过 → 进入内循环修复：

```
内循环（CG-1 收敛控制）:
  1. 错误清单交 LLM 修正对应片段
  2. 重新 merge + validate
  3. 分类失败：
     - SCHEMA_ERROR  — 字段缺失/格式错误 → 修片段
     - REF_ERROR     — ID 引用断裂 → 修引用
     - LOGIC_GAP     — 业务逻辑不完整 → 补充片段
  4. 收敛条件：
     - 最多 3 轮修复
     - 每轮错误数必须 ≤ 上一轮（单调递减）
     - 违反单调递减 → 停止修复，剩余标记为 KNOWN_GAP
     - 第 3 轮仍有错误 → 记录为 KNOWN_GAP，继续 Step 4b
```

**Step 4b** — **6V 多维审计**（LLM 执行，不依赖外部工具）

LLM 从六个视角审查已合并产物，输出问题清单写入 `replicate-report.md`：

| 视角 | 审查内容 | 检查方式 |
|------|---------|---------|
| **user** | 每个角色的核心任务是否都被提取了？有没有角色有 0 个 task？ | 比对 role-profiles × task-inventory |
| **business** | 核心业务流是否有 flow 覆盖？orphan_tasks 中有没有核心任务？ | 检查 business-flows 覆盖 + orphan 列表 |
| **tech** | 技术约束（API 限制、并发、事务）是否进入 constraints 或 task.rules？ | 检查 constraint_sources 覆盖 |
| **data** | 数据实体是否完整？字段、关系、索引是否被记录？ | 比对 source-summary.data_entities × task.inputs/outputs |
| **ux** | （仅 frontend/fullstack）screen 的 states 是否覆盖 empty/loading/error/success？ | 检查 experience-map screens |
| **risk** | 安全/合规/隐私约束是否标注？支付/医疗/金融等高风险操作有 protection_level=core？ | 检查 constraints + task.protection_level |

6V 发现的问题分为两类：
- **可修复**：遗漏的 task、缺失的 flow 引用 → 回到 Step 4a 内循环补充
- **需标注**：无法从源码提取的信息（如合规要求需要人工确认）→ 写入 report 的 warnings

**Step 4b.5** — **注意力管理评估**（仅当 `experience_priority.mode` = consumer 或 mixed）

LLM 对 experience-map 中的 consumer 屏幕执行注意力负载检查：

| 检查项 | 阈值 | 问题标记 |
|--------|------|---------|
| 单屏操作步骤数 | >7 步 | `ATTENTION_OVERLOAD` |
| 跨屏记忆需求 | 需要用户记住前一屏信息才能完成当前操作 | `MEMORY_BURDEN` |
| 上下文切换 | 同一 flow 中页面跳转 >3 次 | `CONTEXT_SWITCH` |
| 反馈缺失 | 操作后无 loading/success 状态 | `FEEDBACK_GAP` |

注意力问题写入对应 screen 的 `_attention_flags` 字段，同时汇总到 report。这些 flag 在 dev-forge 的 design-to-spec 阶段会被消费，驱动 UI 简化决策。

**Step 4c** — XV 交叉验证（可选，需 `OPENROUTER_API_KEY`）
- 用不同模型审查产物一致性 → 问题写入产物 flags 字段
- 无 API key 时静默跳过

**Step 4d** — **外循环：意图保真验证**

> "走了这么多步，还在正确的路上吗？"

LLM 回到 source-summary.json 原点，验证提取结果是否覆盖业务意图：

```
OL-D1 模块覆盖度:
  - 读 source-summary.modules（全部模块清单）
  - 每个模块是否产出了至少 1 个 task？
  - file_count > 20 但 task_count = 0 的模块 → 标记为「提取遗漏」

OL-D2 抽象保全度:
  - 读 source-summary.abstractions
  - 每个 consumer_count > 3 的抽象是否进入了 stack-mapping.abstraction_mapping？
  - 未映射的高复用抽象 → 标记为「复用断裂」

OL-D3 横切覆盖度:
  - 读 extraction-plan.dependency_map（LLM 生成的模块间依赖，替代 cr_discover 的机械解析）
  - 读 extraction-plan.cross_cutting
  - 每个 dependency_map 中 type=middleware 的依赖是否在 flow 或 task.prerequisites 中出现？
  - 每个 cross_cutting 关注点是否有对应 task 或 flow 覆盖？
  - 未覆盖的横切点 → 标记为「横切遗漏」

OL-D4 角色完整性:
  - 读 role-profiles.json
  - 每个角色是否有 ≥1 个 use-case（happy_path）？
  - 无 use-case 的角色 → 标记为「角色空壳」

收敛控制（CG-3）:
  - 外循环发现的缺口总数 ≤ Phase 3 产物总条目数的 20%
  - 超过 20% → 停止补充，在 report 中标记"提取覆盖不足，建议提高保真度或扩大分析范围"
  - 外循环最多执行 1 轮（不递归）

追加项处理:
  汇总 OL-D1~D4 的缺口 → 回到 Phase 3 对应 Step 补充片段 → 重新 merge + validate
```

**Step 4e** — `cr_gen_report.py` → replicate-report.md
- 包含：源码概况、保真度、模块覆盖率、跳过项、校验结果、6V 审计结果、注意力评估、XV 发现、外循环意图覆盖度

**Step 4f** — Handoff
- 输出产物清单（路径 + 文件大小）
- 推荐下一步：project-setup → design-to-spec → task-execute
- 跨栈复刻额外提示：检查 stack-mapping.json 中的手动决策点
- KNOWN_GAP 列表（内循环未修复 + 外循环超 20% 的遗漏项）

**Step 4g** — Gap pattern analysis（大闭环）

汇总 `known_gaps.json` 中所有模块的 gap。识别系统性失败模式：(1) 某类合约类型反复失败（如所有 `cross_module_rules` 条目均为 known_gap → 提取策略对该模式有误）；(2) 目标栈某种代码模式导致逆向提取不可靠。将发现写入 `replicate-report.md` §Gap Patterns。若任何类别的 pattern 数 ≥ 3，建议用户在下次复刻前重新运行 Phase 2.5（改进提取规则）。

**replicate-report.md §Gap Patterns 格式：**

```markdown
## Gap Patterns

| Pattern | 受影响合约 | 根因 | 建议 |
|---------|-----------|------|------|
| cross_module_rules 提取 | BC-005, BC-012, BC-019 | 规则通过 DB 约束表达，在 service 层不可见 | 重新运行 Phase 2.5，增加 DB 约束扫描 |
| UI 前置条件检测 | UI-003, UI-007 | 前置条件通过 CSS disabled 属性编码，不在 JS 逻辑中 | Phase 2.5.2 增加基于 CSS 的前置条件提取 |
```

