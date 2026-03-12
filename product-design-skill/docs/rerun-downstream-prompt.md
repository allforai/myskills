# 通用重跑下游提示语

> 适用场景：已用旧版 experience-map 插件（< v2.1.0）完成全流程的项目，需要重跑 Phase 4+ 以提升前端代码质量。
>
> 使用方法：在目标项目目录下新开对话，粘贴下方提示语。

---

```
采用全自动模式，从 Phase 4 experience-map 开始重跑所有下游阶段，直到产品设计全流程完成。

## 为什么要重跑

experience-map 插件已升级到 v2.2.0，修复了以下导致前端代码质量低下的问题：
- 新增 `app` 维度：每个屏幕标注所属独立应用（website/merchant/admin），跨角色业务流中的屏幕按 node role 归属正确的应用
- 分批策略从按 OL 角色改为按 app 分批，确保每个屏幕从正确的应用视角设计
- emotion_design 从字符串改为结构化对象
- states 必须包含业务特定状态（不再是千篇一律的 4 状态模板）
- 大文件处理从单一 Python dict 改为分批设计（禁止模板函数）
- verify loop 新增 9 条设计质量规则
- 新增 Step 3.1 质量提升 loop（3 轮渐进提升，全局评分 ≥ 4.0）
- 线框 Review Hub 显示 app 标签，审核者一眼区分 merchant 和 admin 屏幕

## 前置条件确认

先检查以下产物存在且完整（这些不重跑）：
- .allforai/product-concept/product-concept.json ← Phase 1
- .allforai/product-map/task-inventory.json ← Phase 2
- .allforai/experience-map/journey-emotion-map.json ← Phase 3
- .allforai/experience-map/experience-map-skeleton.json ← 骨架（保留复用）

如果骨架不存在，先运行 Step 1.5 生成骨架再继续。

## 重跑前清理

执行以下清理（保留骨架和 Phase 1-3 产物）：

```bash
# 清理 Phase 4+ 产物
rm -f .allforai/experience-map/experience-map.json
rm -f .allforai/experience-map/experience-map-report.md
rm -f .allforai/experience-map/experience-map-decisions.json
rm -f .allforai/experience-map/interaction-gate.json
rm -f .allforai/experience-map/batch_fill_*.py
rm -f .allforai/experience-map/_batch_*.json
rm -f .allforai/experience-map/_filled_*.json
rm -f .allforai/experience-map/gen_fill_screens.py
rm -f .allforai/experience-map/gen_fix_feedback.py
rm -rf .allforai/wireframe-review/
rm -rf .allforai/use-case/
rm -rf .allforai/feature-gap/
rm -rf .allforai/ui-design/
rm -rf .allforai/ui-review/
rm -rf .allforai/design-audit/
rm -f .allforai/pipeline-decisions-*.json
```

```python
# 回滚 pipeline-decisions.json 到 Phase 3
import json
with open('.allforai/pipeline-decisions.json') as f:
    decisions = json.load(f)
kept = [d for d in decisions if any(p in d.get('phase','') for p in ['Phase 1', 'Phase 2', 'Phase 3'])]
with open('.allforai/pipeline-decisions.json', 'w') as f:
    json.dump(kept, f, ensure_ascii=False, indent=2)
print(f'Kept {len(kept)}, removed {len(decisions)-len(kept)}')
```

## 重跑阶段

### Phase 4: experience-map（强制重跑，使用 v2.1.0）

1. 保留骨架 experience-map-skeleton.json（确定性产物，不重新生成）
2. 从 Step 2 开始，使用分批设计策略（按角色分批，每批独立思考）
3. 通过 Step 3 合格性验收（硬性规则 + 设计质量规则）
4. 通过 Step 3.1 质量提升 loop（3 轮，全局平均 ≥ 4.0）
5. 通过 Step 3.5 Playwright 线框验证
6. 完成 Step 3.6 模式扫描 + 行为规范

### Phase 4.5: interaction-gate（重跑）

### Phase 5: wireframe-review（重跑，人工审核门）

### Phase 6: 并行组（全部重跑）
- use-case
- feature-gap
- ui-design

### Phase 7: ui-verify（重跑）

### Phase 8: design-audit（重跑）

## 执行模式

- 全自动：ERROR 停，WARNING 记日志继续，PASS 自动继续
- Phase 之间零停顿（Phase 5 人工审核除外）
- 质量提升 loop 每轮输出一行摘要（Quality Round N: avg X→Y, improved Z screens）
```

---

## 如果项目已经有 dev-forge 生成的代码

重跑产品设计全流程后，还需要重跑代码生成：

```
产品设计已用新版 experience-map 重跑完成，请基于新的产物重跑 dev-forge 全流程。

注意：
- 新版 experience-map 包含 _quality_score 字段、结构化 emotion_design、业务特定 states
- ui-design 基于新版 experience-map 的 _pattern 和 _behavioral 字段生成
- 前端代码应反映这些质量提升（更丰富的状态处理、情绪化设计、业务特定交互）
```
