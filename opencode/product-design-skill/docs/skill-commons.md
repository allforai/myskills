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
| `playwright` | 检查 `mcp__playwright__browser_navigate` 或 `mcp__playwright__browser_navigate` 工具可用性（任一可用即就绪） | demo-forge, dev-forge, deadhunt | 无降级 — 提示用户安装 |
| `openrouter_mcp` | 检查 `mcp__openrouter__ask_model` 工具可用性 | product-design, dev-forge | 跳过 MCP XV，脚本 XV 仍可用 |
| `openrouter_script` | `_resolve_api_key("OPENROUTER_API_KEY")`：环境变量 → `.mcp.json` env/\_\_keys | product-design (预置脚本) | 静默跳过 XV |
| `brave_search_mcp` | 检查 `mcp__openrouter__brave_web_search` 工具可用性 | demo-forge | 跳过 Brave MCP，脚本仍可用 |
| `brave_search_script` | `_resolve_api_key("BRAVE_API_KEY")`：环境变量 → `.mcp.json` env/\_\_keys | demo-forge (预置脚本) | Brave → WebSearch → AI 生成 |
| `google_ai_mcp` | 检查 `mcp__openrouter__generate_image` 工具可用性 | demo-forge | 跳过 MCP 生图，脚本仍可用 |
| `google_ai_script` | `_resolve_api_key("GOOGLE_API_KEY")`：环境变量 → `.mcp.json` env/\_\_keys | demo-forge (预置脚本) | Imagen 4 → GPT-5 Image → FLUX 2 Pro → 跳过 |
| `fal_ai_mcp` | 检查 `mcp__openrouter__flux_generate_image` 工具可用性 | demo-forge | 跳过 fal.ai MCP 生图/生视频 |
| `fal_ai_script` | `_resolve_api_key("FAL_KEY")`：环境变量 → `.mcp.json` env/\_\_keys | demo-forge (预置脚本) | FLUX 2 Pro（生图）+ Kling（生视频） |
| `stitch_ui` | 检查 `mcp__stitch__create_project` 工具 | product-design | 跳过视觉稿，使用文字规格 |
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

当「重要性=必需」的能力未就绪时，用 向用户提问 提供一键安装选项。**不静默安装，始终先问。**

#### 安装注册表

| 能力 ID | 安装命令 | 安装后追加步骤 | 需重启 Claude Code |
|---------|---------|--------------|-------------------|
| `playwright` | `claude mcp add -s user playwright -- npx -y @playwright/mcp@latest` | 无追加步骤（浏览器按需自动下载） | 是 |
| `openrouter_mcp` | `cd ./mcp-ai-gateway && npm install && npm run build` | 需配置 `OPENROUTER_API_KEY`（运行 `/setup`） | 是 |
| `brave_search_mcp` | ai-gateway 已内置，仅需配置 `BRAVE_API_KEY`（运行 `/setup`） | Key 写入 `.mcp.json` ai-gateway env | 是 |
| `google_ai_mcp` | ai-gateway 已内置，仅需配置 `GOOGLE_API_KEY`（运行 `/setup`） | Key 写入 `.mcp.json` ai-gateway env | 是 |
| `stitch_ui` | `claude mcp add -s user stitch -- npx -y @_davideast/stitch-mcp proxy` | 首次需 OAuth: `python3 ../../shared/scripts/product-design/stitch_oauth.py` | 是 |

#### 引导流程（编排命令的 Phase 0 使用）

当 Phase 0 外部能力快检发现「重要性=必需」的能力未就绪时：

```
1. 向用户提问:
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
      "name": "角色名称",
      "app": "website",
      "client_type": "mobile-ios",
      "screen_granularity": "single_task_focus",
      "high_frequency_tasks": ["高频任务1", "高频任务2", "高频任务3"],
      "design_principle": "单任务聚焦，减少页面跳转"
    }
  ],
  "governance_styles": [
    {
      "flow_domain": "内容发布",
      "style": "auto_review",
      "system_boundary": {
        "in_scope": ["内容编辑与提交"],
        "external": ["身份认证"]
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

## 五、逆向补漏协议（Reverse Backfill Protocol）

### 问题

流水线是单向的：concept → map → experience-map → ... → code。下游发现上游漏掉的东西（如「忘记密码」），如果不回补上游，就会产生「设计孤儿」——有代码但没有屏幕设计、没有用例、没有 UI 规格。

### 原则

**下游是用来补上游的漏，不是用来开新战线的。**

- 上游漏了的支撑功能（如凭证恢复、操作撤销）→ **必须回补上游**，让设计体系完整
- 上游从未讨论过的全新领域（如"要不要加社交功能"）→ **不补，标记为 `unexplored_area`**（见 §六 不确定性追踪），留给产品设计阶段下次迭代
- 区分标准：**能从已有核心功能的闭环推导出来的 = 上游漏了 = 补；推导不出来的 = 新领域 = 不补**

### 回补机制

当 design-to-spec 阶段 1.5 发现 B 类缺失时，**直接回写上游产物**：

```
B 类发现（如「密码恢复」—— 从「登录」的能力级闭环推导出来）
  ↓
回补上游（补漏，不是开新战线）：
  1. task-inventory.json      ← 追加任务条目（标注 _backfill: true）
  2. experience-map.json      ← 追加屏幕条目（标注 _backfill: true）
  3. use-case-tree.json       ← 追加用例条目（标注 _backfill: true）
  ↓
正向生成（基于已回补的上游）：
  4. requirements + design + tasks（正常流程）
  ↓
记录：
  5. negative-space-supplement.json（留痕，记录发现了什么、为什么判定为漏而非新领域）
```

### 回补条目标记

所有回补的条目在原始文件中追加，使用 `_backfill` 标记：

```json
{
  "id": "T099",
  "name": "凭证恢复",
  "_backfill": {
    "source": "design-to-spec 1.5",
    "ns_ref": "NS-001",
    "derived_from": "T005-认证（能力级闭环：凭证丢失恢复）",
    "derivation_ring": 1,
    "backfilled_at": "ISO timestamp"
  },
  "...": "其余字段与正常条目 schema 相同"
}
```

### 回补 vs 新领域的判定

| 判定 | 条件 | 行为 |
|------|------|------|
| **回补** | 能从已有任务/实体的闭环推导出 | 直接回写上游 + 正向生成 spec |
| **新领域** | 推导不出，属于全新业务方向 | 不回写，记入 `_uncertainty.unexplored_areas` |

示例：
- 「密码恢复」← 从「认证」的凭证丢失闭环推导 → **回补**
- 「操作撤销」← 从「提交」的异常恢复闭环推导 → **回补**
- 「社交分享」← 没有任何任务能推导出来 → **新领域，不补**

### 回补收敛原则

补漏必须收敛，不能无限展开。三条收敛保障：

**1. 概念定边界（有限输入）**

概念阶段定义了有限的角色、任务、实体。所有推导都在这个有限集合上操作。概念没提到的 = 不存在的输入 = 不推导。

**2. 推导半径递减（几何衰减）**

```
核心任务（Ring 0）     → N 个任务
一阶推导（Ring 1）     → ~0.3N（直接闭环缺失，如 认证→凭证恢复）
二阶推导（Ring 2）     → ~0.1N（补漏项的闭环缺失，如 凭证恢复→通知不可达时的替代验证）
三阶推导（Ring 3）     → ~0.03N（趋近于零）
```

每个补漏项天然比它的父任务**更简单、更窄**。简单意味着更少的闭环需要检查，产出自然递减——几何级数天然收敛。

**3. 分层截止（阶段接力）**

```
产品设计阶段：只做 Ring 0 + Ring 1（发现级）
开发阶段：接力做 Ring 2+（实现级）
```

每个阶段有明确的截止环，不追更深层的推导。

**收敛判据**（满足任一即停止推导）：

| 判据 | 条件 | 含义 |
|------|------|------|
| 零产出 | 所有维度 × 所有任务 = 0 个新发现 | 推导枯竭 |
| 全降级 | 新发现全部属于二阶或更高阶 | 超出当前阶段职责 |
| 规模反转 | 某个「补漏」的规模 > 其父任务 | 不是漏，是新功能 |

**一句话**：补漏是往圆心收敛，不是往外扩张。概念是圆的边界，推导半径每层递减，阶段接力保证截止。

### 回补后的验证

回补条目写入上游文件后，后续的 FVL 阶段 2 正常审计这些条目——它们和原始条目接受完全相同的验证标准。design-audit 终审时，`_backfill` 条目在覆盖率统计中单独列出。

---

## 六、不确定性追踪协议（Uncertainty Tracking）

### 问题

流水线的每个产物看起来都是确定的——50 个任务、101 个屏幕、200 个用例。但实际上每个阶段都有**未验证的假设**和**未探索的领域**。流水线不区分「我确定」和「我猜的」，导致下游无法对低置信度区域加强审查。

### 原则

**每个阶段产出时，显式声明未验证假设和认知盲区。**

不追求消除不确定性（不可能），而是追求**让不确定性可见**。

### 产出格式

每个阶段的主产出 JSON 中，追加 `_uncertainty` 字段：

```json
{
  "_uncertainty": {
    "confidence": 0.75,
    "unverified_assumptions": [
      {
        "id": "UA-001",
        "assumption": "用户使用邮箱注册而非手机号",
        "impact": "如果错误，需要补手机验证流程",
        "verification_method": "上线后观察注册方式分布",
        "affects": ["S001-登录", "S002-注册", "T005-身份验证"]
      },
      {
        "id": "UA-002",
        "assumption": "用户能自行完成该操作",
        "impact": "如果错误，需要补平台辅助/代办功能",
        "verification_method": "上线后用户访谈",
        "affects": ["S045-操作管理", "T030-核心操作"]
      }
    ],
    "unexplored_areas": [
      {
        "id": "UE-001",
        "area": "国际化支持",
        "reason": "概念阶段未讨论，不确定是否在 scope 内",
        "potential_impact": "如果需要，影响核心业务全链路"
      }
    ],
    "low_confidence_items": [
      {
        "ref": "S067",
        "reason": "参考竞品推测，未经用户验证",
        "confidence": 0.4
      }
    ]
  }
}
```

### 各阶段的不确定性侧重

| 阶段 | 主要不确定性来源 | 典型假设 |
|------|---------------|---------|
| concept | 用户需求理解 | "用户最在意配送速度" |
| product-map | 功能完整性 | "50 个任务覆盖了所有业务场景" |
| experience-map | 交互设计 | "用户能理解这个导航结构" |
| use-case | 场景覆盖 | "这些 sad path 覆盖了主要异常" |
| design-to-spec | 技术方案 | "这个架构能支撑预期并发" |

### 下游消费

- **verify loop**：对 `low_confidence_items` 加权审查（低置信度条目优先审查）
- **design-to-spec**：对上游 `unverified_assumptions` 中 impact=高 的假设，在负空间推导时重点关注
- **event-schema**：将 `verification_method` 不为空的假设自动绑定到埋点事件，生成「假设验证仪表盘」
- **design-audit 终审**：汇总全流水线的 `_uncertainty`，输出「不确定性热力图」

### 与假设验证埋点的绑定

event-schema 生成时（design-to-spec Step 3.8），自动扫描全链路 `_uncertainty.unverified_assumptions`：

```
对每个 verification_method ≠ null 的假设：
  生成对应的埋点事件或分析查询
  标注 assumption_ref: "UA-001"
  在 event-schema.json 中追加 hypothesis_events 数组
```

上线后，这些埋点数据直接验证设计假设——**闭环从设计延伸到了生产环境**。

---

## 七、XV 跨模型交叉验证（实现细节）

XV 是统一验收方法论中 Loop 的可选增强。实现细节：

- **自动检测**：`_resolve_api_key("OPENROUTER_API_KEY")` 从环境变量读取
- **直连 API**：`urllib.request` 直连 `https://openrouter.ai/api/v1/chat/completions`，task→model 路由硬编码于 `_common.py`
- **自动采纳**：高严重度发现自动修正数据，不问用户
- **结果写入**：写入产出的 `cross_model_review` 字段
- **API Key 缺失**：静默跳过（向后兼容）
- **API Key 存在但调用失败**：抛异常终止（不静默吞错）
- **429 限流**：sleep 3s → 重试 1 次 → 失败则抛异常

各技能定义自身的验证点、task_type、发送内容和写入字段（见各 skill 文件）。

---

## 八、闭环输入审计（Closed-Loop Input Audit）

> 每次收集用户输入时，不只记录用户说了什么，还要检查用户**没说但应该说的**。

### 适用场景

任何 skill 在通过 向用户提问 或对话收集用户输入时——产品概念发现、代码复刻理解、技术决策、业务规则确认——都必须在记录用户回答后执行闭环审计。

### 审计方法

用户回答每个问题后，LLM 以该回答为输入，用四类闭环思维追问"还缺什么"：

| 闭环类型 | 追问 | 举例 |
|---------|------|------|
| **配置闭环** | 用户描述的功能靠什么运行？谁来配置它？ | 用户说"AI 自动回帖"→ 谁配置 AI 用哪个模型？模型挂了谁处理？ |
| **异常闭环** | 用户描述的正常路径，失败了怎么办？ | 用户说"付费升级"→ 支付失败怎么办？退款流程？到期续费失败？ |
| **生命周期闭环** | 用户描述的东西被创建后，最终去哪？ | 用户说"发帖讨论"→ 帖子讨论完了怎么收尾？过期帖子怎么处理？ |
| **角色闭环** | 用户描述了消费侧，生产侧呢？ | 用户说"用户发帖+AI回帖"→ 谁管理AI角色？谁审核内容？ |

### 执行原则

- **不问开放题**：发现缺失后生成选择题（延续 product-concept 的铁律）
- **不打断流程**：闭环审计在用户确认当前步骤后执行，发现缺失时在下一轮提问中补充，不回退当前步骤
- **缺失分级**：MUST（没有就无法运行）→ 立即补问；SHOULD（没有体验不完整）→ 记录，后续步骤再问；NICE（锦上添花）→ 记录不问
- **不过度追问**：每个用户回答最多追加 1-2 个闭环补充问题，避免"回答一个问题又冒出五个"的审讯感

### 收敛控制

闭环追问本身也会发散（每个回答又追出新问题）。必须收敛：

- **深度上限**：闭环追问最多 2 层（用户回答 → 追问 1 → 用户回答 → 追问 2 → 停）。第 3 层的缺失记录到决策日志，不再追问
- **SHOULD/NICE 延迟**：只有 MUST 级缺失立即追问。SHOULD 和 NICE 记录下来，在后续步骤（product-map/design-to-spec）中由 LLM 自动推导填充，不需要回头问用户
- **收敛判定**：如果用户连续 2 次回答都没有产生新的 MUST 级缺失 → 闭环审计完成，进入下一步
- **总量限制**：单个 Step 内闭环追问总数 ≤ 3 题。超过的 MUST 缺失合并到下一个 Step 再问

### 各技能定制

| 技能 | 闭环重点 |
|------|---------|
| product-concept | 角色闭环（有消费就有生产）、商业闭环（有收入就有成本） |
| code-replicate | 意图闭环（代码做了什么 vs 用户想要什么）、边界闭环（代码处理了正常路径，异常路径呢） |
| project-forge | 技术闭环（选了技术栈，运维谁管？监控谁看？）、凭证闭环（需要外部服务，Key 从哪来？） |
| design-to-spec | 验收闭环（每个任务的"完成"标准是什么？谁说了算？） |

