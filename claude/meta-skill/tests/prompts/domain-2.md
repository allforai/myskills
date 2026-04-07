# 责任域-2 断言检查
## 负责 capabilities：feature-gap、feature-prune、ui-design

读取以下文件：
- `/Users/aa/workspace/myskills/claude/meta-skill/knowledge/capabilities/ui-design.md`

注意：feature-gap 和 feature-prune 可能没有独立的 capability `.md` 文件，若不存在，从 product-analysis.md 和 ui-design.md 推断其契约，并在 b2_findings 中注明。

## Contract 表

| capability | artifact_path | required_fields | validation_mode |
|------------|---------------|-----------------|-----------------|
| feature-gap | `.allforai/feature-gap/gap-tasks.json` | gaps[].task_ref, gaps[].type, gaps[].priority | B1 mechanical |
| feature-prune | `.allforai/feature-prune/prune-tasks.json` | decisions[].task_id, decisions[].included, decisions[].reason | B1 mechanical |
| ui-design | `.allforai/ui-design/ui-design-spec.md` | screens[](含 screen_name, role), navigation_flows[] | B2 semantic |

## 断言执行步骤

**断言 A**：
- feature-gap：`gap-tasks.json` 及其 required_fields 是否被某个 capability `.md` 声明为 Output？
- feature-prune：`prune-tasks.json` 及其 required_fields 是否被某个 capability `.md` 声明为 Output？
- ui-design：`ui-design-spec.md` 的 required_fields（screens, navigation_flows）是否在 ui-design.md 的 Output 声明中？

**断言 B1（机械链路）**：
- feature-gap：`gaps[].task_ref` 字段名是否与上游 `task-inventory.tasks[].id` 一致？（检查 `.md` 中的引用说明）
- feature-prune：`decisions[].task_id` 是否能回溯到 `gap-tasks.gaps[].task_ref` 或 `task-inventory.tasks[].id`？

**断言 B2（语义链路）**：
- ui-design：`.md` 是否要求 screens 覆盖所有 prune `included=true` 的任务？

## 输出格式（同域-1 的 YAML 结构，domain 改为 域-2）

严格按以下 YAML 格式输出：

```yaml
domain: 域-2
capabilities: [feature-gap, feature-prune, ui-design]

results:
  - capability: feature-gap
    assertion_A: PASS|FAIL
    assertion_B1: PASS|FAIL
    assertion_B2: N/A
    b1_failures: []
    b2_findings: []

  - capability: feature-prune
    assertion_A: PASS|FAIL
    assertion_B1: PASS|FAIL
    assertion_B2: N/A
    b1_failures: []
    b2_findings: []

  - capability: ui-design
    assertion_A: PASS|FAIL
    assertion_B1: N/A
    assertion_B2: PASS|FAIL|FINDING
    b1_failures: []
    b2_findings: []

critical_violations: []
```
