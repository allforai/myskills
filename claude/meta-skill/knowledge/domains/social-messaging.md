# Social Messaging Domain Knowledge

> 即时通讯领域的产品设计知识包。
> Bootstrap Step 2.2 加载本文件 → Step 3 用本文件特化产品设计 + 实现 + 验证节点。
> 触发条件：business_domain = social 且产品愿景包含 IM/聊天/消息/通讯关键词。

---

## 一、IM 特有的设计模式

标准产品设计覆盖通用功能（CRUD、角色、旅程），但 IM 有独特的技术和产品模式，
需要专项引导。以下每个模式包含三部分：what（是什么）、why（为什么 IM 需要）、
check（bootstrap 检查项）。

### 1. 消息同步协议

**What:** 客户端如何获取新消息。两种主流方案：
- Timeline-based sync：服务端维护全局递增序列号，客户端同步到最新序列号
- Cursor-based pagination：按时间戳或消息 ID 分页拉取

**Why:** IM 的核心体验是"发出的消息对方立即看到"。同步协议决定延迟和可靠性。

**Check:**
- 产品概念中有"聊天"/"消息"功能 → workflow 必须包含 realtime infra 节点
- 选择 WebSocket/gRPC streaming/SSE 之一作为推送通道
- 定义离线消息缓存策略（客户端存储 vs 每次重新拉取）

### 2. 消息状态流转

**What:** 消息从发送到已读的状态机：
```
composing → sent → delivered → read
              ↓
           failed → retry
```

**Why:** 用户需要知道消息是否送达、对方是否已读。状态不全 = 用户焦虑。

**Check:**
- 每个状态有对应的 UI 指示器（✓ sent / ✓✓ delivered / 蓝色✓✓ read）
- 状态转换有对应的 API/WebSocket 事件
- 失败状态有重试机制和用户可见的错误提示

### 3. 在线状态与 Last Seen

**What:** 实时显示联系人是否在线，离线时显示最后活跃时间。

**Why:** 在线状态影响用户是否选择发消息。也是"社交存在感"的核心指标。

**Check:**
- 在线状态有更新机制（心跳/WebSocket 连接状态）
- Last seen 有隐私控制（可关闭/只对联系人可见）
- 状态变化有推送给相关联系人的机制

### 4. 已读回执

**What:** 通知发送者消息已被阅读。单聊直接标记，群聊需要聚合（3 人已读）。

**Why:** 已读回执是 IM 的差异化特性（WhatsApp 蓝勾 vs 微信无已读）。

**Check:**
- 单聊和群聊的已读逻辑是否分开处理
- 群聊已读是否有聚合显示（"5 人已读" 而非逐个列出）
- 用户是否可以关闭已读回执（隐私设置）

### 5. 输入指示器

**What:** 显示对方"正在输入..."的实时状态。

**Why:** 减少等待焦虑，增加对话的"在场感"。

**Check:**
- 输入事件通过 WebSocket 推送，不是轮询
- 有防抖机制（不是每次按键都发事件）
- 超时自动消失（对方停止输入 N 秒后隐藏）

### 6. 群成员管理

**What:** 群组的角色层级和权限矩阵：
```
owner → admin → member → restricted
  ↑        ↑        ↑
  全部权限   管理成员   只能发消息
```

**Why:** 群组越大，管理复杂度越高。权限不清 = 混乱。

**Check:**
- 权限矩阵是否完整（谁能邀请/踢人/修改信息/删除消息/禁言）
- 权限转移是否安全（owner 转让、admin 撤销）
- 大群（>200 人）是否有特殊限制（禁止全员 @、限制发送频率）

### 7. 频道模型

**What:** 单向广播频道 vs 可讨论频道（Telegram 模式）。

**Why:** 频道是 IM 从"通讯工具"变成"信息平台"的关键功能。

**Check:**
- 频道与群组在数据模型上是否分离（不同实体 vs 同一实体 + type 字段）
- 订阅/取消订阅的机制
- 频道消息与私聊消息是否共享消息模型
- 频道是否支持评论/讨论区（关联群组模式）

### 8. Bot API 设计

**What:** 允许第三方开发者创建自动化 Bot 的 API 体系。

**Why:** Bot 生态是 Telegram 的核心竞争力。Bot API 设计影响生态活跃度。

**Check:**
- Bot 接收消息的方式（webhook vs long polling）
- 命令解析格式（/command@botname 模式）
- Bot 权限范围（能读什么/能做什么）
- Bot 消息与普通消息在 UI 上的区分

### 9. 端到端加密

**What:** 消息在发送端加密、接收端解密，服务器无法读取明文。

**Why:** 隐私保护。Telegram Secret Chat / Signal / WhatsApp 的核心卖点。

**Check:**
- 密钥交换协议（Diffie-Hellman / X3DH）
- 前向安全（每条消息用不同密钥，历史不可回溯）
- 群聊加密方案（MLS / Sender Keys）
- 加密消息的搜索限制（服务端无法索引加密内容）

### 10. 消息搜索

**What:** 按关键词、发送者、日期、媒体类型搜索历史消息。

**Why:** IM 消息量巨大，搜索是查找信息的关键手段。

**Check:**
- 搜索索引方案（全文搜索引擎 vs DB LIKE）
- 搜索范围（全局 / 按会话 / 按联系人）
- 多语言分词支持
- 加密消息是否可搜索（仅客户端本地搜索）

### 11. 媒体消息处理

**What:** 图片/视频/音频/文件的发送、存储、展示。

**Why:** 现代 IM 中媒体消息占比 >50%。处理不好 = 卡顿、流量浪费。

**Check:**
- 缩略图生成（服务端生成，客户端直接展示小图）
- 渐进式加载（先模糊图再清晰图）
- 大文件上传（分片上传、断点续传）
- 媒体过期策略（是否永久存储、容量限制）

### 12. 贴纸与表情系统

**What:** 贴纸包管理、自定义表情、Emoji 反应。

**Why:** 贴纸是 IM 的情感表达工具，也是商业化渠道。

**Check:**
- 贴纸包的安装/卸载/分享机制
- 自定义表情（用户上传的小图作为 emoji）
- 消息反应（对消息添加 emoji 反应而非回复）
- 贴纸消息与文本消息在消息模型中的统一处理

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
