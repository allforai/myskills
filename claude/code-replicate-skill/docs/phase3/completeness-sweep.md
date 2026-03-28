# Completeness Sweep（Step 3.sweep）

> Phase 3 最后一步，Phase 4 之前。
> 进度追踪 step ID: `"3.sweep"`。`--from-phase 4` 跳过此步，`--from-phase 3.sweep` 仅重跑此步。
> 本文档由 code-replicate-core.md 按需加载，不要提前阅读。

这是纵深防御——即使 EXTRACTION_PLAN_REVIEW（per-module）和 depth_decision（per-screen）已改善覆盖，仍需要**全局视角**兜底。

LLM 从两个相反的方向审视产物完整性：

## 维度 A：源码覆盖（从文件出发）

LLM 遍历源项目目录结构（不是从已提取产物出发），对每个源文件分类：

- **已覆盖**（covered）：被 extraction-plan 的某个 source 引用
- **间接覆盖**（indirectly_covered）：未被直接引用，但其功能被上层文件包含
- **未覆盖**（uncovered）：既未被引用，也未被上层包含

对所有未覆盖文件，LLM 读取文件头部（class 名 + 公开方法签名），判断：
- 工具类/配置/测试 → 合理跳过，记录原因
- 独立用户功能 → `late_discovery`，补充到产物

## 维度 B：源 App 体验走查（从用户出发）

**适用性判断**：LLM 先评估维度 B 是否适用于本项目：
- role-profiles 存在且有终端用户角色（audience_type = consumer / professional）→ 按 UI 体验走查
- role-profiles 不存在或全是 internal/system 角色（如数据管道、后端微服务）→ 降级为 **API/数据流走查**（从调用者视角：哪些 endpoint？哪些角色可调？异常响应如何？每条 DAG/数据流路径是否完整提取？）
- 无 role-profiles 且无 API（如 CLI 工具）→ 标记 dimension_b: N/A

**UI 项目走查**：LLM 基于 role-profiles，为每个角色构建使用旅程。旅程必须覆盖**主线路径 + 异常/边缘路径**：

```json
{
  "role": "普通用户",
  "main_journey": [
    "打开 app → 看到什么？",
    "进入主界面 → 有哪些入口？",
    "进入核心功能 → 能做什么？",
    "操作完成 → 有什么反馈？"
  ],
  "edge_journeys": [
    "断网时 → 离线提示？草稿保存？重发按钮？",
    "消息撤回 → 双方界面如何变化？",
    "多选消息 → 长按 → 合并转发（多步组合操作）",
    "切换账号/登出 → 数据清理？缓存保留？",
    "权限不足 → 看到什么提示？哪些入口隐藏？"
  ]
}
```

**后端/数据管道项目走查**：
```json
{
  "role": "API 调用者",
  "main_journey": [
    "认证 → 获取 token",
    "调用核心 endpoint → 返回什么？",
    "创建/修改/删除资源 → 状态码和响应体？"
  ],
  "edge_journeys": [
    "无权限调用 → 403 响应？",
    "参数错误 → 422 响应格式？",
    "并发冲突 → 409 处理？"
  ]
}
```

对旅程中的每一步，LLM 检查：
- 该步骤的 screen/endpoint 是否在 experience-map/task-inventory 中？
- 该步骤的交互是否在 interaction_triggers 中？（包括 continuous_gesture 和 continuous_binding）
- 该步骤的状态变体是否在 state_variants 中？
- **多步组合操作**的每一步是否都有对应产物？（选中→长按→操作 = 3 个独立检查点）

**跨 screen 一致性检查**：
对于旅程中发现的后台服务/全局状态（下载进度、播放状态、同步状态、通知等），LLM 检查：该服务的 UI 指示器是否在**所有应该出现的 screen** 上都有记录？一个后台服务可能在 5+ 个 screen 上有 UI 表现（如列表项图标、详情页标记、设置页管理入口、全局状态栏），漏掉任何一个 = 复刻后体验不一致。

**信息来源优先级**（构建旅程时）：
1. Phase 2 截图/录像（如果存在）→ 最直观
2. 源码路由表/导航配置 → 所有 screen/endpoint 入口
3. 源码事件绑定（onTap/onClick/onDrag/...）→ 交互清单
4. 源码状态枚举/条件渲染/错误处理 → 状态变体 + 异常路径
5. 源码权限检查 → 角色差异

多信号交叉验证，不依赖单一来源。

## 合并协议

维度 A 的 `late_discovery` + 维度 B 的 `gaps` → 去重 → 生成**补充片段**（格式与 Phase 3 per-module 片段相同，tagged `"source": "sweep"`）→ 通过现有 merge 脚本（cr_merge_tasks.py 等）合并，尊重 ID 范围和铁律 4。

## 输出

写入 `.allforai/code-replicate/completeness-sweep.json`：

```json
{
  "total_source_files": 78,
  "covered": 22,
  "indirectly_covered": 38,
  "uncovered": 18,
  "uncovered_analysis": [
    {"file": "...", "verdict": "late_discovery | skip", "reason": "...", "action": "..."}
  ],
  "journey_checks": [
    {"role": "...", "steps_checked": 28, "gaps_found": 6, "gaps": ["..."]}
  ],
  "late_discoveries_count": 5,
  "journey_gaps_count": 6,
  "merged_fragments": 8,
  "sweep_confidence": "补充后用户可感知功能覆盖率预计从约 85% 提升至 93%"
}
```
