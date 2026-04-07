# 责任域-1 断言检查
## 负责 capabilities：product-concept、reverse-concept、product-analysis

读取以下文件：
- `/Users/aa/workspace/myskills/claude/meta-skill/knowledge/capabilities/product-concept.md`
- `/Users/aa/workspace/myskills/claude/meta-skill/knowledge/capabilities/reverse-concept.md`
- `/Users/aa/workspace/myskills/claude/meta-skill/knowledge/capabilities/product-analysis.md`

## Contract 表（来自设计 spec）

| capability | artifact_path | required_fields | validation_mode |
|------------|---------------|-----------------|-----------------|
| product-concept | `.allforai/product-concept/product-concept.json` | name, vision, target_users[], core_features[] | B2 semantic |
| reverse-concept | `.allforai/product-concept/concept-baseline.json` | features[], business_flows[], constraints[], evidence_sources[] | B1 + B2 |
| product-analysis | `.allforai/product-map/task-inventory.json`, `role-profiles.json` | tasks[].id, tasks[].name, tasks[].role_ref, roles[].name, roles[].id | B1 + B2 |

## 断言执行步骤

**断言 A（结构完整性）**：
对每个 capability，检查其 `.md` 文件中声明的 Output/Required Outputs 是否包含 contract 表中列出的所有 required_fields。

**断言 B1（机械链路）**：
- reverse-concept：`concept-baseline.json` 的 `features[].id` 字段 — `.md` 中是否声明为必填且被下游引用？
  检查：`features[]` 输出声明是否存在，下游（product-analysis）是否引用 concept-baseline 作为输入。
- product-analysis：`tasks[].id` 和 `roles[].id` — 是否被声明为必填？
  检查：feature-gap 的 `gaps[].task_ref` 字段名是否与 `tasks[].id` 一致（查找 product-analysis.md 中的 downstream 引用说明）。

**断言 B2（语义链路）**：
- product-concept：输出的 `name/vision/target_users/core_features` 是否足以描述完整产品愿景？
- reverse-concept：`.md` 是否要求每个输出字段有代码证据支撑（`evidence_sources`）？
- product-analysis：任务覆盖要求（如 >= 10 tasks）是否有明确说明？

## 输出格式

严格按以下 YAML 格式输出：

```yaml
domain: 域-1
capabilities: [product-concept, reverse-concept, product-analysis]

results:
  - capability: product-concept
    assertion_A: PASS|FAIL
    assertion_B1: N/A
    assertion_B2: PASS|FAIL|FINDING
    b1_failures: []
    b2_findings: []

  - capability: reverse-concept
    assertion_A: PASS|FAIL
    assertion_B1: PASS|FAIL
    assertion_B2: PASS|FAIL|FINDING
    b1_failures: []   # 若 FAIL，填写: ["[FIELD_NAME_MISMATCH] field_a → field_b"] 等
    b2_findings: []   # 若 FINDING，填写发现描述

  - capability: product-analysis
    assertion_A: PASS|FAIL
    assertion_B1: PASS|FAIL
    assertion_B2: PASS|FAIL|FINDING
    b1_failures: []
    b2_findings: []

critical_violations: []   # 若有 CONSTRAINT_VIOLATION 或 MISSING_NODE，在此列出
```
