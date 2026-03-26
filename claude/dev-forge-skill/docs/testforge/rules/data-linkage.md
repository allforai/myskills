# 铁律 — 数据完整性 + 联动组（Path C Agent + cr-visual Agent 遵守）

### 25. 控件数据完整性必须有测试守护

数据绑定控件不仅要测"能渲染"，还要测"有数据"。

**测试标准**：
- 数据容器：`expect(rows.length).toBeGreaterThanOrEqual(1)` + 强断言行内容
- 选择器：展开后 `expect(options.length).toBeGreaterThanOrEqual(1)` + 验证选项来自真实 API
- 绑定显示：`expect(text).not.toBe("")` + `expect(text).not.toMatch(/undefined|null|NaN/)`
- 可视化：`expect(dataPoints.length).toBeGreaterThanOrEqual(1)`

**禁止**：
- ❌ 用前端硬编码假数据让测试通过
- ❌ 仅测"组件渲染不报错"而不测"组件显示了真实数据"
- ❌ mock API 返回假数据让控件"看起来有数据"但真实 API 其实没对接

**空控件是真 bug**：数据链路断裂（API 未调用/字段映射错/后端查询空），必须沿数据链路溯源修复。

### 26. 控件联动必须显式测试因果关系

联动测试必须**显式验证因果**：操作 A → B 正确响应。

**测试结构**：
```
1. 设置初始状态（记录 B 的初始值/状态）
2. 执行触发操作（操作 A）
3. 等待响应（联动可能涉及 API 调用）
4. 断言 B 的变化（不只是"B 有值"，而是"B 因为 A 而正确变化"）
5. 反向验证：改回 A → B 恢复/重置
```

**禁止**：
- ❌ 只测最终状态 — 看不出中间哪步联动断了
- ❌ 只测正向不测反向
- ❌ 用 E2E 下游步骤没报错当作"联动正常"
- ❌ 跳过 disabled/enabled 状态检查

**联动断裂是高优先级 bug**：联动是用户核心心智模型。
