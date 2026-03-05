# Demo Forge 设计：独立插件 + 三阶段 + 富媒体管线

日期: 2026-03-05

## 背景

当前 seed-forge 是 dev-forge 内的单文件 skill（661 行），是一份"设计规范"而非"生成系统"。核心差距：
- 无生成引擎，纯靠 LLM 上下文生成
- 图片/视频管线完全手动
- 派生数据一致性无法保证
- 数据量级受上下文窗口限制
- 不支持迭代提升质量

重新定位：不再是"种子数据灌入"，而是**锻造一个可以拿去演示的产品状态**——数据+图片+视频+验证+多轮打磨。

## 决策记录

| 决策 | 选择 | 理由 |
|------|------|------|
| 插件名称 | `demo-forge-skill/`（演示锻造） | 目标已超越种子数据，是完整的产品演示准备 |
| 插件归属 | 独立插件 | 体量够大（4 skill），可独立使用，类似 code-replicate 先例 |
| 富媒体处理 | 独立 skill `media-forge` | 用户明确要求单列；有独立使用价值 |
| 媒体搜索工具 | Brave Search MCP 优先，WebSearch 降级 | Brave 有专门图片/视频搜索，WebSearch 作为降级保底 |
| AI 生图/生视频 | Google Vertex AI（Imagen 3 + Veo 2），API Key 方式 | 一个 Key 覆盖生图+生视频+TTS，和其他 Key 配置方式一致 |
| 媒体存储 | 全部本地化 + 应用上传 API | 禁止外部链接，数据库只存服务端地址 |
| 媒体采集策略 | 搜索优先，AI 生成兜底 | 真实素材 > AI 素材 > 禁止占位符 |
| 素材后处理 | 按需加工（超分/裁剪/转码） | 保证分辨率和格式达标 |
| 质量迭代 | 最多 3 轮自动 Design->Media->Execute->Verify | 验证路由问题到对应阶段 |
| 代码问题路由 | verify 发现代码 bug -> 生成 dev-forge 修复任务 | 数据问题内部闭环，代码问题交还 dev-forge |
| Brave Key 配置 | 扩展 product-design setup-openrouter -> setup-services | 一站式配置所有 API Key |

---

## 插件结构

```
demo-forge-skill/
├── .claude-plugin/
│   └── plugin.json
├── SKILL.md                        # 插件入口
├── skills/
│   ├── demo-design.md              # 阶段一：设计
│   ├── demo-execute.md             # 阶段二：执行
│   ├── demo-verify.md              # 阶段三：验证
│   └── media-forge.md              # 独立：富媒体管线
├── commands/
│   ├── demo-forge.md               # 主编排命令
│   └── df-status.md                # 查看进度
└── docs/
    └── media-processing.md         # 素材加工参考
```

---

## 数据合约

```
.allforai/demo-forge/
├── model-mapping.json          # Design: 代码实体 <-> product-map 映射
├── api-gaps.json               # Design: API 缺口报告
├── demo-plan.json              # Design: 演示数据方案
├── style-profile.json          # Design: 行业风格 + 文本模板
│
├── assets/                     # Media: 本地素材（零外链）
│   ├── avatars/
│   ├── covers/
│   ├── details/
│   ├── banners/
│   └── videos/
├── assets-manifest.json        # Media: 素材清单 + 验收状态
├── upload-mapping.json         # Media: 本地路径 -> 服务端 URL/ID
│
├── forge-data-draft.json       # Execute: 生成的完整数据集（临时 ID）
├── forge-data.json             # Execute: 已灌入数据（真实 ID）
├── forge-log.json              # Execute: 灌入日志
│
├── verify-report.json          # Verify: 验证报告（全量）
├── verify-issues.json          # Verify: 未通过项 + 路由目标
├── screenshots/                # Verify: 验证截图
│
└── round-history.json          # Orchestrator: 多轮迭代记录
```

---

## 阶段一：demo-design（设计）

### 职责

从 product-map 蓝本推导"该生成什么数据、多少条、怎么关联"。纯规划不执行。

### 工作流

```
Step 0: 数据模型映射
  代码实体 <-> product-map 任务/角色
  检测 API 缺口
  -> model-mapping.json, api-gaps.json

Step 1: 演示数据方案设计
  1-A 角色 -> 用户账号（含统一登录凭据）
  1-B 频次 -> 数据量（帕累托: 高70% 中20% 低10%）
  1-C 场景+业务流 -> 数据链路
  1-C-2 灌入方式标注（api / db）
  1-D 约束规则（constraints + task.rules + task.exceptions）
  1-E 枚举全覆盖检查（含终态/异常态）
  1-F 时间分布（近密远疏/工作时间/月度波动）
  1-G 用户行为模式（幂律分布）
  1-H 数据历史深度（90天回溯）
  1-M 媒体字段标注（新增）
  -> demo-plan.json

Step 2: 行业风格与文本模板
  名称/金额/分类风格 + 地区格式 + 文本模板
  -> style-profile.json

Step 2.5: 文本多样性增强（OpenRouter 可选）
  -> 合并到 style-profile.json
```

### Step 1-M 媒体字段标注

遍历所有实体，为每个需要媒体的字段生成清单：

```json
{
  "entity": "Product",
  "field": "cover_image",
  "media_type": "image",
  "purpose": "商品封面",
  "dimensions": "800x800",
  "aspect_ratio": "1:1",
  "count": 80,
  "search_keywords": ["家居用品", "厨房电器"],
  "style_notes": "白底产品图，电商风格",
  "upload_endpoint": "POST /api/upload/image",
  "ref_field": "cover_image_id"
}
```

媒体类型覆盖：

| media_type | 典型场景 | 采集策略 |
|-----------|---------|---------|
| image | 头像、封面、详情图、Banner | Brave 搜索 -> WebSearch 降级 -> Imagen 3 兜底 |
| video | 产品视频、教程、宣传片 | Brave 视频搜索 -> WebSearch 降级 -> Veo 2 / Playwright 录屏兜底 |
| document | PDF 附件、合同扫描件 | 模板填充生成 |
| audio | 语音消息、音频课程 | Google Cloud TTS |

### 重入模式

verify-issues.json 中 route_to="design" 的项 -> 增量修改 demo-plan.json 对应部分，不全量重做。

---

## 阶段独立：media-forge（富媒体管线）

### 定位

独立可运行的富媒体采集->本地化->加工->上传管线。可被 demo-forge 编排调用，也可单独使用。

### 铁律

1. 所有素材必须下载到本地 assets/，零外链
2. 灌入时必须走应用上传 API，数据库只存服务端地址
3. Brave 搜索优先，WebSearch 降级，AI 生成兜底，禁止占位符
4. upload-mapping.json 中 external_url_count 必须为 0（硬校验）

### 工作流

```
M1: 需求盘点
  读 demo-plan.json Step 1-M 媒体字段标注
  汇总需求量，按用途分组确定搜索策略
  -> 不停

M2: 搜索采集（主力）
  优先级:
    1. Brave Search MCP（brave_web_search / brave_image_search / brave_video_search）
    2. Brave 不可用或配额耗尽 -> WebSearch 降级
  关键词从 1-M 的 search_keywords + style_notes 组合
  同组素材用同一组关键词，保证风格一致
  解析结果 -> 下载原图/原视频到 assets/{类别}/
  -> 「M2 搜索采集 done/total，缺口 {gap}」

M3: AI 生成补缺（仅对 M2 未满足的缺口）
  使用 Google Vertex AI（GOOGLE_API_KEY）:
    图片 -> Imagen 3（imagen-3.0-generate-002）
    视频 -> Veo 2（veo-2.0-generate-exp）
    音频 -> Google Cloud TTS
  其他:
    产品操作演示 -> Playwright 录屏（免费，最真实）
    文档 -> PDF 模板填充
  Google AI 不可用 -> 降级到 DALL-E / 本地 Stable Diffusion
  -> 「M3 AI 生成 {N} 项补缺完成」

M3.5: 素材加工（按需）
  质量不达标的素材二次处理:
    分辨率不足 -> AI 超分辨率（Real-ESRGAN / upscale API）
    宽高比不匹配 -> 智能裁剪（保留主体）
    文件过大 -> 压缩（WebP 转换 / 质量调整）
    格式不对 -> 转换（PNG->WebP, MOV->MP4）
    视频过长 -> 裁剪关键片段
    风格不一致 -> 色调/亮度统一调整
  工具:
    图片: sharp / ImageMagick / ffmpeg（本地）
    视频: ffmpeg（裁剪/转码/压缩）
    超分: Real-ESRGAN CLI / upscale API
  -> 加工后覆盖原文件，更新 manifest 尺寸信息

M4: 质量验收
  逐项检查:
    □ 分辨率 >= UI 渲染尺寸 2 倍（Retina）
    □ 宽高比与目标容器匹配
    □ 文件大小合规（图片 <= 2MB，头像 <= 200KB）
    □ 同组素材风格一致
    □ 相邻记录无重复素材
    □ 无水印、无版权标记残留
    □ AI 生成图无明显瑕疵
    □ 视频可播放、时长合理、无黑屏
  不合格 -> 标记 rejected，回 M2/M3/M3.5 补采或再加工
  -> assets-manifest.json

M5: 上传到应用服务器
  读 demo-plan.json 中每个媒体字段的 upload_endpoint
  逐项: 调用上传 API -> 解析响应拿 server_url/server_id -> 写入 mapping
  失败: 重试 2 次，仍失败标记 UPLOAD_FAILED
  端点不存在: 标记 API_GAP
  -> upload-mapping.json

M6: 完整性确认
  □ 所有 verified=true 素材都有 upload-mapping 条目
  □ 无 UPLOAD_FAILED 残留
  □ upload-mapping 中无外部 URL（强制校验）
  -> 汇总完成
```

### assets-manifest.json 结构

```json
{
  "assets": [
    {
      "asset_id": "IMG-001",
      "target_entity": "Product",
      "target_field": "cover_image",
      "media_type": "image",
      "source": "brave_search | websearch | ai_generated",
      "source_url": "https://...",
      "local_path": "assets/covers/IMG-001.webp",
      "original_format": "jpeg",
      "dimensions": "1600x1600",
      "file_size_kb": 234,
      "aspect_ratio": "1:1",
      "processing_applied": ["upscale_2x", "webp_convert"],
      "quality_check": {
        "resolution_ok": true,
        "aspect_ratio_ok": true,
        "size_ok": true,
        "style_consistent": true,
        "no_watermark": true
      },
      "verified": true
    }
  ],
  "summary": {
    "total_needed": 156,
    "search_fulfilled": 130,
    "ai_generated": 18,
    "processed": 42,
    "rejected": 4,
    "verified": 152
  }
}
```

### upload-mapping.json 结构

```json
{
  "mappings": [
    {
      "asset_id": "IMG-001",
      "local_path": "assets/covers/IMG-001.webp",
      "upload_endpoint": "POST /api/upload/image",
      "server_url": "/uploads/2024/03/abc123.webp",
      "server_id": "file_abc123",
      "uploaded_at": "ISO8601",
      "status": "success"
    }
  ],
  "validation": {
    "external_url_count": 0,
    "all_local": true
  }
}
```

### 重入模式

verify-issues.json 中 route_to="media" 的项 -> 按问题类型回到 M2/M3/M3.5/M5，只处理问题项。

---

## 阶段二：demo-execute（执行）

### 职责

消费 demo-plan + style-profile + upload-mapping，生成具体数据并灌入。

### 关键设计

- 媒体字段直接从 upload-mapping.json 读服务端地址
- 派生数据由确定性计算保证（SUM/COUNT），不靠 LLM
- 时间/行为分布由加权采样实现

### 工作流

```
E1: 数据生成
  按场景链路逐条生成:
    文本 -> style-profile 模板随机选取，相邻不重复
    数值 -> 约束范围 + 边界值
    时间 -> 加权采样（近密远疏 + 工作时间 + 月度波动）
    状态 -> 按枚举覆盖分配
    媒体 -> upload-mapping 的 server_url/server_id
    外键 -> 链路依赖自动关联
    派生 -> 数学计算（汇总=明细之和）
  行为分布: 10%重度->50%数据, 30%普通->35%, 60%轻度->15%
  -> forge-data-draft.json

E2: 灌入前自检
  □ 实体完整性（无零记录）
  □ 枚举覆盖（含终态/异常态）
  □ 外键完整性
  □ 派生一致性
  □ 时间逻辑（created < updated，父早于子）
  □ 媒体关联（全部来自 upload-mapping）
  □ 行为分布（重度 ~ 50%）
  □ 文本去重
  数学类问题自动修正，其他标记 PREFLIGHT_ISSUE

E3: 数据灌入
  按场景链路顺序（非字母序）:
    1. DB: 配置表、字典表、API_GAP 实体
    2. API: 用户账号
    3. 混合: 按场景优先级，每场景内父->子->关联
  失败: 独立失败继续，父失败跳过整条链路（CHAIN_FAILED）
  -> forge-data.json, forge-log.json

E4: 派生数据修正
  DB 直写跳过业务逻辑，手动补:
    聚合字段: SELECT SUM -> UPDATE
    计数字段: SELECT COUNT -> UPDATE
    余额/库存: 按流水计算
    搜索索引: 触发 reindex
```

### forge-data-draft.json vs forge-data.json

| 文件 | 阶段 | ID 类型 |
|------|------|---------|
| forge-data-draft.json | E1 生成后 | 临时占位（TEMP-001） |
| forge-data.json | E3 灌入后 | 真实服务端 ID |

draft 保留，clean 后可重灌不必重新生成。

### Clean 模式

```
读 forge-data.json -> 按灌入逆序 DELETE:
  子实体 -> 父实体 -> 用户账号 -> 配置表
统一走 DB DELETE
清空 forge-data.json, forge-log.json
保留 demo-plan, style-profile, assets/, upload-mapping（方案+素材不删）
```

### 重入模式

verify-issues.json 中 route_to="execute" -> 补灌缺失记录、重试 CHAIN_FAILED、重跑 E4 派生修正。

---

## 阶段三：demo-verify（验证）

### 职责

打开产品逐项确认功能正确性 + 视觉正确性。产出结构化问题清单，按类型路由回对应阶段或 dev-forge。

### 工作流

```
V1: 登录验证
  每个角色账号: 能登录 + 看到正确权限数据
  工具: Playwright 自动登录 + 截图

V2: 列表页验证
  □ 有数据且数量合理
  □ 排序正确
  □ 分页可用
  □ 图片正常显示
  □ 无占位文本残留

V3: 详情页验证
  □ 字段完整（无空/null/undefined）
  □ 关联数据正确
  □ 状态流转记录可见
  □ 媒体正常加载

V4: Dashboard / 报表验证
  □ 数字非零
  □ 趋势图有多月数据
  □ 汇总与明细一致

V5: 异常场景验证
  □ 终态记录可查看
  □ 搜索/筛选正常
  □ 边界数据不崩溃

V6: 媒体完整性验证（重点）
  □ 无 broken image
  □ 无占位图
  □ 无外部 URL（检查 DOM img[src] / video[src]）
  □ 宽高比匹配
  □ 视频可播放
  □ 同列表无重复

V7: 问题汇总 + 路由
  -> verify-report.json, verify-issues.json
```

### verify-issues.json 结构

```json
{
  "round": 1,
  "timestamp": "ISO8601",
  "summary": {
    "total_checks": 86,
    "passed": 71,
    "failed": 15,
    "pass_rate": "82.6%"
  },
  "issues": [
    {
      "id": "VI-001",
      "category": "media | data_integrity | coverage | code_bug",
      "severity": "high | medium | low",
      "description": "问题描述",
      "evidence": "screenshots/v1-round1-xxx.png",
      "route_to": "design | media | execute | dev_task | skip",
      "suggested_fix": "修复建议"
    }
  ]
}
```

### 路由规则

| 问题类型 | route_to | 处理方式 |
|---------|----------|---------|
| 数据缺失、枚举未覆盖、链路不完整 | `design` | 增量修改 demo-plan.json |
| 图片 broken、视频不播放、外链残留、占位图 | `media` | 补采/重传/再加工 |
| 外键断裂、派生不一致、灌入失败 | `execute` | 补灌/修正派生 |
| API 返回 500、前端渲染 bug、SQL 错误等代码问题 | `dev_task` | 生成修复任务写入 dev-forge tasks.md（B-FIX round） |
| 纯样式偏好（与数据无关的 UI 微调） | `skip` | 记录但不路由，属于应用开发范畴 |

`dev_task` 路由的问题会生成结构化任务追加到 `.allforai/project-forge/sub-projects/{name}/tasks.md`，格式与 dev-forge 任务一致，归入 B-FIX round。demo-forge 当轮标记该问题为 `DEFERRED_TO_DEV`，不阻塞自身迭代。

---

## 编排器（demo-forge 命令）

### 命令

```
/demo-forge              # 全流程（Design -> Media -> Execute -> Verify，自动多轮）
/demo-forge design       # 仅设计阶段
/demo-forge media        # 仅富媒体采集+加工+上传
/demo-forge execute      # 仅数据灌入
/demo-forge verify       # 仅验证
/demo-forge clean        # 清理已灌入数据
/df-status               # 查看当前轮次进度
```

### 全流程多轮迭代

```
Round 0（首轮）:
  demo-design -> media-forge -> demo-execute -> demo-verify
  pass_rate >= 95%? -> 完成
  否 ->

Round 1（修复轮）:
  读 verify-issues.json，按 route_to 分组:
    design 类  -> 重入 demo-design（增量修改 demo-plan）
    media 类   -> 重入 media-forge（补采+再加工+重传）
    execute 类 -> 重入 demo-execute（补灌+修正）
    dev_task 类 -> 生成任务写入 dev-forge，标记 DEFERRED_TO_DEV
  -> demo-verify（验证修复项 + 回归，dev_task 项跳过）
  pass_rate >= 95%（不含 DEFERRED_TO_DEV）? -> 完成
  否 ->

Round 2-3（最多 3 轮自动迭代）
  仍未通过 -> 输出剩余问题，标记已知问题
```

### round-history.json

```json
{
  "rounds": [
    {
      "round": 0,
      "started_at": "ISO8601",
      "phases_executed": ["design", "media", "execute", "verify"],
      "verify_result": {
        "total_checks": 86,
        "passed": 71,
        "failed": 15,
        "deferred_to_dev": 2,
        "pass_rate": "82.6%"
      }
    },
    {
      "round": 1,
      "started_at": "ISO8601",
      "phases_executed": ["design", "media", "execute", "verify"],
      "issues_addressed": ["VI-001", "VI-002", "VI-003"],
      "verify_result": {
        "total_checks": 86,
        "passed": 82,
        "failed": 2,
        "deferred_to_dev": 2,
        "pass_rate": "97.6%"
      }
    }
  ],
  "final_status": "passed",
  "total_rounds": 2,
  "dev_tasks_generated": 2
}
```

---

## 与 dev-forge 的集成

### Phase 4 改为提示运行 demo-forge

dev-forge project-forge.md Phase 4 改为：

```
Phase 4: 演示数据方案
  提示用户运行 /demo-forge design（plan only）
  验证 demo-plan.json 存在 -> 继续
  注: 完整灌入（media + execute + verify）在 Phase 7 代码完成后执行
```

### Phase 8+ 后追加 Demo Forge 完整执行

Phase 8 验证闭环完成后（代码已稳定），提示：

```
Phase 8 完成，代码已稳定。
建议运行 /demo-forge（完整流程）灌入演示数据并验证。
demo-forge 过程中发现的代码问题会自动生成修复任务。
```

### dev_task 回流机制

demo-verify 发现代码 bug 时：
1. 生成结构化任务（格式与 tasks.md 一致）
2. 追加到对应子项目 tasks.md 的 B-FIX round
3. 用户可运行 /task-execute 处理这些修复任务
4. 修复后重新运行 /demo-forge verify 回归验证

---

## setup-services 扩展（product-design）

扩展现有 setup-openrouter -> setup-services，一站式配置：

| 服务 | Key 格式 | 环境变量 | 用途 |
|------|---------|---------|------|
| OpenRouter | sk-or-... | OPENROUTER_API_KEY | 跨模型交叉验证（XV） |
| Brave Search | BSA... | BRAVE_API_KEY | 媒体搜索（图片/视频）+ 通用搜索增强 |
| Google AI | AIza... | GOOGLE_API_KEY | AI 生图（Imagen 3）+ 生视频（Veo 2）+ TTS |

配置流程：
1. 检测三个 Key 的当前状态
2. 缺失的逐个引导获取（OpenRouter -> Brave -> Google AI）
3. 统一写入 shell 配置文件（~/.zshrc 或 ~/.bashrc）
4. 提示重启 Claude Code

Google API Key 获取: console.cloud.google.com/apis/credentials，需先启用 Vertex AI API（`gcloud services enable aiplatform.googleapis.com`）。

Brave Search 对 product-design 自身的 WebSearch 阶段也有价值（竞品分析、行业调研），不仅服务于 media-forge。Google AI 对 product-design 的 UI 设计预览也有潜在价值。

---

## 实施顺序

1. 创建 demo-forge-skill/ 插件骨架（plugin.json + SKILL.md）
2. 编写 demo-design.md（从现有 seed-forge.md 迁移 + 新增 1-M）
3. 编写 media-forge.md（全新：Brave 搜索 + WebSearch 降级 + AI 兜底 + 加工 + 上传）
4. 编写 demo-execute.md（从现有迁移 + E1 draft + E4 派生修正）
5. 编写 demo-verify.md（全新：Playwright 验证 + 5 路由含 dev_task）
6. 编写 demo-forge.md 编排命令（多轮迭代 + dev_task 回流）
7. 编写 df-status.md 命令
8. 扩展 product-design setup-openrouter -> setup-services（加 Brave）
9. 更新 dev-forge project-forge.md Phase 4 引用 + Phase 8 后提示
10. 删除 dev-forge-skill/skills/seed-forge.md（迁移完成后）
11. 更新 CLAUDE.md 文档（新增 demo-forge 层描述）
