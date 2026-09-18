# 产品体验改造 — 真实宿主验收记录

状态：**待人工执行（unfilled）**。本文件目前是 T-M5-16 的空白模板，不是验收结果。

本轮改造的核心主张——"真实宿主会话里，bootstrap 面对真实用户能产出好的体验方向，并据此交付体验良好的产品"——
是 reality gate：M5 的思维测试（[product-experience-thought-tests.md](product-experience-thought-tests.md)）只证明了
受测文本在模拟决策下站得住，没有、也不可能替代一次真实的人机对话。自动化执行器**不得**代填本文件：
没有人坐在宿主前面就没有真实会话，凭空写下的症状判定与 `host-run` 结论是伪证。
因此下面每个判定字段都停在占位符上，`## 结论` 停在 `host-run: pending`；
T-M5-16 的验收命令在被人填完之前必然失败，这是预期状态，不是缺陷。

填写者：仓库所有者，按 `## 步骤` 逐条执行后就地改写本文件（占位符改成实测值，删掉本段与各处"待人工填写"）。
runbook 出处：[`docs/superpowers/plans/2026-09-18-regression-parity-plan.md`](../superpowers/plans/2026-09-18-regression-parity-plan.md) 的
`Runbook: real-host bootstrap run`。本文件与该 runbook 不一致时，以 plan 为准。

## 执行前须知

- **不要**在 `/Users/aa/workspace/ink-scent` 里操作：本轮的授权信封禁止写入该目录。重跑用新建的空目录。
- 待验收的是本分支（`product-experience-overhaul`）的插件版本：meta-skill 0.20.0 / superstorm 0.43.0。
- 对话里**不要**提示宿主"要做体验设计"、"要有设计节点"之类。三个症状要在不被提示的情况下自己消失才算数。
- 一次会话跑不完可以分次，但每次都要把宿主版本与日期记进 `## 环境`。

## 步骤

1. 安装本分支版本的插件（meta-skill 0.20.0 / superstorm 0.43.0），在 Claude Code 里确认 `/bootstrap` 可用。
2. 新建一个空目录（如 `~/workspace/ink-scent-rerun`），`git init`，在其中开启新的 Claude Code 会话。
3. 把 ink-scent 当初的**原始请求原文**（取自 ink-scent 2026-09-14 的会话记录）粘贴给 `/bootstrap`。正常对话，不要提示它"要做体验设计"。
4. 观察并记录 bootstrap 对话：
   - 是否在讨论体验之前先给出 2–3 条体验方向提案并标明推荐；提案是否回答"谁 / 什么情境 / 什么感受 / 为何回来"，
     而不是把"碎片化学习"直译成时长选择器 / 题型清单（**症状 1**）；
   - 你选定或说"你定"之后，它记的是 `select` 还是 `delegate`；你沉默时它是否自行确认。
5. bootstrap 结束后检查 `.allforai/bootstrap/workflow.json`：是否存在产出 `.allforai/app-design/spec/user-flow-spec.json` 等的
   体验设计节点，是否有 design / runtime 两阶段体验评审且收尾受其阻断（**症状 2**）。
6. 执行 `/run` 到完成。打开产物应用：首次使用是否出现要求用户手填"服务地址"之类的输入框；
   若实现节点遇到未规定的用户可见决定，运行记录里是否出现 `unspecified_user_visible_decision` 而不是自造界面（**症状 3**）。
   完成输出是否打印受托决定清单。
7. 执行 `/product-review`：它是否采信 `docs/experience-review/runtime.md` 而不重评。
8. 可选：在 Codex 与 Pi 宿主各重复步骤 2–5，核对适配器行为一致（Pi 用纯文本提问）。
9. 把结果填进下面的 `## 环境` / `## 症状对照` / `## 对话摘录` / `## 结论`。

## 环境

| 项 | 值 |
|---|---|
| 宿主 | 待人工填写（Claude Code / Codex / Pi，含 CLI 版本） |
| 插件版本 | 待人工填写（meta-skill 0.20.0 / superstorm 0.43.0，以实测为准） |
| 受测 commit | 待人工填写（分支 `product-experience-overhaul` 的具体 commit） |
| 日期 | 待人工填写 |
| 重跑目录 | 待人工填写（**不得**是 `/Users/aa/workspace/ink-scent`） |
| 原始请求来源 | 待人工填写（ink-scent 2026-09-14 会话记录的位置） |

## 症状对照

三行对应本轮诊断的三个症状。每行的判定只能取 `fixed` / `not-fixed` / `partial` 三者之一，
写法是 `verdict:` 后面直接跟那个词（去掉尖括号与整段占位文字），并给出可复查的证据指针
（对话轮次、`.allforai/` 里的文件路径、截图文件名等）；**不给证据指针的判定不算数**。

| 症状 | 本次观察 | 判定与证据 |
|---|---|---|
| 症状 1 直译：把"碎片化学习"直译成时长选择器 / 题型清单，没有先提案体验方向 | 待人工填写（是否先 `propose` 2–3 条方向并标明推荐；提案是否答了谁 / 情境 / 感受 / 为何回来） | `verdict: <fixed\|not-fixed\|partial — 待人工填写>`；证据：待人工填写（对话轮次 + `.allforai/bootstrap/` 里的意图记录） |
| 症状 2 无设计节点：工作流零个体验设计节点、无 design/runtime 两阶段体验质量门 | 待人工填写（`workflow.json` 里体验设计节点与两次评审是否在场、收尾是否被其阻断） | `verdict: <fixed\|not-fixed\|partial — 待人工填写>`；证据：待人工填写（`.allforai/bootstrap/workflow.json` 的节点 id + `.allforai/app-design/` 产物路径） |
| 症状 3 服务地址输入框：最终用户界面里出现"服务地址 / 访问凭证"手填框，未规定的用户可见决定被自造界面吞掉 | 待人工填写（首次使用是否要手填服务地址；遇到未规定决定时是否上报 `unspecified_user_visible_decision`） | `verdict: <fixed\|not-fixed\|partial — 待人工填写>`；证据：待人工填写（首启截图 + 运行记录里的 `unspecified_user_visible_decision` 条目） |

附带观察（不构成判定，但一并记录）：

- `select` vs `delegate`：待人工填写（你选定时记的是什么；说"你定"时记的是什么；你沉默时它是否自行确认）。
- 完成输出的受托决定清单：待人工填写（是否打印、内容是否与实际受托选定一致）。
- `/product-review`：待人工填写（是否采信 `docs/experience-review/runtime.md`，有无重评）。
- 步骤 8（可选）：待人工填写（Codex / Pi 适配器行为是否一致；Pi 是否全程纯文本提问）。

## 对话摘录

按轮次贴关键原文，至少覆盖：体验方向提案那一轮、你选定或委托那一轮、`/run` 里出现未规定用户可见决定的那一处、
`/product-review` 引用既有评审的那一段。原文照贴，不要转述。

> 待人工填写

## 结论

host-run: pending

填写说明：人工执行完毕后，把上面这一行改成 `host-run: pass`（三个症状都消失，且过程中没有新的体验级退化）
或 `host-run: fail`（任一症状仍在，或出现新的退化），并在下面一段写清判定理由与后续动作。
在此之前本文件不构成验收证据。

- 判定理由：待人工填写
- 后续动作：待人工填写（若 fail，指向需要返工的任务或文本）
