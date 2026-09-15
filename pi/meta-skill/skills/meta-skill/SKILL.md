---
name: meta-skill
description: >
  Explicitly invoked Pi adapter for the myskills product pipeline. Use only when the
  user invokes /skill:meta-skill or /skill:bootstrap for a project that needs product,
  experience, art, or game design before implementation and verification. Generate
  project-specific node-specs, .allforai/bootstrap/workflow.json, and .pi/skills/run/SKILL.md.
  For one large engineering goal without a product-design phase, tell the user about
  superstorm or grillstorm on Claude/Codex instead. User-invoked only; never invoke it yourself.
---

# Meta-Skill — Pi

用户显式调用 `/skill:meta-skill [command]` 才运行。模型不得自行启动。
此包是 Claude meta-skill 的 Pi 适配：共享 `.allforai/` 合约。完成度盘问是另一个包的 `/skill:cross-exam`。
不声称 superstorm、grillstorm 或 product-review 已移植到 Pi。

命令参数（`/skill:meta-skill` 之后的 `User:` 行）选择入口。读完对应文件后只执行那一个，不要继续本文件。

| 参数 | 执行 |
|------|------|
| 空、`bootstrap`、或一个项目路径 | 读取并遵循 `../bootstrap/SKILL.md` |
| `setup [check\|reset\|update\|impact]` | 读取并遵循 `../setup/SKILL.md` |
| `journal [topic]` | 读取并遵循 `../journal/SKILL.md` |
| `journal-merge` | 读取并遵循 `../journal-merge/SKILL.md` |
| `run` | 停止。run 由 bootstrap 写到目标项目 `.pi/skills/run/SKILL.md`。告诉用户在那个项目里调用 `/skill:run`，不要在这里伪造编排器。 |

相对路径从本 skill 目录解析。不要把 `claude/meta-skill/skills/` 下的能力 `SKILL.md` 注册或当作 Pi skill 调用。
