# 单主题借思路 · 第一批基线（A/B/C/D）

日期：2026-09-21。结论：**四条里 1 条有用（A 暂缓带重开条件，且缺的是"放它的位置"），3 条没用（模型自己就会）——不采纳的照样一个字都不加；A 的拟改动等用户确认。**

方法与前几轮一致：每条一个场景，各跑两遍（共 8 个 fresh 受试，`oracle`，只读被测能力文件 + 场景包）；
判据在运行前写下。场景包与八份原文在 [borrow-runs-1/](borrow-runs-1/)。

## 判定

| 条目 | 借来的做法 | 场景 | 实测 | 结论 |
|---|---|---|---|---|
| A | 说"以后再做"必须写明**什么情况发生就重新捡起来** | 独立开票工具 3 周裁剪范围（`feature-prune.md`） | 两遍都把"缓"和"砍"在文字里分开了（"本次对 T04–T09 是延后而非砍掉，未来版本重新进入 gap"；"T05 待海外需求出现再开"），**但没有逐项写出可观察的重开条件**——因为没有地方写 | **有用**：缺一个字段 |
| B | 综合多份材料要**每份都取到**，不能前两份定调 | 六份材料（两份行业报告、两篇竞品博客、一份评测、一个论坛帖）综合成结论（`product-concept.md`） | 两遍都把六份逐份记账：A/B 口径冲突"双记并标 unresolved、不取平均不择一"；C/D 降权为"自述主张，不计入 strengths"；E 作唯一硬价格；F 作行为线索（3 条返工抱怨 + 2 条够用）。没有出现"只看前两份" | **无用** |
| C | 情绪曲线**必须有低谷，低谷必须有出处**；"每阶段都满意"是反例 | 跨行转账六步流程（`journey-emotion-schema.md`） | 两遍都写出低谷（step3 anxious 5 / step4 frustrated 6 或 anxious 6 / step5 anxious 7）并挂 `source_refs` 指向给定评论与访谈；收尾正向但不掩盖低谷 | **无用**（schema 里"强度不得挤在 3–5""high/critical 要 source_refs"已经逼出来了） |
| D | 每个目标指标配一个**护栏指标**，且永不被平均 | 客服提速工具写成功指标（`product-concept.md` Sub-Phase 9） | 两遍都写了质量护栏与反作弊条款：D-1 点名"只看速度可以被'先回一句已收到'刷满"并列 reopen/CSAT/转人工；D-2 直接写"判定规则：S1 达标但任一护栏越线 → 指标判为未达成，登记 `speed_gaming`" | **无用** |

B/C/D 的通过不是"勉强"，是它们自发写出了条文想要的动作；A 的缺口也不在判断力，而在产物结构——
模型知道那些项是"缓"而不是"砍"，但 `prune-tasks.json` 的字段只有 `included/reason/tier`，没有承载"何时重开"的位置。

## A 的拟改动（待用户确认后才写入）

`claude/meta-skill/knowledge/capabilities/feature-prune.md`，三处小改，共约 6 行：

1. schema 增加一个可选字段（`included=false` 且属"缓"时必填）：

```json
"reopen_when": "<string — optional, but required when included=false means 'not this release' rather than 'never': the observable signal that puts this task back on the table (a count, an event, or a date). Omit only for a permanent exclusion and say so in reason>"
```

2. schema 之后那段补一句：

```markdown
A deferred task and a rejected one are different decisions: `reopen_when` says what would bring it back
("a second customer asks for it", "after v1 has run four weeks"), and `reason` alone cannot stand in for it — "later" and "not needed" are not the same claim, and a downstream reader cannot tell which one was made.
```

3. Required Quality 增加一条：

```markdown
- Every `included = false` task either carries `reopen_when`, or states in `reason` that the exclusion is permanent and why
```

## 尚未验证

- 只有本机会话模型一个（`oracle` 四份 + 四场景各两遍），不是跨模型样本；场景手写。
- 其余单主题项仍未测：反向映射（功能逐项挂回结果）、护栏…以外的 Job 语法约束、"没人反驳说明写得太安全"、
  去装饰测试、最差触点抽样（覆盖设置/错误/空态）、反常读数先排除、稳定 schema 契约、门自报覆盖率。
- 第 5 步写法层（"删掉这段判断会变差吗"过一遍 `product-concept.md`）未做。