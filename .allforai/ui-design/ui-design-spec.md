# UI 设计规格

> 风格: Material Design 3
> 生成时间: 2026-02-27T20:27:55Z
> 产品: 让每个人都敢开口说英语 — 通过场景对话×记忆曲线闭环，把哑巴英语变成自信表达

## 设计语言基础

### 配色系统

- 主色 (Primary): #6750A4
- 次色 (Secondary): #625B71
- 强调色 (Tertiary): #7D5260
- 背景: #FFFBFE
- 表面 (Surface): #FFFBFE
- 表面变体: #E7E0EC
- 功能色: 成功 #2E7D32 · 警告 #ED6C02 · 错误 #B3261E

### 排版

- Display: 57px / 400
- Headline: 32px / 400
- Title: 22px / 500
- Body: 16px / 400 / 行高 24px
- Label: 14px / 500
- 字体推荐: 'Roboto', 'Noto Sans SC', sans-serif

### 组件规范

- 圆角: 12px
- 间距系统: 4px 基准 (4/8/12/16/24/32)
- 按钮: Filled (主操作) / Outlined (次要) / Text (辅助)
- 卡片: Elevated (阴影) / Filled (填充) / Outlined (边框)
- 输入框: 默认 outlined，聚焦态主色边框
- 导航: Bottom navigation (C端) / Navigation rail (B端)

### 推荐组件库

- 首选: Flutter Material 3
- 备选: MUI (React)

---

## 界面规格

### 模块: 场景对话

#### 场景列表页（S001）[consumer] [core]

**界面目的**: 入口页，合并推荐

**功能类别**: 核心功能

**布局模式**: 单列卡片流

**主要操作**:
  - 浏览场景列表 (Filled Button)
  - 按角色/难度/主题筛选 (Filled Button)
  - 选择场景 (Filled Button)

**关键状态设计**:
  - 空态: 插图 + 引导文案 + CTA 按钮
  - 加载中: 骨架屏 (shimmer)
  - 错误: Snackbar (错误色) + 重试按钮
  - 成功: Snackbar (成功色) / 页面跳转

#### 场景详情页（S002）[consumer] [core]

**界面目的**: 

**功能类别**: 核心功能

**布局模式**: 单列卡片流

**主要操作**:
  - 查看场景简介 (Filled Button)
  - 开始对话 (Filled Button)

**关键状态设计**:
  - 空态: 插图 + 引导文案 + CTA 按钮
  - 加载中: 骨架屏 (shimmer)
  - 错误: Snackbar (错误色) + 重试按钮
  - 成功: Snackbar (成功色) / 页面跳转

#### AI对话页（S003）[consumer] [core]

**界面目的**: 核心交互页

**功能类别**: 核心功能

**布局模式**: 单列卡片流

**主要操作**:
  - 语音输入 (Filled Button)
  - 文字输入 (Filled Button)
  - 查看AI回复 (Filled Button)
  - 查看生词收集 (Outlined Button)

**关键状态设计**:
  - 空态: 插图 + 引导文案 + CTA 按钮
  - 加载中: 骨架屏 (shimmer)
  - 错误: Snackbar (错误色) + 重试按钮
  - 成功: Snackbar (成功色) / 页面跳转

#### 对话报告页（S004）[consumer] [core]

**界面目的**: 

**功能类别**: 核心功能

**布局模式**: 单列卡片流

**主要操作**:
  - 查看综合评分 (Filled Button)
  - 查看语法错误清单 (Outlined Button)
  - 查看表达建议 (Outlined Button)
  - 重新开始同场景 (Outlined Button)

**关键状态设计**:
  - 空态: 插图 + 引导文案 + CTA 按钮
  - 加载中: 骨架屏 (shimmer)
  - 错误: Snackbar (错误色) + 重试按钮
  - 成功: Snackbar (成功色) / 页面跳转

#### 自由对话页（S005）[consumer] [core]

**界面目的**: 

**功能类别**: 核心功能

**布局模式**: 单列卡片流

**主要操作**:
  - 选择话题 (Outlined Button)
  - 自由语音/文字输入 (Outlined Button)
  - AI自由回复 (Outlined Button)

**关键状态设计**:
  - 空态: 插图 + 引导文案 + CTA 按钮
  - 加载中: 骨架屏 (shimmer)
  - 错误: Snackbar (错误色) + 重试按钮
  - 成功: Snackbar (成功色) / 页面跳转

### 模块: 发音纠正

#### 发音详细报告页（S006）[consumer] [core]

**界面目的**: 

**功能类别**: 核心功能

**布局模式**: 单列卡片流

**主要操作**:
  - 查看音素级评分 (Outlined Button)
  - 播放标准发音对比 (Outlined Button)
  - 查看发音趋势 (Outlined Button)

**关键状态设计**:
  - 空态: 插图 + 引导文案 + CTA 按钮
  - 加载中: 骨架屏 (shimmer)
  - 错误: Snackbar (错误色) + 重试按钮
  - 成功: Snackbar (成功色) / 页面跳转

### 模块: 记忆曲线

#### 记忆曲线复习页（S007）[consumer] [core]

**界面目的**: 

**功能类别**: 核心功能

**布局模式**: 单列卡片流

**主要操作**:
  - 查看今日复习任务 (Filled Button)
  - 开始闪卡复习 (Filled Button)
  - 标记已记住/未记住 (Filled Button)
  - 查看复习统计 (Outlined Button)

**关键状态设计**:
  - 空态: 插图 + 引导文案 + CTA 按钮
  - 加载中: 骨架屏 (shimmer)
  - 错误: Snackbar (错误色) + 重试按钮
  - 成功: Snackbar (成功色) / 页面跳转

#### 词汇本页（S008）[consumer] [core]

**界面目的**: 

**功能类别**: 核心功能

**布局模式**: 单列卡片流

**主要操作**:
  - 浏览词汇列表 (Outlined Button)
  - 按来源/状态筛选 (Outlined Button)
  - 查看词汇详情 (Outlined Button)

**关键状态设计**:
  - 空态: 插图 + 引导文案 + CTA 按钮
  - 加载中: 骨架屏 (shimmer)
  - 错误: Snackbar (错误色) + 重试按钮
  - 成功: Snackbar (成功色) / 页面跳转

### 模块: 场景库管理

#### 场景脚本编辑器（S009）[professional] [core]

**界面目的**: 

**功能类别**: 核心功能

**布局模式**: 侧边导航 + 内容区（表格/列表导向）

**主要操作**:
  - 创建新场景 (Filled Button)
  - 编辑对话节点 (Filled Button)
  - 保存草稿 (Filled Button)
  - 预览场景对话 (Outlined Button)

**关键状态设计**:
  - 空态: 插图 + 引导文案 + CTA 按钮
  - 加载中: 骨架屏 (shimmer)
  - 错误: Snackbar (错误色) + 重试按钮
  - 成功: Snackbar (成功色) / 页面跳转

#### 审核队列页（S010）[professional] [core]

**界面目的**: 

**功能类别**: 核心功能

**布局模式**: 侧边导航 + 内容区（表格/列表导向）

**主要操作**:
  - 查看待审核列表 (Filled Button)
  - 审核通过 (Filled Button)
  - 驳回并备注 (Filled Button)

**关键状态设计**:
  - 空态: 插图 + 引导文案 + CTA 按钮
  - 加载中: 骨架屏 (shimmer)
  - 错误: Snackbar (错误色) + 重试按钮
  - 成功: Snackbar (成功色) / 页面跳转

#### 场景包管理页（S011）[professional] [core]

**界面目的**: 

**功能类别**: 核心功能

**布局模式**: 侧边导航 + 内容区（表格/列表导向）

**主要操作**:
  - 查看场景包列表 (Outlined Button)
  - 上架场景包 (Outlined Button)
  - 下架场景包 (Outlined Button)

**关键状态设计**:
  - 空态: 插图 + 引导文案 + CTA 按钮
  - 加载中: 骨架屏 (shimmer)
  - 错误: Snackbar (错误色) + 重试按钮
  - 成功: Snackbar (成功色) / 页面跳转

### 模块: 游戏化与轻社交

#### 学习连胜与成就页（S012）[consumer] [core]

**界面目的**: 

**功能类别**: 核心功能

**布局模式**: 单列卡片流

**主要操作**:
  - 查看连胜天数 (Filled Button)
  - 领取连胜奖励 (Filled Button)
  - 查看成就徽章 (Outlined Button)

**关键状态设计**:
  - 空态: 插图 + 引导文案 + CTA 按钮
  - 加载中: 骨架屏 (shimmer)
  - 错误: Snackbar (错误色) + 重试按钮
  - 成功: Snackbar (成功色) / 页面跳转

#### 排行榜页（S013）[consumer] [core]

**界面目的**: 

**功能类别**: 核心功能

**布局模式**: 单列卡片流

**主要操作**:
  - 查看好友排名 (Outlined Button)
  - 查看全站排名 (Outlined Button)

**关键状态设计**:
  - 空态: 插图 + 引导文案 + CTA 按钮
  - 加载中: 骨架屏 (shimmer)
  - 错误: Snackbar (错误色) + 重试按钮
  - 成功: Snackbar (成功色) / 页面跳转

#### 积分商城页（S014）[consumer] [core]

**界面目的**: 

**功能类别**: 核心功能

**布局模式**: 单列卡片流

**主要操作**:
  - 查看积分余额 (Outlined Button)
  - 兑换奖品 (Outlined Button)
  - 查看兑换记录 (Outlined Button)

**关键状态设计**:
  - 空态: 插图 + 引导文案 + CTA 按钮
  - 加载中: 骨架屏 (shimmer)
  - 错误: Snackbar (错误色) + 重试按钮
  - 成功: Snackbar (成功色) / 页面跳转

#### 分享成果页（S015）[consumer] [core]

**界面目的**: 

**功能类别**: 核心功能

**布局模式**: 单列卡片流

**主要操作**:
  - 选择分享模板 (Outlined Button)
  - 分享到社交媒体 (Outlined Button)

**关键状态设计**:
  - 空态: 插图 + 引导文案 + CTA 按钮
  - 加载中: 骨架屏 (shimmer)
  - 错误: Snackbar (错误色) + 重试按钮
  - 成功: Snackbar (成功色) / 页面跳转

### 模块: 学习档案与进度

#### 个人学习档案页（S016）[consumer] [core]

**界面目的**: 

**功能类别**: 核心功能

**布局模式**: 单列卡片流

**主要操作**:
  - 查看口语能力雷达图 (Outlined Button)
  - 查看学习目标进度 (Outlined Button)
  - 查看历史对话列表 (Outlined Button)

**关键状态设计**:
  - 空态: 插图 + 引导文案 + CTA 按钮
  - 加载中: 骨架屏 (shimmer)
  - 错误: Snackbar (错误色) + 重试按钮
  - 成功: Snackbar (成功色) / 页面跳转

#### 学习统计报告页（S017）[consumer] [core]

**界面目的**: 

**功能类别**: 核心功能

**布局模式**: 单列卡片流

**主要操作**:
  - 查看周/月学习数据 (Outlined Button)
  - 查看开口时长趋势 (Outlined Button)
  - 查看场景通关率 (Outlined Button)

**关键状态设计**:
  - 空态: 插图 + 引导文案 + CTA 按钮
  - 加载中: 骨架屏 (shimmer)
  - 错误: Snackbar (错误色) + 重试按钮
  - 成功: Snackbar (成功色) / 页面跳转

### 模块: 角色场景推荐

#### 角色偏好设置页（S018）[consumer] [core]

**界面目的**: 

**功能类别**: 核心功能

**布局模式**: 单列卡片流

**主要操作**:
  - 选择角色类型 (Outlined Button)
  - 设置学习目标 (Outlined Button)
  - 选择感兴趣场景 (Outlined Button)

**关键状态设计**:
  - 空态: 插图 + 引导文案 + CTA 按钮
  - 加载中: 骨架屏 (shimmer)
  - 错误: Snackbar (错误色) + 重试按钮
  - 成功: Snackbar (成功色) / 页面跳转

### 模块: 紧急场景速学

#### 紧急场景速学页（S019）[consumer] [core]

**界面目的**: 

**功能类别**: 核心功能

**布局模式**: 单列卡片流

**主要操作**:
  - 选择紧急场景 (Outlined Button)
  - 查看关键句模板 (Outlined Button)
  - 跟读练习 (Outlined Button)

**关键状态设计**:
  - 空态: 插图 + 引导文案 + CTA 按钮
  - 加载中: 骨架屏 (shimmer)
  - 错误: Snackbar (错误色) + 重试按钮
  - 成功: Snackbar (成功色) / 页面跳转

### 模块: 订阅与付费

#### 订阅方案页（S020）[consumer]

**界面目的**: 

**功能类别**: 基本功能

**布局模式**: 单列卡片流

**主要操作**:
  - 查看订阅方案 (Outlined Button)
  - 选择方案并支付 (Outlined Button)

**关键状态设计**:
  - 空态: 插图 + 引导文案 + CTA 按钮
  - 加载中: 骨架屏 (shimmer)
  - 错误: Snackbar (错误色) + 重试按钮
  - 成功: Snackbar (成功色) / 页面跳转

#### 订阅管理页（S021）[consumer]

**界面目的**: 

**功能类别**: 基本功能

**布局模式**: 单列卡片流

**主要操作**:
  - 查看当前订阅 (Outlined Button)
  - 续费/升级 (Outlined Button)
  - 取消订阅 (Outlined Button)

**关键状态设计**:
  - 空态: 插图 + 引导文案 + CTA 按钮
  - 加载中: 骨架屏 (shimmer)
  - 错误: Snackbar (错误色) + 重试按钮
  - 成功: Snackbar (成功色) / 页面跳转

#### 场景包购买页（S022）[consumer]

**界面目的**: 

**功能类别**: 基本功能

**布局模式**: 单列卡片流

**主要操作**:
  - 浏览可购场景包 (Outlined Button)
  - 购买场景包 (Outlined Button)

**关键状态设计**:
  - 空态: 插图 + 引导文案 + CTA 按钮
  - 加载中: 骨架屏 (shimmer)
  - 错误: Snackbar (错误色) + 重试按钮
  - 成功: Snackbar (成功色) / 页面跳转

### 模块: 运营数据看板

#### 关键指标看板（S023）[professional] [core]

**界面目的**: 

**功能类别**: 核心功能

**布局模式**: 侧边导航 + 内容区（表格/列表导向）

**主要操作**:
  - 查看DAU/MAU/留存 (Filled Button)
  - 查看开口时长指标 (Filled Button)
  - 设置指标告警 (Outlined Button)

**关键状态设计**:
  - 空态: 插图 + 引导文案 + CTA 按钮
  - 加载中: 骨架屏 (shimmer)
  - 错误: Snackbar (错误色) + 重试按钮
  - 成功: Snackbar (成功色) / 页面跳转

#### 用户行为分析页（S024）[professional] [core]

**界面目的**: 

**功能类别**: 核心功能

**布局模式**: 侧边导航 + 内容区（表格/列表导向）

**主要操作**:
  - 查看行为漏斗 (Outlined Button)
  - 创建自定义分析 (Outlined Button)
  - 导出分析数据 (Outlined Button)

**关键状态设计**:
  - 空态: 插图 + 引导文案 + CTA 按钮
  - 加载中: 骨架屏 (shimmer)
  - 错误: Snackbar (错误色) + 重试按钮
  - 成功: Snackbar (成功色) / 页面跳转

#### A/B测试管理页（S025）[professional] [core]

**界面目的**: 

**功能类别**: 核心功能

**布局模式**: 侧边导航 + 内容区（表格/列表导向）

**主要操作**:
  - 创建A/B测试 (Outlined Button)
  - 查看测试结果 (Outlined Button)
  - 停止/启动测试 (Outlined Button)

**关键状态设计**:
  - 空态: 插图 + 引导文案 + CTA 按钮
  - 加载中: 骨架屏 (shimmer)
  - 错误: Snackbar (错误色) + 重试按钮
  - 成功: Snackbar (成功色) / 页面跳转

#### 运营报告生成页（S026）[professional] [core]

**界面目的**: 

**功能类别**: 核心功能

**布局模式**: 侧边导航 + 内容区（表格/列表导向）

**主要操作**:
  - 选择报告模板 (Outlined Button)
  - 生成运营报告 (Outlined Button)
  - 导出报告 (Outlined Button)

**关键状态设计**:
  - 空态: 插图 + 引导文案 + CTA 按钮
  - 加载中: 骨架屏 (shimmer)
  - 错误: Snackbar (错误色) + 重试按钮
  - 成功: Snackbar (成功色) / 页面跳转

### 模块: AI质量监控

#### AI对话质量评分页（S027）[professional] [core]

**界面目的**: 

**功能类别**: 核心功能

**布局模式**: 侧边导航 + 内容区（表格/列表导向）

**主要操作**:
  - 查看质量评分概览 (Filled Button)
  - 查看低分对话列表 (Outlined Button)
  - 查看评分趋势 (Outlined Button)

**关键状态设计**:
  - 空态: 插图 + 引导文案 + CTA 按钮
  - 加载中: 骨架屏 (shimmer)
  - 错误: Snackbar (错误色) + 重试按钮
  - 成功: Snackbar (成功色) / 页面跳转

#### 异常对话标注页（S028）[professional] [core]

**界面目的**: 

**功能类别**: 核心功能

**布局模式**: 侧边导航 + 内容区（表格/列表导向）

**主要操作**:
  - 查看待标注对话 (Outlined Button)
  - 标注异常类型 (Outlined Button)
  - 提交标注 (Outlined Button)

**关键状态设计**:
  - 空态: 插图 + 引导文案 + CTA 按钮
  - 加载中: 骨架屏 (shimmer)
  - 错误: Snackbar (错误色) + 重试按钮
  - 成功: Snackbar (成功色) / 页面跳转

#### Prompt模板管理页（S029）[professional] [core]

**界面目的**: 

**功能类别**: 核心功能

**布局模式**: 侧边导航 + 内容区（表格/列表导向）

**主要操作**:
  - 查看Prompt模板列表 (Outlined Button)
  - 创建新Prompt模板 (Outlined Button)
  - 编辑Prompt模板 (Outlined Button)

**关键状态设计**:
  - 空态: 插图 + 引导文案 + CTA 按钮
  - 加载中: 骨架屏 (shimmer)
  - 错误: Snackbar (错误色) + 重试按钮
  - 成功: Snackbar (成功色) / 页面跳转

#### 发音评估参数页（S030）[professional] [core]

**界面目的**: 

**功能类别**: 核心功能

**布局模式**: 侧边导航 + 内容区（表格/列表导向）

**主要操作**:
  - 查看当前评估参数 (Outlined Button)
  - 调整音素阈值 (Outlined Button)
  - 测试参数效果 (Outlined Button)

**关键状态设计**:
  - 空态: 插图 + 引导文案 + CTA 按钮
  - 加载中: 骨架屏 (shimmer)
  - 错误: Snackbar (错误色) + 重试按钮
  - 成功: Snackbar (成功色) / 页面跳转

### 模块: 用户管理与系统配置

#### 用户管理页（S031）[professional]

**界面目的**: 

**功能类别**: 基本功能

**布局模式**: 侧边导航 + 内容区（表格/列表导向）

**主要操作**:
  - 搜索用户 (Filled Button)
  - 查看用户详情 (Outlined Button)
  - 封禁/解禁用户 (Outlined Button)

**关键状态设计**:
  - 空态: 插图 + 引导文案 + CTA 按钮
  - 加载中: 骨架屏 (shimmer)
  - 错误: Snackbar (错误色) + 重试按钮
  - 成功: Snackbar (成功色) / 页面跳转

#### 订阅与退款管理页（S032）[professional]

**界面目的**: 

**功能类别**: 基本功能

**布局模式**: 侧边导航 + 内容区（表格/列表导向）

**主要操作**:
  - 查看订阅列表 (Outlined Button)
  - 处理退款申请 (Outlined Button)

**关键状态设计**:
  - 空态: 插图 + 引导文案 + CTA 按钮
  - 加载中: 骨架屏 (shimmer)
  - 错误: Snackbar (错误色) + 重试按钮
  - 成功: Snackbar (成功色) / 页面跳转

#### 系统配置页（S033）[professional]

**界面目的**: 

**功能类别**: 基本功能

**布局模式**: 侧边导航 + 内容区（表格/列表导向）

**主要操作**:
  - 查看系统参数 (Outlined Button)
  - 修改参数值 (Outlined Button)

**关键状态设计**:
  - 空态: 插图 + 引导文案 + CTA 按钮
  - 加载中: 骨架屏 (shimmer)
  - 错误: Snackbar (错误色) + 重试按钮
  - 成功: Snackbar (成功色) / 页面跳转

#### 权限角色管理页（S034）[professional]

**界面目的**: 

**功能类别**: 基本功能

**布局模式**: 侧边导航 + 内容区（表格/列表导向）

**主要操作**:
  - 查看角色列表 (Outlined Button)
  - 创建/编辑角色权限 (Outlined Button)
  - 分配用户角色 (Outlined Button)

**关键状态设计**:
  - 空态: 插图 + 引导文案 + CTA 按钮
  - 加载中: 骨架屏 (shimmer)
  - 错误: Snackbar (错误色) + 重试按钮
  - 成功: Snackbar (成功色) / 页面跳转

#### 投诉处理页（S035）[professional]

**界面目的**: 

**功能类别**: 基本功能

**布局模式**: 侧边导航 + 内容区（表格/列表导向）

**主要操作**:
  - 查看投诉列表 (Outlined Button)
  - 处理投诉 (Outlined Button)
  - 回复用户 (Outlined Button)

**关键状态设计**:
  - 空态: 插图 + 引导文案 + CTA 按钮
  - 加载中: 骨架屏 (shimmer)
  - 错误: Snackbar (错误色) + 重试按钮
  - 成功: Snackbar (成功色) / 页面跳转

### 模块: 注册登录与个人设置

#### 注册页（S036）[consumer]

**界面目的**: 

**功能类别**: 基本功能

**布局模式**: 单列卡片流

**主要操作**:
  - 手机号/邮箱注册 (Outlined Button)
  - 第三方登录注册 (Outlined Button)

**关键状态设计**:
  - 空态: 插图 + 引导文案 + CTA 按钮
  - 加载中: 骨架屏 (shimmer)
  - 错误: Snackbar (错误色) + 重试按钮
  - 成功: Snackbar (成功色) / 页面跳转

#### 登录页（S037）[consumer]

**界面目的**: 

**功能类别**: 基本功能

**布局模式**: 单列卡片流

**主要操作**:
  - 账号密码登录 (Filled Button)
  - 第三方快捷登录 (Filled Button)
  - 验证码登录 (Filled Button)

**关键状态设计**:
  - 空态: 插图 + 引导文案 + CTA 按钮
  - 加载中: 骨架屏 (shimmer)
  - 错误: Snackbar (错误色) + 重试按钮
  - 成功: Snackbar (成功色) / 页面跳转

#### 个人设置页（S038）[consumer]

**界面目的**: 

**功能类别**: 基本功能

**布局模式**: 单列卡片流

**主要操作**:
  - 修改头像/昵称 (Outlined Button)
  - 修改通知偏好 (Outlined Button)
  - 修改语言设置 (Outlined Button)

**关键状态设计**:
  - 空态: 插图 + 引导文案 + CTA 按钮
  - 加载中: 骨架屏 (shimmer)
  - 错误: Snackbar (错误色) + 重试按钮
  - 成功: Snackbar (成功色) / 页面跳转

#### 重置密码页（S039）[consumer]

**界面目的**: 

**功能类别**: 基本功能

**布局模式**: 单列卡片流

**主要操作**:
  - 输入注册邮箱/手机 (Outlined Button)
  - 输入验证码 (Outlined Button)
  - 设置新密码 (Outlined Button)

**关键状态设计**:
  - 空态: 插图 + 引导文案 + CTA 按钮
  - 加载中: 骨架屏 (shimmer)
  - 错误: Snackbar (错误色) + 重试按钮
  - 成功: Snackbar (成功色) / 页面跳转

### 模块: 首次体验

#### 新手引导页（S040）[consumer]

**界面目的**: 

**功能类别**: 基本功能

**布局模式**: 单列卡片流

**主要操作**:
  - 选择学习目的 (Outlined Button)
  - 选择当前水平 (Outlined Button)
  - 体验示范对话 (Outlined Button)

**关键状态设计**:
  - 空态: 插图 + 引导文案 + CTA 按钮
  - 加载中: 骨架屏 (shimmer)
  - 错误: Snackbar (错误色) + 重试按钮
  - 成功: Snackbar (成功色) / 页面跳转

### 模块: 推送与通知

#### 通知中心页（S041）[consumer]

**界面目的**: 

**功能类别**: 基本功能

**布局模式**: 单列卡片流

**主要操作**:
  - 查看学习提醒 (Filled Button)
  - 查看系统通知 (Outlined Button)
  - 管理通知设置 (Outlined Button)

**关键状态设计**:
  - 空态: 插图 + 引导文案 + CTA 按钮
  - 加载中: 骨架屏 (shimmer)
  - 错误: Snackbar (错误色) + 重试按钮
  - 成功: Snackbar (成功色) / 页面跳转

### 模块: 用户反馈

#### 意见反馈页（S042）[consumer]

**界面目的**: 

**功能类别**: 基本功能

**布局模式**: 单列卡片流

**主要操作**:
  - 选择反馈类型 (Outlined Button)
  - 填写反馈内容 (Outlined Button)
  - 上传截图 (Outlined Button)

**关键状态设计**:
  - 空态: 插图 + 引导文案 + CTA 按钮
  - 加载中: 骨架屏 (shimmer)
  - 错误: Snackbar (错误色) + 重试按钮
  - 成功: Snackbar (成功色) / 页面跳转

