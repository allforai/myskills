# 校验报告

> 生成时间: 2026-02-25T15:20:00Z

## Part 1: 完整性扫描

| 级别 | 数量 |
|------|------|
| ERROR | 0 |
| WARNING | 17 |
| INFO | 20 |

### WARNING 明细

| 任务 | 缺失项 |
|------|--------|
| T003 查看对话报告 | exceptions, rules |
| T005 发音纠正 | exceptions |
| T009 创建场景脚本 | exceptions |
| T013 学习连胜 | exceptions |
| T020 个性化推荐 | exceptions, rules |
| T025 指标看板 | exceptions |
| T029 AI质量评分 | exceptions, rules |
| T032 发音参数调整 | exceptions |
| T035 配置系统参数 | exceptions |
| T036 权限管理 | exceptions |
| T039 登录账户 | rules |
| T042 注销账户 | exceptions |
| T044 学习提醒推送 | exceptions, rules |

> 另有 20 个中低频任务缺少 exceptions/value，属于 INFO 级

## Part 2: 冲突重扫

| ID | 类型 | 描述 | 严重度 |
|----|------|------|--------|
| V001 | IDEMPOTENCY_CONFLICT | T022（购买订阅）和T024（购买场景包）均涉及支付，未明确幂等防重复规则 | 中 |
| V003 | STATE_DEADLOCK | T032（发音参数调整）有回滚规则但无回滚异常流 | 低 |

## Part 3: 竞品差异

对比竞品：Speak、ELSA Speak、Duolingo Max、Praktika AI

### 我有竞品没有（4个）

| 功能 | 对应任务 | 说明 |
|------|----------|------|
| 记忆曲线语境嵌入复习 | T007 | 核心差异化：词汇嵌入新场景语境复习 |
| 紧急场景速学 | T021 | 新移民出发前10分钟预演 |
| 角色专属场景路径 | T019 | 职场/旅行/移民专属推荐 |
| 自由对话引导复习 | T004 | 自由对话中自然融入记忆曲线词汇 |

### 竞品有我没有（6个）

| 功能 | 竞品 | 建议 |
|------|------|------|
| AI视频通话 | Duolingo Max, Praktika | V2评估，技术成本高 |
| 标准化考试备考 | ELSA, Praktika | 偏离场景口语定位 |
| 多语言支持 | Speak, Duolingo, Praktika | 聚焦英语，非当前优先级 |
| 口音选择 | ELSA | 对新移民有价值，建议评估 |
| 语法解释模块 | Duolingo Max | 可融入对话报告 |
| 多模态输入 | Praktika | 使用频率低，非优先级 |

### 都有但做法不同（3个）

| 功能 | 我们的做法 | 竞品做法 |
|------|-----------|----------|
| 发音纠正 | 融入对话轻提示 | ELSA: 独立评估+音素报告 |
| 游戏化 | 连胜+排行榜+积分（轻量） | Duolingo: XP+联赛+成就（重游戏化） |
| 场景对话 | 角色专属+AI+人审混合 | Speak: 任务导向自动结束 |
