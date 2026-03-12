# 技能通用增强协议

> 本文档定义三项增强协议的**通用框架**。各 skill 仅需引用本文件并补充自身定制内容。

---

## 一、动态趋势补充（WebSearch）

执行任何技能时，除经典理论外，建议补充近 12–24 个月的实践文章与案例：

- **来源优先级**：官方规范/权威研究 > 一线产品团队实践 > 社区文章
- **决策留痕**：对关键结论记录 `ADOPT|REJECT|DEFER` 与理由，避免"只收集不决策"
- **来源写入**：`.allforai/product-design/trend-sources.json`（跨阶段共用）

各技能提供自身领域的搜索关键词示例（见各 skill 文件）。

---

## 二、外部能力探测协议

> 统一各技能对外部工具/服务的探测、使用和降级模式。避免各技能各写各的降级逻辑。

### 能力注册表

| 能力 ID | 探测方式 | 使用插件 | 降级策略 |
|---------|---------|---------|---------|
| `playwright` | 检查 `mcp__playwright__browser_navigate` 或 `mcp__plugin_playwright_playwright__browser_navigate` 工具可用性（任一可用即就绪） | demo-forge, dev-forge, deadhunt | 无降级 — 提示用户安装 |
| `openrouter_mcp` | 检查 `mcp__plugin_product-design_ai-gateway__ask_model` 工具可用性 | product-design, dev-forge | 跳过 MCP XV，脚本 XV 仍可用 |
| `openrouter_script` | `_resolve_api_key("OPENROUTER_API_KEY")`：环境变量 → `.mcp.json` env/\_\_keys | product-design (预置脚本) | 静默跳过 XV |
| `brave_search_mcp` | 检查 `mcp__plugin_product-design_ai-gateway__brave_web_search` 工具可用性 | demo-forge | 跳过 Brave MCP，脚本仍可用 |
| `brave_search_script` | `_resolve_api_key("BRAVE_API_KEY")`：环境变量 → `.mcp.json` env/\_\_keys | demo-forge (预置脚本) | Brave → WebSearch → AI 生成 |
| `google_ai_mcp` | 检查 `mcp__plugin_product-design_ai-gateway__generate_image` 工具可用性 | demo-forge | 跳过 MCP 生图，脚本仍可用 |
| `google_ai_script` | `_resolve_api_key("GOOGLE_API_KEY")`：环境变量 → `.mcp.json` env/\_\_keys | demo-forge (预置脚本) | Imagen 4 → GPT-5 Image → FLUX 2 Pro → 跳过 |
| `fal_ai_mcp` | 检查 `mcp__plugin_product-design_ai-gateway__flux_generate_image` 工具可用性 | demo-forge | 跳过 fal.ai MCP 生图/生视频 |
| `fal_ai_script` | `_resolve_api_key("FAL_KEY")`：环境变量 → `.mcp.json` env/\_\_keys | demo-forge (预置脚本) | FLUX 2 Pro（生图）+ Kling（生视频） |
| `stitch_ui` | 检查 `mcp__plugin_product-design_stitch__create_project` 工具 | product-design | 跳过视觉稿，使用文字规格 |
| `websearch` | 内置工具，始终可用 | product-design, demo-forge | 无需降级 |

### 统一探测模式

每个技能在执行前，对其依赖的外部能力执行探测。模式统一为三级：

```
探测 → 可用：正常使用
     → 不可用 + 有降级链：走降级链，输出一行提示
     → 不可用 + 无降级链 + 重要性=必需：触发交互式安装引导
     → 不可用 + 无降级链 + 重要性=可选：跳过，输出一行提示
```

**提示格式统一**：

```
{step_name} ⊘ {能力名} 不可用，{降级动作}
```

示例：
- `M2 搜索采集 ⊘ Brave Search 不可用，降级到 WebSearch`
- `XV 交叉验证 ⊘ OpenRouter 不可用，跳过交叉验证`
- `V1 登录验证 ⊘ Playwright 不可用` → 触发安装引导

### 交互式安装引导

当「重要性=必需」的能力未就绪时，用 AskUserQuestion 提供一键安装选项。**不静默安装，始终先问。**

#### 安装注册表

| 能力 ID | 安装命令 | 安装后追加步骤 | 需重启 Claude Code |
|---------|---------|--------------|-------------------|
| `playwright` | `claude mcp add -s user playwright -- npx -y @playwright/mcp@latest` | 无追加步骤（浏览器按需自动下载） | 是 |
| `openrouter_mcp` | `cd {PLUGIN_ROOT}/mcp-ai-gateway && npm install && npm run build` | 需配置 `OPENROUTER_API_KEY`（运行 `/setup`） | 是 |
| `brave_search_mcp` | ai-gateway 已内置，仅需配置 `BRAVE_API_KEY`（运行 `/setup`） | Key 写入 `.mcp.json` ai-gateway env | 是 |
| `google_ai_mcp` | ai-gateway 已内置，仅需配置 `GOOGLE_API_KEY`（运行 `/setup`） | Key 写入 `.mcp.json` ai-gateway env | 是 |
| `stitch_ui` | `claude mcp add -s user stitch -- npx -y @_davideast/stitch-mcp proxy` | 首次需 OAuth: `python3 {PLUGIN_ROOT}/scripts/stitch_oauth.py` | 是 |

#### 引导流程（编排命令的 Phase 0 使用）

当 Phase 0 外部能力快检发现「重要性=必需」的能力未就绪时：

```
1. AskUserQuestion:
   「{能力名} 未就绪，后续 {phase_name} 需要此工具。是否立即安装？」
   选项:
     1. 是，帮我安装
     2. 跳过，我稍后自行安装
     3. 查看安装详情

2. 选择「是，帮我安装」→ 执行安装命令（Bash）→ 安装后追加步骤 → 报告结果
   - 成功 → 提示「安装成功。需重启 Claude Code 生效。现在重启还是继续当前流程？」
   - 失败 → 展示错误信息 + 手动安装命令，继续流程（降级或跳过该阶段）

3. 选择「跳过」→ 记录跳过，按降级策略处理
   - 有降级链 → 走降级链
   - 无降级链 → 跳过依赖此能力的阶段，在最终报告中标注

4. 选择「查看安装详情」→ 展示完整安装步骤 + 前置要求 → 回到步骤 1
```

#### 单技能内的探测（非编排命令）

单独运行技能时（如直接 `/demo-verify`），不做完整引导，只输出一行提示 + 安装命令：

```
⊘ Playwright 不可用。安装: claude mcp add -s user playwright -- npx -y @playwright/mcp@latest（安装后需重启 Claude Code）
```

### 技能声明规范

各技能在「增强协议」或「前提」节中，用以下格式声明外部能力依赖：

```markdown
**外部能力依赖**：

| 能力 | 重要性 | 降级行为 |
|------|--------|---------|
| playwright | 必需 | 阻塞，提示安装 |
| openrouter_mcp | 可选 | 跳过 XV |
```

### 全局状态检测

运行 `/setup check` 可一次性查看所有外部能力状态。

---

## 三、多级上下文协议（Push-Pull Context Protocol）

### 问题

流水线中每个阶段只读直接上游的产物，导致信息逐层衰减：

```
concept → map → experience-map → ui-design → dev-forge
 100%     70%      50%             30%          10%
```

概念阶段的关键决策（治理风格、操作频度、系统边界）经过 4 层转换后几乎消失。LLM 在最后一层只能做机械翻译，丧失了业务判断力。

### 原则

**推拉结合：概念蒸馏基线推送到所有阶段 + 每个阶段按需拉取关心的原始数据。**

任何阶段的 LLM 上下文 = 概念蒸馏基线（推） + 直接上游产物 + 按需拉取的跨级原始字段（拉）。

---

### 3.A 推（Push）：概念蒸馏基线

#### 什么是概念蒸馏基线

概念阶段完成后，自动从全量概念产物中提取一份紧凑的 **concept-baseline.json**，包含所有下游阶段都需要的核心决策。这份基线：

- **自动生成**：concept 阶段完成后由编排器生成，不需要用户干预
- **只读**：下游阶段只读不改，修改概念需要回到 concept 阶段
- **紧凑**：控制在 2KB 以内，每个阶段都能无负担加载
- **全量推送**：每个下游阶段的前置检查都自动加载此文件

#### 基线内容（固定 schema）

```json
{
  "_meta": {
    "generated_from": "product-concept phase",
    "generated_at": "ISO timestamp",
    "source_files": ["product-concept.json", "role-value-map.json", "product-mechanisms.json"]
  },
  "mission": "一句话产品定位",
  "target_market": "目标市场简述",
  "roles": [
    {
      "id": "R1",
      "name": "买家",
      "app": "website",
      "client_type": "mobile-ios",
      "screen_granularity": "single_task_focus",
      "high_frequency_tasks": ["浏览商品", "下单", "查看物流"],
      "design_principle": "单任务聚焦，减少页面跳转"
    }
  ],
  "governance_styles": [
    {
      "flow_domain": "商品上架",
      "style": "auto_review",
      "system_boundary": {
        "in_scope": ["商品信息填写"],
        "external": ["实名认证"]
      }
    }
  ],
  "errc_highlights": {
    "must_have": ["核心功能列表"],
    "differentiators": ["差异化功能列表"],
    "eliminate": ["明确排除的功能"]
  },
  "pipeline_preferences": {
    "auto_mode": true,
    "ui_style": "..."
  }
}
```

#### 生成时机与位置

- **生成时机**：Phase 1 concept 完成（verify loop 通过后），编排器自动执行
- **存储位置**：`.allforai/product-concept/concept-baseline.json`
- **生成方式**：LLM 从 `product-concept.json` + `role-value-map.json` + `product-mechanisms.json` 提取上述 schema 字段
- **更新策略**：concept 重跑时重新生成；下游阶段不修改

#### 下游加载方式

每个 skill 的「前置检查」中，第一步始终是：

```
概念蒸馏基线（自动加载）：
  读取 .allforai/product-concept/concept-baseline.json
  → 作为 LLM 上下文的背景知识，指导本阶段所有生成和验收决策
  → 文件不存在 → WARNING，不阻塞（兼容旧产物）
```

---

### 3.B 拉（Pull）：按需跨级原始数据

#### 何时需要拉取

概念蒸馏基线是紧凑摘要，覆盖通用决策。但某些阶段需要**原始数据的细节**来做精确判断——这时用拉取。

例如：
- experience-map 需要拉取 `governance_styles[].downstream_implications` 来决定某个屏幕是否需要审核队列组件——基线只有 `style: "auto_review"`，不够细
- use-case 需要拉取 `roles[].jobs[].pain_relievers` 来生成 sad path 用例——基线只有 `high_frequency_tasks`
- dev-forge 需要拉取 `roles[].operation_profile.density` 来决定缓存策略——基线只有 `screen_granularity`

#### 声明格式

每个 skill 的「前置检查」中，在概念蒸馏基线之后，声明需要拉取的跨级原始字段：

```
跨级原始数据拉取（按需）：
  product-concept.json:
    - roles[].jobs[].pain_relievers          → 生成 sad path 用例的来源
  product-mechanisms.json:
    - governance_styles[].downstream_implications → 决定是否生成审核队列组件
    - governance_styles[].rationale              → 验收时判断治理设计是否合理
  role-value-map.json:
    - roles[].operation_profile.density          → 决定缓存策略和预加载行为
```

#### 拉取原则

- **只拉取基线未覆盖的细节**：基线已有的字段不重复拉取
- **声明用途**：每个拉取字段必须说明本阶段如何使用，防止"全量拉取"
- **控制粒度**：用 JSONPath 精确到字段，不加载整个文件

---

### 3.C 推拉结合的完整上下文模型

```
任何阶段的 LLM 上下文:

┌─────────────────────────────────────────────┐
│  概念蒸馏基线（推）                            │  ← 自动加载，~2KB
│  concept-baseline.json                       │
├─────────────────────────────────────────────┤
│  直接上游产物                                 │  ← 常规输入
│  如 experience-map 读取 task-inventory        │
├─────────────────────────────────────────────┤
│  跨级原始数据（拉）                            │  ← 按需声明，只拉需要的字段
│  如 governance_styles[].downstream_implications│
└─────────────────────────────────────────────┘
        ↓
   LLM 生成 + 验收（4D/6V/闭环）
```

**token 预算参考**：
- 概念蒸馏基线：~500-800 tokens（固定开销，每个阶段都有）
- 跨级拉取：0-2000 tokens（按需，大多数阶段只拉 2-5 个字段）
- 直接上游：视产物大小（这是当前已有的开销）

### 3.D 常用拉取字段参考

以下字段在多个下游阶段被频繁使用。**基线已包含的字段标注 [B]**，其余为拉取候选：

| 字段 | 来源 | 基线? | 下游使用方 | 用途 |
|------|------|:-----:|-----------|------|
| `mission` | product-concept.json | [B] | 所有阶段 | 产品定位基准，防止功能偏离 |
| `roles[].app` | role-value-map.json | [B] | 所有阶段 | 代码/屏幕归属哪个子项目 |
| `roles[].screen_granularity` | role-value-map.json | [B] | experience-map, ui-design | 屏幕拆分策略 |
| `governance_styles[].style` | product-mechanisms.json | [B] | experience-map, use-case, dev-forge | 审核屏幕/用例/代码的有无 |
| `governance_styles[].system_boundary` | product-mechanisms.json | [B] | experience-map, use-case, dev-forge | 哪些功能只写集成接口 |
| `pipeline_preferences` | product-concept.json | [B] | 所有阶段 | 自动模式、UI 风格 |
| `errc_highlights` | product-concept.json | [B] | 所有阶段 | 功能优先级基准 |
| `governance_styles[].downstream_implications` | product-mechanisms.json | 拉取 | experience-map, dev-forge | 决定具体组件需求 |
| `governance_styles[].rationale` | product-mechanisms.json | 拉取 | use-case | 验收治理设计合理性 |
| `roles[].jobs[].pain_relievers` | product-concept.json | 拉取 | use-case | 生成 sad path 用例 |
| `roles[].operation_profile.density` | role-value-map.json | 拉取 | ui-design, dev-forge | 缓存策略、预加载行为 |
| `roles[].operation_profile.high_frequency_tasks` | role-value-map.json | [B] | experience-map | 前置高频操作入口 |

### 3.E 阶段转换思维（Phase Transition Mindset）

产品设计和开发阶段对闭环的关注点根本不同：

```
产品设计阶段（从无到有）          开发阶段（补缺补漏）
────────────────────          ────────────────────
关注正空间：该有什么？            关注负空间：什么会出错？
闭环粒度：识别+标记              闭环粒度：100% 实现
异常处理：列出主要场景            异常处理：穷举所有路径
状态覆盖：标注四态               状态覆盖：每个状态都有代码
```

**产品设计阶段的闭环是「发现级」**：识别出闭环应该存在（pain↔reliever、happy↔sad path、action↔feedback），标记需要什么。产品设计不可能穷举所有异常——它的职责是把正常流程和关键异常场景想清楚。

**开发阶段的闭环是「实现级」**：100% 补全所有闭环。产品设计只标了 3 个 exceptions，开发阶段需要从这 3 个推导出 15 个（网络超时、并发冲突、权限变更、数据不一致、外部服务降级……）。

**dev-forge 的职责转换**：design-to-spec 不应只「翻译」产品设计的异常列表，而应**主动推导负空间**——以产品设计的正常流程为输入，系统性地推导所有可能的异常路径、边界条件、竞态条件、降级策略。

**闭环严格度对照**：

| 闭环类型 | 产品设计（发现级） | 开发（实现级） |
|---------|-----------------|-------------|
| 配置闭环 | 标注「需要配置」 | 配置表/端点 + 默认值 + 热更新机制 |
| 监控闭环 | 标注「需要观测」 | 埋点事件 + 告警规则 + 仪表盘 |
| 异常闭环 | 列出主要异常场景 | 穷举异常 + 重试策略 + 降级方案 + 用户提示 |
| 生命周期闭环 | 标注「有创建需有清理」 | TTL + 定时任务 + 归档策略 + 级联删除 |
| 映射闭环 | 标注 A↔B 关系 | 外键/索引 + 一致性校验 + 孤儿清理 |
| 导航闭环 | 标注可达性 | 路由守卫 + 404 处理 + 回退策略 + 深链接 |

### 3.F 与上游基线验收的关系

上游基线验收（§4.6）检查的是「下游产物是否忠实反映上游意图」。推拉协议是其**数据基础**——不加载上游数据就无法做基线验收。三者配合：

```
推（始终）：每个阶段自动获得概念蒸馏基线 → 验收时用于全局一致性检查
拉（按需）：加载概念层的具体字段 → 验收时用于精确判断
验收（输出时）：检查生成的屏幕/代码是否符合基线 + 拉取的原始数据
```

---

## 四、统一验收方法论

每个生成阶段的产出质量由四个相互独立的思想工具保障。它们不是可选增强，而是所有阶段的验收标准。

### 4.1 四维信息卡（4D）

每个关键产出对象必须经受四层追问：

| 维度 | 追问 | 作用 |
|------|------|------|
| **D1 结论** | 结论本身是否正确、完整、合逻辑？ | 验证「是什么」 |
| **D2 证据** | 结论的依据是什么？可追溯吗？ | 验证「凭什么」 |
| **D3 约束** | 有哪些前提条件和限制？遗漏了什么？ | 验证「边界在哪」 |
| **D4 决策** | 为什么做这个选择而非其他？取舍是什么？ | 验证「为什么」 |

### 4.2 六视角矩阵（6V）

每个关键产出对象必须从六个独立视角审视，防止单一视角盲区：

| 视角 | 关注点 |
|------|--------|
| **user** | 用户能完成目标吗？体验如何？ |
| **business** | 支撑商业目标吗？影响营收/转化吗？ |
| **tech** | 技术可实现吗？有不可控依赖吗？ |
| **ux** | 交互一致吗？学习成本低吗？ |
| **data** | 可观测吗？能采集到验证假设的数据吗？ |
| **risk** | 安全/合规/隐私风险？高风险操作有保护吗？ |

### 4.3 闭环思维

**原理**：产品中不存在孤立的功能。每个功能都存在于大大小小的循环中。验收时对每个产出追问：这个循环完整吗？

**通用闭环类型**（适用于所有阶段）：

| 闭环类型 | 追问模式 |
|---------|---------|
| **配置闭环** | 这个东西靠什么运行？谁来配置它？ |
| **监控闭环** | 运行得好不好？谁来看效果？ |
| **异常闭环** | 失败了怎么办？谁来处理？恢复路径是什么？ |
| **生命周期闭环** | 创建了最终去哪？有过期/清理/归档吗？ |
| **映射闭环** | A 和 B 是一对的，有 A 必须有 B（pain↔reliever, happy↔sad path, action↔feedback） |
| **导航闭环** | 进得去能出来吗？有没有死胡同？ |

追问模式是统一的，但**闭环的验收严格度因阶段而异**——见下方 §4.4。

### 4.4 验证循环（Loop）

**原理**：生成一次不可能完美。验收不是一次性检查，而是循环修正直到干净。

**统一循环模式**：

```
脚本收集上下文 + 审查问题 → stdout JSON
    ↓
Claude Code 用 4D + 6V + 闭环思维审查
    ↓
发现问题 → 修改源文件 → 重新运行脚本 → 再审
    ↓
没有问题 → 通过，进入下一阶段
```

**执行入口**：`python3 verify_review.py <BASE> --phase <phase> [--xv]`

**XV 增强**（可选）：`--xv` 标志触发跨模型交叉验证，将产出摘要发送给第二个 AI 模型（通过 OpenRouter API），获取独立意见。XV 是 Loop 的增强手段，不是独立阶段。

#### 产品设计 vs 开发：同一个 Loop，不同的使命

4D/6V/闭环/XV 是统一的思想工具，但在产品设计和开发阶段承担**根本不同的使命**：

```
产品设计阶段的 verify loop             开发阶段的 verify loop (FVL)
─────────────────────────           ─────────────────────────
使命：从无到有，发现正空间              使命：补缺补漏，补全负空间
─────────────────────────           ─────────────────────────
4D 追问侧重：                        4D 追问侧重：
  D1 正常流程是否正确？                  D1 异常路径是否穷举？
  D2 有用户/市场证据吗？                 D2 有技术方案支撑吗？
  D3 产品边界在哪？                     D3 工程边界条件覆盖了吗？
  D4 为什么选这个方案？                  D4 为什么选这个降级策略？

6V 审查侧重：                        6V 审查侧重：
  user: 能完成目标吗？                  user: 出错时知道怎么办吗？
  business: 支撑商业目标吗？             business: 异常不会造成资损吗？
  tech: 技术可行吗？                    tech: 并发/超时/降级方案？
  ux: 交互一致吗？                     ux: 错误提示友好吗？
  data: 能采集数据吗？                  data: 异常有监控告警吗？
  risk: 有保护吗？                     risk: 攻击面覆盖了吗？

闭环严格度：                         闭环严格度：
  发现级 — 标记闭环应该存在              实现级 — 100% 代码覆盖
  识别 3 个主要异常                     推导 15 个异常 + 全部有处理
  标注「需要配置」                      配置表 + 默认值 + 热更新
  标注「需要观测」                      埋点 + 告警 + 仪表盘
```

**关键原则**：产品设计阶段不可能也不应该穷举所有异常——它的职责是把正常流程和关键场景想清楚。开发阶段拿到产品设计的正常流程后，必须**主动推导负空间**（异常路径、边界条件、竞态、降级），达到 100% 闭环。产品设计标记的 exceptions 是线索，不是完整清单。

### 4.5 四者关系

```
Loop（循环）是执行框架 —— 驱动「生成→审查→修正」的迭代
  ├── 4D（四维）是审查深度 —— 对每个对象追问四层
  ├── 6V（六视角）是审查广度 —— 从六个角度看同一个对象
  └── 闭环是审查完整性 —— 检查循环是否断裂
      └── XV（交叉验证）是审查独立性 —— 用另一个模型交叉检验
```

产品设计的 Loop 关注「是否发现了」，开发的 Loop 关注「是否实现了」。同一套工具，不同的验收标准。

四者缺一不可：没有 Loop，审查是一次性的；没有 4D，审查停留在表面；没有 6V，审查有盲区；没有闭环，审查发现不了断裂。

### 4.6 上游基线验收（Upstream Baseline Validation）

**原理**：上游产物不是「生成完就丢掉」的中间文件，而是下游验收的基线（baseline）。每个阶段的产出同时承担两个角色：

```
阶段 N 的产出 = 阶段 N+1 的输入 + 阶段 N+1 的验收基线
```

**验收方式**：下游生成产物后，LLM 同时加载上游产物和下游产物，**以 LLM 判断力（而非机械规则匹配）**审查下游是否忠实反映了上游意图。这与 Loop 中的其他验收维度（4D/6V/闭环）一样，都是 LLM 驱动的语义判断。

**上游→下游对照链**：

| 上游产物 | 下游产物 | LLM 审查视角 |
|---------|---------|-------------|
| product-concept → roles/mission | product-map → role-profiles/tasks | 概念中的角色意图是否在地图中忠实体现？任务是否回应了 mission？ |
| product-map → business-flows | journey-emotion → journey_lines | 每条业务流的语义是否在旅程线的情绪弧线中体现？异常分支有对应情绪吗？ |
| journey-emotion → emotion_nodes | experience-map → screens | 情绪意图（design_hint）是否在界面设计中落地？高风险节点有保护设计吗？ |
| product-map → task-inventory | experience-map → screens.tasks | 任务意图是否在界面中有对应的交互入口？ |
| experience-map → screens | ui-design → HTML previews | 界面结构意图是否在视觉设计中保持？ |
| experience-map → operation_lines | interaction-gate → lines | 操作线的体验设计意图是否在可用性评分中被考量？ |
| task-inventory → tasks | use-case → use_cases | 任务的业务语义是否在用例中完整覆盖？ |
| task-inventory → tasks | feature-gap → gaps | 缺口分析是否基于任务清单的完整理解？ |

**落地方式**：每个 skill 的验收 Loop 中，LLM 加载上游产物作为审查上下文，在已有的 4D/6V/闭环审查中自然融入基线对照。基线验收不通过 = LLM 修正后重新验收（同 Loop 中其他不通过项）。

**核心原则**：上游产物不是「生成完就丢掉」的中间文件，而是下游验收的活基线。上游质量越高（字段越具体、意图越清晰），下游验收越精准。反过来，如果上游产出含糊（如情绪全是 neutral），基线验收就失去了判断依据。

**与闭环思维的关系**：上游基线验收是映射闭环的跨阶段扩展。映射闭环检查同一阶段内的 A↔B 对应关系，基线验收检查跨阶段的 上游A → 下游B 对应关系。

---

## 四、XV 跨模型交叉验证（实现细节）

XV 是统一验收方法论中 Loop 的可选增强。实现细节：

- **自动检测**：`_resolve_api_key("OPENROUTER_API_KEY")` 从环境变量读取
- **直连 API**：`urllib.request` 直连 `https://openrouter.ai/api/v1/chat/completions`，task→model 路由硬编码于 `_common.py`
- **自动采纳**：高严重度发现自动修正数据，不问用户
- **结果写入**：写入产出的 `cross_model_review` 字段
- **API Key 缺失**：静默跳过（向后兼容）
- **API Key 存在但调用失败**：抛异常终止（不静默吞错）
- **429 限流**：sleep 3s → 重试 1 次 → 失败则抛异常

各技能定义自身的验证点、task_type、发送内容和写入字段（见各 skill 文件）。
