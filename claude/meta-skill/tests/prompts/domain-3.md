# 责任域-3 断言检查
## 负责 capabilities：translate、compile-verify

读取以下文件：
- `/Users/aa/workspace/myskills/claude/meta-skill/knowledge/capabilities/compile-verify.md`

注意：translate 可能没有独立 capability `.md`，若不存在，从 bootstrap.md 和 compile-verify.md 推断其契约，并在 b2_findings 中注明。

## Contract 表

| capability | artifact_path | required_fields | validation_mode |
|------------|---------------|-----------------|-----------------|
| translate | 源代码文件（非 .allforai/） | 每个 prune included=true 任务对应至少一个实现文件 | B2 semantic |
| compile-verify | build artifacts (dist/, .apk, .app, binary) | exit_code=0, artifact_paths[](每模块一条) | B1 mechanical |

## 断言执行步骤

**断言 A**：
- translate：是否有 `.md` 声明"每个 prune included 任务必须对应实现文件"？
- compile-verify：`exit_code=0` 和 `artifact_paths[]` 是否在 compile-verify.md 的 Output/Rules 中声明？

**断言 B1（机械链路）**：
- compile-verify：Platform-Specific Build Commands 表是否覆盖所有 7 种 module 类型（Flutter/React Native/iOS/Android/Next.js/React/Go）？每种是否有对应的 artifact 路径？

**断言 B2（语义链路）**：
- translate：prune 范围传递到 translate 实现范围的机制是否有描述？

## 关键约束检查

compile-verify.md 是否包含"Split by Platform (REQUIRED for multi-platform projects)"的说明？
若包含，是否明确禁止将 Flutter 和 npm 放在同一节点？

## 输出格式（同域-1 的 YAML 结构，domain 改为 域-3）

严格按以下 YAML 格式输出：

```yaml
domain: 域-3
capabilities: [translate, compile-verify]

results:
  - capability: translate
    assertion_A: PASS|FAIL
    assertion_B1: N/A
    assertion_B2: PASS|FAIL|FINDING
    b1_failures: []
    b2_findings: []

  - capability: compile-verify
    assertion_A: PASS|FAIL
    assertion_B1: PASS|FAIL
    assertion_B2: N/A
    b1_failures: []
    b2_findings: []

critical_violations: []
```
