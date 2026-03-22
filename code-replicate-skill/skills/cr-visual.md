---
name: cr-visual
description: >
  Use when user wants to "compare UI visually", "视觉还原", "截图对比",
  "UI 还原度", "看看界面像不像", "visual comparison", "screenshot diff",
  or mentions comparing source and target app screenshots for UI fidelity.
---

# 视觉还原度 — CR Visual v1.0

> 源 App vs 目标 App 逐屏截图/录像 → 对比 → 修复 → 重新对比 → 直到视觉一致

## 定位

cr-visual 是复刻流程的**最后一步** — 在 cr-fidelity + product-verify + testforge 全部通过后执行。

```
/cr-fidelity → /product-verify → /testforge → /cr-visual（这里）
```

**前置条件**：测试全绿，App 能稳定运行。截图对比需要 App 正常工作。

**多角色对比**：如果 `role-view-matrix.json` 存在 → 逐角色截图并分别对比。

**动态效果对比**：如果 `interaction-recordings.json` 存在 → 源 App 的录像已在 Phase 2.13 采集。cr-visual 对目标 App 执行同样的操作录制 → LLM 观看两段录像对比：
- 动画类型是否一致（淡入淡出 vs 滑动 vs 无动画）
- 动画时长是否接近
- 交互反馈是否等价（拖拽排序的视觉反馈、hover 状态变化）
- match_level: high / medium / low / mismatch

---

## 流程

```
Step 1: 获取 screen 列表（从 experience-map）
Step 2: 获取源 App 截图/录像（Phase 2 已采集 or 现场采集）
Step 3: 获取目标 App 截图/录像
Step 4: LLM 逐屏对比（结构级 + 动态效果）
Step 5: 差异报告 + 评分
Step 6: 修复差异（LLM 修改目标代码）
Step 7: 重新截图/录像 → 重新对比 → 达标退出
```

`full` 模式 = Step 1-7 闭环（最多 3 轮）
`analyze` 模式 = Step 1-5 仅出报告
`fix` 模式 = Step 6-7 基于上次报告修复

---

## Step 1: Screen 列表 + 路由映射

从 `.allforai/experience-map/experience-map.json` 提取所有 screen，建立路由映射：

```
1. 从 experience-map 提取每个 screen 的 name、route（如有）、layout_type
2. 读 .allforai/code-replicate/visual/route-map.json（Phase 2c-visual 生成的路由→截图映射）
3. 建立配对：screen name ↔ route path ↔ 源截图文件名
   - experience-map screen 有 route → 直接匹配 route-map
   - experience-map screen 无 route → LLM 按 screen name 和 route-map 的语义相似度匹配
4. 跳过无法配对的 screen
```

---

## Step 1.5: 源 App 启动信息

cr-visual 需要知道怎么启动和导航源 App。信息来源（优先级）：

1. **replicate-config.json 的 `source_app` 字段**（code-replicate Phase 1 收集）：
   ```json
   "source_app": {
     "start_command": "npm run dev",
     "backend_start_command": "cd server && npm start",
     "seed_command": "npm run db:seed",
     "url": "http://localhost:3000",
     "login": {
       "username": "test@example.com",
       "password": "test123",
       "bypass_command": "设置环境变量/API调用来绕过2FA（如有）"
     },
     "platform": "web | mobile | desktop"
   }
   ```
   Phase 1 Preflight 时 LLM 应向用户询问：
   - 源 App 如何启动？需要先启动后端吗？
   - 有测试数据吗？seed 命令是什么？
   - 需要登录吗？有验证码/2FA 吗？怎么绕过？

2. **用户通过 `--source` 参数直接提供 URL**

3. **用户通过 `--screenshots` 提供已有截图**

如果 replicate-config 没有 `source_app` 且用户未传参 → AskUserQuestion 引导。

---

## Step 2: 源 App 截图

**方式 A（首选）— Phase 2 已采集**：
- 检查 `.allforai/code-replicate/visual/source/` 是否已有截图
- 已有 → 直接复用（Phase 2c-visual 在复刻早期已自动采集，此时源项目环境可能已不在）

**方式 B — 用户提供截图目录**：
- 读取 `--screenshots` 目录中的图片文件
- LLM 将图片文件名与 experience-map screen name 配对

**方式 C — 源 App 仍可运行**：
- 按 Phase 2c-visual 的完整协议执行（启动后端 → seed 数据 → 启动前端 → 登录 → 截图）
- 任何前置条件失败（后端不可用、数据库为空、登录失败）→ 不截图，报具体失败原因

**无截图可用** → 报错退出：「源 App 截图不可用。请提供 --screenshots 目录，或确保源 App 环境完整（后端 + 数据 + 登录凭证）」

---

## Step 3: 目标 App 截图

**Web 目标**：Playwright browser_navigate → browser_take_screenshot → 保存到 `visual/target/`

**移动端目标**：Maestro navigate → screenshot → 保存到 `visual/target/`

**桌面端目标（WPF/MAUI/Electron）**：
- Electron → 有 Web 内核，Playwright 可用 ✓
- WPF/WinForms/MAUI native → Playwright 不可用：
  - 尝试：用 Bash 启动 App → 等待窗口 → 系统截图工具（如 `screencapture` macOS / `nircmd` Windows）
  - 但无法自动导航到各屏幕 — 只能截启动画面
  - **降级**：提示用户手动导航目标 App 并截图到 `visual/target/`，标记 `MANUAL_CAPTURE`
  - 报告中注明：「桌面 App 自动截图受限，{N} 个 screen 需要手动提供」

---

## Step 4: LLM 逐屏对比

对每对截图（source/screen_name.png vs target/screen_name.png），LLM 用 Read 查看两张图片，评估：

**结构级对比（做）**：
- 区域划分是否等价？（头部/内容/底部/侧边栏）
- 关键 UI 元素是否存在？（按钮、输入框、列表、卡片）
- 数据展示区域的位置是否合理？
- 导航入口是否可见？（菜单、Tab、返回按钮）
- 信息层级是否一致？（标题 > 副标题 > 正文的层次感）

**不做**：
- 像素级颜色对比（目标可以换主题色）
- 字体/字号精确匹配（目标可以用不同字体）
- 间距/留白精确匹配（目标可以重新设计间距）
- 动画/过渡效果（截图看不到）

**跨平台调整**：
- 如果 stack-mapping 有 `platform_adaptation.ux_transformations`
- 按转换期望评估：mobile 单列 → desktop 多面板不算 gap
- mobile 底部导航 → desktop 侧边栏不算 gap

**每个 screen 输出**：
```json
{
  "screen": "screen name",
  "match_level": "high | medium | low | mismatch",
  "score": 100 | 70 | 40 | 0,
  "differences": "LLM 自由描述差异",
  "source_screenshot": "visual/source/xxx.png",
  "target_screenshot": "visual/target/xxx.png"
}
```

---

## Step 5: 报告

写入 `.allforai/code-replicate/visual-report.json` + `visual-report.md`：

```json
{
  "generated_at": "ISO8601",
  "total_screens": 20,
  "compared": 18,
  "skipped": 2,
  "overall_score": 82,
  "screens": [
    {"screen": "...", "match_level": "high", "score": 100, "differences": "无明显差异"},
    {"screen": "...", "match_level": "low", "score": 40, "differences": "列表布局从卡片式变成了表格式，缺少筛选栏"}
  ]
}
```

`visual-report.md` 包含：
- 每个 screen 的截图路径对（用户可直接查看）
- 差异描述
- 整体评分
- 低分 screen 的修复方案

---

## Step 6+7: 修复闭环 — 调用 ralph-loop

视觉还原追求 **100% 一致**，不是"差不多就行"。使用 ralph-loop 持续修复直到完美。

**启动 ralph-loop**：

```
/ralph-loop 启动视觉还原修复循环

每轮执行:
  1. 读 visual-report.json → 找到 match_level ≠ high 的 screen
  2. 按 score 从低到高排序 → 取最低分的 1 个 screen
  3. 读源截图/录像 + 目标截图/录像 → 识别具体差异
  4. 修复目标代码：
     - 布局结构 → 改模板/CSS
     - 组件缺失 → 补组件
     - 主题变量 → 修正变量值
     - 素材缺失 → 补图标/图片/字体
     - 动画缺失 → 补 CSS transition / 动画代码
     - 数据展示差异 → 检查数据获取逻辑
  5. 构建验证（确保不破坏编译）
  6. 对修复的 screen 重新截图/录像
  7. 重新对比 → 更新 visual-report.json
  8. 该 screen 达到 high → 下一个 screen
     仍未 high → 继续修该 screen（不同角度的差异）

退出条件:
  - 所有 screen match_level = high → 100% 达成
  - 或达到 30 轮上限
```

**关键要求**：

**必须使用真实数据和真实服务**：
- 截图时目标 App 必须连接**真实后端**（不是 mock server）
- 页面展示的必须是**真实业务数据**（不是 seed 的采样数据）
- 如果源 App 截图时用的是真实数据 → 目标 App 截图时也必须用同样的数据源
- 数据差异导致的界面差异不是视觉 bug — 但**空数据 vs 有数据**的差异是 bug

**每轮只修 1 个 screen**：
- 聚焦一个问题修到完美，不跳来跳去
- 修完一个 screen（high）再修下一个
- 避免"改了 A 破了 B"的来回

**30 轮不是上限而是最低保证**：
- 60 个页面 × 可能每个页面需要 1-3 轮 → 需要足够多的轮次
- 如果 30 轮后还有 screen 未达 high → 继续（ralph-loop 不限轮次）
- 只有当所有 screen 都 high 或用户手动终止时才停

---

## 局限性

- LLM 的视觉对比是**主观的** — 报告附截图路径，用户应复核
- 需要 App 能运行且可导航到各页面（需要测试账号/数据）
- 移动端截图依赖 Maestro 或用户手动截图
- 不覆盖交互行为（只能看静态截图，不能验证点击/滑动）

---

## 加载核心协议

> 核心协议详见 ${CLAUDE_PLUGIN_ROOT}/skills/code-replicate-core.md
