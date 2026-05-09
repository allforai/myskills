# 责任域-Codex 断言检查
## 负责 capabilities：concept-contract、app-design、game-design（新增字段）、bootstrap（新增字段）

读取以下文件：
- `/Users/aa/workspace/myskills/claude/meta-skill/knowledge/capabilities/concept-contract.md`
- `/Users/aa/workspace/myskills/claude/meta-skill/knowledge/capabilities/app-design.md`
- `/Users/aa/workspace/myskills/claude/meta-skill/knowledge/capabilities/game-design.md`
- `/Users/aa/workspace/myskills/claude/meta-skill/skills/bootstrap.md`
- `/Users/aa/workspace/myskills/claude/meta-skill/knowledge/orchestrator-template.md`
- `/Users/aa/workspace/myskills/claude/meta-skill/scripts/orchestrator/check_artifacts.py`

## Contract 表（来自 Codex 改进 spec）

| capability / file | artifact / field | required_content | validation_mode |
|-------------------|-----------------|------------------|-----------------|
| concept-contract.md | output: `concept-contract.json` | `schema_version`, `canonical_registry`, `file_prefix` per type, halt on unapproved gate | A + B1 + B2 |
| app-design.md | canonical registry | 6 nodes present, required vs optional split, approval-records path `app-design/` | A + B1 |
| game-design.md | `current_state` enum | `locked` as 5th state | A + B1 |
| game-design.md | `substitution` object | `locked: null` key | B1 |
| game-design.md | `summary.by_state` | `locked: 0` key | B1 |
| game-design.md | lifecycle section | transition rules for all 5 states, UPSTREAM_DEFECT on locked overwrite | A + B2 |
| game-design.md | `review_checklist` | in approval-records schema AND in node frontmatter | A |
| bootstrap.md | workflow.json schema | `hard_blocked_by` AND `alignment_refs` fields present (not `blocked_by`) | A + B1 |
| bootstrap.md | exit_artifacts schema | object form with `path` + `validation_commands` | A |
| bootstrap.md | `has_concept_drift` | 3 conditions; `concept_drift_source` covers conditions 2 AND 3 as "game-design-gate" | A + B2 |
| bootstrap.md | concept-freeze injection | YAML frontmatter uses `hard_blocked_by` (not `blocked_by`) | B1 |
| orchestrator-template.md | Core Loop step 4 | `hard_blocked_by` and `alignment_refs` both mentioned with distinct semantics | A + B2 |
| check_artifacts.py | artifact loop | `isinstance(item, dict)` branch; extracts `path` and `validation_commands` | B1 |

## 断言执行步骤

### 断言 A（结构完整性）

对每个文件/capability，检查其中声明的结构是否包含 contract 表中要求的所有字段/内容。

- concept-contract.md：输出 Schema 中是否包含 `schema_version`、`canonical_registry`、所有类型的 `file_prefix` 派生规则（character/tile/environment/ui/vfx/icon/audio-cover）？是否有 Completion Check 节？
- app-design.md：Canonical Node Registry 是否包含全部 6 个节点？是否明确区分 required/optional？Human Gate Protocol 节是否引用 `.allforai/app-design/approval-records.json`（非 game-design）？
- game-design.md：`current_state` 枚举是否包含 `locked`？是否存在 Asset Lifecycle Transition Rules 节？`review_checklist` 是否出现在 approval-records.json schema 中？
- bootstrap.md：workflow.json schema 是否包含 `hard_blocked_by` 和 `alignment_refs`（无 `blocked_by`）？exit_artifacts 是否包含 `path` + `validation_commands` 对象形式？`has_concept_drift` 是否列出 3 个触发条件？
- orchestrator-template.md：Core Loop step 4 是否包含 `hard_blocked_by` 和 `alignment_refs` 的说明？

### 断言 B1（机械链路）

检查字段名跨文件一致性（不能出现 A 文件输出 X，B 文件期望 Y 的情况）。

**B1-1：concept-contract.md — file_prefix 声明 vs 输出 Schema 一致性**
- Step 2 的类型派生规则（如 `character → npc_{asset_id}`）是否与输出 Schema 中 `canonical_registry.characters[].file_prefix` 的示例格式 `"npc_<slug>"` 一致？

**B1-2：app-design.md — screen_id 跨节点引用一致性**
- `ia-design.json` 输出的 `screens[].screen_id` 字段名，与 `user-flow-design.json` 的步骤中引用的字段名（`steps[].screen`）是否有语义一致性说明（screen_id → screen）？

**B1-3：game-design.md — locked 状态三处一致**
- `locked` 是否同时出现在：(a) `current_state` 枚举、(b) `substitution` 对象键、(c) `summary.by_state` 对象键？三处缺任一 → FAIL。

**B1-4：bootstrap.md — concept-freeze YAML frontmatter 字段名**
- 在 bootstrap.md 的 concept-freeze 节点注入块中，verbatim node-spec YAML frontmatter 使用的是 `hard_blocked_by` 还是 `blocked_by`？必须是 `hard_blocked_by`。

**B1-5：bootstrap.md — concept_drift_source 条件覆盖**
- `has_concept_drift` 的第 3 个条件（re-approved with revision_notes）是否被明确映射到 `concept_drift_source: "game-design-gate"`（而非未标注或映射到其他值）？

**B1-6：check_artifacts.py — dict/string 双路支持**
- 文件中是否存在 `isinstance` 检查用于区分 dict 和 string artifact 格式？是否提取了 `item["path"]` 和 `item.get("validation_commands", [])`？

### 断言 B2（语义正确性）

检查指令内容是否足以让 LLM 子代理正确执行，无歧义。

**B2-1：concept-contract.md — 命名冲突防护语义**
- 文件是否明确说明了"为什么"需要 canonical_registry（防止命名不一致），以及下游节点必须读取 `canonical_registry` 而非自行命名？

**B2-2：game-design.md — locked 状态不可逆语义**
- 生命周期规则是否明确表达：locked 资产不可被覆盖/重新生成，违反时 LLM 应报 UPSTREAM_DEFECT 并停止？

**B2-3：bootstrap.md — hard_blocked_by vs alignment_refs 语义区分**
- 两个字段的说明是否足够清晰，让 bootstrap 生成的节点图和 orchestrator 调度决策不会混淆？迁移说明是否告知 `blocked_by` 等同于 `hard_blocked_by`？

**B2-4：orchestrator-template.md — 调度行为差异**
- orchestrator 对 `hard_blocked_by` 的行为（不可启动）vs `alignment_refs` 的行为（可并行启动，但降级读取）是否有不同的调度指令？

## 输出格式

严格按以下 YAML 格式输出，不添加额外字段：

```yaml
domain: 域-Codex
capabilities: [concept-contract, app-design, game-design, bootstrap, orchestrator-template, check_artifacts]

results:
  - capability: concept-contract
    assertion_A: PASS|FAIL
    assertion_B1: PASS|FAIL
    assertion_B2: PASS|FAIL|FINDING
    b1_failures: []
    b2_findings: []

  - capability: app-design
    assertion_A: PASS|FAIL
    assertion_B1: PASS|FAIL
    assertion_B2: N/A
    b1_failures: []
    b2_findings: []

  - capability: game-design (new fields)
    assertion_A: PASS|FAIL
    assertion_B1: PASS|FAIL
    assertion_B2: PASS|FAIL|FINDING
    b1_failures: []
    b2_findings: []

  - capability: bootstrap (new fields)
    assertion_A: PASS|FAIL
    assertion_B1: PASS|FAIL
    assertion_B2: PASS|FAIL|FINDING
    b1_failures: []
    b2_findings: []

  - capability: orchestrator-template
    assertion_A: PASS|FAIL
    assertion_B1: N/A
    assertion_B2: PASS|FAIL|FINDING
    b1_failures: []
    b2_findings: []

  - capability: check_artifacts.py
    assertion_A: N/A
    assertion_B1: PASS|FAIL
    assertion_B2: N/A
    b1_failures: []
    b2_findings: []

critical_violations: []   # 若有 CONSTRAINT_VIOLATION 或缺失关键字段，在此列出
```
