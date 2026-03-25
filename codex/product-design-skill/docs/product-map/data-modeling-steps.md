# Data Modeling Steps (Steps 7-8)

> Part of the **product-map** skill. Loaded by the orchestrator at runtime.

---

## Step 7: 数据建模

从任务清单、业务流、约束条件推导后端实体模型和 API 契约。

### 生成方式

LLM 直接分析任务清单和业务流，理解领域语义后建立实体模型。脚本按 module 机械分组无法正确建模实体关系（已验证会产出单个巨型实体）。

**重要**：若 `entity-model.json` 已存在且 `entity_count > 1`，视为用户已手动 curate，**不得覆盖**。仅在文件不存在或 entity_count <= 1 时生成。

**推导逻辑**（LLM 理解语义后执行）：
- 从业务领域理解出发，识别核心实体及其关系（不是简单按 module 分组）
- 每个实体有独立字段列表，字段类型从业务含义推导（价格→decimal，图片→file[]，状态→enum）
- 业务流节点顺序推导状态机（transitions）和实体关系（1:N, M:N）
- 约束条件映射到字段约束（"金额不能为负" → amount: min:0）
- CRUD 任务推导 REST API 契约（R→GET, C→POST, U→PUT, D→DELETE, 状态操作→PATCH）

### 实体行为建模（结构之上的动态模型）

> 见 `skill-commons.md` S3.E「阶段转换思维」——产品设计阶段建发现级行为模型，开发阶段补全到实现级。

实体的结构（字段、类型、外键）只是静态骨架。LLM 还需为核心实体建立**行为模型**：

1. **状态机完整性**：不仅列出状态和转换，还要补全：
   - 每个状态下哪些操作可用/禁用
   - 非法状态转换列表（如「已完成→待处理」是非法的）
   - 终态可达性：每个入口状态都能到达某个终态吗

2. **跨实体不变量**（`invariants` 字段）：
   实体之间必须始终成立的业务规则：
   ```json
   "invariants": [
     {
       "id": "INV-001",
       "rule": "有未完成关联记录的实体不可禁用/删除",
       "entities": ["parent_entity", "child_entity"],
       "enforcement": "禁用/删除操作前检查关联记录状态",
       "violation_action": "阻止操作 + 提示原因"
     },
     {
       "id": "INV-002",
       "rule": "撤销操作时已消耗的关联资源必须处理（退回或作废）",
       "entities": ["main_entity", "consumed_resource"],
       "enforcement": "撤销流程中增加资源处理步骤",
       "violation_action": "操作挂起 + 人工处理"
     }
   ]
   ```

3. **业务流变体**（`flow_variants` 字段）：
   核心业务流的合法变体枚举：
   ```json
   "flow_variants": [
     {
       "flow": "核心业务流名称",
       "variants": [
         {"id": "FV-001", "name": "标准流程", "condition": "满足常规条件"},
         {"id": "FV-002", "name": "部分处理", "condition": "数据量/复杂度超出单次处理"},
         {"id": "FV-003", "name": "延迟处理", "condition": "依赖条件未就绪"}
       ]
     }
   ]
   ```

**输出**：
- `.allforai/product-map/entity-model.json` -- 实体模型（字段、类型、约束、状态机、关系、不变量、流变体）
- `.allforai/product-map/api-contracts.json` -- API 契约（method, path, request/response schema）
- `.allforai/product-map/data-model-report.md` -- 人类可读报告

**用户确认**：展示实体列表、字段数、API 数量，请用户审阅。

---

## Step 8: 视图对象

从实体模型和 API 契约生成前端视图对象（View Object），每个 VO 对应一个界面视图。

**预置脚本**：`../../shared/scripts/product-design/gen_view_objects.py`

```bash
python3 ../../shared/scripts/product-design/gen_view_objects.py <BASE>
```

**推导逻辑**：
- 每个任务的 CRUD x 实体 → 一个 VO
  - R + 列表任务 → ListItemVO（interaction_type: MG2-L 或 MG1）
  - R + 详情任务 → DetailVO（interaction_type: MG2-D）
  - C 任务 → CreateFormVO（interaction_type: MG2-C）
  - U 任务 → EditFormVO（interaction_type: MG2-E）
  - 状态操作 → StateActionVO（interaction_type: MG3）
- 每个 VO 包含 Action Binding：按钮/链接与后端接口或本地操作的完整绑定
  - type: navigate（页面跳转）/ api_call（调用接口）/ local_storage（本地存储）
  - 前置条件、二次确认、输入表单、成功/失败行为

**输出**：
- `.allforai/product-map/view-objects.json` -- 视图对象（字段、Action Binding、interaction_type）

**用户确认**：展示 VO 列表及类型分布，请用户审阅。如需审核数据模型全貌，可在 `/review` 统一审核站点的数据模型 tab 中查看。
