# 责任域-5 断言检查
## 负责 capabilities：demo-forge、quality-checks、code-tuner、launch-prep

读取以下文件：
- `/Users/aa/workspace/myskills/claude/meta-skill/knowledge/capabilities/demo-forge.md`
- `/Users/aa/workspace/myskills/claude/meta-skill/knowledge/capabilities/quality-checks.md`
- `/Users/aa/workspace/myskills/claude/meta-skill/knowledge/capabilities/tune.md`
- `/Users/aa/workspace/myskills/claude/meta-skill/knowledge/capabilities/launch-prep.md`

## Contract 表

| capability | artifact_path | required_fields | validation_mode |
|------------|---------------|-----------------|-----------------|
| demo-forge | `.allforai/demo-forge/forge-data/` | seed_data[](含 role_ref), demo_scenarios[] | B1 mechanical |
| quality-checks | `.allforai/quality-checks/deadhunt-report.json`, `fieldcheck-report.json` | dead_routes[](含 file:line), field_mismatches[], fix_tasks[] | B1 mechanical |
| code-tuner | `.allforai/code-tuner/tuner-report.json`, `tuner-tasks.json` | compliance_score, duplication_score, abstraction_score, tuner_tasks[].id | B1 mechanical |
| launch-prep | `.allforai/launch-prep/launch-checklist.json` | competitive_research(完成标志), checklist[](含 item, status) | B2 semantic |

## 断言执行步骤

**断言 A**：每个 capability 的 required_fields 是否在 `.md` Output 声明中存在？

**断言 B1（机械链路）**：
- demo-forge：`seed_data[].role_ref` 是否被声明为引用 `role-profiles.json`？
- quality-checks：`fix_tasks` 是否被声明为包含 `file:line` 引用？
- code-tuner：compliance_score / duplication_score / abstraction_score 是否被声明为数值型输出？

**断言 B2（语义链路）**：
- launch-prep：checklist 是否要求覆盖目标平台合规项（App Store / Google Play / Web）？

## 输出格式（同域-1 的 YAML 结构，domain 改为 域-5，capabilities 列表更新）

严格按以下 YAML 格式输出：

```yaml
domain: 域-5
capabilities: [demo-forge, quality-checks, code-tuner, launch-prep]

results:
  - capability: demo-forge
    assertion_A: PASS|FAIL
    assertion_B1: PASS|FAIL
    assertion_B2: N/A
    b1_failures: []
    b2_findings: []

  - capability: quality-checks
    assertion_A: PASS|FAIL
    assertion_B1: PASS|FAIL
    assertion_B2: N/A
    b1_failures: []
    b2_findings: []

  - capability: code-tuner
    assertion_A: PASS|FAIL
    assertion_B1: PASS|FAIL
    assertion_B2: N/A
    b1_failures: []
    b2_findings: []

  - capability: launch-prep
    assertion_A: PASS|FAIL
    assertion_B1: N/A
    assertion_B2: PASS|FAIL|FINDING
    b1_failures: []
    b2_findings: []

critical_violations: []
```
