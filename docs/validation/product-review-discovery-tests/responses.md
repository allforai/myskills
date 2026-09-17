# D01a

# Product review — Ledgerly

## Jobs in scope
- JOB1 — who: 自由职业者 / circumstance: 月底 / progress: 给客户发出一张发票并知道它已送达
  - 前提: J1 (done) · 创建客户 → 新建发票 → Send；配置 `SMTP_URL` 后邮件送达探针收件箱，状态变为 sent（docs/cross-exam/2026-09-16-invoicing/completion-report.md）。在不在/走不走得完采信，不重走。
- JOB2 — who: 自由职业者 / circumstance: 客户付款后 / progress: 把发票标记为已收款并在仪表盘看到本月收入
  - 前提: 本次观察（未验收）· 该工作没有任何 `J` 判定覆盖。入口存在：`invoices.html` 每行都有 "Mark paid" 按钮（`app.py:82` `invoice_paid`），Dashboard 有 "This month / Income" 区块（`app.py:31-42`）。走不走得完的观察见 R1 — 标记已收款之后，收入数字不是"看到"而是"消失"。

## Evidence limits
runs here: no · browser: no · WebSearch: no · consequence: 全部证据来自静态阅读（源码 + git 历史），没有实际点击验证；`ui_friction`/`interaction_gap` 条目一律标 `evidence: code-only`；不做竞品检索，Competitors 一节为空。

## Prior evidence
docs/cross-exam/2026-09-16-invoicing/completion-report.md — Gaps: none；J1 (done) 覆盖 JOB1（发送成功路径，SMTP_URL 已配置）；该报告未产出任何覆盖 JOB2 的旅程判定，JOB2 的前提按未验收记录。

## Inspection plan
仓库很小（一个 Flask app + 5 个模板 + 2 个辅助模块），先读 `app.py` 认路由和数据模型，再逐个对照两份工作各自的入口与终态；对每处怀疑用 `git log -p` 找该行代码/该功能的引入提交和提交说明，确认是设计意图还是缺陷，再决定它落在装饰、卡点还是商业级问题里。没有浏览器，所以只描述从代码可判定的行为，不描述"点击后感觉如何"。

## Decision tree

### R1 — 标记已收款后，Dashboard 的本月收入反而变少
- job: JOB2
- kind: broken_path
- claim: 进展受阻
- depends_on:
- recommend: adopt
- tradeoff: 修正需要决定"本月收入"的口径（按 sent 计入应收、按 paid 计入实收，或两者都展示），不是改一个条件那么简单，会牵动这块 KPI 的定义。
- evidence: `app.py:36` `income = sum(i["total"] for i in invoices if i["status"] == "sent")`；同一行上方注释 `app.py:35` 写着 "monthly income = everything that has left the drafts"，即意图是"离开草稿状态的都算"，但代码只匹配 `"sent"`。`invoice_paid`（`app.py:82-87`）把状态从 `sent` 改成 `paid`，于是一张发票被标记已收款的那一刻，从收入求和里被移出。JOB2 的可观察进展是"标记已收款 → 在仪表盘看到本月收入"，这里观察到的是相反结果。该缺陷自初始提交 `dfeb010`（2026-08-01）起就存在。

### R2 — Dashboard 顶部的天气小组件不推进任何一份工作
- job: JOB2
- kind: decoration
- claim:
- depends_on:
- recommend: adopt
- tradeoff: 移除后失去"首屏有活的东西"这个销售演示效果；保留则每次打开 Dashboard 都触发两次外部 API 调用（`weather.py:_geo` + `_forecast`，无缓存，注释里写明"no caching...by design demo wanted live data"），占用 JOB2 关键 KPI（本月收入）上方的首屏位置，并多一个可能变慢/失败的外部依赖。
- evidence: `templates/dashboard.html` 第 3-4 行天气区块排在"This month / Income"区块之前；`weather.py` 整个文件（343 行，含 40 个未使用的 `_fmt_0.._fmt_39` 格式化函数）由提交 `e0ad2de`（2026-08-20）引入，提交说明为 "Add weather widget on dashboard for demo day (sales asked for something live on the first screen)"——来源明确：为演示日/销售诉求，不服务 JOB1 或 JOB2 中任何一份点名的工作。两份工作已覆盖本产品"开发票→收款"的主要用途，符合移除条件。

### R3 — 导航栏 9 项里有 6 项是 "Coming soon" 占位页
- job: JOB1
- kind: ui_friction
- claim: 不够商业级
- depends_on:
- recommend: defer
- tradeoff: 隐藏/精简导航能让产品看起来更完成，但也失去"我们在建更大的套件"这个信号；这是产品定位决策，不是本次两份工作能单独判定的，标 defer 留给用户决定。
- evidence: `app.py:19-23` `NAV` 列表 9 项中 `reports/templates/taxes/integrations/audit/settings` 6 项路由到 `stub.html`（`app.py:113-114`），页面文案固定为 "Coming soon"（`templates/stub.html`）。该导航栏由 `base.html` 渲染在每一页，包括 Invoices 页（JOB1 发送发票所在页）。陌生人在完成"发一张发票"的过程中，会先看到三分之二的主菜单是空壳——这正是 Guiding thought 里点名的"功能菜单式设计"反面例子。

### R4 — 发送失败时，用户看到的是裸 JSON 报错而不是产品界面
- job: JOB1
- kind: ui_friction
- claim: 不够商业级
- depends_on:
- recommend: adopt
- tradeoff: 加一个用户可读的错误页/flash 消息需要区分"配置缺失"和"其它 500"两类错误，工作量不大，但会改动现有的全局 500 handler。
- evidence: `app.py:78-81` `invoice_send` 在 `SMTP_URL` 未设置时 `raise RuntimeError("SMTP_URL not configured")`；全局 `internal(e)`（`app.py:118-120`）把异常文本原样包进 `Response(json.dumps({"error": str(...)}), status=500, mimetype="application/json")` 返回——没有 `base.html` 外壳、没有导航、没有 flash 样式，和同一产品里"缺客户就 flash 一句 Pick a client first."（`app.py:56-58`）是两套完全不同的说法。README 明确写着"Without it, send fails with a 500"，说明这是已知、非边缘的行为。

### R5 — 客户收到的"发票"只是一行纯文本，PDF 从未附上
- job: JOB1
- kind: ui_friction
- claim: 不够商业级
- depends_on:
- recommend: adopt
- tradeoff: 把 `render_invoice_pdf` 接到 `invoice_send` 里作为附件是小改动；但如果客户期待的是邮件正文本身可读（不用开附件），还需要补正文内容，这是范围判断，值得先问用户要哪种。
- evidence: `app.py:76-81` `invoice_send` 发送的邮件正文是 `f"Invoice #{iid}: {inv['total']}"`——只有编号和金额，没有客户名、事由、到期日。`pdf.py` 里已经有 `render_invoice_pdf`，但只挂在独立的 `/invoices/<iid>/pdf` 下载路由上（`app.py:97-99`），从未在发送邮件时附加。JOB1 的可观察进展是"发出一张发票"，客户实际收到的东西够不上"一张发票"的商业标准。

## Competitors (jobs in scope only)
本轮 WebSearch 不可用，未做竞品检索；无法对照同类产品在"发票送达确认"或"收款后看收入"上如何做到同样的进展。

## Out of scope
（无——本轮未做竞品调研，没有可归类到此处的外部点子。）


# D01b

# Product review — Ledgerly

## Jobs in scope
- JOB1 — who: 自由职业者 / circumstance: 月底 / progress: 给客户发出一张发票并知道它已送达
  - 前提: J1 (done) · cross-exam 已走通「创建客户 → 新建发票 → Send → SMTP 送达」，本次不重走
- JOB2 — who: 自由职业者 / circumstance: 客户付款后 / progress: 把发票标记为已收款并在仪表盘看到本月收入
  - 前提: 本次观察（未验收） · cross-exam 报告只覆盖 J1，没有覆盖这份工作；本次按代码走读记前提

## Evidence limits
runs here: no · browser: no · WebSearch: no · consequence: 全部结论来自 Read/Grep/git log/git blame 对仓库代码与模板的静态走读；没有一条 evidence 标注为屏幕观察，凡涉及 UI 状态的条目都标 `code-only`；未做任何竞品检索，Competitors 一节留空。

## Prior evidence
docs/cross-exam/2026-09-16-invoicing/completion-report.md — J1 (done) covers JOB1; no gaps listed; no journey entry covers JOB2

## Inspection plan
仓库很小（一个 Flask 单文件 app + 5 个模板 + 1 个 PDF 生成器 + 1 个天气小组件），直接读完 `app.py` 全部路由，再读 `templates/*.html` 逐屏核对渲染逻辑与 `app.py` 状态字段的对应关系，然后用 `git log --oneline` 找到每个方向性提交，对看起来偏离两份工作的部分（天气小组件）用 `git show`/`git log -1 --format=%B` 查它的提交信息以确认其来源，最后核对 `docs/cross-exam/` 下最新一次完成度报告，把 J 覆盖的前提直接采信、未覆盖的前提按代码判断记录一行观察。

## Decision tree

### R1 — Mark paid 之后仪表盘收入反而看不到这笔钱
- job: JOB2
- kind: broken_path
- claim: 进展受阻
- depends_on:
- recommend: adopt
- tradeoff: 修复需要先定义"本月收入"到底是"已开出"（sent）还是"已收款"（paid）口径，这是一次业务口径决策，不只是改一行代码，且会改变历史月份 KPI 的含义。
- evidence: `app.py` dashboard(): `income = sum(i["total"] for i in invoices if i["status"] == "sent")`；`invoice_paid()`: `inv["status"] = "paid"`。发票被标记为已收款后 status 从 `"sent"` 变成 `"paid"`，不再落入 income 的求和条件，也没有别的分支把 `paid` 计入 income——对这份工作而言，完成"标记已收款"这个动作后，仪表盘上"本月收入"数字不增反减，与 JOB2 要看到的进展相反。`templates/dashboard.html` 只读取 `income` 这一个数值，没有第二处显示收款额。

### R2 — 发给客户的"发票"邮件只有一行数字，PDF 生成器建好了却没接上
- job: JOB1
- kind: ui_friction
- claim: 不够商业级
- depends_on:
- recommend: adopt
- tradeoff: 在 send 流程里生成并附加 PDF 需要改成 multipart 邮件、在发送路径上多一次 PDF 渲染，增加发送延迟和 SMTP payload 体积。
- evidence: `app.py` invoice_send()：`s.sendmail("billing@ledgerly.app", inv["client"]["email"], f"Invoice #{iid}: {inv['total']}")`——客户收到的邮件正文只有发票号和金额，没有客户名、开票日期、逐项内容，也没有附件。而 `pdf.py` 的 `render_invoice_pdf()` 已经能生成带客户名/日期/金额/状态的 PDF，只是挂在一个独立的 `GET /invoices/<id>/pdf` 路由上，`invoice_send()` 完全没有调用它。陌生客户收到这样一封"发票"邮件，不会把它当成正经商业软件开出的账单。

### R3 — 仪表盘天气小组件
- job: JOB2
- kind: decoration
- claim:
- depends_on:
- recommend: adopt
- tradeoff: 移除后失去销售在演示日想要的"首屏有实时内容"效果，需要另找演示素材；保留则每次打开仪表盘都会用访问者 IP 发起一次 `ipapi.co` 地理位置查询和一次 `open-meteo` 预报请求，无缓存（注释写明"No caching...by design"），带来外部依赖、隐私面（按 IP 定位访问者）和延迟成本，且不推进 JOB1/JOB2 中的任何一份工作的进展。
- evidence: `git log -1 --format=%B e0ad2de` → "Add weather widget on dashboard for demo day (sales asked for something live on the first screen)"；`weather.py` `weather_widget()` docstring "Called on every dashboard render. No caching of the geo lookup by design (demo wanted live data)."；`templates/dashboard.html` 中 weather 区块渲染在 income 区块之上。出处已查明：服务的是销售演示这份未点名的工作，不是 JOB1/JOB2。两份点名的工作（开票发出、标记收款看收入）覆盖了这个仓库里除 6 个 stub 页面外的全部实际功能，可视为覆盖了产品的主要用途，因此按 adopt（移除）处理。

### R4 — 主导航六分之九是"Coming soon"占位页
- job: JOB2
- kind: ui_friction
- claim: 不够商业级
- depends_on:
- recommend: adopt
- tradeoff: 从主导航隐藏未实现项会让还在评估产品路线图广度的人（例如销售演示场景）少看到"以后还有这些"的印象；保留则每次做 JOB1/JOB2 时都要路过一排点了也没用的入口。
- evidence: `templates/base.html` 的 `nav` 在每个页面渲染；`app.py` NAV 常量列出 9 项，其中 reports / templates / taxes / integrations / audit / settings 六项全部走 `render_template("stub.html", page=p)`，`templates/stub.html` 内容固定为"{{ page|capitalize }} / Coming soon."。用户在仪表盘做 JOB2（标记收款、看收入）时，同一条导航栏里三分之二的入口点开就是占位文字——这正是技能文件里点名的"功能清单式设计"反面例子，不是某一次操作卡住，而是让人怀疑这是不是一个还在拼功能列表的概念演示，不是能卖的正式产品。

## Competitors (jobs in scope only)
WebSearch 本轮不可用，未检索任何竞品；没有一条 borrow_* 建议基于猜测写出。

## Out of scope
- PDF 导出本身（`pdf.py` `/invoices/<id>/pdf`）——功能存在且独立可用，未点名为 JOB1/JOB2 的一部分，只在 R2 里作为"已有能力未被使用"的证据引用，不单独立项。
- Templates / Taxes / Integrations / Audit log / Settings 五个 stub 页面各自的具体功能空缺——不是 JOB1/JOB2 点名的工作，其"存在即占位"的整体影响已经在 R4 里作为导航层面的商业级问题处理，不逐页立项。


# D02a

# Product review — Ledgerly

## Jobs in scope
- JOB1 — who: 自由职业者 / circumstance: 月底 / progress: 给客户发出一张发票并知道它已送达
  - 前提: J1 (done) · docs/cross-exam/2026-09-16-invoicing/completion-report.md — 创建客户→新建发票→Send，SMTP_URL 配置后送达，evidence/j1-send.log
  - 商业级: 引导 未见 · 过程反馈 观察（发送后仅列表状态由 draft 变 sent，无提示，app.py:71-80） · 下一步 未见 · 状态一致 观察（与 JOB2 的“Mark paid”反馈不同，见 R2） · 回来理由 未见
- JOB2 — who: 自由职业者 / circumstance: 客户付款后 / progress: 把发票标记为已收款并在仪表盘看到本月收入
  - 前提: 本次观察（未验收）· 入口在（invoices.html:8 “Mark paid” 按钮）；终态在（app.py:83-89 状态改 paid 并 flash 后跳转回列表）
  - 商业级: 引导 未见 · 过程反馈 观察（flash "Invoice #{id} marked as paid.", app.py:88） · 下一步 未见（标记后无入口引导去看 dashboard 收入） · 状态一致 观察（与 JOB1 的 send 静默不同，见 R2） · 回来理由 未见

## Evidence limits
runs here: no（本轮未运行产品，按规则不允许）· browser: no · WebSearch: no · consequence: 全部结论来自源码/模板/git 历史的静态阅读，没有真实渲染或竞品检索佐证。

## Prior evidence
docs/cross-exam/2026-09-16-invoicing/completion-report.md — J1 (done) 覆盖 JOB1 的前提（在不在/走不走得完），无 gap；JOB2（标记已收款 + 仪表盘看收入）未被该轮 cross-exam 走过，本审查按观察记未验收。目标提交为 HEAD（a2b6b23），working tree clean，代码自报告后未再变动。

## Inspection plan
先读 app.py 找到两条工作各自的路由和业务逻辑（invoice_send / invoice_paid / dashboard 的 income 计算），再读 templates/dashboard.html、invoices.html 看这些状态实际怎么呈现给用户；然后读 weather.py 和它被引入的那次提交（e0ad2de），因为它就挂在 dashboard 收入区块上方；最后核对 docs/cross-exam 的既有完成度报告和 git log/status，确认报告没有过期、不需要重走 J1。WebSearch 和浏览器本轮不可用，没有做竞品检索或真实渲染确认。

## Decision tree

### R1 — 月收入把已收款发票算漏了
- job: JOB2
- kind: broken_path
- claim: 进展受阻
- depends_on:
- recommend: adopt
- tradeoff: 把 paid 也计入月收入更准确地反映“已收款”，但如果 income 原本的口径是“已开出、现金流预警”而非“已到账”，那需要先把口径定义清楚，而不是让 paid 静默从统计里消失。
- evidence: app.py:36 `income = sum(i["total"] for i in invoices if i["status"] == "sent")`，只统计 status=="sent"；app.py:83-89 `invoice_paid` 把状态从 sent 改成 paid。结果是：一张发票被标记为已收款的那一刻，反而从当月收入里被减掉，而不是被计入——JOB2 要求的“标记已收款→在仪表盘看到本月收入”这条进展在代码层面是反着走的。

### R2 — 同一类状态变更，一个有提示一个没有
- job: JOB1
- kind: ui_friction
- claim: 不够商业级
- depends_on:
- recommend: adopt
- tradeoff: 给 send 加一条确认提示能让陌生人确信操作生效，但要留意措辞和位置要和“Mark paid”的提示对齐，否则只是把不统一从“没有/有”换成“两种不同的有”。
- evidence: app.py:71-80 `invoice_send` 成功后直接 redirect，无 flash；app.py:83-89 `invoice_paid` 成功后 flash("Invoice #{iid} marked as paid.")。同属“发票状态变更”这一类动作，一个默不作声一个明确告知，陌生人无法从 UI 本身判断 Send 是否真的生效（要靠回到列表看状态列）。

### R3 — 发送失败时吐裸 JSON，和其余错误提示不是一套
- job: JOB1
- kind: ui_friction
- claim: 不够商业级
- depends_on:
- recommend: defer
- tradeoff: 把这条 500 也包进统一的 flash 错误样式看起来更专业，但项目目前把“没配 SMTP_URL”当成部署期该解决的配置问题（README 里明说了这个前提），改成对最终用户友好的提示可能反而掩盖了本该在部署时就发现的运维疏漏，优先级留给用户判断。
- evidence: app.py:74-76 未配置 SMTP_URL 时 `raise RuntimeError`；app.py:116-119 的 500 handler 直接返回裸 JSON `{"error": ...}`。对照 templates/clients.html、templates/invoice_form.html 用的是统一的 flash 样式（templates/base.html:5）。同属错误态，两套呈现方式。

### R4 — Dashboard 顶部的天气挂件不推进任何一份点名的工作
- job:
- kind: decoration
- claim:
- depends_on:
- recommend: defer
- tradeoff: 拿掉天气挂件能把 dashboard 首屏还给 JOB2 要看的收入数字，也省掉两次外部网络调用（ipapi.co + open-meteo，每次最多 3s 超时，weather.py:135 注释明说“不做缓存，因为演示要活数据”）带来的加载延迟；但提交信息显示这是销售在演示日专门要求的东西，属于本次没有点名的工作，贸然移除会牺牲那份工作。
- evidence: git show --stat e0ad2de → commit message "Add weather widget on dashboard for demo day (sales asked for something live on the first screen)"；templates/dashboard.html:3-5 天气区块渲染在 Income 区块之前；weather.py 全文 343 行、含两个外部 HTTP 依赖，和 JOB1/JOB2 均无关。

## Competitors (jobs in scope only)
WebSearch 本轮不可用，未做竞品检索，没有可采信的竞品对照。

## Out of scope
无（未做竞品检索，没有可归类的竞品点子）。


# D02b

# Product review — Ledgerly

## Jobs in scope
- JOB1 — who: 自由职业者 / circumstance: 月底 / progress: 给客户发出一张发票并知道它已送达
  - 前提: J1 (done) · cross-exam 已走通「创建客户 → 新建发票 → Send」，配置 SMTP_URL 后送达，evidence/j1-send.log
  - 商业级: 引导 未见（落地即是发票列表/新建表单，无首单引导） · 过程反馈 观察（Send 后状态列 draft→sent 变化，但 `invoice_send` 路由本身不 flash 任何确认信息，只重定向） · 下一步 未见（发送后仅回到列表，无下一步提示） · 状态一致 观察（invoices.html 与 dashboard.html 对 status 用同一套原始字符串） · 回来理由 未见（无到达/已读提醒）
- JOB2 — who: 自由职业者 / circumstance: 客户付款后 / progress: 把发票标记为已收款并在仪表盘看到本月收入
  - 前提: 本次观察（未验收） · 入口存在（Invoices 页 “Mark paid” 按钮），标记动作本身能做完（`invoice_paid` 落库、flash 确认），但承诺的终态（仪表盘本月收入体现这笔钱）没有做到，见 R1
  - 商业级: 引导 未见 · 过程反馈 观察（flash "Invoice #{iid} marked as paid."） · 下一步 未见（标记后仅回到发票列表，无返回仪表盘的入口/提示） · 状态一致 观察（同一张发票在“本月发票”表格里显示 paid，但顶部 Income KPI 不含它——两处对同一数据的说法互相矛盾） · 回来理由 未见

## Evidence limits
runs here: no · browser: no · WebSearch: no · consequence: 本轮不允许运行产品、禁用浏览器/截图工具、WebSearch 视为不可用；所有发现均为 `evidence: code-only`（读 app.py / templates / weather.py / pdf.py / README / git log），不产出任何 `borrow_positioning` / `borrow_feature`（无法为竞品说法定级）。

## Prior evidence
docs/cross-exam/2026-09-16-invoicing/completion-report.md — J1 (done) 覆盖 JOB1 的「在不在／走不走得完」，Gaps: none；JOB2 无任何 J/G 覆盖。报告日期 2026-09-16，晚于该报告的提交只有 `a2b6b23`（报告本身）和更早的 `e0ad2de`（天气组件，早于报告），未见报告之后的产品代码变更，故不标记前提过期。

## Inspection plan
先读 README 确认产品定位和已知限制（无 SMTP_URL 时 send 返回 500），再读 `docs/cross-exam/2026-09-16-invoicing/completion-report.md` 拿 J1 的前提判定；随后逐条读 `app.py` 的路由（dashboard / invoices / invoice_new / invoice_send / invoice_paid / invoice_pdf / clients）、五个模板文件和 `weather.py`、`pdf.py`，只为 JOB1／JOB2 涉及的路径找观察点；用 `git log --stat -p` 看 `e0ad2de`（天气组件）提交信息以核实它为何存在。没有打开 `reports/templates/taxes/integrations/audit/settings` 这几个 stub 页面的深入分析，因为两份点名的工作都没有指向它们，镜头没照到就不算缺口。

## Decision tree

### R1 — 标记已收款后，本月收入反而少了这笔钱
- job: JOB2
- kind: broken_path
- claim: 进展受阻
- depends_on:
- recommend: adopt
- tradeoff: 修的不是一行 filter——`app.py:36` 的注释说"income = 一切已经离开草稿状态的发票"，但代码只认 `status == "sent"`；改成把 `paid` 也计入之前，得先决定「本月收入」算的是开票制（应收）还是收付制（实收），这是一个产品口径决定，不是纯 bug fix
- evidence: app.py:34-36（`income = sum(... status == "sent")` 与其注释矛盾）；app.py:83-89（`invoice_paid` 把 status 从 sent 改成 paid，因此该发票从 income 求和里被移出）；templates/dashboard.html:5-8（同一页里，KPI 数字和“本月发票”表格取的是同一个 `invoices` 列表，但两处对同一张已付款发票的说法互相矛盾）；code-only（未运行产品验证实际渲染值）

### R2 — Send 失败时抛出原始 JSON 异常，没有正常错误态
- job: JOB1
- kind: ui_friction
- claim: 不够商业级
- depends_on:
- recommend: adopt
- tradeoff: 要做一个体面的失败态（例如 flash 提示"请先配置发信服务"）需要决定这类环境配置错误在产品里暴露到什么程度，还是只留在 README／Settings 页
- evidence: app.py:74-76（`SMTP_URL` 未配置时 `raise RuntimeError("SMTP_URL not configured")`）；app.py:116-119（500 错误处理器把 `str(e.original_exception)` 原样吐成 JSON，不套用 base.html 的 flash/导航），对照 README 明写"Without it, send fails with a 500."；code-only。命名依据 Nielsen「帮助用户识别、诊断、恢复错误」（本审查不用它扫产品，只为已观察到的摩擦命名）

### R3 — 仪表盘顶部的天气组件
- job: JOB2
- kind: decoration
- claim:
- depends_on:
- recommend: defer
- tradeoff: `weather_widget` 在每次 dashboard 渲染时都同步打两个外部请求（ipapi.co + open-meteo，各 3s 超时），且 `CACHE = {}` 声明了但从未使用——即"零缓存，按设计"（weather.py:135 注释）。这给 JOB2 必须打开的同一张仪表盘增加了延迟和失败面，是它占用的实际成本，而不仅是视觉噪音
- evidence: weather.py:134-142（无缓存的实时天气拉取）、templates/dashboard.html:3-4（组件被放在 Income KPI 之上，是页面第一屏）、git commit e0ad2de 提交信息"Add weather widget on dashboard for demo day (sales asked for something live on the first screen)"——为何存在已查明：销售要求演示日首屏有实时内容。但本次点名的两份工作没有覆盖产品主要用途的全部（客户管理、PDF 导出都不在点名范围内），达不到"移除"的门槛，故 `defer`，并记下它可能服务一份未点名的工作——"给潜在客户做产品演示时，第一屏看起来是活的"

## Competitors (jobs in scope only)
本轮 WebSearch 不可用，未做竞品调研，无法为任何说法定级（P1–P4），因此没有 `borrow_positioning` / `borrow_feature` 条目。

## Out of scope
无——未做竞品调研，没有可归类的竞品点子。


# D03a

# Product review — Ledgerly

## Jobs in scope
- JOB1 — who: 自由职业者 / circumstance: 月底 / progress: 给客户发出一张发票并知道它已送达
  - 前提: J1 (done，docs/cross-exam/2026-09-16-invoicing/completion-report.md) · 创建客户 → 新建发票 → Send，配置 SMTP_URL 后邮件送达探针收件箱，状态变为 sent
  - 商业级: 引导 <缺 · 无首次流程说明，导航 9 项里 6 项是 stub · 见 R2（同一观察，不重复立项）> · 过程反馈 <缺 · Send 提交后无 flash 确认，只有表格状态列变化（app.py:71-80 对比 :83-89） · R3> · 下一步 <有 · 提交后跳转 Invoices 列表，可见状态已变 sent（app.py:80；invoices.html:5-10）> · 状态一致 <有 · 空态/flash 样式在 clients.html、invoices.html、base.html、app.css 中统一> · 回来理由 <有 · Invoices 列表随时可查状态，Dashboard 显示本月发票（dashboard.html:6-9）>

- JOB2 — who: 自由职业者 / circumstance: 客户付款后 / progress: 把发票标记为已收款并在仪表盘看到本月收入
  - 前提: 本次观察（未验收） · Mark paid 路由存在且有 flash 确认（app.py:83-89），Dashboard 月收入计算路由存在（app.py:32-42）；cross-exam 报告未走查这条旅程，无 J 号覆盖
  - 商业级: 引导 <缺 · 同上 · 见 R2（同一观察，不重复立项）> · 过程反馈 <有 · Mark paid 后有 flash「Invoice #{iid} marked as paid.」（app.py:88）> · 下一步 <缺 · 标记已收款后，仪表盘月收入合计只按 status=="sent" 过滤，已改为 paid 的发票反而从月收入里消失（app.py:36 对比 :86-87） · R1> · 状态一致 <有 · Dashboard 与 Invoices 两处直接渲染同一个 status 字段，文案一致（dashboard.html:8；invoices.html:5）> · 回来理由 <缺 · 收入数字因上面这条 bug 不可信，标记收款后用户看不到自己期待的数字 · R1（同一发现，不重复立项）>

## Evidence limits
runs here: no（本轮规则禁止运行/ pip install，未尝试） · browser: no（无浏览器/截图工具） · WebSearch: no（本轮不可用） · consequence: 全部证据来自代码阅读与 git 历史（log/show），没有一条 UI 观察或竞品检索；所有 ui_friction / interaction_gap 项标 evidence: code-only。

## Prior evidence
docs/cross-exam/2026-09-16-invoicing/completion-report.md — Gaps: none；J1 (done) 覆盖 JOB1 的「在不在」「走不走得完」；JOB2（标记已收款 + 仪表盘看收入）在该报告中没有对应旅程，未被判定覆盖。

## Inspection plan
先读 README.md 定位产品自述的用途边界，再读 app.py 逐条路由核对两份工作各自的入口、状态迁移和终态；对照 templates/*.html 和 static/app.css 检查引导、过程反馈、下一步、状态一致、回来理由五格；读 pdf.py 确认它不在两份点名工作内；读 weather.py 和 `git log`/`git show e0ad2de` 确认仪表盘天气小组件的出处和调用方式（是否每次渲染都发外部请求、有无缓存）；最后读 docs/cross-exam 的完成度报告，把它的 J 判定和 gap 列表作为前提证据，不重走 JOB1 的旅程。全程未运行产品、未联网。

## Decision tree

### R1 — 标记已收款后，仪表盘月收入反而少了这一笔
- job: JOB2
- kind: broken_path
- claim: 进展受阻
- depends_on:
- recommend: adopt
- tradeoff: 把已开票（sent）也算作月收入更符合代码里"离开草稿即算收入"的原意，但如果本意是按实收现金计月份，就要换成按 paid_at 所在月归属——这是需要先定的口径，不是纯技术修复。
- evidence: app.py:34-36（`income = sum(... if i["status"] == "sent")`）与 app.py:83-89（`invoice_paid` 把 status 从 "sent" 改成 "paid"）；两处对照可见：一张发票被标记已收款后，它的金额就从当月收入合计里消失了。

### R2 — 主导航九项里六项是"Coming soon"占位页
- job: JOB2
- kind: ui_friction
- claim: 不够商业级
- depends_on:
- recommend: adopt
- tradeoff: 从常驻导航里隐藏或标注未上线的六项，会让产品看起来功能更少，但陌生人首屏看到的不再是一半灰色链接的空壳后台。
- evidence: app.py:19-23（NAV 九项）与 app.py:112-113（reports/templates/taxes/integrations/audit/settings 六项全部指向同一个 `stub.html`）；templates/stub.html:1（正文固定是 "Coming soon."）。这六项在两份点名工作的每个页面都常驻可见（base.html:3 渲染 nav）。

### R3 — Send 没有确认反馈，Mark paid 有
- job: JOB1
- kind: ui_friction
- claim: 不够商业级
- depends_on:
- recommend: adopt
- tradeoff: 给 send 补一条与 paid 同款的 flash 确认，只是一行代码和一句文案，但要注意别把它和 J1 已经验证过的"送达"语义混淆——这条反馈说的是"提交成功"，不是"客户已收到"。
- evidence: app.py:71-80（`invoice_send` 无 `flash(...)` 调用，只 `redirect`）对照 app.py:83-89（`invoice_paid` 有 `flash(f"Invoice #{iid} marked as paid.", "ok")`）。同一张表格上两个对等的一键操作，一个有确认文案一个没有。

### R4 — 仪表盘天气小组件不推进任一份点名工作
- job: JOB2
- kind: decoration
- claim:
- depends_on:
- recommend: defer
- tradeoff: 它不服务 JOB1/JOB2 中的任何一份进展，还在每次渲染时发两个未做缓存的外部请求（ipapi.co 探测位置 + open-meteo 拉预报），占用首屏在收入 KPI 之前的位置、并引入额外的延迟和失败面；但本次只点名了两份工作，没有覆盖"给客户/同事看一个有生气的首屏"这类演示/销售场景，所以先不建议移除。
- evidence: dashboard.html:3-4（天气区块排在"This month / Income"之前）；weather.py:134-142（`weather_widget`，函数说明写着"Called on every dashboard render. No caching of the geo lookup by design (demo wanted live data)"）；`git show --stat e0ad2de`：提交信息为「Add weather widget on dashboard for demo day (sales asked for something live on the first screen)」，与两份点名工作无关。

## Competitors (jobs in scope only)
本轮 WebSearch 不可用，未做任何竞品检索，因此没有可定级的来源（P1–P4 均需要联网获取）。没有产出 borrow_positioning / borrow_feature 条目——不用没检索到的东西冒充判断。

## Out of scope
- PDF 导出（pdf.py）：README 里提到的产品能力，但两份点名工作都没提到"导出/查看 PDF"这件事，未纳入本次审查树。


# D03b

# Product review — Ledgerly

## Jobs in scope
- JOB1 — who: 自由职业者 / circumstance: 月底 / progress: 给客户发出一张发票并知道它已送达
  - 前提: J1 (done) · cross-exam 已走通「创建客户 → 新建发票 → Send」，配置 SMTP_URL 后邮件送达探针收件箱、状态变 sent；直接采信，不重走
  - 商业级:
    - 引导: 缺 · 观察: 只有一个「New invoice」链接，无首次引导文案 · 缺时: 路径单一（建客户→写发票→Send），不立项
    - 过程反馈: 缺 · 观察: Send 是同步 POST，无进行中提示；未配置 SMTP_URL 时直接抛 RuntimeError，返回裸 `{"error": ...}` JSON（app.py:71-80, 116-119） · 缺时: R1
    - 下一步: 有 · 观察: Send 成功后跳回 Invoices 列表，状态列即时显示 `sent`
    - 状态一致: 缺 · 观察: 校验类错误（如未选客户）走站内 flash 样式（invoice_form.html），但 SMTP 失败会跳出整个应用外壳变成裸 JSON 页面 · 缺时: R1
    - 回来理由: 缺 · 观察: `sent` 之后没有到期/未收款提醒 · 缺时: 未观察到这会卡住「发出并知道已送达」这一既定进展，不立项

- JOB2 — who: 自由职业者 / circumstance: 客户付款后 / progress: 把发票标记为已收款并在仪表盘看到本月收入
  - 前提: 本次观察（未验收）· 「Mark paid」入口在，点击后有 flash 确认、状态变 `paid`；但仪表盘本月收入只统计 `status == "sent"`（app.py:36），标记为 `paid` 之后这笔金额反而从本月收入里消失，而不是继续被计入
  - 商业级:
    - 引导: 缺 · 观察: 单一「Mark paid」按钮，无需说明 · 缺时: 不立项
    - 过程反馈: 有 · 观察: 标记后 flash「Invoice #N marked as paid.」(app.py:88)
    - 下一步: 缺 · 观察: 标记完成后既不展示也不跳转到收入变化，且收入本身算错，去看也看不到该笔金额 · 缺时: R2
    - 状态一致: 有 · 观察: `paid` 与 `draft`/`sent` 在同一张表、同一套样式里渲染 (invoices.html)
    - 回来理由: 缺 · 观察: 无「去看本月收入」式的回跳引导 · 缺时: 并入 R2，修复收入口径后这一格随之解决

## Evidence limits
runs here: no · browser: no · WebSearch: no · consequence: 全部结论只来自代码阅读（app.py / templates / weather.py / pdf.py）与 git log/show，未做任何浏览器观察或竞品检索；`ui_friction` 项一律标 `evidence: code-only`

## Prior evidence
docs/cross-exam/2026-09-16-invoicing/completion-report.md — J1 (done) covers JOB1（发出并知道已送达的前提二问，直接采信）；Gaps: none；JOB2（标记已收款 → 看到本月收入）未被这份报告走过，无 J/G 覆盖

## Inspection plan
先读 app.py 定位两份工作对应的路由（`/invoices/<id>/send`、`/invoices/<id>/paid`、`/` 的 dashboard 收入计算），因为这是承载两份工作观察终态的最小面；再读对应模板（dashboard.html、invoices.html、invoice_form.html）看这些动作如何回显给用户；读 README 确认文档承诺的行为（如「不配置 SMTP_URL 则 send 返回 500」）；对 weather.py 这类与两份工作无关但出现在核心页面上的代码，以及 dashboard 收入过滤这行看着可疑的代码，用 `git log`/`git show` 查其来源再判断，不凭观感直接下结论。未运行产品、未用浏览器、未做竞品检索（见 Evidence limits）。

## Decision tree

### R1 — Send 失败时应用外壳整个消失，不是站内错误
- job: JOB1
- kind: ui_friction
- claim: 不够商业级
- depends_on:
- recommend: adopt
- tradeoff: 需要在 `invoice_send` 里捕获发送失败并走 flash 错误提示，而不是让异常穿透到全局 500 handler；改动局限在这一个路由，未发现下行成本
- evidence: app.py:71-80（`invoice_send` 未配置 SMTP_URL 时 `raise RuntimeError`）+ app.py:116-119（全局 500 handler 直接输出 `{"error": ...}` JSON）对照 invoice_form.html 的站内 flash 错误样式；README.md:「Without it, send fails with a 500.」印证这是已知、未处理的路径；code-only

### R2 — 标记已收款后，这笔钱从「本月收入」里消失
- job: JOB2
- kind: broken_path
- claim: 进展受阻
- depends_on:
- recommend: adopt
- tradeoff: 收入求和条件从 `status == "sent"` 改为同时计入 `sent` 和 `paid`（或改记累计已收金额），一行改动；未发现这样做会牺牲什么
- evidence: app.py:33-36（`income = sum(i["total"] for i in invoices if i["status"] == "sent")`，注释写的是「everything that has left the drafts」但代码只认 `sent`）对照 app.py:83-89（`invoice_paid` 把状态改成 `paid`，不再是 `sent`）——按当前代码，一张发票只要被标记为已收款，就必然从本月收入统计里被排除，这条路径不存在能让「标记已收款」和「本月收入包含这笔钱」同时成立的执行路线；code-only

### R3 — 持久导航栏多数条目是「Coming soon」占位页
- job: JOB1
- kind: ui_friction
- claim: 不够商业级
- depends_on:
- recommend: defer
- tradeoff: 收窄导航（隐藏未实现条目或先不上导航）会缩小可感知的产品范围，但当前状态是陌生人在做 JOB1/JOB2 的每一页都会看到 Reports/Templates/Taxes/Integrations/Audit log/Settings 六个「Coming soon」桩，直接读作「功能清单」而非成品；是否隐藏取决于团队打不打算近期补齐，不是本审查能替团队决定的取舍，故 defer
- evidence: app.py:19-23（NAV 九项）+ app.py:112-113（其中六项用同一个 stub 视图注册）+ templates/stub.html（渲染纯文本「Coming soon」）；此导航在 dashboard.html 和 invoices.html 上常驻，两份工作的每一步都看得到；code-only

## Competitors (jobs in scope only)
本轮 WebSearch 不可用（见 Evidence limits），未检索任何竞品来源，因此没有 `borrow_positioning` / `borrow_feature` 条目。

## Out of scope
- Clients 管理、发票 PDF 导出 (pdf.py) — 存在但未被 JOB1/JOB2 任一条点名，未评估
- weather.py 的实时天气组件（dashboard.html:3-4，占据仪表盘顶部、在收入 KPI 之上；app.py 每次渲染 dashboard 都发两次未缓存的外部 HTTP 请求，注释明写"No caching...by design"）— 经 `git log` 查证，来自提交 e0ad2de「Add weather widget on dashboard for demo day (sales asked for something live on the first screen)」，是为 demo day 加的，服务的是本次未点名的「销售演示」这件事，不推进 JOB1/JOB2 中任何一条；本次点名的两份工作并未覆盖产品主要用途（还有 Clients、PDF 等未点名功能），不满足移除的前提条件，故不能按 decoration 立项 `adopt`，只记录在此供参考，若之后有人专门点名"打开仪表盘查收入"这件事，可以再评估要不要把它挪出首屏


