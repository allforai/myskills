# Experience Map — Generation Steps (Step 1 / 1.5 / 2)

> Loaded by the experience-map orchestrator after output-schema.md.
> Covers: data loading, skeleton generation, and LLM free-design phase.

---

## 工作流

```
前置检查：
  .allforai/product-concept/concept-baseline.json      自动加载（推拉协议 §三.A）→ 不存在则 WARNING，不阻塞
  .allforai/experience-map/journey-emotion-map.json    必须存在
  .allforai/product-map/task-inventory.json             必须存在
  .allforai/product-map/role-profiles.json              可选
  .allforai/product-map/business-flows.json             可选
  .allforai/product-map/view-objects.json               可选
  .allforai/product-map/entity-model.json               可选
  .allforai/product-concept/product-concept.json        可选（跨级拉取源）

  跨级原始数据拉取（按需，推拉协议 §三.B）：
    product-mechanisms.json:
      - governance_styles[].downstream_implications  → 决定是否生成审核队列/状态屏幕
      - governance_styles[].rationale                → 验收时判断治理设计是否合理
    role-value-map.json:
      - roles[].operation_profile.density            → 决定后台屏幕的 view_modes 复杂度

Step 1: 加载全部上游数据
      读取 concept-baseline.json（产品定位、角色粒度、治理风格 — 背景知识）
      读取跨级拉取字段（downstream_implications, density）
      读取所有可用的前置数据到上下文
      ↓
Step 1.5: 生成骨架（自动）
      运行 gen_experience_map.py 生成 experience-map-skeleton.json
      确定性字段预填（operation_lines、nodes、screens 结构、data_fields、interaction_type、flow_context）
      ↓
Step 2: LLM 自由设计体验地图
      加载骨架，在此基础上填充 LLM 创意字段
      LLM 理解产品语义后，自主设计每个界面
      按角色分组，每个角色的界面独立设计
      ↓
（后续 Step 3+ 见 validation-steps.md）
```

---

### Step 1：加载全部上游数据

加载所有可用的前置数据。LLM 需要充分理解：

1. **产品是什么** — product-concept 的定位、创新概念、目标用户
2. **用户要做什么** — task-inventory 的全部任务（区分 basic/core）
3. **数据长什么样** — entity-model 的实体、字段、关系、状态机
4. **流程怎么走** — business-flows 的业务流节点和交接关系
5. **每步什么感受** — journey-emotion 的情绪弧线和设计提示
6. **界面需要什么数据** — view-objects 的字段和操作绑定

---

### Step 1.5：生成骨架（自动）

运行预构建脚本生成确定性骨架，减少 LLM token 消耗和幻觉：

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/gen_experience_map.py <BASE_PATH> --mode auto --shard experience-map
```

**脚本输出**：`experience-map-skeleton.json`，包含：

| 已填充（确定性） | LLM 待填充（占位空值） |
|-----------------|---------------------|
| operation_lines 结构（从 business-flows） | `name`（界面名称） |
| nodes（从 flow nodes） | `description`（设计意图） |
| screen.tasks（从 task_ref） | `components`（组件清单） |
| screen.platform（从 role audience_type） | `interaction_pattern`（交互模式） |
| screen.interaction_type（⚠️ 机械推断，仅供参考） | `emotion_design`（情绪设计） |
| screen.data_fields（从 entity-model + view-objects） | `states`（界面状态） |
| screen.vo_ref（从 view-objects 匹配） | `layout_type`（语义化布局名称） |
| screen.actions（从 CRUD 推断） | `layout_description`（空间布局描述） |
| screen.flow_context（从操作线顺序） | |
| screen 去重（同 task+role 复用） | |
| 独立/孤儿任务的额外操作线 | |
| _emotion_ref（从 journey-emotion 附加） | |
| _governance_hint（从 product-mechanisms 附加到 operation_line） | |

**骨架加载**：Step 2 中 LLM 读取骨架文件，在已有结构上填充创意字段。**重要**：骨架中的 `interaction_type` 是脚本的机械推断，LLM 在 Phase B 自由设计时应忽略它，设计完成后在 Phase C 最后一步才决定最终的 interaction_type。

---

### Step 2：LLM 自由设计体验地图

LLM 加载 `experience-map-skeleton.json`，在骨架基础上进行设计。骨架提供了 operation_lines > nodes > screens 结构、data_fields、flow_context 等确定性数据。

**⚠️ 关键设计顺序：先设计，后映射渲染器**

骨架中预填的 `interaction_type` 是脚本的机械推断，**LLM 必须忽略它，先完成自由设计，最后才回头选择最接近的渲染器类型**。这样做是为了防止 LLM 被 interaction_type 锚定，导致所有同类型屏幕长得一样。

```
错误顺序：看到 interaction_type=MG2-C → "这是表单" → 复制表单模板 → 所有表单一样
正确顺序：理解业务目的 → 自由设计布局和组件 → 最后选 interaction_type 给渲染器用
```

**LLM 在骨架上的工作**（按此顺序执行）：

**Phase A — 理解上下文**（每个屏幕都要做）：
1. **消费 `_governance_hint`**：骨架中每条 operation_line 可能携带 `_governance_hint` 字段（含 style/downstream_implications/system_boundary）。LLM **必须**阅读此字段并据此决定：该操作线中的屏幕是否需要审核/审批界面？注册/提交表单应包含哪些字段？哪些功能是外部系统不需要表单？`downstream_implications` 中声明的屏幕需求是否都有对应屏幕？
2. **合并/拆分 screens**：骨架按 1 task = 1 screen 生成，LLM **必须**根据用户意图执行合并：
    - **后台角色**（`multi_function_per_page`）：同一实体的 list/create/edit/detail/status-change 任务 → 合并为一个屏幕，原操作变为 view_modes（见「后台屏幕范式」）。合并后 tasks 合并所有原屏幕的 task_id
    - **前端角色**（`single_task_focus`）：**不等于每个 task 独立一个屏幕**。同一用户意图下的相关任务应自然聚合（见「信息密度是连续光谱」）。例如：商品详情页聚合查看+评价+问答+加购；个人中心聚合个人信息+宠物档案入口+订单入口。用 Tab/折叠/卡片区分信息层次，而非拆成独立页面。可拆分复杂流程任务为多步骤屏幕

**Phase B — 自由设计**（核心创意阶段，**不看 interaction_type**）：
3. 回答**「业务目的三问」**（见 output-schema.md 布局差异化设计原则）：核心目的 → 信息结构 → 物理布局
4. 填充 `layout_type` + `layout_description`：从三问答案推导。layout_type 必须是语义名称（如 `auth_card`、`priority_queue`），不能是通用标签
5. 填充 `name`：为每个界面命名（中文产品语言）
6. 填充 `description`：说明设计意图（2-3 句话，回答 D1+D4，包含三问推导过程）
7. 填充 `components`：设计组件清单（每个含 type/purpose/behavior/data_source/render_as）。`render_as` 必须根据组件业务用途从 12 值枚举中选择（见 output-schema.md render_as 说明），不可省略
8. 填充 `interaction_pattern`：描述交互模式（1-2 句话）
9. 填充 `emotion_design`：基于 `_emotion_ref` 的情绪设计决策
10. 填充 `states`：empty/loading/error/success + 业务特定状态
11. **填充 `view_modes`**：对 `multi_function_per_page` 角色的屏幕，设计屏幕内的视图模式流转

**Phase C — 审查与映射**（设计完成后回头修正）：
12. **审查 `data_fields`**：骨架从 entity-model 机械复制字段，LLM 必须以用户视角逐字段审查：
   - **该不该出现**：系统自动生成的字段（如主键、时间戳、外键）不应出现在创建/编辑表单中
   - **能不能编辑**：骨架的 `input_widget` 不区分界面语境，LLM 须根据业务语义判断可编辑性
13. **最后一步：选择 `interaction_type`**：根据已完成的设计，从渲染器支持列表中选择**最接近**的类型。这一步纯粹为了渲染器兼容，不影响已设计的 layout_type/components/layout_description

**额外的设计思考**（超越骨架）：

1. **理解数据结构**：entity-model 告诉你每个界面需要展示什么字段、有哪些状态转换
2. **匹配情绪弧线**：journey-emotion 告诉你用户在每个节点的情绪，指导交互密度和反馈方式
3. **尊重前后台交互指导思想差异**（见 output-schema.md「前后台交互指导思想」section）：
   - consumer：人多低频 → 低信息密度、强引导、单任务聚焦、显式操作、严格容错
   - professional：人少高频 → 高信息密度、弱引导、同页多功能、隐式操作（行内编辑/批量/快捷键）、宽松容错
4. **组件语义前提验证**：每个组件/筛选/排序/分类方式都隐含了对底层数据的假设（作用域、基数、更新来源、统计基础等）。设计时必须验证这些假设是否被当前屏幕的数据模型支撑 — 如果数据模型不满足组件的语义前提，该组件就不应出现。具体执行：对每个组件回答三个问题——(a) 这个组件预设的数据来源是什么？（全局聚合 vs 用户私有 vs 实时流） (b) 当前屏幕的数据实际是什么？ (c) 两者是否匹配？不匹配则删除该组件
5. **创新界面**：product-concept 中的创新概念应该有独特的交互设计，不套用标准模板。创新功能的交互模式应从其业务本质推导，而非退化为通用表单
6. **治理风格驱动设计**：骨架中每条 operation_line 已注入 `_governance_hint`（来自 product-mechanisms.json），LLM **必须**阅读并遵循。如果骨架无此字段，从 concept-baseline.json 的 `governance_styles` 和 product-mechanisms.json 的完整数据中拉取。对每条业务流：
   - **严格管控**（strict）→ 必须有审核队列、状态跟踪、审核员工作台
   - **自动审核**（auto_review）→ 系统自动处理，只需异常队列和规则配置界面，**不需要**人工审核屏幕
   - **宽松高效**（lenient）→ **不生成审核屏幕**，改用举报/申诉通道、违规记录、事后追究
   - **`downstream_implications`** → 直接转化为屏幕需求（如"需要规则引擎配置界面"→ 必须有对应屏幕）
   - **`system_boundary.external`** → 该功能不在本系统屏幕中出现为可编辑表单（如"实名认证"是外部系统，注册表单只需最小信息+外部系统入口）
   - **`system_boundary.in_scope`** → 只有这些功能需要完整的表单/流程屏幕
7. **操作频度驱动粒度**：读取每个角色的 `operation_profile`，决定屏幕合并/拆分策略：
   - `screen_granularity: "multi_function_per_page"` → 相关任务优先合并为同一屏幕的不同 Tab/Section，减少跳转
   - `screen_granularity: "single_task_focus"` → 每个任务独立屏幕，纵深导航
   - `high_frequency_tasks` 中的任务 → 必须在 1-2 次点击内可达，不能藏在深层菜单

**屏幕合并原则**：搜索和列表通常是同一屏幕的两种状态（搜索是在现有列表上执行过滤，产生新的结果列表），不应拆为两个独立屏幕。类似地，同一实体的"查看全部"和"按条件筛选"也是同一屏幕的不同 view_mode。判断是否合并的标准：两个屏幕操作的是同一数据集合且交互模式可以用 Tab/筛选/搜索框切换 → 合并为一个屏幕的不同 view_mode。

**屏幕去重**：同一个任务可能出现在多条业务流中（如"下载场景包"同时出现在 F001/F002/F003/F004）。LLM 为该任务只设计一个屏幕（一个 screen_id），在不同操作线的节点中复用同一个 screen 对象。**同一个操作线内不应出现重复的 screen_id**。

**设计输出**：对每个界面写出 `description`（设计意图）、`components`（组件清单）、`interaction_pattern`（交互模式描述），而不仅仅是一个交互类型标签。

**大文件处理（分批设计）**：当 screen 数 > 30 时，**禁止**将全部设计决策压缩到一个 Python dict 中——这会导致模板化设计，丧失逐屏思考的质量。改用以下分批策略：

1. **按应用分批**：将所有屏幕按 `app` 字段分组（如 website 组、merchant 组、admin 组），每组作为一个批次。**注意**：跨角色操作线中的屏幕按各自的 `app` 归入不同批次（而非按操作线的主角色），确保每个屏幕从正确的应用视角设计
2. **每批次独立设计**：LLM 加载该批次涉及的上游数据子集（相关任务、实体、情绪节点），从该应用用户的视角对每个屏幕独立思考后输出设计
3. **使用 Python 脚本合并**：每批次的设计结果写入临时 JSON 文件，最终用 Python 脚本合并到骨架中
4. **逐屏质量保证**：每个屏幕的 `description` 必须 2-3 句话（≥ 40 字）、`states` 必须包含业务特定状态、`emotion_design` 必须回应 `_emotion_ref`

**批次脚本模板**（LLM 为每个批次生成一个这样的脚本）：

```python
# batch_fill_{app}.py — 按应用分批，每个屏幕独立设计，不共享模板函数
# 注意：该批次内所有屏幕属于同一个应用（如 merchant），从该应用用户的视角设计
#
# 设计流程：
# 1. 对每个屏幕，先回答「业务目的三问」（见布局差异化设计原则）
# 2. 从三问的答案推导 layout_type 和 components
# 3. 确保与前一个屏幕的布局不同（如果相同，重新审视三问的答案）

BATCH_DESIGNS = {
    "S001": {
        # ── 业务目的三问（指导设计，不写入 JSON） ──
        # Q1 核心目的: 用户快速完成注册，建立对平台的信任
        # Q2 信息结构: 聚焦输入，最少字段，信任标识前置
        # Q3 物理布局: 居中卡片，不需要侧边栏，背景留白
        # ── 从三问推导的设计 ──
        "name": "...",
        "description": "...(≥40字，回答 D1+D4，包含三问推导过程的设计理由)...",
        "components": [       # 每个含 type/purpose/behavior/data_source/render_as
            {
                "type": "login_form",
                "purpose": "用户输入邮箱和密码登录",
                "behavior": "实时校验邮箱格式，密码错误震动反馈",
                "data_source": "user_input",
                "render_as": "input_form"  # 多字段表单 → input_form
            },
            {
                "type": "oauth_buttons",
                "purpose": "LINE/Google/Apple 第三方登录入口",
                "behavior": "点击跳转对应 OAuth 授权页",
                "data_source": "oauth_config",
                "render_as": "action_bar"  # 按钮组（非表单）→ action_bar
            }
        ],
        "interaction_pattern": "...",
        "layout_type": "auth_card",  # 从 Q3 推导，不是从 interaction_type 复制
        "layout_description": "居中登录卡片(480px宽)，上方 logo+品牌标语，卡片内邮箱/密码字段+登录按钮，下方注册链接和 OAuth 入口，背景为浅色品牌色渐变",
        "emotion_design": {    # 结构化对象，不是字符串
            "source_emotion": "...",
            "source_hint": "...",
            "design_response": "...",
            "visual_tone": "...",
            "interaction_density": "..."
        },
        "states": {            # 必须包含业务特定状态
            "empty": "...(该屏幕特有的空状态描述)...",
            "loading": "...",
            "error": "...",
            "success": "...",
            "business_state_1": "...(该屏幕特有的业务状态)..."
        }
    },
    # ...
}
```

**`layout_description` 字段**（新增必填）：用 1-2 句话描述该屏幕的**具体空间布局**——各区域的位置、大小、视觉权重。不同于 `interaction_pattern`（描述用户操作方式），`layout_description` 描述的是静态视觉结构。这个字段的目的是强迫 LLM 在脑中"画"出每个屏幕的样子，而非只贴标签。下游线框渲染器可以用这个描述生成更精确的布局。

**禁止的反模式**：
- ❌ `def get_states(platform, interaction_type)` — 模板函数，所有屏幕生成一样的状态
- ❌ `emotion_design = "简单的一句话"` — 字符串而非结构化对象
- ❌ 所有 desktop 屏幕都用 `sidebar-content`，所有 mobile 屏幕都用 `single-column`
- ❌ `description` 只有一句话重复屏幕名称
- ❌ `layout_type` 直接复用 interaction_type 名称（如 "MG2-L"、"form"、"list"）
- ❌ 多个屏幕共享相同的 `layout_description`（每个屏幕的空间布局描述必须独特）
- ❌ 跳过「业务目的三问」直接写 layout_type（三问注释是强制的思考过程）
