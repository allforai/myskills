# Answer key — D01 (discovery on a real codebase, code-only)

Jobs (pre-confirmed triples handed to the subject):
- JOB1 = 自由职业者 / 月底 / 给客户发出一张发票并知道它已送达   (J1 done in cross-exam)
- JOB2 = 自由职业者 / 客户付款后 / 把发票标记为已收款并在仪表盘看到本月收入   (no J coverage)

## Must find (true positives)
- D1 send has no feedback: invoice_send redirects to list with no flash/no delivery signal; only the status column silently changes. → JOB1, claim 不够商业级 (核心动作无过程反馈), kind ui_friction/interaction_gap, NOT broken_path (J1 covers).
- D2 first entry no guidance: dashboard = 9-item nav + "No data" table; no CTA to create first client/invoice; 6 nav items are "Coming soon" stubs. → JOB1 or JOB2, 不够商业级 (无引导 / 功能菜单式主线).
- D3 income excludes paid: dashboard income = sum(status == "sent"); marking paid removes the invoice from income. → JOB2, claim 进展受阻, kind broken_path (allowed: JOB2 has no J), evidence app.py line.
- D4 weather widget decoration: 343 lines, two external HTTP calls per dashboard load, no cache; git log gives why (demo day / sales). → decoration; tradeoff must name cost; adopt (remove) is permitted because why-exists found AND JOB1+JOB2 cover the product's main use (invoicing). defer also acceptable if the subject argues coverage; unacceptable: silently dropping it, or adopt without citing the commit.
- D5 two error vocabularies: validation errors → flash; SMTP missing → raw JSON 500 from errorhandler. → 不够商业级 (同类状态两套说法), evidence app.py errorhandler + invoice_send.

## Must NOT write (traps)
- T1 no recurring invoices / no reminders → convention, not a job; at most Out of scope.
- T2 reportlab 3.6 old / pdf.py minimal → not a product finding.
- T3 Clients page as decoration → wrong; it is the prerequisite for JOB1.
- T4 CSS palette bland (#e8e4d8 Georgia) → taste, delete.
- T5 re-walking J1 / missing_job or broken_path on JOB1 → forbidden.

## Report hygiene
- Evidence limits: runs here no · browser no · WebSearch no → every item code-only.
- Prior evidence line names J1 (done) for JOB1; JOB2 前提 = 本次观察（未验收）.
- Inspection plan paragraph present.
- No source edits; only write is the report path given.
