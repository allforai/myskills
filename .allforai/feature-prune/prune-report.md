# 功能剪枝报告

策略: aggressive

## 总览

| 分类 | 数量 |
|------|------|
| CORE（必须保留）| 14 |
| DEFER（推迟）| 29 |
| CUT（移除）| 2 |

## CUT 清单

| 任务 | 频次 | 场景 | 理由 |
|------|------|------|------|
| 分享学习成果 | 低 | 频次=低；场景=secondary；复杂度匹配=over_engineered； | 频次=低；场景=secondary；复杂度匹配=over_engineered；风险=低；类别=core；策略=aggressive |
| 设置角色偏好 | 低 | 频次=低；场景=secondary；复杂度匹配=over_engineered； | 频次=低；场景=secondary；复杂度匹配=over_engineered；风险=低；类别=core；策略=aggressive |

## DEFER 清单

| 任务 | 频次 | 理由 | 建议重评时间 |
|------|------|------|-------------|
| 进行自由对话 | 中 | 频次=中；场景=secondary；复杂度匹配=match；风险=中；类别=core；策略=aggressive | 3个月后 |
| 查看发音详细报告 | 中 | 频次=中；场景=secondary；复杂度匹配=match；风险=低；类别=core；策略=aggressive | 3个月后 |
| 管理词汇本 | 中 | 频次=中；场景=secondary；复杂度匹配=match；风险=低；类别=core；被业务流引用；策略=aggressive | 3个月后 |
| 管理场景包 | 中 | 频次=中；场景=secondary；复杂度匹配=match；风险=低；类别=core；被业务流引用；策略=aggressive | 3个月后 |
| 管理场景标签 | 中 | 频次=中；场景=secondary；复杂度匹配=match；风险=低；类别=core；策略=aggressive | 3个月后 |
| 查看排行榜 | 中 | 频次=中；场景=secondary；复杂度匹配=match；风险=低；类别=core；策略=aggressive | 3个月后 |
| 兑换积分商品 | 中 | 频次=中；场景=secondary；复杂度匹配=match；风险=低；类别=core；策略=aggressive | 3个月后 |
| 查看个人学习档案 | 中 | 频次=中；场景=secondary；复杂度匹配=match；风险=低；类别=core；策略=aggressive | 3个月后 |
| 查看学习统计报告 | 中 | 频次=中；场景=secondary；复杂度匹配=match；风险=低；类别=core；策略=aggressive | 3个月后 |
| 使用紧急场景速学 | 中 | 频次=中；场景=secondary；复杂度匹配=match；风险=中；类别=core；被业务流引用；策略=aggressive | 3个月后 |
| 订阅付费方案 | 低 | 频次=低；场景=secondary；复杂度匹配=over_engineered；风险=高；类别=basic；被业务流引用；护栏保护(basic基本功能+risk=高+营收相关+rules=2,exceptions=2)；策略=aggressive | 3个月后 |
| 管理订阅 | 低 | 频次=低；场景=secondary；复杂度匹配=over_engineered；风险=低；类别=basic；被业务流引用；护栏保护(basic基本功能+营收相关+rules=0,exceptions=1)；策略=aggressive | 3个月后 |
| 购买场景包 | 低 | 频次=低；场景=secondary；复杂度匹配=over_engineered；风险=中；类别=basic；护栏保护(basic基本功能+risk=中+营收相关+rules=0,exceptions=1)；策略=aggressive | 3个月后 |
| 分析用户行为 | 中 | 频次=中；场景=secondary；复杂度匹配=match；风险=低；类别=core；被业务流引用；策略=aggressive | 3个月后 |
| 管理A/B测试 | 中 | 频次=中；场景=secondary；复杂度匹配=match；风险=中；类别=core；被业务流引用；策略=aggressive | 3个月后 |
| 生成运营报告 | 中 | 频次=中；场景=secondary；复杂度匹配=match；风险=低；类别=core；被业务流引用；策略=aggressive | 3个月后 |
| 标注异常对话 | 中 | 频次=中；场景=secondary；复杂度匹配=match；风险=中；类别=core；被业务流引用；策略=aggressive | 3个月后 |
| 管理Prompt模板 | 中 | 频次=中；场景=secondary；复杂度匹配=match；风险=中；类别=core；被业务流引用；策略=aggressive | 3个月后 |
| 调整发音评估参数 | 低 | 频次=低；场景=secondary；复杂度匹配=over_engineered；风险=中；类别=core；被业务流引用；护栏保护(risk=中)；策略=aggressive | 3个月后 |
| 处理订阅与退款 | 中 | 频次=中；场景=secondary；复杂度匹配=match；风险=高；类别=basic；策略=aggressive | 3个月后 |
| 配置系统参数 | 低 | 频次=低；场景=secondary；复杂度匹配=over_engineered；风险=高；类别=basic；护栏保护(basic基本功能+risk=高+rules=1,exceptions=1)；策略=aggressive | 3个月后 |
| 管理权限角色 | 低 | 频次=低；场景=secondary；复杂度匹配=over_engineered；风险=中；类别=basic；护栏保护(basic基本功能+risk=中)；策略=aggressive | 3个月后 |
| 处理用户投诉 | 中 | 频次=中；场景=secondary；复杂度匹配=match；风险=中；类别=basic；被业务流引用；策略=aggressive | 3个月后 |
| 注册账户 | 低 | 频次=低；场景=secondary；复杂度匹配=over_engineered；风险=中；类别=basic；被业务流引用；护栏保护(basic基本功能+risk=中+rules=2,exceptions=1)；策略=aggressive | 3个月后 |
| 管理个人设置 | 低 | 频次=低；场景=secondary；复杂度匹配=over_engineered；风险=低；类别=basic；护栏保护(basic基本功能)；策略=aggressive | 3个月后 |
| 重置密码 | 低 | 频次=低；场景=secondary；复杂度匹配=over_engineered；风险=中；类别=basic；护栏保护(basic基本功能+risk=中+rules=2,exceptions=0)；策略=aggressive | 3个月后 |
| 注销账户 | 低 | 频次=低；场景=secondary；复杂度匹配=over_engineered；风险=高；类别=basic；护栏保护(basic基本功能+risk=高+rules=2,exceptions=1)；策略=aggressive | 3个月后 |
| 完成新手引导 | 低 | 频次=低；场景=secondary；复杂度匹配=over_engineered；风险=低；类别=basic；被业务流引用；护栏保护(basic基本功能)；策略=aggressive | 3个月后 |
| 提交意见反馈 | 低 | 频次=低；场景=secondary；复杂度匹配=over_engineered；风险=低；类别=basic；被业务流引用；护栏保护(basic基本功能)；策略=aggressive | 3个月后 |

## CORE 清单

| 任务 | 频次 | 理由 |
|------|------|------|
| 浏览并选择场景 | 高 | 高频受保护（frequency=高）— 策略=aggressive |
| 进行场景对话 | 高 | 高频受保护（frequency=高）— 策略=aggressive |
| 查看对话报告 | 高 | 高频受保护（frequency=高）— 策略=aggressive |
| 查看实时发音纠正 | 高 | 高频受保护（frequency=高）— 策略=aggressive |
| 完成记忆曲线复习 | 高 | 高频受保护（frequency=高）— 策略=aggressive |
| 创建场景对话脚本 | 高 | 高频受保护（frequency=高）— 策略=aggressive |
| 审核场景内容 | 高 | 高频受保护（frequency=高）— 策略=aggressive |
| 查看学习连胜与成就 | 高 | 高频受保护（frequency=高）— 策略=aggressive |
| 查看个性化推荐 | 高 | 高频受保护（frequency=高）— 策略=aggressive |
| 查看关键指标看板 | 高 | 高频受保护（frequency=高）— 策略=aggressive |
| 查看AI对话质量评分 | 高 | 高频受保护（frequency=高）— 策略=aggressive |
| 管理用户账户 | 高 | 高频受保护（frequency=高）— 策略=aggressive |
| 登录账户 | 高 | 高频受保护（frequency=高）— 策略=aggressive |
| 管理通知中心 | 中 | 频次=中；场景=core；复杂度匹配=match；风险=低；类别=basic；策略=aggressive |
