---
name: classify
description: Batch-classify or score many records (dozens or more) that all answer the same fixed questions — pick one of N options, place on a defined scale, or yes/no probability — by sending them to Jev (TypeSafe's typed decision model, via OpenRouter). For comment/ticket/email/lead/transcript triage and similar bulk judgments. Not for a handful of items, per-item different questions, or anything that needs generated text.
---

# classify — 用 Jev 做批量判断

Jev 只做一件事：对一段数据回答事先定好选项的题，并给出概率。它便宜、快，每条独立作答，不占你的上下文。
分工是：**你出题、校准、处理拿不准的；Jev 把同一组题对每一条答一遍。** 它答得快不等于答得对——
它的价值在于把"确定的大多数"和"需要细看的少数"分开，让你的注意力只花在后者上。
整个流程是一个闭环：样本暴露题目的毛病 → 你改题目或阈值 → 再看样本 → 认可后全量 → 拿不准的由你或用户裁决、
裁决写回结果 → 调好的题目存下来给下一次用。哪一环断了，结果就只是"Jev 说的"，不是"核实过的"。

## 什么时候用，什么时候不用

用：数据有几十条以上，每条问的是同一组问题，答案能事先枚举成选项 / 分档 / 是否。
不用：只有几条（你自己判更好）；每条要问的不一样；需要写出解释、摘要或改写；需要多步推理才能下结论
（拆成几道原子题后能用就拆，拆不开就不用）。

## 前提

- `OPENROUTER_API_KEY` 已设置。没有就停下告诉用户。可以提议改由你自己判，但要明说那不是 Jev 的结果。
- 数据来源在外发放行清单 `${XDG_CONFIG_HOME:-~/.config}/jev/allow.json`（`{"paths": [...]}`）里。
  脚本退出码 3 = 不在清单里、没有发出任何数据：把路径告诉用户、说明会发给 OpenRouter 上的 Jev，
  用户同意后再把路径加进清单。**不得绕过脚本、用 curl 或别的方式把数据发给 Jev。**

## 交付验收

每一条都要满足，做不到的在交付时明说。

1. **题目**（题目文件 `{"questions": {...}, "thresholds": {...}}`，`questions` 是 Jev 原生格式）：
   每题只问一件事；`choice` 的每个选项、`score` 的每一档、`noul` 的是与否都写判定标准（`criteria`），
   不能只有标签；阈值写进 `thresholds`（choice / score 填一个数，noul 填 `{"hi", "lo"}` 或一个数）。
   开始前先看 `${XDG_CONFIG_HOME:-~/.config}/jev/question-sets/` 里有没有同类数据用过的题目。
2. **数据**：JSONL，每行 `{"id", "state"}`；`state` 只放判断需要的字段，不带无关的个人信息。
   输入是你从别的文件转换出来的，`--source` 写原始文件的路径。
3. **校准并留下记录**：超过 50 行时，先 `--sample 20` 试跑（单独的输出文件），逐条看样本结果，数出你不同意几条。
   只是阈值不合适 → 改 `thresholds` 后 `rebucket`（不花钱）；题目本身有问题 → 改题目，用新输出文件重新试跑。
   认可后运行 `approve`，如实填 `--disagree` 与 `--notes`；仍有不同意却要继续，只能在用户同意时加 `--accept-reason`（写用户原话）。
   脚本没有 approve 记录时会拒绝全量运行。`--skip-calibration "理由"` 只在用户明确同意不校准时用，理由写用户的原话。
4. **全量跑**：花费超过上限（默认 1 美元）时脚本会先拒绝并给出估算；把估算告诉用户，同意后加 `--confirm-cost`。
5. **review 桶**：每一条要么由你判、要么交给用户，**不得当作 auto 用**。裁决写成 JSONL（`{"id", "by": "claude"|"user", "answers": {题目id: 结论}}`）
   用 `resolve` 记下；summary 的 `unresolved_review` 要么是 0，要么在交付说明里列出剩下的是哪些、为什么没裁决。
6. **failed 桶**：同一命令重跑一次（脚本只重试失败的）；仍失败的列出来。
7. **交付说明**必须包含：哪些结论来自 Jev、各桶条数、阈值、校准记录（样本数、不同意数、要点）、
   review 桶怎么处理的（你判了几条、交给用户几条、还剩几条）、有没有 `long_context` 行（这些行 Jev 更慢、更不准）、
   花费（summary 的 `cost_usd`）。结果表用 `export` 出 CSV：`final_*` 是最终结论，`decided_by` 是谁定的（`jev` / `claude` / `user`）。
8. **存题目**：校准通过的题目用 `save-set` 存下来，下次同类数据直接用。

## 命令

```bash
B="${CLAUDE_PLUGIN_ROOT}/scripts/jev_batch.py"
python3 "$B" run --input rows.jsonl --questions q.json --out sample.jsonl --source <原始数据> --sample 20
python3 "$B" rebucket --out sample.jsonl --questions q.json            # 只改了阈值时
python3 "$B" approve --out sample.jsonl --questions q.json --disagree 0 --notes "无"
python3 "$B" run --input rows.jsonl --questions q.json --out out.jsonl --source <原始数据>
python3 "$B" resolve --out out.jsonl --questions q.json --decisions decisions.jsonl
python3 "$B" export --out out.jsonl --csv out.csv
python3 "$B" save-set --out out.jsonl --questions q.json --name <简短名字>
```

`run`、`approve`、`rebucket` 打印 summary（同时写到 `<out>.summary.json`）。同一输出文件可以重复 `run`：已完成的行跳过，
失败的行重试；改了题目就要换输出文件，只改阈值不用。退出码：0 成功，2 拒绝（看 stderr 的原因），3 不在放行清单。

示例题目文件：

```json
{
  "questions": {
    "kind": {"type": "choice", "instructions": "这条留言属于哪一类？",
             "criteria": {"praise": "表达满意或感谢", "complaint": "表达不满或报告问题", "suggestion": "提出改进或新功能建议", "question": "在提问，等待回答"}},
    "needs_reply": {"type": "noul", "instructions": "这条留言是否需要我们回复？",
                    "criteria": {"true": "提了问题或投诉，且没有看到我们的回复", "false": "纯表态，或已经被回复过"}}
  },
  "thresholds": {"kind": 0.8, "needs_reply": {"hi": 0.9, "lo": 0.1}}
}
```
