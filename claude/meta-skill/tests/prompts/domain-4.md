# 责任域-4 断言检查
## 负责 capabilities：test-verify、product-verify

读取以下文件：
- `/Users/aa/workspace/myskills/claude/meta-skill/knowledge/capabilities/test-verify.md`
- `/Users/aa/workspace/myskills/claude/meta-skill/knowledge/capabilities/product-verify.md`

## Contract 表

| capability | artifact_path | required_fields | validation_mode |
|------------|---------------|-----------------|-----------------|
| test-verify | `.allforai/test-verify/test-verify-report.json` | results[].module_id, results[].layer, results[].pass_rate, composite_score | B1 + B2 |
| product-verify | `.allforai/product-verify/verify-report.json` | static_score, dynamic_score, composite_score, issues[] | B1 + B2 |

## 断言执行步骤

**断言 A**：
- test-verify：required_fields 中的 results[].module_id / layer / pass_rate / composite_score 是否在 `.md` 的 Output 声明中存在？
- product-verify：static_score / dynamic_score / composite_score / issues[] 是否在 `.md` 的 Output 声明中存在？

**断言 B1（机械链路）**：
- test-verify：Platform-Specific Test Commands 表是否覆盖 7 种 module 类型？
  重点检查：Flutter (`flutter test`)、iOS (`xcodebuild test`)、Android (`./gradlew connectedAndroidTest`) 是否有对应条目？
- product-verify：composite_score 是否被声明为数值类型输出？

**断言 B2（语义链路）**：
- test-verify："Split by Platform"约束（Do NOT put Flutter tests and Playwright tests in same node）是否有明确声明？
- product-verify：dynamic 验证是否要求覆盖 ui-design 的所有 screens？

**关键约束检查（必须明确报告）**：
- test-verify.md 是否包含"Playwright CANNOT test native mobile apps"或等价声明？位于哪一行/节？
- product-verify.md 是否包含"Playwright CANNOT test native mobile apps"或等价声明？位于哪一行/节？

若任一 capability 缺少此声明 → assertion_B2 = FAIL，b2_findings 说明缺失位置。

## 输出格式（同域-1 的 YAML 结构，domain 改为 域-4）

严格按以下 YAML 格式输出：

```yaml
domain: 域-4
capabilities: [test-verify, product-verify]

results:
  - capability: test-verify
    assertion_A: PASS|FAIL
    assertion_B1: PASS|FAIL
    assertion_B2: PASS|FAIL|FINDING
    b1_failures: []
    b2_findings: []

  - capability: product-verify
    assertion_A: PASS|FAIL
    assertion_B1: PASS|FAIL
    assertion_B2: PASS|FAIL|FINDING
    b1_failures: []
    b2_findings: []

critical_violations: []
```
