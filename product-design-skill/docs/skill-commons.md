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

## 三、统一验收方法论

每个生成阶段的产出质量由四个相互独立的思想工具保障。它们不是可选增强，而是所有阶段的验收标准。

### 3.1 四维信息卡（4D）

每个关键产出对象必须经受四层追问：

| 维度 | 追问 | 作用 |
|------|------|------|
| **D1 结论** | 结论本身是否正确、完整、合逻辑？ | 验证「是什么」 |
| **D2 证据** | 结论的依据是什么？可追溯吗？ | 验证「凭什么」 |
| **D3 约束** | 有哪些前提条件和限制？遗漏了什么？ | 验证「边界在哪」 |
| **D4 决策** | 为什么做这个选择而非其他？取舍是什么？ | 验证「为什么」 |

### 3.2 六视角矩阵（6V）

每个关键产出对象必须从六个独立视角审视，防止单一视角盲区：

| 视角 | 关注点 |
|------|--------|
| **user** | 用户能完成目标吗？体验如何？ |
| **business** | 支撑商业目标吗？影响营收/转化吗？ |
| **tech** | 技术可实现吗？有不可控依赖吗？ |
| **ux** | 交互一致吗？学习成本低吗？ |
| **data** | 可观测吗？能采集到验证假设的数据吗？ |
| **risk** | 安全/合规/隐私风险？高风险操作有保护吗？ |

### 3.3 闭环思维

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

不同阶段的闭环侧重点不同，但追问模式是统一的。各阶段的具体闭环审查点见 `verify_review.py` 的 review questions。

### 3.4 验证循环（Loop）

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

### 3.5 四者关系

```
Loop（循环）是执行框架 —— 驱动「生成→审查→修正」的迭代
  ├── 4D（四维）是审查深度 —— 对每个对象追问四层
  ├── 6V（六视角）是审查广度 —— 从六个角度看同一个对象
  └── 闭环是审查完整性 —— 检查循环是否断裂
      └── XV（交叉验证）是审查独立性 —— 用另一个模型交叉检验
```

四者缺一不可：没有 Loop，审查是一次性的；没有 4D，审查停留在表面；没有 6V，审查有盲区；没有闭环，审查发现不了断裂。

### 3.6 上游基线验收（Upstream Baseline Validation）

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
