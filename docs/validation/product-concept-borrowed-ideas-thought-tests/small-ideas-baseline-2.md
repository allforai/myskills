# 单主题借思路 · 第二批基线（E/F/G/H）

日期：2026-09-21。结论：**四条借来的做法都没用（模型自己就会），但这一批实测出一条真正的缺口——不是借来的，是用户当场提出的要求：砍掉的功能必须经用户确认。** 场景包与八份原文在 [borrow-runs-2/](borrow-runs-2/)。

方法同前：每条一个场景、各跑两遍（8 个 fresh `oracle` 受试，只读被测能力文件 + 场景包），判据运行前写下。

## 判定

| 条目 | 借来的做法 | 场景 | 实测 | 结论 |
|---|---|---|---|---|
| E | 砍功能时把每项**挂回它推进的那份工作**，孤儿项即删除候选 | 开票工具范围裁剪，混入三项挂不到工作的（换肤、深色模式、日报推送）（`feature-prune.md`） | 两遍都逐项追到价值/工作再决定：T04「no workflow/value delta」、T05「preference-only，'trending' 不是价值」、T08「'每天'是系统推送频率，不是用户任务，frequency-first 不因此升档」。孤儿项都被识别并延后 | **无用**（反向映射自发做到） |
| F | **最差的那一屏决定感受**，抽样要覆盖"背面"（设置、错误、空态） | 记账 App 月度报表上线，主路径打磨过，空状态临时文案、导出失败只手工试过一次（`visual-verify.md`） | 两遍都把"临时文案的空状态""只手测一次的 500 分支"标成本轮最高风险，并**拒绝**把手工断网那次算成已验证；未改动的设置页/登录页仍按能力要求全轴回归，不由自己"跳过" | **无用**（且能力里"覆盖不抽样"那条更强） |
| G | 反常读数**先排除别的解释**（口径、分母、同期改动、平台拆分） | 结算页改版后完成率 62%→38%，同周还有支付默认项变更与 10% 灰度（`runtime-smoke-verify.md`） | 两遍都拒绝把这份读数当本节点证据（类型不符 → `unprovable`），并列出三个混杂因素（另一处默认项改动、拼单灰度、无对照的周对周），要求 A/B 或 switchback 后才谈因果，明确写"相关性不是因果" | **无用** |
| H | Job 陈述三条约束：无产品名 / 有"当…时" / 功能·情感·社交分开 | 三个角色（老板、兼职会计、店员）写 JTBD（`product-concept.md`） | 两遍都写出"当…时，我想要…，这样…"且不含功能/界面词；都主动把用户原话与已确认方案标成**方案而非 job**，不许反写成处境。第三类（明示功能/情感/社交）没有逐条标注，但情感/社交诉求本身都出现了（"不用靠记性说话""不打断老板"） | **无用** |

## 这一批实测出来的真缺口（用户 2026-09-21 提出）

用户在测 E 期间提出：**「砍了什么功能，必须要与用户确认过才行」**。查过之后：

- 现在的机制只覆盖**节点图**：加节点/改依赖会在 bootstrap 与 `/run` 边界要求重新确认（`plan-confirmation.json` + `validate_bootstrap.py`/`validate_unattended_readiness.py` 的 `unconfirmed_plan_delta`）。
- **砍功能不在其中**：一个功能被砍，节点图可以完全不变，所以无人值守时它可以自己决定砍谁、你事后才看到。`feature-prune.md` 里没有任何"用户确认"字样（grep 为空）。
- 这一批的实测正好证实：E-1/E-2 两遍都把排除项写成 `Defer.` 当成定论，只回头问"Excel 迁移前提是否成立""要不要花掉剩余预算"，**没有把砍掉的那批交给用户确认**。

拟改动（`feature-prune.md`，两处约 4 行，待用户确认后才写入）：

```markdown
Cutting scope is the user's call, not this node's: `included = false` is a proposal until the user has
confirmed the dropped set. The report presents every exclusion as task + reason + tier and asks for that
confirmation; an unattended run records the dropped set as pending confirmation and does not let downstream
nodes implement the pruned scope as if it were approved.
```

```markdown
- Exclusions are confirmed by the user before they are treated as final (unattended runs route them as pending)
```

## 尚未验证

- 只有本机会话模型一个（`oracle`，每条两遍），不是跨模型样本；场景手写。
- 其余单主题项仍未测："没人反驳说明写得太安全"、去装饰测试（剥掉颜色看情感信号）、门自报覆盖率、
  稳定 schema 契约、"反常读数"之外的读数类条目。
- 第 5 步写法层（"删掉这段判断会变差吗"过一遍 `product-concept.md`）未做。