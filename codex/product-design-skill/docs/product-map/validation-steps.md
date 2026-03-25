# Validation Steps (Step 9)

> Part of the **product-map** skill. Loaded by the orchestrator at runtime.

---

## Step 9: 校验

Step 6 完成后必须执行，所有模式均不可跳过。分三部分顺序执行，完成后统一展示，一次用户确认。

### 生成方式

LLM 执行三部分验证：Part 1（完整性扫描）+ Part 2（冲突重扫）+ Part 3（竞品差异）。完整性检查中的 WARNING 级判断（如"高频任务是否需要 alternative_flow"）需要业务语义理解。

可选辅助脚本：`../../shared/scripts/product-design/gen_validation_report.py`（用于 Part 1/2 的机械性字段检查，LLM 必须在其上补充 Part 3 竞品差异分析和语义完整性判断）。

### Part 1: 完整性扫描

遍历 `task-inventory.json` 所有任务，按字段层级分级检查：

**ERROR 级（required 字段缺失）**：

| 检查项 | Flag |
|--------|------|
| `main_flow` 为空或缺失 | `MISSING_MAIN_FLOW` |
| `owner_role` 缺失 | `MISSING_OWNER` |
| `frequency` 或 `risk_level` 缺失 | `MISSING_PRIORITY` |

**WARNING 级（recommended 字段缺失，仅高频+高风险任务）**：

| 检查项 | Flag |
|--------|------|
| `exceptions` 为空或缺失 | `MISSING_EXCEPTIONS` |
| `acceptance_criteria` 少于 3 条 | `THIN_AC` |
| `rules` 为空 | `MISSING_RULES` |

**INFO 级（recommended 字段缺失，中低频任务）**：

| 检查项 | Flag |
|--------|------|
| `exceptions` 为空或缺失 | `INFO_MISSING_EXCEPTIONS` |
| `acceptance_criteria` 少于 3 条 | `INFO_THIN_AC` |
| `value` 字段缺失 | `INFO_MISSING_VALUE` |

**展示规则**：ERROR 级全部列出；WARNING 级列出具体任务；INFO 级仅展示统计数字（如「另有 X 个中低频任务缺少 exceptions，属于 INFO 级」）。

### Part 2: 冲突重扫

基于完整地图重扫，比 Step 4 覆盖更广：

| 冲突类型 | Flag | 说明 |
|----------|------|------|
| 跨角色规则矛盾 | `CROSS_ROLE_CONFLICT` | A 角色的规则和 B 角色的规则互相冲突 |
| 状态流转死锁 | `STATE_DEADLOCK` | 任务 A 的输出状态被任务 B 的规则拒绝 |
| 幂等规则不一致 | `IDEMPOTENCY_CONFLICT` | 两个任务对同一对象的幂等规则不一致 |

### Part 3: 竞品差异（`competitors` 非空时执行）

Web 搜索加载各竞品功能概况，与完整任务清单做 diff，生成三列。

**对比维度**：根据 `competitor-profile.json` 中的 `comparison_scope` 确定对比焦点：
- `platform_features`：对比平台级功能模块（如核心业务、用户管理、数据分析），以我方任务清单的功能模块为基准
- `user_experience`：对比用户交互体验（如搜索、推荐、下单流程）
- `business_model`：对比商业模式（如佣金结构、会员体系、广告模式）
- `comprehensive`：全方位对比

Web 搜索策略：优先访问竞品官方功能页、官方帮助文档目录，其次参考第三方对比评测。
对比粒度：以任务清单中的 name 为基准单位。
搜索失败处理：若某竞品数据无法获取，记录 `"data_source": "unavailable"`，不中断 Part 3，其余竞品继续分析。

| 列 | 含义 | 用户决策 |
|----|------|----------|
| `we_have_they_dont` | 我们有竞品没有 | 确认是否作为差异化保留 |
| `they_have_we_dont` | 竞品有我们没有 | 评估是否补齐 |
| `both_have_different_approach` | 都有但做法不同 | 确认设计分歧方向 |

Web 搜索完成后，将竞品功能数据补全到 `competitor-profile.json`，`analysis_status` 改为 `"completed"`。

### 用户确认

三部分结果合并展示，用户确认：
- 哪些完整性问题是真实问题（vs 误报）
- 哪些冲突需要处理
- 哪些竞品差距需要跟进

确认后将结果写入 `validation-report.json` 和 `validation-report.md`。

**回写**：Step 9 完成后，将校验结果回写到 `product-map.json` 的 `summary` 字段（`validation_issues`、`competitor_gaps`），确保汇总文件始终反映最新状态。

### `validation-report.json` Schema

> 详见 ./docs/schemas/validation-report-schema.md

输出：`.allforai/product-map/validation-report.json`、`.allforai/product-map/validation-report.md`、`.allforai/product-map/competitor-profile.json`（补全）
