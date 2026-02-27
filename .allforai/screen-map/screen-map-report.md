# 界面地图报告摘要

> 执行时间: 2026-02-27T19:16:30Z
> 执行模式: full（全自动）
> 产品规模: 中型（45 个任务）
> 受众模式: typed（consumer 3 + professional 4）
> 概念感知: none

## 总览

| 维度 | 数量 |
|------|------|
| 界面总数 | 42 个 |
| 按钮/操作总数 | 129 个 |
| 已覆盖任务 | 45 / 45 |
| 异常覆盖缺口 | 71 个 |
| 界面级冲突 | 0 个 |

## 高频操作（Top 20%）

| 界面 | 操作 | click_depth |
|------|------|-------------|
| 场景列表页 | 浏览场景列表 | 1 |
| 场景列表页 | 查看个性化推荐 | 1 |
| AI对话页 | 语音输入 | 1 |
| AI对话页 | 文字输入 | 1 |
| AI对话页 | 查看AI回复 | 1 |
| AI对话页 | 实时发音纠正提示 | 1 |
| 对话报告页 | 查看综合评分 | 1 |
| 记忆曲线复习页 | 查看今日复习任务 | 1 |
| 记忆曲线复习页 | 开始闪卡复习 | 1 |
| 记忆曲线复习页 | 标记已记住/未记住 | 1 |
| 审核队列页 | 查看待审核列表 | 1 |
| 学习连胜与成就页 | 查看连胜天数 | 1 |
| 学习连胜与成就页 | 领取连胜奖励 | 1 |
| 关键指标看板 | 查看DAU/MAU/留存 | 1 |
| 关键指标看板 | 查看开口时长指标 | 1 |
| AI对话质量评分页 | 查看质量评分概览 | 1 |
| 用户管理页 | 搜索用户 | 1 |
| 登录页 | 账号密码登录 | 1 |
| 登录页 | 第三方快捷登录 | 1 |
| 登录页 | 验证码登录 | 1 |
| 场景列表页 | 按角色/难度/主题筛选 | 2 |
| 场景列表页 | 选择场景 | 2 |
| 场景详情页 | 查看场景简介 | 2 |
| 场景详情页 | 开始对话 | 2 |
| 场景脚本编辑器 | 创建新场景 | 2 |
| 场景脚本编辑器 | 编辑对话节点 | 2 |
| 场景脚本编辑器 | 保存草稿 | 2 |
| 审核队列页 | 审核通过 | 2 |
| 审核队列页 | 驳回并备注 | 2 |
| 通知中心页 | 查看学习提醒 | 2 |

## 缺口清单

- [medium] MISSING_VALIDATION: AI对话页 → CUD 操作「文字输入」缺少 validation_rules
- [medium] MISSING_VALIDATION: 记忆曲线复习页 → CUD 操作「标记已记住/未记住」缺少 validation_rules
- [medium] MISSING_VALIDATION: 场景脚本编辑器 → CUD 操作「创建新场景」缺少 validation_rules
- [medium] MISSING_VALIDATION: 场景脚本编辑器 → CUD 操作「编辑对话节点」缺少 validation_rules
- [medium] MISSING_VALIDATION: 审核队列页 → CUD 操作「审核通过」缺少 validation_rules
- [medium] MISSING_VALIDATION: 场景包管理页 → CUD 操作「上架场景包」缺少 validation_rules
- [medium] MISSING_VALIDATION: 场景包管理页 → CUD 操作「下架场景包」缺少 validation_rules
- [medium] MISSING_VALIDATION: 场景包管理页 → CUD 操作「编辑标签和关键词」缺少 validation_rules
- [medium] MISSING_VALIDATION: 积分商城页 → CUD 操作「兑换奖品」缺少 validation_rules
- [medium] MISSING_VALIDATION: 分享成果页 → CUD 操作「分享到社交媒体」缺少 validation_rules
- [medium] MISSING_VALIDATION: 角色偏好设置页 → CUD 操作「选择角色类型」缺少 validation_rules
- [medium] MISSING_VALIDATION: 角色偏好设置页 → CUD 操作「设置学习目标」缺少 validation_rules
- [medium] MISSING_VALIDATION: 角色偏好设置页 → CUD 操作「选择感兴趣场景」缺少 validation_rules
- [medium] MISSING_VALIDATION: 紧急场景速学页 → CUD 操作「收藏到词汇本」缺少 validation_rules
- [medium] MISSING_VALIDATION: 订阅管理页 → CUD 操作「续费/升级」缺少 validation_rules
- [medium] MISSING_VALIDATION: 订阅管理页 → CUD 操作「取消订阅」缺少 validation_rules
- [medium] MISSING_VALIDATION: 场景包购买页 → CUD 操作「购买场景包」缺少 validation_rules
- [medium] MISSING_VALIDATION: 关键指标看板 → CUD 操作「设置指标告警」缺少 validation_rules
- [medium] MISSING_VALIDATION: 用户行为分析页 → CUD 操作「创建自定义分析」缺少 validation_rules
- [medium] MISSING_VALIDATION: A/B测试管理页 → CUD 操作「停止/启动测试」缺少 validation_rules
- [medium] MISSING_VALIDATION: 运营报告生成页 → CUD 操作「生成运营报告」缺少 validation_rules
- [medium] MISSING_VALIDATION: 异常对话标注页 → CUD 操作「提交标注」缺少 validation_rules
- [medium] MISSING_VALIDATION: Prompt模板管理页 → CUD 操作「创建新Prompt模板」缺少 validation_rules
- [medium] MISSING_VALIDATION: Prompt模板管理页 → CUD 操作「编辑Prompt模板」缺少 validation_rules
- [medium] MISSING_VALIDATION: Prompt模板管理页 → CUD 操作「发布Prompt到生产环境」缺少 validation_rules
- [medium] MISSING_VALIDATION: 用户管理页 → CUD 操作「封禁/解禁用户」缺少 validation_rules
- [medium] MISSING_VALIDATION: 权限角色管理页 → CUD 操作「创建/编辑角色权限」缺少 validation_rules
- [medium] MISSING_VALIDATION: 权限角色管理页 → CUD 操作「分配用户角色」缺少 validation_rules
- [medium] MISSING_VALIDATION: 投诉处理页 → CUD 操作「回复用户」缺少 validation_rules
- [medium] MISSING_VALIDATION: 注册页 → CUD 操作「第三方登录注册」缺少 validation_rules
- [medium] MISSING_VALIDATION: 个人设置页 → CUD 操作「修改头像/昵称」缺少 validation_rules
- [medium] MISSING_VALIDATION: 个人设置页 → CUD 操作「修改通知偏好」缺少 validation_rules
- [medium] MISSING_VALIDATION: 个人设置页 → CUD 操作「修改语言设置」缺少 validation_rules
- [medium] MISSING_VALIDATION: 个人设置页 → CUD 操作「注销账户」缺少 validation_rules
- [medium] MISSING_VALIDATION: 新手引导页 → CUD 操作「选择学习目的」缺少 validation_rules
- [medium] MISSING_VALIDATION: 新手引导页 → CUD 操作「选择当前水平」缺少 validation_rules
- [medium] MISSING_VALIDATION: 通知中心页 → CUD 操作「管理通知设置」缺少 validation_rules
- [medium] MISSING_VALIDATION: 意见反馈页 → CUD 操作「上传截图」缺少 validation_rules
- [medium] MISSING_VALIDATION: 意见反馈页 → CUD 操作「提交反馈」缺少 validation_rules
- [medium] SILENT_FAILURE: AI对话页 → 中高风险任务 T002 的操作「文字输入」缺少异常处理
- [medium] SILENT_FAILURE: 自由对话页 → 中高风险任务 T004 的操作「自由语音/文字输入」缺少异常处理
- [medium] SILENT_FAILURE: 场景脚本编辑器 → 中高风险任务 T009 的操作「创建新场景」缺少异常处理
- [medium] SILENT_FAILURE: 场景脚本编辑器 → 中高风险任务 T009 的操作「编辑对话节点」缺少异常处理
- [medium] SILENT_FAILURE: 场景脚本编辑器 → 中高风险任务 T009 的操作「保存草稿」缺少异常处理
- [medium] SILENT_FAILURE: 审核队列页 → 中高风险任务 T010 的操作「审核通过」缺少异常处理
- [medium] SILENT_FAILURE: 审核队列页 → 中高风险任务 T010 的操作「驳回并备注」缺少异常处理
- [medium] SILENT_FAILURE: 紧急场景速学页 → 中高风险任务 T021 的操作「收藏到词汇本」缺少异常处理
- [medium] SILENT_FAILURE: A/B测试管理页 → 中高风险任务 T027 的操作「创建A/B测试」缺少异常处理
- [medium] SILENT_FAILURE: A/B测试管理页 → 中高风险任务 T027 的操作「停止/启动测试」缺少异常处理
- [medium] SILENT_FAILURE: 异常对话标注页 → 中高风险任务 T030 的操作「标注异常类型」缺少异常处理
- [medium] SILENT_FAILURE: 异常对话标注页 → 中高风险任务 T030 的操作「提交标注」缺少异常处理
- [medium] SILENT_FAILURE: Prompt模板管理页 → 中高风险任务 T031 的操作「创建新Prompt模板」缺少异常处理
- [medium] SILENT_FAILURE: Prompt模板管理页 → 中高风险任务 T031 的操作「编辑Prompt模板」缺少异常处理
- [medium] SILENT_FAILURE: 发音评估参数页 → 中高风险任务 T032 的操作「调整音素阈值」缺少异常处理
- [medium] SILENT_FAILURE: 权限角色管理页 → 中高风险任务 T036 的操作「创建/编辑角色权限」缺少异常处理
- [medium] SILENT_FAILURE: 权限角色管理页 → 中高风险任务 T036 的操作「分配用户角色」缺少异常处理
- [medium] SILENT_FAILURE: 投诉处理页 → 中高风险任务 T037 的操作「处理投诉」缺少异常处理
- [medium] SILENT_FAILURE: 投诉处理页 → 中高风险任务 T037 的操作「回复用户」缺少异常处理
- [medium] SILENT_FAILURE: 注册页 → 中高风险任务 T038 的操作「第三方登录注册」缺少异常处理
- [medium] SILENT_FAILURE: 重置密码页 → 中高风险任务 T041 的操作「设置新密码」缺少异常处理
- [low] NO_EMPTY_STATE: 场景列表页 → 列表界面「场景列表页」缺少空状态设计
- [low] NO_EMPTY_STATE: 词汇本页 → 列表界面「词汇本页」缺少空状态设计
- [low] NO_EMPTY_STATE: 审核队列页 → 列表界面「审核队列页」缺少空状态设计
- [low] NO_EMPTY_STATE: 场景包管理页 → 列表界面「场景包管理页」缺少空状态设计
- [low] NO_EMPTY_STATE: 个人学习档案页 → 列表界面「个人学习档案页」缺少空状态设计
- [low] NO_EMPTY_STATE: 场景包购买页 → 列表界面「场景包购买页」缺少空状态设计
- [low] NO_EMPTY_STATE: AI对话质量评分页 → 列表界面「AI对话质量评分页」缺少空状态设计
- [low] NO_EMPTY_STATE: Prompt模板管理页 → 列表界面「Prompt模板管理页」缺少空状态设计
- [low] NO_EMPTY_STATE: 订阅与退款管理页 → 列表界面「订阅与退款管理页」缺少空状态设计
- [low] NO_EMPTY_STATE: 权限角色管理页 → 列表界面「权限角色管理页」缺少空状态设计
- [low] NO_EMPTY_STATE: 投诉处理页 → 列表界面「投诉处理页」缺少空状态设计