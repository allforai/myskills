---
name: cr-visual
description: >
  Use when user wants to "compare UI visually", "视觉还原", "截图对比",
  "UI 还原度", "看看界面像不像", "visual comparison", "screenshot diff",
  or mentions comparing source and target app screenshots for UI fidelity.
---

# 视觉还原度 — CR Visual v1.0

> 源 App vs 目标 App 逐屏截图 → 结构级对比 → 差异报告

## 定位

cr-visual 是复刻流程的**最后一步** — 在 cr-fidelity + product-verify + testforge 全部通过后执行。

```
/cr-fidelity → /product-verify → /testforge → /cr-visual（这里）
```

**前置条件**：测试全绿，App 能稳定运行。截图对比需要 App 正常工作。

---

## 流程

```
Step 1: 获取 screen 列表（从 experience-map）
Step 2: 获取源 App 截图（运行截图 or 用户提供）
Step 3: 获取目标 App 截图（Playwright/Maestro 截图）
Step 4: LLM 逐屏对比（结构级，不是像素级）
Step 5: 输出差异报告
```

---

## Step 1: Screen 列表

从 `.allforai/experience-map/experience-map.json` 提取所有 screen：
- 每个 screen 的 name、route（如有）、layout_type
- 按 operation_line 分组
- 跳过没有 route 或无法导航到的 screen

---

## Step 1.5: 源 App 启动信息

cr-visual 需要知道怎么启动和导航源 App。信息来源（优先级）：

1. **replicate-config.json 的 `source_app` 字段**（code-replicate Phase 1 收集）：
   ```json
   "source_app": {
     "start_command": "cd ./source-project && npm run dev",
     "url": "http://localhost:3000",
     "login": {"username": "test@example.com", "password": "test123"},
     "platform": "web | mobile | desktop"
   }
   ```
   Phase 1 Preflight 时 LLM 应向用户询问：「源 App 如何启动？需要登录凭证吗？」

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

**方式 C — 源 App 仍可运行（Web）**：
- 用 source_app.start_command 启动源 App
- 等待 source_app.url 可达 → 登录 → 逐屏截图
- 保存到 `.allforai/code-replicate/visual/source/`

**方式 D — 源 App 仍可运行（移动端）**：
- Maestro 可用 → `maestro screenshot` 逐屏截图
- 不可用 → 提示用户手动截图并提供目录

**无截图可用** → 报错退出：「源 App 截图不可用。请提供 --screenshots 目录，或确保源 App 可启动」

---

## Step 3: 目标 App 截图

同 Step 2 的逻辑，但对目标 App 执行。
保存到 `.allforai/code-replicate/visual/target/`

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
- 低分 screen 的改进建议

---

## 局限性

- LLM 的视觉对比是**主观的** — 报告附截图路径，用户应复核
- 需要 App 能运行且可导航到各页面（需要测试账号/数据）
- 移动端截图依赖 Maestro 或用户手动截图
- 不覆盖交互行为（只能看静态截图，不能验证点击/滑动）

---

## 加载核心协议

> 核心协议详见 ${CLAUDE_PLUGIN_ROOT}/skills/code-replicate-core.md
