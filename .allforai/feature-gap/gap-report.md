# 功能缺口报告

## 摘要

- 任务缺口: 37 个
- 界面缺口: 42 个
- 旅程缺口: 45 个
- 业务流缺口: 1 个

## Flag 统计

| Flag | 数量 |
|------|------|
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
| 高 | GAP-070 | AI对话页 — SILENT_FAILURE | SILENT_FAILURE | 操作 '语音输入' 无失败反馈定义 |
| 高 | GAP-071 | AI对话页 — SILENT_FAILURE | SILENT_FAILURE | 操作 '文字输入' 无失败反馈定义 |
| 高 | GAP-077 | 记忆曲线复习页 — SILENT_FAILURE | SILENT_FAILURE | 操作 '标记已记住/未记住' 无失败反馈定义 |
| 高 | GAP-080 | 场景脚本编辑器 — SILENT_FAILURE | SILENT_FAILURE | 操作 '创建新场景' 无失败反馈定义 |
| 高 | GAP-081 | 场景脚本编辑器 — SILENT_FAILURE | SILENT_FAILURE | 操作 '编辑对话节点' 无失败反馈定义 |
| 高 | GAP-082 | 场景脚本编辑器 — SILENT_FAILURE | SILENT_FAILURE | 操作 '保存草稿' 无失败反馈定义 |
| 高 | GAP-084 | 审核队列页 — SILENT_FAILURE | SILENT_FAILURE | 操作 '审核通过' 无失败反馈定义 |
| 高 | GAP-085 | 审核队列页 — SILENT_FAILURE | SILENT_FAILURE | 操作 '驳回并备注' 无失败反馈定义 |
| 高 | GAP-091 | 学习连胜与成就页 — SILENT_FAILURE | SILENT_FAILURE | 操作 '领取连胜奖励' 无失败反馈定义 |
| 高 | GAP-115 | 关键指标看板 — SILENT_FAILURE | SILENT_FAILURE | 操作 '设置指标告警' 无失败反馈定义 |
| 高 | GAP-134 | 用户管理页 — SILENT_FAILURE | SILENT_FAILURE | 操作 '封禁/解禁用户' 无失败反馈定义 |
| 高 | GAP-003 | 查看实时发音纠正 — NO_EXCEPTIONS | NO_EXCEPTIONS | 任务 T005 (查看实时发音纠正) 检测到 NO_EXCEPTIONS |
| 高 | GAP-007 | 完成记忆曲线复习 — NO_EXCEPTIONS | NO_EXCEPTIONS | 任务 T007 (完成记忆曲线复习) 检测到 NO_EXCEPTIONS |
| 高 | GAP-011 | 创建场景对话脚本 — CRUD_INCOMPLETE | CRUD_INCOMPLETE | 任务 T009 (创建场景对话脚本) 检测到 CRUD_INCOMPLETE |
| 高 | GAP-017 | 查看学习连胜与成就 — NO_EXCEPTIONS | NO_EXCEPTIONS | 任务 T013 (查看学习连胜与成就) 检测到 NO_EXCEPTIONS |
| 高 | GAP-030 | 查看个性化推荐 — NO_EXCEPTIONS | NO_EXCEPTIONS | 任务 T020 (查看个性化推荐) 检测到 NO_EXCEPTIONS |
| 高 | GAP-036 | 查看关键指标看板 — NO_EXCEPTIONS | NO_EXCEPTIONS | 任务 T025 (查看关键指标看板) 检测到 NO_EXCEPTIONS |
| 高 | GAP-044 | 查看AI对话质量评分 — NO_EXCEPTIONS | NO_EXCEPTIONS | 任务 T029 (查看AI对话质量评分) 检测到 NO_EXCEPTIONS |
| 高 | GAP-051 | 管理用户账户 — CRUD_INCOMPLETE | CRUD_INCOMPLETE | 任务 T033 (管理用户账户) 检测到 CRUD_INCOMPLETE |
| 高 | GAP-001 | 查看对话报告 — NO_RULES | NO_RULES | 任务 T003 (查看对话报告) 检测到 NO_RULES |
| 高 | GAP-004 | 查看实时发音纠正 — NO_RULES | NO_RULES | 任务 T005 (查看实时发音纠正) 检测到 NO_RULES |
| 高 | GAP-031 | 查看个性化推荐 — NO_RULES | NO_RULES | 任务 T020 (查看个性化推荐) 检测到 NO_RULES |
| 高 | GAP-037 | 查看关键指标看板 — NO_RULES | NO_RULES | 任务 T025 (查看关键指标看板) 检测到 NO_RULES |
| 高 | GAP-045 | 查看AI对话质量评分 — NO_RULES | NO_RULES | 任务 T029 (查看AI对话质量评分) 检测到 NO_RULES |
| 高 | GAP-050 | 管理用户账户 — NO_RULES | NO_RULES | 任务 T033 (管理用户账户) 检测到 NO_RULES |
| 高 | GAP-056 | 登录账户 — NO_RULES | NO_RULES | 任务 T039 (登录账户) 检测到 NO_RULES |
| 中 | GAP-067 | 场景列表页 — NO_PRIMARY | NO_PRIMARY | 界面 S001 (场景列表页) 无主操作按钮 |
| 中 | GAP-068 | 场景详情页 — NO_PRIMARY | NO_PRIMARY | 界面 S002 (场景详情页) 无主操作按钮 |
| 中 | GAP-069 | AI对话页 — NO_PRIMARY | NO_PRIMARY | 界面 S003 (AI对话页) 无主操作按钮 |
| 中 | GAP-072 | 对话报告页 — NO_PRIMARY | NO_PRIMARY | 界面 S004 (对话报告页) 无主操作按钮 |
| 中 | GAP-076 | 记忆曲线复习页 — NO_PRIMARY | NO_PRIMARY | 界面 S007 (记忆曲线复习页) 无主操作按钮 |
| 中 | GAP-079 | 场景脚本编辑器 — NO_PRIMARY | NO_PRIMARY | 界面 S009 (场景脚本编辑器) 无主操作按钮 |
| 中 | GAP-083 | 审核队列页 — NO_PRIMARY | NO_PRIMARY | 界面 S010 (审核队列页) 无主操作按钮 |
| 中 | GAP-090 | 学习连胜与成就页 — NO_PRIMARY | NO_PRIMARY | 界面 S012 (学习连胜与成就页) 无主操作按钮 |
| 中 | GAP-114 | 关键指标看板 — NO_PRIMARY | NO_PRIMARY | 界面 S023 (关键指标看板) 无主操作按钮 |
| 中 | GAP-123 | AI对话质量评分页 — NO_PRIMARY | NO_PRIMARY | 界面 S027 (AI对话质量评分页) 无主操作按钮 |
| 中 | GAP-133 | 用户管理页 — NO_PRIMARY | NO_PRIMARY | 界面 S031 (用户管理页) 无主操作按钮 |
| 中 | GAP-150 | 登录页 — NO_PRIMARY | NO_PRIMARY | 界面 S037 (登录页) 无主操作按钮 |
| 高 | GAP-074 | 自由对话页 — SILENT_FAILURE | SILENT_FAILURE | 操作 '自由语音/文字输入' 无失败反馈定义 |
| 高 | GAP-087 | 场景包管理页 — SILENT_FAILURE | SILENT_FAILURE | 操作 '上架场景包' 无失败反馈定义 |
| 高 | GAP-088 | 场景包管理页 — SILENT_FAILURE | SILENT_FAILURE | 操作 '下架场景包' 无失败反馈定义 |
| 高 | GAP-089 | 场景包管理页 — SILENT_FAILURE | SILENT_FAILURE | 操作 '编辑标签和关键词' 无失败反馈定义 |
| 高 | GAP-094 | 积分商城页 — SILENT_FAILURE | SILENT_FAILURE | 操作 '兑换奖品' 无失败反馈定义 |
| 高 | GAP-104 | 紧急场景速学页 — SILENT_FAILURE | SILENT_FAILURE | 操作 '跟读练习' 无失败反馈定义 |
| 高 | GAP-105 | 紧急场景速学页 — SILENT_FAILURE | SILENT_FAILURE | 操作 '收藏到词汇本' 无失败反馈定义 |
| 高 | GAP-117 | 用户行为分析页 — SILENT_FAILURE | SILENT_FAILURE | 操作 '创建自定义分析' 无失败反馈定义 |
| 高 | GAP-119 | A/B测试管理页 — SILENT_FAILURE | SILENT_FAILURE | 操作 '创建A/B测试' 无失败反馈定义 |
| 高 | GAP-120 | A/B测试管理页 — SILENT_FAILURE | SILENT_FAILURE | 操作 '停止/启动测试' 无失败反馈定义 |
| 高 | GAP-122 | 运营报告生成页 — SILENT_FAILURE | SILENT_FAILURE | 操作 '生成运营报告' 无失败反馈定义 |
| 高 | GAP-125 | 异常对话标注页 — SILENT_FAILURE | SILENT_FAILURE | 操作 '标注异常类型' 无失败反馈定义 |
