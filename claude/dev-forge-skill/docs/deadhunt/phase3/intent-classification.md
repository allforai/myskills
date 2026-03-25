### 3.8 死链意图判定 (Intent Classification)

> **发现死链只是第一步，判断它该修还是该删才是关键。**
> 不做意图判定的后果：开发者花两天修复一个"查看详情"按钮，结果发现这个功能早就被产品经理砍掉了。

#### 四种意图分类

```
┌──────────────────────────────────────────────────────────────────────┐
│                    死链意图判定 (Intent)                              │
├──────────┬───────────────────────────────────────────────────────────┤
│ 🔴 FIX   │ 前端/路由坏了 → 修复代码                                  │
│ 🟡 CLEAN │ 功能已废弃/砍掉了，入口残留 → 删除入口                      │
│ 🟠 HIDE  │ 功能开发中/未上线，入口提前暴露 → 隐藏入口                   │
│ 🔵 PERM  │ 当前用户/角色不该看到这个入口 → 修复权限控制                  │
└──────────┴───────────────────────────────────────────────────────────┘
```

#### 判定信号矩阵

通过交叉多个信号来推断意图：

```typescript
interface IntentSignals {
  // —— 后端信号 ——
  api_exists: boolean;           // 后端有对应 API 吗？
  api_returns_data: boolean;     // API 返回了有效数据吗？（不是 404/500）
  db_model_exists: boolean;      // 数据库有对应表/模型吗？
  db_has_data: boolean;          // 表里有数据吗？

  // —— 前端信号 ——
  route_registered: boolean;     // 前端路由注册了吗？
  component_exists: boolean;     // 对应的组件文件存在吗？
  component_is_stub: boolean;    // 组件是占位/空壳？（< 20 行或只有 TODO）
  other_clients_have: boolean;   // 其他客户端有这个功能吗？

  // —— 代码历史信号 ——
  recently_modified: boolean;    // 相关代码最近改过吗？（30 天内）
  has_todo_or_fixme: boolean;    // 代码里有 TODO/FIXME/WIP 注释吗？
  in_feature_branch: boolean;    // 是否在未合并的 feature 分支？
  has_feature_flag: boolean;     // 是否受 feature flag 控制？

  // —— 配置信号 ——
  in_menu_config: boolean;       // 菜单配置里有这个入口吗？
  permission_controlled: boolean;// 入口有权限控制吗？
  disabled_or_hidden_attr: boolean; // 元素有 disabled/hidden/v-if=false？
}
```

#### 判定规则

```typescript
function classifyIntent(link: DeadLinkRecord, signals: IntentSignals): Intent {

  // ═══════════════════════════════════════════
  // 规则 1: FIX (该修) — 后端一切正常，前端坏了
  // ═══════════════════════════════════════════
  if (signals.api_exists && signals.api_returns_data && signals.route_registered
      && signals.component_exists && !signals.component_is_stub) {
    // 后端有数据，前端有组件，路由有注册，但就是 404
    // → 大概率是路由路径拼写问题
    return {
      intent: 'FIX',
      confidence: 'high',
      reason: '后端 API 正常，前端组件存在，路由已注册，但页面 404 — 检查路由配置和路径拼写',
      action: '修复路由配置或路径引用',
    };
  }

  if (signals.api_exists && !signals.api_returns_data && signals.db_model_exists) {
    // API 端点在但返回错误 → 后端 bug
    return {
      intent: 'FIX',
      confidence: 'high',
      reason: 'API 端点存在但返回错误',
      action: '修复后端接口',
    };
  }

  if (signals.other_clients_have) {
    // 其他客户端有这个功能 → 当前客户端应该也有
    return {
      intent: 'FIX',
      confidence: 'high',
      reason: '其他客户端有此功能 — 当前客户端是遗漏',
      action: '补全当前客户端的功能',
    };
  }

  // ═══════════════════════════════════════════
  // 规则 2: CLEAN (该删) — 后端也没有了
  // ═══════════════════════════════════════════
  if (!signals.api_exists && !signals.route_registered) {
    // 后端没 API，前端没路由，但菜单/按钮还在
    return {
      intent: 'CLEAN',
      confidence: 'high',
      reason: '后端无 API，前端无路由 — 纯 UI 残留',
      action: '删除菜单项/按钮/链接',
    };
  }

  if (!signals.api_exists && signals.route_registered
      && signals.component_exists && !signals.recently_modified) {
    // 有路由有组件但后端 API 已删除，且代码很久没动
    return {
      intent: 'CLEAN',
      confidence: 'high',
      reason: '后端 API 已不存在，组件长期未维护 — 废弃功能',
      action: '删除路由、组件和入口',
    };
  }

  if (signals.component_exists && !signals.recently_modified
      && !signals.api_exists && !signals.db_has_data) {
    // 组件存在但后端什么都没有，数据库也没数据
    return {
      intent: 'CLEAN',
      confidence: 'medium',
      reason: '前端有壳但后端完全没有对应实现 — 可能是被砍掉的功能',
      action: '确认后删除相关前端代码',
    };
  }

  // ═══════════════════════════════════════════
  // 规则 3: HIDE (该藏) — 开发中，还没做完
  // ═══════════════════════════════════════════
  if (signals.component_is_stub || signals.has_todo_or_fixme) {
    return {
      intent: 'HIDE',
      confidence: 'high',
      reason: '组件是占位/有 TODO 注释 — 功能开发中',
      action: '用 feature flag 或权限控制隐藏入口，完成后再开放',
    };
  }

  if (signals.recently_modified && signals.in_feature_branch) {
    return {
      intent: 'HIDE',
      confidence: 'high',
      reason: '代码在 feature 分支且最近修改 — 开发中功能提前暴露',
      action: '隐藏入口直到功能完成并合并',
    };
  }

  if (signals.recently_modified && !signals.api_returns_data) {
    return {
      intent: 'HIDE',
      confidence: 'medium',
      reason: '前端最近修改但后端还没跟上 — 前后端开发进度不同步',
      action: '暂时隐藏入口，等后端完成后开放',
    };
  }

  // ═══════════════════════════════════════════
  // 规则 4: PERM (权限问题)
  // ═══════════════════════════════════════════
  if (signals.permission_controlled && signals.api_exists) {
    return {
      intent: 'PERM',
      confidence: 'high',
      reason: 'API 存在且有权限控制，但当前账号能看到入口 — 前端权限过滤失效',
      action: '修复前端权限指令/组件，隐藏无权限的入口',
    };
  }

  if (signals.disabled_or_hidden_attr) {
    return {
      intent: 'PERM',
      confidence: 'medium',
      reason: '入口有 disabled/hidden 属性但未生效',
      action: '检查条件渲染逻辑',
    };
  }

  // ═══════════════════════════════════════════
  // 兜底: 无法判定 → 标记让用户确认
  // ═══════════════════════════════════════════
  return {
    intent: 'UNKNOWN',
    confidence: 'low',
    reason: '无法自动判定 — 需要人工确认',
    action: '请确认此功能是否需要保留',
  };
}
```

#### 信号采集方法

```bash
# —— 后端信号 ——

# API 是否存在 (对运行中的后端做探测)
curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/admin/reports/daily

# 数据库模型/表是否存在
# MySQL
mysql -e "SHOW TABLES LIKE '%report%';"
# PostgreSQL
psql -c "\dt *report*"

# —— 前端信号 ——

# 组件文件是否存在
find . -name "*Report*" -o -name "*report*" | grep -v node_modules

# 组件是否是占位/空壳 (少于 20 行有效代码)
wc -l src/pages/reports/daily.tsx
grep -c "TODO\|FIXME\|WIP\|PLACEHOLDER\|暂未实现\|开发中\|待完善" src/pages/reports/daily.tsx

# —— 代码历史信号 ——

# 最近是否修改过 (30 天内)
git log --since="30 days ago" --oneline -- src/pages/reports/
# 如果没有输出 → 长期未动

# 是否有 feature flag 控制
grep -rn "featureFlag\|feature_flag\|FEATURE_\|isEnabled" \
  --include="*.ts" --include="*.tsx" --include="*.vue" src/ | grep -i "report"

# 是否在未合并的分支中
git branch --contains $(git log --oneline -1 --format=%H -- src/pages/reports/) 2>/dev/null
```

#### 批量信号采集脚本

```bash
#!/bin/bash
# collect-intent-signals.sh — 对每个死链批量采集判定信号
# 用法: ./collect-intent-signals.sh <dead-links-report.json> <project-root>

REPORT="$1"
PROJECT="$2"
BACKEND_URL="${3:-http://localhost:8080}"

# 对 report 中的每条记录
cat "$REPORT" | jq -r '.records[] | "\(.url)\t\(.source)"' | while IFS=$'\t' read -r url source; do

  echo "=== 分析: $url ==="

  # 推断资源名
  resource=$(echo "$url" | grep -oP '/\K[a-z]+' | head -1)

  # 后端信号
  api_status=$(curl -s -o /dev/null -w "%{http_code}" "${BACKEND_URL}${url}" 2>/dev/null)
  echo "  API 状态: $api_status"

  # 前端信号: 路由是否注册
  route_found=$(grep -r "path.*${url}" --include="*.ts" "$PROJECT/src/router/" 2>/dev/null | wc -l)
  echo "  路由: $( [ "$route_found" -gt 0 ] && echo 'YES' || echo 'NO' )"

  # 前端信号: 组件是否存在
  component=$(find "$PROJECT/src" -iname "*${resource}*" -name "*.tsx" -o -name "*.vue" 2>/dev/null | head -1)
  echo "  组件文件: ${component:-NOT FOUND}"

  # 组件是否是空壳
  if [ -n "$component" ]; then
    lines=$(wc -l < "$component")
    todos=$(grep -c "TODO\|FIXME\|WIP" "$component" 2>/dev/null || echo 0)
    echo "  组件行数: $lines (TODO/FIXME: $todos)"
  fi

  # 代码历史
  if [ -n "$component" ]; then
    recent=$(git -C "$PROJECT" log --since="30 days ago" --oneline -- "$component" 2>/dev/null | wc -l)
    echo "  近期修改: $( [ "$recent" -gt 0 ] && echo "YES ($recent commits)" || echo 'NO (30天内无修改)' )"
  fi

  echo ""
done
```

### 3.9 404 扫描报告汇总（含意图判定）

所有 Layer 完成后，汇总生成 `dead-links-report.json`：

```json
{
  "scan_time": "2026-02-16T12:00:00Z",
  "client": "admin",
  "summary": {
    "total_dead_links": 23,
    "by_intent": {
      "FIX": 8,
      "CLEAN": 7,
      "HIDE": 4,
      "PERM": 2,
      "UNKNOWN": 2
    },
    "by_layer": {
      "L1_navigation": 3,
      "L2_interaction": 5,
      "L3_api": 8,
      "L4_resource": 4,
      "L5_boundary": 3
    }
  },
  "records": [
    {
      "layer": "1a",
      "url": "/reports/daily",
      "source": "侧边栏菜单: 日报管理 → /reports/daily",
      "intent": "CLEAN",
      "confidence": "high",
      "signals": {
        "api_exists": false,
        "route_registered": true,
        "component_exists": true,
        "component_lines": 12,
        "has_todo": true,
        "recently_modified": false,
        "other_clients_have": false
      },
      "reason": "后端 API 已不存在，组件只有 12 行含 TODO — 废弃功能",
      "action": "删除菜单配置中的'日报管理'入口，删除路由和空壳组件",
      "file_hints": ["src/config/menu.ts:45", "src/router/report.ts:12", "src/pages/reports/daily.tsx"]
    },
    {
      "layer": "2a",
      "url": "/users/detail",
      "source": "用户管理列表 > 行操作 > 查看按钮",
      "intent": "FIX",
      "confidence": "high",
      "signals": {
        "api_exists": true,
        "api_returns_data": true,
        "route_registered": true,
        "component_exists": true,
        "component_lines": 180,
        "recently_modified": true,
        "other_clients_have": true
      },
      "reason": "后端 API 正常，组件完整且最近修改 — 路由路径不匹配",
      "action": "检查路由配置，/users/:id/detail 可能应为 /users/:id",
      "file_hints": ["src/router/user.ts:23"]
    },
    {
      "layer": "1a",
      "url": "/data-center",
      "source": "侧边栏菜单: 数据中心 → /data-center",
      "intent": "HIDE",
      "confidence": "high",
      "signals": {
        "api_exists": false,
        "route_registered": true,
        "component_exists": true,
        "component_lines": 35,
        "has_todo": true,
        "recently_modified": true,
        "has_feature_flag": false
      },
      "reason": "组件有 TODO 且最近修改 — 功能开发中但入口已暴露",
      "action": "在菜单配置中添加 feature flag 控制，开发完成后再开放",
      "file_hints": ["src/config/menu.ts:67"]
    },
    {
      "layer": "2d",
      "url": "/system/audit",
      "source": "系统设置 > 审计管理按钮",
      "intent": "PERM",
      "confidence": "high",
      "signals": {
        "api_exists": true,
        "api_returns_data": true,
        "route_registered": true,
        "component_exists": true,
        "permission_controlled": true,
        "current_user_has_permission": false
      },
      "reason": "API 存在且正常，但当前测试账号无权限却能看到入口 — 前端权限控制失效",
      "action": "检查权限指令 v-permission='audit:view' 是否生效",
      "file_hints": ["src/pages/system/index.tsx:34"]
    },
    {
      "layer": "1a",
      "url": "/legacy/reports",
      "source": "侧边栏菜单: 旧版报表 → /legacy/reports",
      "intent": "CLEAN",
      "confidence": "high",
      "signals": {
        "api_exists": false,
        "route_registered": false,
        "component_exists": false,
        "recently_modified": false,
        "in_menu_config": true
      },
      "reason": "后端无 API，前端无路由、无组件 — 菜单配置纯残留",
      "action": "从菜单配置中删除此条目",
      "file_hints": ["src/config/menu.ts:89"]
    }
  ]
}
```

