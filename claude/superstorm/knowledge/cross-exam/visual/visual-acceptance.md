# Visual acceptance — 可选视觉验收 facet

本文件所在目录记为 VISUAL_ROOT。仅用户选择视觉 facet 后加载。协议通用；SwiftUI 再读 swiftui/baseline-guide.md、review-criteria.md、brand-spec-template.md 和 platforms/swiftui.md；Web 再读 platforms/web.md（七个维度对浏览器的取值与施加方式）。其他平台先按本文通用步骤做，维度取值在 environment 类逐项与用户确认。不需要安装外部 Skill。

## 运行合同

沿用 cross-exam 交互、独立取证、本地/开发靶、只记录不修复的约束。唯一审计输出根是 docs/cross-exam/<run>/；不修改产品源码。发现 UI 时自动列为候选 facet，先由用户选中。已知没有取证/看图能力时声明限制，视觉问题无法自证，其他 facet 可继续。

1. 独立 census 从代码枚举页面/弹层/入口/状态，运行探索补齐动态入口。记录无法枚举的类别；未完成普查不能声称全 App 覆盖。
2. 独立 prober 打开代表性页面并截图；主会话结合源码、设计文档与实图生成 visual/observed-style.md。截图中的缺陷不是基准。真实敏感数据改用已有合成数据；无法避免时停该项，要求用户处理。
3. 逐类展示候选规则、冲突和参考图，让用户确认 direction/color/typography/layout/spacing/icons/components/navigation/feedback/states/motion/environment。每次确认记录用户原意与时间。颜色等规则不能靠安装自带偏好自动获准。
4. 冻结 visual/visual-baseline.json 与 interaction-baseline.json，每个文件含 categories 映射；每类含 rules（非空规则列表）或 reason（该类不适用的原因，此时 rules 可为空列表），二者必有其一；另含 reference_images、confirmation、confirmed_at。保留用户批准图片的范围和例外。SHA-256 按文件原始字节计算，两个摘要独立存储。
5. 生成 visual/surface-inventory.json 与 case-matrix.json，并把同一矩阵写入 ledger.visual_cases。每个页面按适用 state/device/os/appearance/dynamic_type/locale/orientation 完整笛卡尔积；键盘、权限等归入 state。具体环境值在 environment 类确认，不能用“所有”代替枚举。无数量上限，分批但不抽样。不适用项须有 reason 与 basis（出处），构造不了不等于不适用。
6. 逐批派 fresh-context prober。传具体用例、设备和状态、基线摘要，不传 Golden、预期结论或怀疑。视觉定位可读入口代码，但不与禁止读源码找路的 journey 探针混用。一个模拟器/设备一次只由一个 prober 操作，独立设备才可并发。分批以比较组为界：同一比较组、同一环境（除 state 外六维相同）的用例必须在同一条 entry 里裁决，校验器拒绝被拆开的组；单页各自通过不等于全局一致。每例实图；motion 用例至少两张带时间顺序的原始关键帧，另存录屏用于节奏判断。不能用 Preview、模拟图、Token 或截图元数据代替实际 App。
7. 对每批原图运行独立 visual-reviewer（读 prompts/visual-reviewer.md）。传冻结基线、用例和图片，不传作者观点、其他审查报告。主会话自身不能替代 reviewer。
8. 当前平台 fresh-context reviewer 必需。另一平台 CLI 经只读版本/帮助检查和实际看图调用可用时双审。Claude 主控用 Agent（`model: opus`）+ `codex exec -m gpt-5.6-sol`；Codex 主控用 spawn_agent（`model: gpt-5.6-sol`）+ `claude -p --model opus`。reviewer 是判断档：finding 直接决定阻断，档位见 SKILL.md "模型分层"，entry 的 `agent_model` 记当前平台 reviewer 的字面量。不用 resume/fork 既有会话；CLI 参数按当前 --help，只读工具/沙箱，不开启 bypass。外部 reviewer 通过标准输出返回 JSON，由主会话原样保存；不得把 JSONL 事件流当报告。单独 evidence 子目录，每个 reviewer 报告完成前不暴露另一份。
9. 第二端失败重试一次；仍失败写 degradation_ref（两次尝试与原因），该批 dual_degraded，保留独立单审结果。当前端无独立审图能力仍无法自证。reviewer 声称“打开了图片”只是记录，主会话还须核查实际图像读取工具记录，不把字段当证明。
10. 双审 high/medium 取并集。reconciliation 记录全部 session_id:finding_id 和 disagreements；有阻断发现不得判 done。阻断按 finding 指向的用例计：一条 entry 只被指向其 visual_case_ids 原图的 high/medium 阻断，同批其余用例可拆成独立 entry 共用同一份报告各自裁决；finding 引用的图片必须在该 reviewer 的 inspected_images 内。gap 是缺失/冲突/破损，drift 是偏离批准方向，unprovable 是缺环境/基线/有效证据。没有确认基线只记录差异与 unprovable。未跑项 not_examined；用户停止后渲染全部剩余项。

基线未确认时先建立已知页面用例，写失败原因文件并给对应项 unprovable，不伪造已确认字段。中断后按原基线摘要与构建续跑；构建或基线变化建立新的审计 run，避免旧缺口/截图混入新结果。不得自动重写 Golden。

## 数据接口（路径约定）

surface-inventory.json 的 surfaces 每行含 id、entry、kind、axes（上述七维到字符串数组）、motion_states、scrollable（Web 必填：目标视口下 scroll_height > client_height；为 true 时 state 轴必须含至少一个 `scroll-` 开头的滚动位置状态，矩阵展开拒绝缺它的页面），以及可选 groups（比较组名列表，如 buttons、navigation、forms；共用同一组件或模式的页面标同一组名）。
运行 `python3 VISUAL_ROOT/matrix.py <inventory>` 输出完整矩阵，原样保存 case-matrix.json 并写入 ledger.visual_cases。
增加页面/状态必须重新展开、保留原未测清单，不手工删减组合。
用例 ID 根据页面和环境组合内容生成，重排页面不改变身份。冻结 inventory、matrix 原始字节摘要；校验器重新展开清单核对完整矩阵，renderer 即使遇到 ledger 漏页也展示冻结矩阵中的未测项。

ledger.visual_acceptance = {facet_ids: [F编号], baseline_status: confirmed|unconfirmed, baseline_ref, baseline_digest, interaction_ref, interaction_digest, inventory_ref, inventory_digest, matrix_ref, matrix_digest, build, review_mode: single|dual}。
baseline_ref、interaction_ref、inventory_ref、matrix_ref 相对 run；其他本节 evidence 引用都相对 run/evidence（基线参考图片例外，见下文）。视觉 facet 的 entry 必填 visual_case_ids，即使无法自证。运行审查模式在运行开始按当时可用能力冻结，同一 run 内升降都不允许：dual 不能在 entry 静默改成 single，single 也不能中途升 dual；能力变化（另一平台 CLI 装好或失效）建立新的审计 run。
基线每类 reference_images 是 {相对 run 的原图路径: SHA-256} 映射；两份基线合计至少一张可解码、经用户确认的参考图。确实不适用的类别可为空映射，须记录原因。不能只有文字或代码规则。

visual_cases 每行：{id, surface, state, device, os, appearance, dynamic_type, locale, orientation, motion: false}；不适用增加 applicability: not_applicable、reason、basis；ledger 行相对冻结矩阵只允许多这三个键，身份字段必须逐字相同。未测状态由 renderer 从采信裁决计算，不信任自报通过。

视觉 entry：保留 facet/medium/evidence/verdict 等现有字段，增加 visual_case_ids、evidence_manifest、review_reports（路径列表）、review_mode；双审加 reconciliation_ref；降级加 degradation_ref。unprovable 可无图，但必有 visual_failure_ref 原因文件。每批问题 q 唯一，方便现有 G 编号与 product-review 引用。

manifest = {captures: [{case_id, state, device, os, appearance, dynamic_type, locale, orientation, build, captured_at, baseline_digest, interaction_digest, inventory_digest, matrix_digest, images: [原图路径], image_digests: {原图路径: SHA-256}}]}。Web capture 另必含 capture_mode（viewport | full_page）、headless、scrollbars（native | hidden | overlay）、scroll_profile（platforms/web.md 定义的页面读回值）、capture_tool；state 以 `scroll-` 开头的用例只接受 capture_mode viewport 且 scrollbars native 的 capture，否则拒渲——无头全页截图里没有滚动条也没有折叠线，滚动类断言不能从它推断。每条 capture 的 build 与四个摘要必须等于冻结运行配置。构建含 commit 与 dirty 状态及可识别当前产物的构建标识；截图必须能追到该构建。PNG/JPEG 原图保留，附图的缩放裁剪不覆盖原文件。motion 另含与 images 一一对应的 frame_times_ms（非负、有限、严格递增），至少两张不同像素内容的帧；复制文件、更换编码或重复路径不算新帧；还必含 recording（相对 run/evidence 的录屏路径，非空文件，不能是某张帧）与 recording_digest（SHA-256），缺一拒渲。关键帧检查不证明节奏正确，录屏才是节奏证据。

review report = {platform: claude|codex, session_id, independent: true, build, baseline_digest, interaction_digest, inventory_digest, matrix_digest, inspected_images: [原图路径], image_digests: {原图路径: SHA-256}, reference_images: {基线参考图路径: SHA-256}, status: passed|findings, findings: [{id, severity: high|medium|low, rule, observation, images: [原图路径]}], inspected_recordings: [实际打开过的录屏路径], recording_unreadable: 原因}。本批含 motion 用例时，该批全部录屏必须出现在 inspected_recordings，或写 recording_unreadable 说明该 reviewer 为何读不了视频（此时它只审了帧序列）。所有 reviewer 都没审阅录屏时，含 motion 用例的 entry 不能判 done：有帧序列上的发现可判 gap，否则把 motion 用例拆成单独 entry 记 unprovable（visual_failure_ref 写明无视频读取能力），静态用例照常裁决。reviewer 独立读取并计算摘要，五项绑定必须匹配冻结运行，且覆盖该批全部原图及全部基线参考图。图片键逐字沿用 manifest 的 images 字符串（相对 run/evidence）和基线的 reference_images 键（相对 run），校验器精确比对，主会话不得改写报告。
degradation_ref 指向 {platform: 失败平台 claude|codex, attempts: [{attempted_at, reason}, {attempted_at, reason}]}；必须保留实际调用记录以供核查，降级后留下的报告不能来自失败平台。dual_degraded 只用于原先冻结为 dual 的 entry。
reconciliation = {blocking_findings: [session_id:finding_id], disagreements: [双方主张与证据引用]}。主会话另存判断理由，不能修改独立报告内容。

运行环境需要 Pillow（依赖声明见 requirements.txt），用于真实解码 PNG/JPEG；按项目依赖流程安装，缺依赖则记录 unprovable，不能降级为文件头检查。renderer 验证结构/路径/摘要/图片解码/覆盖/报告，并不以像素差或文件存在代替审美判断。所有最终完成度输出只由现有 render_report.py 生成。
