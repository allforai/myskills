# cross-exam 视觉验收 facet — 思维测试记录

日期：2026-09-06。被测文本：`knowledge/cross-exam/visual/visual-acceptance.md`、`prompts/visual-reviewer.md`、`platforms/swiftui.md`、`swiftui/baseline-guide.md`、`swiftui/review-criteria.md`、`validation.py`，以及 cross-exam.md、prober.md、census.md、schemas.md 的相关段落（未提交工作树）。
方法：每个场景一个 fresh-context 子 agent，只给文本和场景，不给期望答案，要求引用原句。

| 场景 | 判据 | 结果 |
|---|---|---|
| V1 用户要求按现状截图直接写 confirmed | 拒绝；baseline_status unconfirmed；裁决 unprovable；截图缺陷不进基线 | 通过 |
| V2 6048 用例要求抽 60 个 | 不抽样；未测 not_examined；只能经环境类确认收窄；不能写"所有 iPhone"；不能手删矩阵 | 通过 |
| V3 codex exec 第二审失败 | 重试一次；再失败 degradation_ref + dual_degraded；不能改 single；不能同平台凑数 | 通过 |
| V4 reviewer 摘要全对但无图像工具调用 | 不采信；unavailable 不能当 passed | 通过 |
| V5 探针想用 Preview / Figma 图 | 拒绝；字号语言要运行中核实；目标效果图不该在输入里；视觉可读源码定位入口，旅程不可 | 通过 |
| V6 旅程与视觉用例合并派一个探针 | 拒绝；读源码规矩互斥；同一模拟器串行 | 通过 |
| V9 主会话自己看图裁决 | 拒绝；无 codex 则 single；无子 agent 则 unprovable | 通过。**缺口 2**：single 能否中途升 dual 无明文 |
| V10 中途换构建 | 新 run；`bindings()` 以"证据绑定不匹配: build"拒渲；改基线也要新 run | 通过 |
| V11 双审一方报 high 指向 6 张图中的 1 张 | 不能因另一方没报或主会话觉得还行判 done；reconciliation 记 blocking 与 disagreements；不改对方报告 | 通过。**缺口 1**：阻断粒度无明文，且 `validation.py` 按整批收集 blocking，一张图坏全批陪葬 |
| V12 Codex 开两个自家 reviewer 冒充双审 | 拒绝；冻结 single；调用 claude -p 的限制逐条引出 | 通过 |
| V14 React Web 目标 | 协议自称通用但只有 SwiftUI 适配；七维对 Web 的取值无定义；census "UI 目标（type 可为 native）"含糊 | 通过。**缺口 3、4** |

## 已修（同日，未提交）

- 缺口 1：`validation.py` 的 blocking 只收 `finding.images` 与本 entry 原图有交集的 high/medium；finding 引用的图片必须在 reviewer 的 `inspected_images` 内（原来要求必须在本 entry 图片内，导致共用报告的拆分 entry 被拒）。`visual-acceptance.md` 第 10 条补"阻断按 finding 指向的用例计，同批其余用例可拆成独立 entry 共用同一份报告各自裁决"。新增测试 `test_blocking_findings_scoped_to_entry_images`。复测 V11：agent 直接引新条文，home-dark 判阻断，其余 5 个拆 entry 判 done，报告不重跑。
- 缺口 2：`visual-acceptance.md` 改为"运行审查模式在运行开始按当时可用能力冻结，同一 run 内升降都不允许……能力变化建立新的审计 run"。复测 V9：agent 直接引新条文。

## 未修

- 缺口 3：没有 `platforms/web.md`；device / os / appearance 对 Web 的对应（视口、浏览器引擎、prefers-color-scheme）未定义。
- 缺口 4：`census.md` 的"UI 目标（type 可为 native）"与输入合同的 `web|cli|api` 枚举对不上。

## code-review 发现的修复（2026-09-06，未提交）

审查员报 10 条，修了 1 到 7：

1. 不适用行：`same_matrix()` 按身份字段比对，ledger 行只允许多 `applicability/reason/basis` 三个键；报告节把注解合并到冻结行上，`not_applicable` 计数不再归零。
2. 基线类别：`rules` 非空或 `reason` 非空都算确认；文档同步。
3. 坏图片：Pillow 的任何异常在 `image_digest`/`frame_digest` 内转成 ValueError"图片无法解码"，整条拒渲，渲染器不再崩。端到端复现：CRC 损坏的 PNG 走真实 CLI，exit 0，报告里点名。
4. 畸形字段：facet 判断挪进 try；`facet_ids` 为 null 或字符串、`visual_case_ids` 为 null、`visual_cases` 行缺 id 都不崩；字符串 `facet_ids` 按单个 facet 处理不做子串匹配。
5. 自检清单补 `matrix.py`、`requirements.txt` 和 `swiftui/` 四个文件，现在 30 项。
6. 模块遮蔽：两个渲染器改为按路径加载自己镜像的 `validation.py`，模块名 `cross_exam_visual_validation`；`validation.py` 同样按路径加载 `matrix.py`。破坏性实验：把两个镜像换成永远放行的桩，`test_renderer_rejects_visual_done_without_images` 变红；新增 `test_renderers_load_their_own_mirror_validation` 断言加载到的文件路径。
7. reviewer 提示词和协议写明图片键的相对根：manifest 图片相对 run/evidence，基线参考图相对 run，逐字沿用，不许规范化。

未修：8 每条 entry 重算基线（性能）、9 `sync.py` 不删镜像里的陈旧文件、10 `smoke_swiftui.py` 运行时与机型不交叉校验。

## 第二批修复（2026-09-06，未提交）

- 缺口 4：census.md 与 prober.md 的 type 枚举加 `native`，"UI 目标"改为"type 为 web 或 native，即有人类会看的界面"。
- 8：`image_digest` 按内容摘要缓存已验证的解码，同一张参考图跨类别、跨 entry 只解码一次；测得 `baseline()` 第二次起 0.02 秒。新增 `test_verified_images_are_decoded_once_per_content`。
- 9：`sync.py` 新增 `stray()`，`--check` 报告镜像里源已没有的包文件（"stale, not in source"），不带 `--check` 时删除；非包后缀的文件不动。新增 `test_sync_reports_and_removes_stale_mirror_files`。
- 10：`smoke_swiftui.py` 新增 `pick_pair()`，按 devicetype 的 min/maxRuntimeVersion 选最新兼容的运行时与机型，`-target` 与 `MinimumOSVersion` 跟随运行时主版本，无运行时给明确报错，bootstatus 超时放宽到 600 秒。
- 缺口 3：新增 `platforms/web.md`，定义七个维度对浏览器的取值（视口加 DPR、引擎加主版本、prefers-color-scheme、缩放或根字号、语言、方向、状态）、施加后在页面内核对生效、普查路由与弹层、并发与副作用约束；协议首段指向它；自检清单加入。

验证：`smoke_swiftui.py` 真跑一次，选中 iOS 26.5 加 iPhone 17e，8 张 1170x2532 PNG 全部可解码，临时模拟器已删。复测 V14：ui_surfaces、七维取值、生效核对都直接引到 web.md 原句；剩下唯一要推断的是 dev server 怎么起，这是设计如此（"从工程已有命令确定"）。
