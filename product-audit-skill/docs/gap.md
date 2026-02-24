# Step 2: Gap 分类 (Gap Classification)

> 将 Step 1 的匹配结果分为五类，确定每个功能的实现状态。

---

## 1. 分类规则

| 分类 | 条件 | 含义 | 处理 |
|------|------|------|------|
| **COMPLETE** | 计划了 + matched with high/medium confidence + evidence complete | 功能已完整实现 | 无需处理，进入 Step 3 闭环验证 |
| **PARTIAL** | 计划了 + matched + evidence incomplete (e.g., has route but no API, or has API but no UI) | 功能部分实现 | 列出已实现/未实现部分，用户决定 |
| **MISSING** | 计划了 + no match in implemented features | 功能未实现 | 用户决定：是 MISSING 还是 DEFERRED |
| **UNPLANNED** | implemented + no match in planned features | 代码有但文档没提 | 用户决定：补文档、删代码、或标为计划外特性 |
| **DEFERRED** | 计划了 + 用户在确认时标记为故意推迟 | 有意不做 | 记录到 audit-decisions.json，不算问题 |

核心原则：**COMPLETE 和 PARTIAL 由算法判定，MISSING/UNPLANNED/DEFERRED 需要用户确认。**

---

## 2. 分类执行逻辑

Step-by-step algorithm:

1. Take all matched pairs from Step 1 → initial classification
2. For high-confidence matches: check if evidence is complete (has route + component + API or at least 2/3) → **COMPLETE** or **PARTIAL**
3. For `unmatched_planned` features → initial **MISSING**
4. For `unmatched_implemented` features → initial **UNPLANNED**
5. Check `audit-decisions.json` for previously confirmed DEFERRED → auto-apply

```
输入: step1-output.json (匹配结果)
     audit-decisions.json (历史决策，可选)

处理流程:
  matched_pairs ──→ evidence 完整性检查 ──→ COMPLETE / PARTIAL
  unmatched_planned ──────────────────────→ MISSING (待确认)
  unmatched_implemented ──────────────────→ UNPLANNED (待确认)
  audit-decisions.json 中的 DEFERRED ────→ 自动标记，不再询问

输出: gap-analysis.json
```

---

## 3. PARTIAL 判定细则

A feature is PARTIAL when:

- Has route but no corresponding API call
- Has API endpoint but no UI page
- Has form but no submit handler
- Has list view but no create/edit/delete
- Has backend logic but no frontend entry point

判定依据——至少需要以下 evidence 中的 2/3 才算 COMPLETE:

| Evidence 类型 | 说明 | 示例 |
|---------------|------|------|
| **route** | 前端路由定义 | `router.ts` 中有 `/users` |
| **component** | 页面/组件文件 | `src/pages/Users.tsx` 存在 |
| **api** | 后端 API 端点或前端 API 调用 | `GET /api/users` 或 `api.getUsers()` |

只有 1/3 → PARTIAL。0/3 且在 planned 中 → MISSING。

For each PARTIAL, list:
- What's implemented (with evidence `file:line`)
- What's not found (what was looked for and where)

示例输出:

```
PF-005 用户管理
  分类: PARTIAL
  已实现:
    - route: /users (src/router/index.ts:23)
    - component: src/pages/UserList.tsx:1
  未找到:
    - API 调用: 搜索了 src/api/**, src/services/** 未找到 user 相关请求
    - CRUD: 只有 list，缺少 create/edit/delete
```

---

## 4. 用户确认点

分类完成后，按类别向用户呈现结果并请求确认。

### For MISSING:

> "以下功能在需求源中提及但代码中未找到。是否确实未实现，还是故意推迟？"

Each MISSING item should have option:
- `确认 MISSING` — 确实没做，算作缺口
- `标记为 DEFERRED` — 故意推迟，不算问题（需填写原因）
- `我漏看了，实际已实现` — 重新搜索，提供线索

### For UNPLANNED:

> "以下功能在代码中存在但需求源未提及。是否为计划外特性、是否需要补充文档？"

Each UNPLANNED item:
- `确认 UNPLANNED` — 确实是计划外的，保留记录
- `这是已知特性，需求源遗漏了` — 补充到 planned features，重新分类

### For PARTIAL:

> "以下功能部分实现，请确认分析是否准确。"

用户可以:
- 确认分析正确
- 指出遗漏的 evidence（例如 "API 在 src/lib/rpc.ts 里，不在 src/api/ 下"）

---

## 5. audit-decisions.json 机制

User decisions are persisted so incremental runs don't re-ask confirmed items.

文件位置: 项目根目录 `audit-decisions.json`

```json
{
  "decisions": [
    {
      "feature_id": "PF-003",
      "feature_name": "批量导出",
      "classification": "DEFERRED",
      "reason": "计划 v2.0 实现",
      "decided_at": "2024-01-15",
      "decided_by": "user"
    },
    {
      "feature_id": "IF-012",
      "feature_name": "health-check endpoint",
      "classification": "UNPLANNED",
      "reason": "运维需要，需求源未提及但保留",
      "decided_at": "2024-01-15",
      "decided_by": "user"
    }
  ]
}
```

行为规则:
- On incremental runs, previously confirmed **DEFERRED** items are auto-applied without re-asking
- Previously confirmed **UNPLANNED** items also auto-apply
- If code changes since last decision (file modified after `decided_at`), flag for re-review
- User can run `--reset-decisions` to clear all and re-confirm

---

## 6. 输出格式

输出文件: `gap-analysis.json`

```json
{
  "features": [
    {
      "id": "PF-001",
      "name": "用户登录",
      "classification": "COMPLETE",
      "planned_source": "docs/prd.md:42",
      "implemented_evidence": {
        "route": "/login",
        "component": "src/pages/Login.tsx:1",
        "api": "POST /api/auth/login"
      },
      "notes": ""
    },
    {
      "id": "PF-005",
      "name": "用户管理",
      "classification": "PARTIAL",
      "planned_source": "docs/prd.md:67",
      "implemented_evidence": {
        "route": "/users",
        "component": "src/pages/UserList.tsx:1",
        "api": null
      },
      "missing_parts": ["API 调用未找到", "缺少 create/edit/delete"],
      "notes": "needs_confirmation"
    },
    {
      "id": "PF-003",
      "name": "批量导出",
      "classification": "MISSING",
      "planned_source": "docs/prd.md:88",
      "implemented_evidence": null,
      "notes": "needs_confirmation"
    },
    {
      "id": "IF-012",
      "name": "health-check endpoint",
      "classification": "UNPLANNED",
      "planned_source": null,
      "implemented_evidence": {
        "route": null,
        "component": null,
        "api": "GET /api/health"
      },
      "notes": "needs_confirmation"
    },
    {
      "id": "PF-008",
      "name": "数据归档",
      "classification": "DEFERRED",
      "planned_source": "docs/prd.md:120",
      "implemented_evidence": null,
      "notes": "计划 v2.0 实现 (auto-applied from audit-decisions.json)"
    }
  ],
  "summary": {
    "COMPLETE": 10,
    "PARTIAL": 3,
    "MISSING": 2,
    "UNPLANNED": 1,
    "DEFERRED": 1
  },
  "confirmed_by_user": false
}
```

字段说明:

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | string | 功能 ID，PF- 前缀为计划功能，IF- 前缀为实现功能 |
| `classification` | enum | COMPLETE / PARTIAL / MISSING / UNPLANNED / DEFERRED |
| `planned_source` | string \| null | 需求源位置 (file:line) |
| `implemented_evidence` | object \| null | 实现证据 (route, component, api) |
| `missing_parts` | string[] | 仅 PARTIAL 有，列出缺失部分 |
| `notes` | string | `needs_confirmation` 表示需要用户确认 |
| `confirmed_by_user` | boolean | 全部确认后为 true，Step 3 才能执行 |

---

## 与其他步骤的关系

```
Step 1 (匹配) ──→ Step 2 (分类) ──→ 用户确认 ──→ Step 3 (闭环验证)
                       │                   │
                       │                   └─→ audit-decisions.json (持久化)
                       │
                       └─→ gap-analysis.json (输出)
```

Step 3 只处理 `confirmed_by_user: true` 的结果。未确认的结果会阻塞后续流程。

---

> **铁律速查** — 详见 `${CLAUDE_PLUGIN_ROOT}/skills/feature-audit.md` 的「5 条铁律」章节。
> 本步骤强相关：**用户权威**（所有分类由用户最终确认）、**词汇纪律**（只说"未找到""未提及"，禁用"应该""建议"）、**硬编码禁令**（不建议添加功能）。
