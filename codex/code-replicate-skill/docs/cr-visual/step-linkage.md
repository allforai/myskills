# Step 4.6: 控件联动验证

> 本文档由 cr-visual orchestrator 派遣的 **linkage agent** 加载。
> 职责：验证控件联动的因果关系（操作 A → B 是否正确响应）。
> **前置条件**：`interaction-recordings.json` 存在且含 `linkage_verify` 步骤。无此文件或无联动步骤 → 返回空结果。

## 核心原则

Step 4/4.5 检查的是静态状态（截图里看到什么），本步骤检查的是**动态因果**（操作 A → B 是否正确响应）。

## 执行协议

对 interaction-recordings 中每个 `linkage_verify` 步骤：

```
1. 在目标 App 上执行 trigger_action（如 select "广东省"）
2. 等待联动响应（短暂 wait，通常 500ms-2s）
3. 逐个验证 expected_effects：

   options_update（级联选择）：
     → 展开下游选择器 → 截图 → 选项列表非空且内容与触发值关联
     → 与源 App 同步骤截图对比

   visibility_toggle（条件显隐）：
     → 检查目标控件的 visible 状态变化
     → 截图验证：控件出现/消失与源 App 一致

   enabled_toggle（条件启禁）：
     → 检查目标控件的 disabled/enabled 状态
     → 截图对比或 DOM 属性检查

   value_update（自动计算）：
     → 读取目标控件的显示值
     → 与源 App 的对应值对比（或根据已知公式验证正确性）
     → 特别关注：NaN、0、空白 = 计算链路断裂

   data_filter（联动筛选）：
     → 切换后截图 → 表格/列表内容是否正确过滤
     → 行数变化是否合理（不是全量也不是零行）

   detail_load（主从联动）：
     → 点击主控件某行 → 截图详情区域
     → 详情内容是否对应被点击行的数据（强断言：字段值匹配）

   reset（联动重置）：
     → 上级变化后 → 下级是否正确清空/恢复默认

4. 每个联动检查点输出：
   - linkage_result: pass / fail / partial
   - 失败时记录：trigger_control、target_control、effect_type、expected、actual
```

## 评分

```
每个联动检查点的结果：
  pass    → 不扣分
  partial → -5 分（联动触发了但结果不完全正确，如选项有但内容不对）
  fail    → -10 分（联动完全无效，下游控件无响应）
```

## 输出

对每个 screen 返回：
```json
{
  "screen": "screen name",
  "linkage_score": 90,
  "linkage_results": [
    {
      "trigger_control": "省份下拉框",
      "trigger_action": "select 广东省",
      "target_control": "城市下拉框",
      "effect_type": "options_update",
      "result": "fail",
      "expected": "选项更新为广东省城市",
      "actual": "选项列表仍为空",
      "root_cause": "onChange 未调用 fetchCities()，事件绑定丢失",
      "penalty": -10
    }
  ]
}
```
