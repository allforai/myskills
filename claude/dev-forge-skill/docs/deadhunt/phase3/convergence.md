## 多轮收敛机制（深度测试）

> 与 Phase 1 静态分析相同的逐轮递进思想，但驱动方式从 grep 换成浏览器交互。
> 浏览器操作成本更高，因此最大迭代次数为 **2**（1 轮基础 + 最多 2 轮收敛 = 最多 3 轮）。

### 收敛循环结构

```
Round 1 (基础遍历):  执行 3.3 - 3.14 全部步骤（5层扫描 + CRUD + 数据展示）
                      记录 findings 数量 = count_r1
        ↓
Round 2 (模式学习):  从 Round 1 结果提取 URL/交互模式 → 用新模式访问同类页面
                      delta_r2 = 新发现数量
        ↓
Round 3 (交叉验证):  用 Phase 1 静态分析结果反查深度测试遗漏，反之亦然
                      delta_r3 = 新发现数量
        ↓
Round 4 (扩散搜索):  对问题模块的关联模块做完整交互测试（非快速遍历）
                      delta_r4 = 新发现数量
        ↓
收敛检查: if (delta_r2 + delta_r3 + delta_r4 > 0) && (iteration < 2)
            → 回到 Round 2
          else → 收敛完成
```

标记方式同 Phase 1：`source: "pattern_learning" / "cross_validation" / "diffusion"`

---

### 3.15 Round 2: 模式学习（深度测试）

> 从上轮浏览器测试结果中提取 URL 模式和交互模式，对同类页面做补充测试。

#### 模式提取规则

| 发现类型 | 提取的模式 | 新测试动作 |
|---------|-----------|-----------|
| `/order/detail` 页面 404 | URL 模式: `*/detail` | 浏览器直接访问所有 `*/detail` 路由（`/user/detail`, `/product/detail` ...） |
| `/api/order/*` 前缀的 API 全部 404 | API 前缀模式 | 访问所有依赖 `/api/order/*` 的页面，检查是否同样受影响 |
| 某个 UI 框架组件（如 `ant-table`）的操作按钮不可达 | 交互模式: 表格行操作 | 对其他使用同类表格的列表页补充行操作测试 |
| 某页面的面包屑链接 404 | 导航模式: 面包屑 | 补充检查其他深层页面的面包屑是否都可用 |
| 某 chunk 加载 404（懒加载失败） | 资源模式: chunk | 尝试访问所有懒加载路由，检查 chunk 是否都能加载 |

#### 执行步骤

1. 遍历 Round 1 深度测试 findings
2. 按上表提取 URL 模式和交互模式
3. 去重合并，生成新的页面访问列表和交互动作列表
4. **只访问 Round 1 没覆盖到的页面/路由**
5. 对每个新访问的页面，执行 `visitAndCollectAll()`（3.0 中的单次遍历多层收集函数）
6. 新发现标记 `source: "pattern_learning"`

---

### 3.16 Round 3: 交叉验证（深度测试）

> Phase 1 静态分析和 Phase 3 深度测试互相验证，填补对方的盲区。

#### Phase 1 → Phase 3 反查

用静态分析结果驱动深度测试补充：

```
静态分析发现幽灵路由 /products/import
  → 浏览器实际访问此路由，确认页面是否可用
  → 从商品列表页尝试各种交互（点击按钮、展开下拉），看是否有入口

静态分析发现幽灵 API: DELETE /api/coupons/batch
  → 浏览器打开优惠券列表页
  → 尝试勾选多条记录，看是否出现批量操作栏
  → 监听网络请求，检查是否有调用此 API 的交互

静态分析发现 CRUD 缺失: 商品管理缺导入功能
  → 浏览器打开商品列表页
  → 检查工具栏是否有导入按钮（可能被权限/feature flag 隐藏）
```

#### Phase 3 → Phase 1 反哺

深度测试发现的问题反馈给静态分析结果：

```
深度测试发现某按钮点击后 API 404: POST /api/settings/backup
  → 回查 Phase 1 静态分析的 api-reverse-coverage.json
  → 如果静态分析没有标记此 API → 补记到静态分析结果中
  → 说明静态分析的 grep 模式遗漏了这种 API 注册方式

深度测试发现某页面加载时 chunk 404
  → 回查 Phase 1 的 routes.json，检查此路由是否被标记
  → 可能发现路由注册方式是 React.lazy() 动态导入，Phase 1 的 grep 没覆盖
```

#### 执行步骤

1. 读取 Phase 1 的 `static-analysis/` 下所有 JSON 结果
2. 对 Phase 1 发现但 Phase 3 Round 1 未触及的条目：
   - 生成浏览器访问和交互动作
   - 执行测试
3. 对 Phase 3 Round 1 发现但 Phase 1 未标记的条目：
   - 补记到 `static-analysis/` 对应的 JSON 中，具体写入规则：
     - API 404 → 写入 `api-reverse-coverage.json` 的 `orphan_frontend_apis`
     - 路由不可达 → 写入 `unreachable-routes.json`
     - CRUD 缺失 → 写入 `crud-coverage.json`
   - 示例：Phase 3 发现 POST /api/settings/backup 返回 404
     ```json
     // 写入 static-analysis/api-reverse-coverage.json → orphan_frontend_apis[]
     {
       "method": "POST",
       "path": "/api/settings/backup",
       "frontend_file": "src/pages/settings/backup.tsx:42",
       "severity": "critical",
       "analysis": "前端调用了此接口，但后端没有对应路由（Phase 3 浏览器测试发现）",
       "result": "运行时 404",
       "source": "cross_validation_p3"
     }
     ```
4. 新发现标记 `source: "cross_validation"`

---

### 3.17 Round 4: 扩散搜索（深度测试）

> 对问题模块的关联模块做**完整交互测试**，而非 Round 1 的快速遍历。

#### 关联关系（同 Phase 1）

1. 同目录兄弟
2. 同路由前缀
3. 共享 API 前缀
4. 共享组件
5. 同批次修改

#### 与 Phase 1 扩散的区别

Phase 1 扩散搜索只做 grep 分析。Phase 3 扩散搜索用浏览器做完整交互：

| Phase 1 扩散 | Phase 3 扩散 |
|-------------|-------------|
| grep 路由是否注册 | 浏览器实际访问该路由 |
| grep 是否有 CRUD 代码模式 | 浏览器点击新增/编辑/删除按钮 |
| grep API 是否被调用 | 浏览器操作并监听实际 API 请求 |

#### 执行步骤

1. 收集 Round 1-3 所有问题模块
2. 按 5 种关联关系找到关联模块
3. 过滤掉已被 Round 1-3 访问过的模块
4. 对剩余关联模块：
   - 访问页面，执行 `visitAndCollectAll()` 全层收集
   - 如果是列表页，额外测试表格行操作和工具栏按钮
5. 新发现标记 `source: "diffusion"`

---

### 3.18 深度测试收敛追踪

记录到 `reports/convergence-deep.json`：

```json
{
  "phase": "deep",
  "max_iterations": 2,
  "rounds": [
    { "round": 1, "type": "baseline",         "new_findings": 8, "total": 8 },
    { "round": 2, "type": "pattern_learning",  "new_findings": 3, "total": 11 },
    { "round": 3, "type": "cross_validation",  "new_findings": 1, "total": 12 },
    { "round": 4, "type": "diffusion",         "new_findings": 0, "total": 12 }
  ],
  "converged_at_round": 4,
  "baseline_findings": 8,
  "convergence_bonus": 4,
  "bonus_rate": "50%"
}
```

合并到 `dead-links-report.json` 的顶层：

```json
{
  "scan_time": "...",
  "client": "admin",
  "convergence": {
    "total_rounds": 4,
    "baseline_findings": 8,
    "final_findings": 12,
    "bonus_rate": "50%"
  },
  "summary": { ... },
  "records": [ ... ]
}
```

---

