# code-tuner

A Claude Code plugin skill that analyzes server-side code for architectural violations, cross-layer duplication, abstraction opportunities, and validation issues. Outputs a comprehensive score (0-100) and actionable refactoring task list. Supports three-tier, two-tier, and DDD architectures across Java, Go, Node.js, Python, .NET, Rust, PHP, and Ruby.

## Installation

```bash
claude plugin install /path/to/code-tuner-skill
```

## Usage

```
/code-tuner full
/code-tuner compliance
/code-tuner duplication
/code-tuner abstraction
/code-tuner report
```

Or use natural language:

```
请用 code-tuner 分析我的项目。项目路径是 /path/to/project。项目状态是未上线。
please use code-tuner to analyze my project at /path/to/project. It's pre-launch.
```

Modes:
- **full** — Phase 0 → 1 → 2 → 3 → 4 (default)
- **compliance** — Architecture compliance only
- **duplication** — Duplication detection only
- **abstraction** — Abstraction analysis only
- **report** — Regenerate report from existing phase outputs

Lifecycle is asked interactively if not specified (pre-launch or maintenance).

## Output

All output goes to `.allforai/code-tuner/` in your project root.

```
your-project/
└── .allforai/code-tuner/
    ├── tuner-profile.json        # Phase 0: 项目画像（架构类型、层级映射、模块列表）
    ├── phase1-compliance.json    # Phase 1: 架构违规列表
    ├── phase2-duplicates.json    # Phase 2: 重复检测结果
    ├── phase3-abstractions.json  # Phase 3: 抽象机会
    ├── tuner-report.md           # Phase 4: 综合报告（0-100 评分 + 问题热力图）
    └── tuner-tasks.json          # Phase 4: 重构任务清单（按优先级排序）
```

## License

MIT
