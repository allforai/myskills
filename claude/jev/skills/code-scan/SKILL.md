---
name: code-scan
description: Scan many code chunks (a whole repo, a diff, or every match of a pattern) against the same plain-language yes/no rules with Jev — semantic lint like "does this log line print a secret", "does this comment contradict the code", "does this change weaken a test" — then verify every hit yourself. Not for reviewing one file or for bug hunting that needs reasoning across files.
---

# code-scan — 用 Jev 按大白话规则扫代码

把代码切成小块，每块对同一组"是否"规则各答一次。Jev 负责在大量代码里快速圈出可疑的块；
**结论由你下**：Jev 圈出的每一块你都要打开源码确认，没确认过的不算问题。
你的确认与否定要写回结果——它们决定这条规则下次还能不能用：误报过半的规则不改就存不下来。

## 什么时候用，什么时候不用

用：规则能写成对单个代码片段的是 / 否问题，且要过的片段很多（整个仓库、一个大 diff、某个模式的全部出现处）。
不用：只看一两个文件（你直接读）；结论依赖跨文件追踪或运行时行为；规则本身需要推理才能判断。

## 前提

与 classify 相同：`OPENROUTER_API_KEY` 已设置；**代码仓库根目录**在 `${XDG_CONFIG_HOME:-~/.config}/jev/allow.json` 里
（切块脚本与批量脚本都会检查，退出码 3 = 不在清单、没有发出任何东西：告诉用户会把代码片段发给 OpenRouter 上的 Jev，
用户同意后再加）。不得绕过脚本、用 curl 或别的方式发送代码。

## 交付验收

1. **规则文件**：每条规则是一道 `noul` 题，只问一件事，写 `criteria` 说明"是"和"否"各指什么；阈值写进 `thresholds`。
   先看 `question-sets/` 里有没有现成的规则集。
2. **切块**：按规则挑切法——日志、密钥一类用 `grep`（先用模式缩小范围），注释与命名用 `window`，
   审一次改动用 `hunk`，小文件多的仓库用 `file`。切块文件放在临时目录，不要写进用户仓库。
3. **校准**：块数超过 50 时先 `--sample 20` 试跑，检查样本里的命中与漏判，调规则或阈值，`approve` 留记录。规则同 classify。
4. **全量跑**：`--source` 写仓库根目录；花费超上限时把估算告诉用户再 `--confirm-cost`。
5. **逐条确认并写回**：`hits` 列出的每一块，你都打开源码对应行确认，每条命中写一行裁决
   `{"id", "by": "claude", "rule": "<规则id>", "verdict": "confirmed"|"false_positive", "note": "一句理由"}`，用 `resolve` 记下。
   报告里只把 confirmed 的列为问题（文件、行号、规则、理由）；false_positive 单独列为"Jev 误报"并计数。
6. **review 桶**（落在上下阈值之间的块）：说明条数；数量少就逐条看并同样写裁决，多就按规则抽查，写明抽查了多少。
7. **交付说明**：规则清单、切法、块数、各桶条数、每条规则的命中 / 确认 / 误报（summary 的 `rules`）、review 怎么处理的、花费。
   本 skill 只报告，不改代码；修不修由用户决定。
8. **存规则**：值得复用的规则集用 `save-set` 存；脚本拒存时（某条规则已核实 ≥ 4 次且误报过半），先改那条规则。

## 命令

```bash
K="${CLAUDE_PLUGIN_ROOT}/scripts/code_chunks.py"
B="${CLAUDE_PLUGIN_ROOT}/scripts/jev_batch.py"
python3 "$K" --root <repo> --by grep --pattern 'log|print' --context 3 --out <tmp>/chunks.jsonl
python3 "$B" run --input <tmp>/chunks.jsonl --questions rules.json --out <tmp>/sample.jsonl --source <repo> --sample 20
python3 "$B" approve --out <tmp>/sample.jsonl --questions rules.json --disagree 0 --notes "无"
python3 "$B" run --input <tmp>/chunks.jsonl --questions rules.json --out <tmp>/scan.jsonl --source <repo>
python3 "$B" hits --out <tmp>/scan.jsonl --questions rules.json
python3 "$B" resolve --out <tmp>/scan.jsonl --questions rules.json --decisions <tmp>/verdicts.jsonl
python3 "$B" save-set --out <tmp>/scan.jsonl --questions rules.json --name <简短名字>
```

切法参数：`--by file|window|grep|hunk`；`window` 用 `--lines 80 --overlap 10`；`grep` 用 `--pattern <正则> --context N`；
`hunk` 用 `--base <git 引用> --context N`；可在末尾加路径限定范围。块的 id 是 `路径:起始行-结束行`。

示例规则文件：

```json
{
  "questions": {
    "logs_secret": {"type": "noul", "instructions": "这段代码是否把密钥、token、密码或完整卡号写进了日志或打印输出？",
                    "criteria": {"true": "日志 / print 的参数里直接或间接包含凭据或卡号", "false": "没有日志，或日志内容不含凭据"}},
    "stale_comment": {"type": "noul", "instructions": "这段代码里是否有注释描述的行为与代码实际行为不符？",
                      "criteria": {"true": "注释说的和代码做的对不上", "false": "注释与代码一致，或没有注释"}}
  },
  "thresholds": {"logs_secret": {"hi": 0.8, "lo": 0.1}, "stale_comment": {"hi": 0.9, "lo": 0.1}}
}
```
