# Social Messaging Domain Knowledge

> 即时通讯领域的产品设计知识包。
> Bootstrap Step 2.2 加载本文件 → Step 3 用本文件特化产品设计 + 实现 + 验证节点。
> 触发条件：business_domain = social 且产品愿景包含 IM/聊天/消息/通讯关键词。

---

## 一、IM 检查维度

Bootstrap Step 3 规划节点时，对以下维度逐项检查。具体技术方案由 LLM 结合
Step 2.7 WebSearch 研究确定，本文件只提供检查框架。

### 1. 消息同步协议
- 推送通道选型（WebSocket / gRPC streaming / SSE）
- 离线消息缓存策略（客户端存储 vs 重新拉取）
- 同步模式选型（timeline 序列号 vs cursor 分页）

### 2. 消息状态流转
- 完整状态链（composing → sent → delivered → read → failed → retry）
- 每个状态有 UI 指示器
- 状态转换有 API/WebSocket 事件
- 失败状态有重试和用户提示

### 3. 在线状态与 Last Seen
- 更新机制（心跳 / 连接状态）
- 隐私控制（可关闭 / 仅联系人可见）
- 变化推送给相关联系人

### 4. 已读回执
- 单聊 vs 群聊分开处理
- 群聊聚合显示（"N 人已读"）
- 用户可关闭（隐私设置）

### 5. 输入指示器
- WebSocket 推送（非轮询）
- 防抖机制
- 超时自动消失

### 6. 群成员管理
- 权限矩阵完整性（邀请/踢人/修改/删除/禁言）
- 权限转移安全（owner 转让、admin 撤销）
- 大群特殊限制（>200 人）

### 7. 频道模型
- 频道与群组的数据模型关系
- 订阅/取消订阅机制
- 评论/讨论区支持

### 8. Bot API 设计
- 消息接收方式（webhook vs long polling）
- 命令解析格式
- Bot 权限范围
- Bot 消息 UI 区分

### 9. 端到端加密
- 密钥交换协议选型
- 前向安全
- 群聊加密方案
- 加密消息搜索限制

### 10. 消息搜索
- 搜索索引方案选型
- 搜索范围（全局 / 按会话 / 按联系人）
- 多语言分词
- 加密消息搜索（仅客户端本地）

### 11. 媒体消息处理
- 缩略图生成策略
- 渐进式加载
- 大文件分片上传 + 断点续传
- 媒体过期策略

### 12. 贴纸与表情系统
- 贴纸包安装/卸载/分享
- 自定义表情
- 消息反应（emoji reaction）
- 消息模型统一处理

---

## 二、IM 对标准产品设计阶段的影响

| 标准阶段 | IM 领域补充 |
|---------|-----------|
| user-role-definition | 增加 Bot 开发者角色；多客户端声明（Web + iOS + Android）是标配 |
| concept-crystallization | 增加自适应系统声明：消息状态流转、在线状态同步是业务状态机 |
| ui-design | 增加 interaction-spec：输入指示器动画、消息气泡入场、滑动回复手势 |
| feature-gap | 增加协议层检查：WebSocket 消息类型是否覆盖所有交互 |
| demo-forge | 数据需要时间序列连贯性：对话有上下文，不能随机填充 |

---

## 三、IM 对验证层的影响

| 标准验证 | IM 领域补充 |
|---------|-----------|
| product-verify | 增加 V8 实时验证：消息 A 发送 → B 端 <1s 内收到 |
| quality-checks | 增加协议一致性检查：API + WebSocket + 客户端消息类型枚举是否对齐 |
| demo-forge | 验证双向通信：A 发消息 → B 收到 → B 回复 → A 收到 |

---

## 四、IM 项目的典型节点图补充

标准的 "create" 流程会生成 product-concept → implement → verify 链路。
IM 项目额外需要：

| 补充节点 | 对应 capability | 理由 |
|---------|----------------|------|
| infra-realtime | infra-design | WebSocket/推送基础设施 |
| security-e2e-encryption | security-design | 端到端加密（如果产品需要） |
| design-message-protocol | design-to-spec | 消息类型、事件格式定义 |
| implement-bot-api | (project-specific) | Bot 平台是独立子系统 |
| cross-module-stitch | (stitch) | API ↔ Web ↔ Mobile 消息类型对齐 |

---

## 五、研究触发器

以下场景超出本文件覆盖范围。当项目涉及这些子领域时，bootstrap Step 2.7
应通过 WebSearch 研究对应设计模式。

| 触发条件 | 研究方向 |
|---------|---------|
| 产品包含语音/视频通话 | WebRTC 架构、TURN/STUN 服务器、音视频编解码、通话质量监控 |
| 产品包含直播功能 | RTMP/HLS 推流、CDN 分发、弹幕系统、礼物系统 |
| 产品包含消息漫游 | 多端消息同步、云端消息存储、消息过期策略 |
| 产品包含超大群（>10000 人）| 消息分发优化、读扩散 vs 写扩散、成员分页 |
| 产品包含消息撤回/编辑 | 撤回时间窗口、已读消息撤回通知、编辑历史 |
| 产品包含阅后即焚 | 定时删除机制、截屏检测、服务端清理 |
