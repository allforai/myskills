## Phase 2: 制定测试计划

基于静态分析的结果，生成测试计划 `test-plan.json`：

```json
{
  "generated_at": "2026-02-16T12:00:00Z",
  "summary": {
    "total_modules": 15,
    "modules_to_test": 12,
    "skipped_modules": 3,
    "estimated_test_cases": 48,
    "static_issues_found": 7
  },
  "test_cases": [
    {
      "id": "TC-001",
      "module": "用户管理",
      "category": "crud_completeness",
      "action": "verify_create_entry",
      "description": "验证用户管理列表页，点击后能否正常打开新增表单",
      "steps": [
        "1. 导航到用户管理页面 /system/users",
        "2. 查找新增/添加按钮",
        "3. 点击按钮",
        "4. 验证打开了新增表单或跳转到新增页面",
        "5. 验证页面返回状态码不是 404/500"
      ],
      "expected": "存在可点击的新增入口，点击后正常展示新增界面",
      "priority": "high",
      "source": "static_analysis|manual"
    },
    {
      "id": "TC-002",
    "module": "全局",
      "category": "dead_link",
      "action": "verify_menu_link",
      "description": "验证菜单'日报管理'链接 /reports/daily 是否有效",
      "steps": [
        "1. 点击侧边栏菜单 '日报管理'",
        "2. 验证页面正常加载",
        "3. 验证不是 404/500/空白页"
      ],
      "expected": "页面正常展示，无 404 错误",
      "priority": "critical",
      "source": "static_analysis"
    }
  ],
  "skip_list": [
    {
      "module": "操作日志",
      "reason": "只读模块，不需要创建/编辑/删除",
      "still_test": ["read_list", "read_detail", "dead_link"]
    }
  ]
}
```

**测试用例生成规则：**

1. **读取 `crud_by_client` 中当前端的配置**，只生成该端应有操作的测试用例
2. 对每个模块，按该端的 `crud` 字段生成对应用例（有 C 则测新增，有 D 则测删除...）
3. 对每个模块的 `extra_actions` 生成额外操作验证用例
4. 对每个**静态分析发现的死链**，生成 1 个链接有效性验证用例
5. 对每个**孤儿路由**，生成 1 个可达性验证用例
6. 对**导航菜单所有入口**，生成遍历测试用例
7. **跨端一致性**（批量模式）：对同角色的不同端（如 H5 vs App），检查功能是否一致
8. **全局覆盖率**（批量模式）：检查所有端合计是否覆盖了 API 提供的所有操作
