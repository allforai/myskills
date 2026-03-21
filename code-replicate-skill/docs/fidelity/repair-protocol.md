# 修复闭环协议 (阶段 B + C)

> 差距分类 → 批量修复 → 重测 → 收敛

---

## 阶段 B: 差距修复

### 差距分类

LLM 将 gaps 分为三类：

| 类别 | 含义 | 处理 |
|------|------|------|
| `CODE_FIX` | 目标代码缺少实现或实现错误 | 直接修改目标代码 |
| `ARTIFACT_GAP` | .allforai 产物遗漏导致 dev-forge 未生成 | cr-fidelity 内部补充产物 |
| `DESIGN_DECISION` | 架构差异导致，需要人工决策 | 写入报告 warnings，不自动修复 |

### CODE_FIX 修复安全协议

**按维度批量修复**：

1. **批量修改**：同一维度的所有 CODE_FIX 一次性全部修改
2. **批量测试**：该维度全部修改完成后，跑一次测试
3. **测试结果处理**：
   - 全部通过 → 该维度修复完成，进入下一维度
   - 部分失败 → 逐个回滚最近修改的文件，每回滚一个重跑测试，直到测试通过
   - 被回滚的 gap → 重分类为 `DESIGN_DECISION`
4. **无测试项目**：跳过测试步骤，标注 `untested_fixes`

### ARTIFACT_GAP 修复

cr-fidelity 内部处理，**不要求用户退出重跑 `/code-replicate`**：

1. LLM 读 extraction-plan.json 定位遗漏来源
2. LLM 读源码对应文件，生成补充片段 → 写入 fragments/
3. 调用 merge 脚本重新合并对应产物
4. 调用 `cr_validate.py` 校验补充后的产物
5. 少量（≤3 个新条目）→ cr-fidelity 直接在目标代码中补充实现
6. 大量（>3 个新条目）→ 标记为 `DESIGN_DECISION`，建议用户重跑 `/design-to-spec`

### DESIGN_DECISION 处理

不自动修复，但记录足够信息让用户决策：
- 具体的差异描述
- 推荐的解决方向
- 用户决策后执行 `/cr-fidelity fix` 重测

### 修复范围控制

- 每轮最多修复 **20 个 CODE_FIX** + **5 个 ARTIFACT_GAP**
- 超出则按 score 影响排序，优先修复**最低分维度**的 gaps
- DESIGN_DECISION 不计入修复额度

---

## 阶段 C: 重测循环

### 重测策略

**纯 CODE_FIX 轮** → 增量重测：
1. 记录修改了哪些文件（`modified_files` 列表）
2. 更新 fidelity-index.json 中受影响的映射
3. 只重新评估修改的文件所属维度，其他维度保持上轮分数

**含 ARTIFACT_GAP 轮** → 全量重测：
- 产物基线变了 → 所有维度必须重新评分
- 新增但未实现的条目 → 直接计为 gap

### 收敛控制 (CG-F)

```
收敛条件:
  - 达标: overall_score ≥ threshold → 输出终报，退出
  - 最多 3 轮
  - 每轮总修复 gap 数必须 > 0（有在进步）
  - 跨维度回归处理:
    · 本轮修改了文件集合 S
    · 重测时发现维度 Dx 分数下降 > 5 分
    · 找出 S 中属于 Dx 检查范围的文件子集 S_dx
    · 回滚 S_dx 中所有修改 → 重跑 Dx 单维度评分 → 确认恢复
    · 被回滚文件关联的 gap 重分类为 DESIGN_DECISION
    · 其他维度的修改保留
  - 第 3 轮仍未达标 → 输出报告 + 剩余 gaps，建议人工介入
```

### 终报输出

`fidelity-report.json` 和 `fidelity-report.md` 更新为最终轮结果，包含：
- 各维度最终评分 + 各轮变化趋势
- 已修复的 gaps（含修改的文件和 diff 摘要）
- 未修复的 gaps（DESIGN_DECISION + 超限项 + 连锁回滚项）
- 各轮修复记录
- 下一步建议
