# cross-exam 模型分层 — 思维测试记录

日期：2026-09-06。被测文本：`claude/superstorm/skills/cross-exam/SKILL.md`、`codex/cross-exam-skill/SKILL.md`、
`visual/visual-acceptance.md`（镜像）。方法：每个场景一个 fresh-context 子 agent，只给文本和场景，
不给期望答案，要求引用原句。

设计：按"观察还是判断"定档。会话档（不传 model，继承）= 盘问官、作者自审时的复核官；判断档
（opus / gpt-5.6-sol）= 普查官、视觉 reviewer；取证档（sonnet / gpt-5.6-luna，退 terra）= 实测官、
枚举官。重派同档；`entries[].agent_model`、`census_model`、`patterns[].enumerator_model` 落盘。

| 场景 | 判据 | 结果 |
|---|---|---|
| T1 Claude 主控、Opus 会话：残缺重派想升 opus；作者自审复核官选模；普查官选模；落盘字段 | 重派同档 sonnet；复核官不传 model；普查 opus；三个字段 | 通过：四点都直接引到新条文；唯一推断是把场景描述对上“返回残缺”的定义 |
| T2 Codex 主控：spawn_agent 无 model 参数；有参数时三种字面量与回退；跨平台双审命令；重派升档 | 会话模型加 `(session)`；sol / luna / luna，退 terra；`claude -p --model opus` 与 `codex exec -m gpt-5.6-sol`；不升 | 通过：四点都直接引到条文。唯一推断是 `(session)` 后缀是否也适用于 enumerator_model，已把三个字段写明 |
