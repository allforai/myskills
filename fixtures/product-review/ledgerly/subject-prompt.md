这是一次隔离的思维测试：你扮演已被用户显式调用 `/product-review` 的主会话，协议全文在下面这份文件里，读它，然后照它执行。

规则：
- 协议文件：{SKILL}
- 产品仓库：{APP}（一个 git 仓库；可以 Read / Glob / Grep 里面的文件，可以在该目录下跑 `git log` / `git blame` / `git show`）。**不要运行产品，不要 pip install，不要改动仓库里的任何文件。**
- 除了上面两处，不要读取任何其它路径；不要 WebSearch / WebFetch（本轮视为不可用）；没有浏览器和截图工具；不派子代理。
- 报告写到 {OUT}（用 Write），不要写到别处。

场景：用户已经在 Intake 中确认了两份工作（三元组已读回确认，不用再问）：
- JOB1 = 自由职业者 / 月底 / 给客户发出一张发票并知道它已送达
- JOB2 = 自由职业者 / 客户付款后 / 把发票标记为已收款并在仪表盘看到本月收入

Run directory 已定为 docs/product-review/2026-09-17-ledgerly/（但你只把 recommendations.md 写到 {OUT}）。用户在场。

现在从 Facts 开始做完整个流程，写出 recommendations.md，最后给用户一段不超过 300 字的答复。答复里附上你逐条自查时删掉了哪些候选、为什么。不要猜测测试的预期答案。
