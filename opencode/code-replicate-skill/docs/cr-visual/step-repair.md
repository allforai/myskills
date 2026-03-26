# Step 6+7: 修复闭环

> 本文档由 cr-visual orchestrator 派遣的 **repair agent** 加载。
> 职责：逐 screen 修复差异，重新截图验证，循环至全部 high。
> **本 agent 专注修复**，每轮只修 1 个 screen。

## 核心要求

视觉还原追求 **100% 一致**，不是"差不多就行"。

> **外部插件增强**：如果 `ralph-loop` 插件已安装，可用 `/ralph-loop` 启动自动修复循环。

## 修复循环

每轮执行：

```
1. 读 visual-report.json → 找到 match_level ≠ high 的 screen
2. 按 score 从低到高排序 → 取最低分的 1 个 screen
3. 读源截图/录像 + 目标截图/录像 → 识别具体差异
4. 诊断根因层级：

   UI 层（直接修）:
     - 布局结构 → 改模板/CSS
     - 组件缺失 → 补组件
     - 主题变量 → 修正变量值
     - 素材缺失 → 补图标/图片/字体
     - 动画缺失 → 补 CSS transition / 动画代码

   数据完整性层（data_integrity_gap → 按溯源结果修）:
     - API 未调用/URL 错误 → 修前端 API 调用代码
     - API 返回空 → 检查后端查询逻辑/数据库 → 修后端或补 seed
     - 字段映射错误 → 修前端数据绑定
     - 枚举/静态选项缺失 → 补枚举定义（禁止硬编码假数据）
     - Store/State 未初始化 → 修状态管理初始化逻辑
     ⚠️ 禁止用硬编码假数据蒙混

   联动层（linkage fail/partial → 按联动类型修）:
     - 事件绑定丢失 → 补 onChange/onSelect/onClick 绑定
     - 联动 API 未调用 → 修事件处理函数
     - 联动状态未传递 → 修 setState/dispatch/emit
     - computed/watch 缺失 → 补响应式计算链
     - 条件显隐/启禁逻辑缺失 → 补条件绑定
     - 联动重置缺失 → 补上级变化时的下级 reset
     ⚠️ 修复后必须重新执行 linkage_verify

   非 UI 层（根因升级 → 修完回来）:
     - 权限 → 检查 RBAC → 修权限代码
     - 请求报错 → 检查错误码 → 修错误定义
     - 图标/字体碎裂 → 补 asset
     - 基础设施差异 → 检查协议/加密层

5. 执行修复：
   UI 层 → 直接 Edit 目标代码
   数据完整性层 → 修复真实数据链路
   联动层 → 修复事件绑定/状态传递/响应式计算链
   非 UI 层 → 根因升级 → 修完回来

6. 构建验证（确保不破坏编译）
7. 对修复的 screen 重新截图/录像
8. 重新对比 → 更新 visual-report.json
9. 该 screen 达到 high → 下一个 screen
   仍未 high → 继续修该 screen

退出条件:
  - 所有 screen match_level = high → 100% 达成
  - 或达到 30 轮上限（用户可选择继续）
```

## 关键约束

**必须使用真实数据和真实服务**：
- 截图时目标 App 必须连接**真实后端**（不是 mock server）
- 页面展示的必须是**真实业务数据**
- **空数据 vs 有数据**的差异是 bug

**每轮只修 1 个 screen**：
- 聚焦一个问题修到完美，不跳来跳去
- 避免"改了 A 破了 B"的来回

**30 轮不是上限而是最低保证**：
- 只有当所有 screen 都 high 或用户手动终止时才停
