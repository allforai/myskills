# 计划：Stitch 高质量 UI 嵌入 product-design 工作流

## Context

当前 `ui-design` 阶段（Phase 6）产出仅有文字规格（`ui-design-spec.md`）和基础 HTML 卡片预览，缺乏真实视觉稿。Google Stitch 可从文字描述生成高质量视觉 UI + React 代码，且已有 MCP Server 接口。

目标：
1. 在产品概念阶段让用户选择是否接入 Stitch
2. 独立脚本 `gen_ui_stitch.py` 构建 Stitch-ready prompts（Option B）
3. `ui-design.md` 技能在 Phase 6 尾部执行 Stitch 调用（MCP 工具）

---

## 架构说明

```
product-concept Phase (Step 3.5)
  └─ Q4: 是否生成高质量视觉 UI？
     └─ 写入 pipeline_preferences.stitch_ui: true | false
           ↓
Phase 6: ui-design
  Step 1-5: 现有流程（spec.md + HTML cards）
  Step 5.5: [NEW] Stitch 视觉生成（stitch_ui=true 时）
    ├─ Python: gen_ui_stitch.py → stitch-prompts.json（prompt 构建）
    └─ Claude: 调用 Stitch MCP 工具 → ui-design/stitch/（视觉生成）
```

**Python 脚本负责**：数据准备、prompt 构建、文件输出
**Claude 技能负责**：调用 Stitch MCP 工具（Python 无法直接调用 MCP）

---

## 改动清单

### 1. `docs/schemas/product-concept-schemas.md`
**位置**：`pipeline_preferences` 对象（当前第 52-56 行）
**改动**：新增 `stitch_ui` 字段

```json
"pipeline_preferences": {
  "ui_style": "material-design-3 | ...",
  "competitors": [...],
  "scope_strategy": "aggressive | balanced | conservative | undecided",
  "stitch_ui": true | false   // NEW：是否在 ui-design 阶段调用 Stitch 生成视觉稿
}
```

---

### 2. `skills/product-concept.md`
**位置**：Step 3.5 Pipeline Preferences（Q3 之后，约第 560 行）
**改动**：追加 Q4，写入 `stitch_ui`

```markdown
**Q4（可选）高质量 UI 视觉稿**

检测 STITCH_API_KEY 环境变量：
- 已配置 → 提示「Stitch 已就绪」，直接询问是否启用
- 未配置 → 提示「需先配置 Stitch API Key（免费，stitch.withgoogle.com/settings），
  现在跳过，后续可手动运行 gen_ui_stitch.py」

AskUserQuestion:
  question: "是否在 UI 设计阶段使用 Stitch 生成高质量视觉稿？"
  options:
    - label: "是，启用 Stitch（推荐，需 API Key）"
      description: "自动为 IC001 核心界面 + 高频界面生成视觉 UI，可导出 Figma / React 代码"
    - label: "否，使用文字规格"
      description: "生成 ui-design-spec.md + HTML 预览，不调用 Stitch"

写入：pipeline_preferences.stitch_ui = true | false
```

---

### 3. `scripts/gen_ui_stitch.py`（新建）
**职责**：prompt 构建器，不调用 Stitch（Python 无法调 MCP）

```
输入：
  - .allforai/screen-map/screen-map.json
  - .allforai/ui-design/ui-design-spec.md（style tokens）
  - .allforai/product-concept/product-concept.json（mission + 风格）

屏幕优先级选择：
  P0（必跑）：IC001 关键屏 — S010/S020/S021/S022/S025（5个）
  P1（高频）：购物链路核心 — S031/S040/S041/S042/S050（5个）
  默认 10 个，可通过 --screens S010,S025 覆盖

每个屏幕的 prompt 结构：
  - App context（品牌/市场/风格 token）
  - Screen purpose + primary action
  - Actions（主操作 Filled Button / 次操作 Outlined Button）
  - States（empty/loading/error/success 处理）
  - Special notes（IC001 标记、日文市场提示）

输出：
  .allforai/ui-design/stitch-prompts.json
  格式：[{ screen_id, screen_name, priority, prompt, style_hint, notes }]

运行方式：
  python3 gen_ui_stitch.py <BASE> [--screens S010,S025] [--mode auto]

检查 pipeline_preferences.stitch_ui：
  false → 仍生成 stitch-prompts.json（供手动使用），不阻塞
  true  → 正常运行，后续 Claude 技能读取并调 Stitch MCP
```

---

### 4. `skills/ui-design.md`
**位置**：Step 5（HTML 预览）之后，design-decisions 记录之前
**改动**：新增 Step 5.5

```markdown
### Step 5.5：Stitch 视觉生成（条件执行）

**跳过条件**：`pipeline_preferences.stitch_ui ≠ true`

**执行流程**：

1. 运行 prompt 构建脚本：
   ```
   python3 <SCRIPTS>/gen_ui_stitch.py <BASE> --mode auto
   ```
   输出：`ui-design/stitch-prompts.json`（10 个屏幕的结构化 prompt）

2. 检测 Stitch 可用性（双通道）：
   - MCP 工具：`mcp__plugin_product-design_stitch__*` 是否可用
   - 环境变量：`STITCH_API_KEY` 是否设置

3a. **可用** → 对每个 prompt 调用 Stitch MCP 工具：
   - 优先 P0（5个 IC001 界面），再 P1（5个高频界面）
   - 结果写入 `ui-design/stitch/S{id}-{name}.{ext}`
   - 记录 Stitch 链接 / React 代码路径到 `ui-design/stitch-index.json`

3b. **不可用** → 仅输出 prompts，展示手动使用说明：
   ```
   Stitch 未配置，已生成 stitch-prompts.json。
   手动使用：访问 stitch.withgoogle.com，粘贴各屏幕 prompt 生成视觉稿。
   配置方式：获取 API Key → 设置 STITCH_API_KEY 环境变量 → 重新运行 ui-design
   ```

**输出文件**：
  - `ui-design/stitch-prompts.json`（始终生成）
  - `ui-design/stitch/`（Stitch 可用时）
  - `ui-design/stitch-index.json`（Stitch 可用时，记录链接）
```

---

### 5. `.mcp.json`
**位置**：`product-design-skill/.mcp.json`
**改动**：追加 stitch server（条件可选，建议用 conditional 注释说明）

```json
{
  "mcpServers": {
    "openrouter": { ... },
    "stitch": {
      "command": "npx",
      "args": ["-y", "@_davideast/stitch-mcp"],
      "env": {
        "STITCH_API_KEY": "${STITCH_API_KEY}"
      }
    }
  }
}
```

> 注：STITCH_API_KEY 未设置时 MCP Server 启动会静默失败，不影响主流程。

---

## 非阻断原则

| 条件 | 行为 |
|------|------|
| `stitch_ui=false` | 跳过 Step 5.5，正常完成 |
| `stitch_ui=true` + API Key 未配置 | 输出 stitch-prompts.json，提示手动使用 |
| `stitch_ui=true` + MCP 调用失败 | 记录 warning，跳过失败项，继续 |
| Stitch 生成部分失败 | 成功的写入，失败的跳过，不回滚 |

---

## 优先屏幕（10个，控制配额）

| 优先级 | 屏幕 | 说明 |
|--------|------|------|
| P0 | S010 买家首页 | IC001 入口 |
| P0 | S020 宠物列表页 | IC001 档案管理入口 |
| P0 | S021 创建宠物档案页 | IC001 核心表单 |
| P0 | S022 宠物档案详情/编辑页 | IC001 核心 |
| P0 | S025 处方推荐列表页 | IC001 差异化核心 |
| P1 | S031 商品详情页 | 最高频转化界面 |
| P1 | S040 购物车 | 高频 |
| P1 | S041 结算页 | 高风险高频 |
| P1 | S042 支付页 | 高风险高频 |
| P1 | S050 订单列表 | 高频 |

---

## 关键文件路径

| 文件 | 状态 | 说明 |
|------|------|------|
| `skills/product-concept.md` | 修改 | 第 560 行附近加 Q4 |
| `docs/schemas/product-concept-schemas.md` | 修改 | 第 52-56 行加 stitch_ui |
| `scripts/gen_ui_stitch.py` | 新建 | ~120 行，prompt 构建器 |
| `skills/ui-design.md` | 修改 | Step 5 后加 Step 5.5（~50行） |
| `.mcp.json` | 修改 | 追加 stitch server（6行） |

---

## 可复用的现有工具

- `_common.py: xv_available()` — 参考其双通道检测模式
- `_common.py: parse_args()` — 脚本参数解析（含 --mode auto）
- `_common.py: load_screen_map()` — 读取 screen-map.json
- `_common.py: load_product_concept()` — 读取 product-concept.json
- `_common.py: write_json()` + `ensure_dir()` — 文件输出
- `_common.py: append_pipeline_decision()` — 决策日志
- `xv_prompts.py` — 参考 prompt 构建模式

---

## 计划文档输出

本计划文件同步保存到：
```
/home/dv/myskills/product-design-skill/docs/stitch-integration-plan.md
```

---

## 验证方式

1. 运行 `python3 gen_ui_stitch.py <BASE>` → 确认 `stitch-prompts.json` 生成，10 个屏幕
2. 手动设置 `STITCH_API_KEY` → 重跑，确认 Step 5.5 分支切换
3. 运行 full product-concept → 确认 Q4 出现在 Step 3.5 最后
4. 读 `product-concept.json` → 确认 `pipeline_preferences.stitch_ui` 字段写入
5. 跑 full ui-design → 确认 Step 5.5 在 `stitch_ui=true` 时触发，`false` 时跳过
