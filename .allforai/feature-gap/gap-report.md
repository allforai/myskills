# 功能缺口报告

## 摘要

- 任务缺口: 45 个
- 界面缺口: 42 个
- 旅程缺口: 45 个
- 业务流缺口: 1 个
- 状态机缺口: 0 个

## Flag 统计

| Flag | 数量 |
|------|------|
| NO_ACCEPTANCE_CRITERIA | 45 |
| NO_PRIMARY | 42 |
| SILENT_FAILURE | 32 |
| NO_RULES | 28 |
| NO_EXCEPTIONS | 28 |
| CRUD_INCOMPLETE | 10 |
| HIGH_RISK_NO_CONFIRM | 4 |

## 用户旅程评分

- AI 训练师: 平均 2.0/4（4 条旅程）
- 内容运营: 平均 2.0/4（4 条旅程）
- 数据运营: 平均 2.0/4（4 条旅程）
- 新移民: 平均 2.0/4（1 条旅程）
- 系统管理员: 平均 2.0/4（5 条旅程）
- 职场人士: 平均 2.0/4（27 条旅程）

## 缺口任务清单（按优先级排序）

| 优先级 | ID | 任务 | 缺口类型 | 描述 |
|--------|----|------|---------|------|
| 高 | GAP-115 | AI对话页 — SILENT_FAILURE | SILENT_FAILURE | 操作 '语音输入' 无失败反馈定义 |
| 高 | GAP-116 | AI对话页 — SILENT_FAILURE | SILENT_FAILURE | 操作 '文字输入' 无失败反馈定义 |
| 高 | GAP-122 | 记忆曲线复习页 — SILENT_FAILURE | SILENT_FAILURE | 操作 '标记已记住/未记住' 无失败反馈定义 |
| 高 | GAP-125 | 场景脚本编辑器 — SILENT_FAILURE | SILENT_FAILURE | 操作 '创建新场景' 无失败反馈定义 |
| 高 | GAP-126 | 场景脚本编辑器 — SILENT_FAILURE | SILENT_FAILURE | 操作 '编辑对话节点' 无失败反馈定义 |
| 高 | GAP-127 | 场景脚本编辑器 — SILENT_FAILURE | SILENT_FAILURE | 操作 '保存草稿' 无失败反馈定义 |
| 高 | GAP-129 | 审核队列页 — SILENT_FAILURE | SILENT_FAILURE | 操作 '审核通过' 无失败反馈定义 |
| 高 | GAP-130 | 审核队列页 — SILENT_FAILURE | SILENT_FAILURE | 操作 '驳回并备注' 无失败反馈定义 |
| 高 | GAP-136 | 学习连胜与成就页 — SILENT_FAILURE | SILENT_FAILURE | 操作 '领取连胜奖励' 无失败反馈定义 |
| 高 | GAP-160 | 关键指标看板 — SILENT_FAILURE | SILENT_FAILURE | 操作 '设置指标告警' 无失败反馈定义 |
| 高 | GAP-179 | 用户管理页 — SILENT_FAILURE | SILENT_FAILURE | 操作 '封禁/解禁用户' 无失败反馈定义 |
| 高 | GAP-001 | 浏览并选择场景 — NO_ACCEPTANCE_CRITERIA | NO_ACCEPTANCE_CRITERIA | 任务 T001 (浏览并选择场景) 检测到 NO_ACCEPTANCE_CRITERIA |
| 高 | GAP-002 | 进行场景对话 — NO_ACCEPTANCE_CRITERIA | NO_ACCEPTANCE_CRITERIA | 任务 T002 (进行场景对话) 检测到 NO_ACCEPTANCE_CRITERIA |
| 高 | GAP-004 | 查看对话报告 — NO_ACCEPTANCE_CRITERIA | NO_ACCEPTANCE_CRITERIA | 任务 T003 (查看对话报告) 检测到 NO_ACCEPTANCE_CRITERIA |
| 高 | GAP-007 | 查看实时发音纠正 — NO_EXCEPTIONS | NO_EXCEPTIONS | 任务 T005 (查看实时发音纠正) 检测到 NO_EXCEPTIONS |
| 高 | GAP-009 | 查看实时发音纠正 — NO_ACCEPTANCE_CRITERIA | NO_ACCEPTANCE_CRITERIA | 任务 T005 (查看实时发音纠正) 检测到 NO_ACCEPTANCE_CRITERIA |
| 高 | GAP-013 | 完成记忆曲线复习 — NO_EXCEPTIONS | NO_EXCEPTIONS | 任务 T007 (完成记忆曲线复习) 检测到 NO_EXCEPTIONS |
| 高 | GAP-014 | 完成记忆曲线复习 — NO_ACCEPTANCE_CRITERIA | NO_ACCEPTANCE_CRITERIA | 任务 T007 (完成记忆曲线复习) 检测到 NO_ACCEPTANCE_CRITERIA |
| 高 | GAP-019 | 创建场景对话脚本 — NO_ACCEPTANCE_CRITERIA | NO_ACCEPTANCE_CRITERIA | 任务 T009 (创建场景对话脚本) 检测到 NO_ACCEPTANCE_CRITERIA |
| 高 | GAP-020 | 创建场景对话脚本 — CRUD_INCOMPLETE | CRUD_INCOMPLETE | 任务 T009 (创建场景对话脚本) 检测到 CRUD_INCOMPLETE |
| 高 | GAP-021 | 审核场景内容 — NO_ACCEPTANCE_CRITERIA | NO_ACCEPTANCE_CRITERIA | 任务 T010 (审核场景内容) 检测到 NO_ACCEPTANCE_CRITERIA |
| 高 | GAP-029 | 查看学习连胜与成就 — NO_EXCEPTIONS | NO_EXCEPTIONS | 任务 T013 (查看学习连胜与成就) 检测到 NO_EXCEPTIONS |
| 高 | GAP-030 | 查看学习连胜与成就 — NO_ACCEPTANCE_CRITERIA | NO_ACCEPTANCE_CRITERIA | 任务 T013 (查看学习连胜与成就) 检测到 NO_ACCEPTANCE_CRITERIA |
| 高 | GAP-049 | 查看个性化推荐 — NO_EXCEPTIONS | NO_EXCEPTIONS | 任务 T020 (查看个性化推荐) 检测到 NO_EXCEPTIONS |
| 高 | GAP-051 | 查看个性化推荐 — NO_ACCEPTANCE_CRITERIA | NO_ACCEPTANCE_CRITERIA | 任务 T020 (查看个性化推荐) 检测到 NO_ACCEPTANCE_CRITERIA |
| 高 | GAP-060 | 查看关键指标看板 — NO_EXCEPTIONS | NO_EXCEPTIONS | 任务 T025 (查看关键指标看板) 检测到 NO_EXCEPTIONS |
| 高 | GAP-062 | 查看关键指标看板 — NO_ACCEPTANCE_CRITERIA | NO_ACCEPTANCE_CRITERIA | 任务 T025 (查看关键指标看板) 检测到 NO_ACCEPTANCE_CRITERIA |
| 高 | GAP-072 | 查看AI对话质量评分 — NO_EXCEPTIONS | NO_EXCEPTIONS | 任务 T029 (查看AI对话质量评分) 检测到 NO_EXCEPTIONS |
| 高 | GAP-074 | 查看AI对话质量评分 — NO_ACCEPTANCE_CRITERIA | NO_ACCEPTANCE_CRITERIA | 任务 T029 (查看AI对话质量评分) 检测到 NO_ACCEPTANCE_CRITERIA |
| 高 | GAP-083 | 管理用户账户 — NO_ACCEPTANCE_CRITERIA | NO_ACCEPTANCE_CRITERIA | 任务 T033 (管理用户账户) 检测到 NO_ACCEPTANCE_CRITERIA |
| 高 | GAP-084 | 管理用户账户 — CRUD_INCOMPLETE | CRUD_INCOMPLETE | 任务 T033 (管理用户账户) 检测到 CRUD_INCOMPLETE |
| 高 | GAP-095 | 登录账户 — NO_ACCEPTANCE_CRITERIA | NO_ACCEPTANCE_CRITERIA | 任务 T039 (登录账户) 检测到 NO_ACCEPTANCE_CRITERIA |
| 高 | GAP-003 | 查看对话报告 — NO_RULES | NO_RULES | 任务 T003 (查看对话报告) 检测到 NO_RULES |
| 高 | GAP-008 | 查看实时发音纠正 — NO_RULES | NO_RULES | 任务 T005 (查看实时发音纠正) 检测到 NO_RULES |
| 高 | GAP-050 | 查看个性化推荐 — NO_RULES | NO_RULES | 任务 T020 (查看个性化推荐) 检测到 NO_RULES |
| 高 | GAP-061 | 查看关键指标看板 — NO_RULES | NO_RULES | 任务 T025 (查看关键指标看板) 检测到 NO_RULES |
| 高 | GAP-073 | 查看AI对话质量评分 — NO_RULES | NO_RULES | 任务 T029 (查看AI对话质量评分) 检测到 NO_RULES |
| 高 | GAP-082 | 管理用户账户 — NO_RULES | NO_RULES | 任务 T033 (管理用户账户) 检测到 NO_RULES |
| 高 | GAP-094 | 登录账户 — NO_RULES | NO_RULES | 任务 T039 (登录账户) 检测到 NO_RULES |
| 中 | GAP-112 | 场景列表页 — NO_PRIMARY | NO_PRIMARY | 界面 S001 (场景列表页) 无主操作按钮 |
| 中 | GAP-113 | 场景详情页 — NO_PRIMARY | NO_PRIMARY | 界面 S002 (场景详情页) 无主操作按钮 |
| 中 | GAP-114 | AI对话页 — NO_PRIMARY | NO_PRIMARY | 界面 S003 (AI对话页) 无主操作按钮 |
| 中 | GAP-117 | 对话报告页 — NO_PRIMARY | NO_PRIMARY | 界面 S004 (对话报告页) 无主操作按钮 |
| 中 | GAP-121 | 记忆曲线复习页 — NO_PRIMARY | NO_PRIMARY | 界面 S007 (记忆曲线复习页) 无主操作按钮 |
| 中 | GAP-124 | 场景脚本编辑器 — NO_PRIMARY | NO_PRIMARY | 界面 S009 (场景脚本编辑器) 无主操作按钮 |
| 中 | GAP-128 | 审核队列页 — NO_PRIMARY | NO_PRIMARY | 界面 S010 (审核队列页) 无主操作按钮 |
| 中 | GAP-135 | 学习连胜与成就页 — NO_PRIMARY | NO_PRIMARY | 界面 S012 (学习连胜与成就页) 无主操作按钮 |
| 中 | GAP-159 | 关键指标看板 — NO_PRIMARY | NO_PRIMARY | 界面 S023 (关键指标看板) 无主操作按钮 |
| 中 | GAP-168 | AI对话质量评分页 — NO_PRIMARY | NO_PRIMARY | 界面 S027 (AI对话质量评分页) 无主操作按钮 |
| 中 | GAP-178 | 用户管理页 — NO_PRIMARY | NO_PRIMARY | 界面 S031 (用户管理页) 无主操作按钮 |
