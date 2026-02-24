# 💀 DeadHunt

**Hunt down dead links, ghost APIs, and broken CRUD in your web app.**

> An [Agent Skill](https://agentskills.io) for Claude Code, OpenCode, Codex, and any SKILL.md-compatible agent.

## What it does

| Problem | How it's found |
|---------|---------------|
| 🔴 Dead links (404) | 5-layer scanning: navigation → interaction → API → resource → edge cases |
| 🟡 Incomplete CRUD | Per-module check: does every module have the Create/Read/Update/Delete it needs? |
| 👻 Ghost features | Bidirectional: backend API exists but no UI button calls it |
| 🗑️ Stale UI | Intent classification: is this dead link a bug to fix, or junk to clean up? |
| 🔒 Permission blindspots | Frontend shows button but user lacks permission |
| 📊 Data display issues | Page opens but shows `undefined`, `NaN`, `Invalid Date` |
| 🔄 Broken flows | Create → Save → List doesn't show new item |
| 🏷️ Field inconsistencies | Cross-layer check: UI field ↔ API field ↔ Entity field ↔ DB column |

## Supported platforms

| Platform | Install method | Status |
|----------|---------------|--------|
| **Claude Code** | Plugin marketplace or `~/.claude/skills/` | ✅ Full support |
| **Claude.ai** | Upload as custom skill | ✅ Full support |
| **OpenCode** | `.opencode/skills/` or `~/.config/opencode/skills/` | ✅ Compatible |
| **Codex CLI** | `.agents/skills/` or `~/.codex/skills/` | ✅ Compatible |
| **Cursor / Windsurf / Roo Code** | Via [OpenSkills](https://github.com/numman-ali/openskills) loader | ✅ Compatible |

## Quick install

### Claude Code (recommended)

```bash
claude plugin add dv/deadhunt-skill
```

### Other platforms

Clone and copy the plugin to your agent's skill directory:

```bash
git clone https://github.com/dv/deadhunt-skill.git
```

## Usage

Once installed, just ask your agent:

```
请用 deadhunt 技能验证我的项目。
项目路径是 /path/to/project。
应用跑在 http://localhost:3000。
```

The agent will automatically detect and use the skill. See [SKILL.md](SKILL.md) for full documentation including:

- 6 usage scenarios (single app, multi-client, quick scan, incremental, etc.)
- Login/auth configuration (form, token, SSO, storage state)
- 3 verification levels (quick scan 30s, standard 2min, full 10min)
- FAQ with 15+ common questions

## Project structure

```
deadhunt-skill/
├── README.md                          # This file
├── LICENSE                            # MIT
├── SKILL.md                           # Main skill file
├── .claude-plugin/
│   ├── plugin.json                    # Claude Code plugin manifest
│   └── marketplace.json               # Claude Code marketplace catalog
├── commands/
│   ├── deadhunt.md                    # Main slash command
│   └── fieldcheck.md                  # Field consistency check command
├── docs/
│   ├── quick-start.md                 # Quick start guide
│   ├── workflow.md                     # Workflow overview
│   ├── auth-strategy.md               # Auth configuration
│   ├── phase0-analyze.md              # Phase 0: Project analysis
│   ├── phase1-static.md               # Phase 1: Static scan
│   ├── phase2-plan.md                 # Phase 2: Test planning
│   ├── phase3-test.md                 # Phase 3: Index (routes to sub-files)
│   ├── phase3/                        # Phase 3: Deep testing sub-files
│   │   ├── overview.md                # Performance optimization & levels
│   │   ├── 404-scanner.md             # Global monitor + Layer 1-5
│   │   ├── intent-classification.md   # Dead link intent (FIX/CLEAN/HIDE/PERM)
│   │   ├── validation.md              # CRUD + data display + business flow
│   │   ├── convergence.md             # Multi-round convergence
│   │   └── patrol.md                  # Patrol engine (Flutter)
│   ├── phase4-report.md               # Phase 4: Report generation
│   ├── phase5-supplement-test.md      # Phase 5: Supplementary tests
│   ├── faq.md                         # FAQ
│   └── fieldcheck/
│       ├── overview.md                # Field check execution flow
│       ├── extractors.md              # Layer extraction strategies
│       ├── matching.md                # Smart matching algorithm
│       └── report.md                  # Report format and schemas
```

### Field consistency check

```
/deadhunt:fieldcheck              # Full chain: UI ↔ API ↔ Entity ↔ DB
/deadhunt:fieldcheck frontend     # Frontend only: UI ↔ API
/deadhunt:fieldcheck backend      # Backend only: API ↔ Entity ↔ DB
/deadhunt:fieldcheck endtoend     # End-to-end: UI ↔ DB (skip middle layers)
/deadhunt:fieldcheck --module user # Single module
```

## Verification levels

| Level | Time | What it does | When to use |
|-------|------|-------------|-------------|
| **Quick scan** | 30s | Static analysis only (no browser) | Every commit |
| **Standard** | 2-3 min | Static + browser walkthrough | Daily |
| **Full** | 10-15 min | + CRUD flow tests + multi-client checks | Before release |

## Multi-client architecture support

Built for real-world projects with multiple frontends:

```
Backend API
├── Admin dashboard (React)      — manages everything
├── Merchant portal (Vue)        — manages own products/orders
├── Customer website (Vue)       — browses and buys
├── Customer H5 (Vue mobile)     — same as website, mobile optimized
├── Customer App (Flutter)       — native mobile
└── Customer MiniProgram (Wechat)— WeChat mini program
```

The skill understands role-based differences (admin vs merchant vs customer) and platform differences (web vs mobile vs mini program), so it won't false-positive when Admin lacks a "place order" button (that's the customer's job).

## Output

All output goes to `.allforai/deadhunt/` in your project root — completely separate from your existing Playwright config and tests.

```
your-project/
└── .allforai/deadhunt/
    ├── playwright.config.ts          # 验证专用配置（不侵入项目原有配置）
    ├── .auth/                        # 验证专用登录状态
    │   └── admin.json
    └── output/                       # 验证产出（自动生成）
        ├── validation-profile.json   # 项目概况（初始化后持久复用）
        ├── static-analysis/          # Phase 1 静态分析结果
        ├── tests/                    # 生成的验证测试脚本
        ├── dead-links-report.json    # 死链报告
        ├── validation-report-*.md    # 可读报告（按客户端分文件）
        ├── fix-tasks.json            # 修复任务清单
        └── field-analysis/           # /fieldcheck 输出
            ├── field-profile.json    # 跨层字段提取结果
            ├── field-mapping.json    # 字段对应关系
            ├── field-issues.json     # 问题清单
            └── field-report.md       # 可读报告
```

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Test your changes
4. Submit a PR

## License

MIT — see [LICENSE](LICENSE) for details.

