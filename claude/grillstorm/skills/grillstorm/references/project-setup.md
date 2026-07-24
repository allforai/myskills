# Project Setup

Run once per repository before the Grillstorm phases. Reuse and update an existing setup
rather than appending duplicates.

## Explore

Inspect:

- `git remote -v` and `.git/config`;
- root `CLAUDE.md` and `AGENTS.md`, especially an existing `## Agent skills` block;
- `docs/agents/`;
- root `CONTEXT.md` or `CONTEXT-MAP.md`;
- root and context-local `docs/adr/`;
- `.scratch/`;
- monorepo signals such as workspace configuration and populated packages.

Present what is already settled and what remains missing. Do not ask about facts exploration
already established.

## Resolve missing configuration

Ask one section at a time with a recommended answer.

### Issue tracker

Recommend GitHub when the remote is GitHub, GitLab when it is GitLab, otherwise local
Markdown. Support another tracker through a short user-supplied operating description.

Record:

- where issues/specs live;
- CLI or file operations for create/read/comment/label/close;
- whether pull/merge requests are a request surface, default `no`.

Local Markdown uses `.scratch/<feature>/spec.md` and one file per issue under
`.scratch/<feature>/issues/<NN>-<slug>.md`.

`docs/grillstorm/<goal>/tasks/` is the long-run execution state. Specs and tickets are also
published to the configured tracker as required by `to-spec` and `to-tickets`; store their
IDs and URLs in `tasks/catalog.md`.

### Triage labels

Because Grillstorm produces executable tickets, configure these canonical roles:

| Role | Default tracker label | Meaning |
| --- | --- | --- |
| `needs-triage` | `needs-triage` | Maintainer evaluation required |
| `needs-info` | `needs-info` | Waiting for information |
| `ready-for-agent` | `ready-for-agent` | Fully specified and autonomous |
| `ready-for-human` | `ready-for-human` | Requires human authority or execution |
| `wontfix` | `wontfix` | Intentionally not actioned |

Recommend defaults. Ask for overrides only when the repository already uses different label
strings. Later `to-spec` and `to-tickets` stages use this mapping when publishing artifacts.

### Domain docs

Default silently to a root `CONTEXT.md` plus `docs/adr/` for a normal repository. Offer
multi-context layout only when genuine monorepo or bounded-context evidence exists:
`CONTEXT-MAP.md` points to per-context glossaries and ADR directories.

### Instruction file

Update `CLAUDE.md` when it exists; otherwise update `AGENTS.md`. If neither exists, ask which
one to create. Never create the other file or overwrite surrounding user content.

## Confirm and write

Show one draft containing:

- the `## Agent skills` block;
- `docs/agents/issue-tracker.md`;
- `docs/agents/triage-labels.md`;
- `docs/agents/domain.md`.

After confirmation, write or update them.

Use this instruction block:

```markdown
## Agent skills

### Issue tracker

<one-line summary>. See `docs/agents/issue-tracker.md`.

### Triage labels

<one-line summary>. See `docs/agents/triage-labels.md`.

### Domain docs

<single-context or multi-context summary>. See `docs/agents/domain.md`.
```

`issue-tracker.md` must contain concrete commands or local paths. `triage-labels.md` contains
the role mapping. `domain.md` tells agents to read the relevant glossary and ADRs, use their
vocabulary, and surface contradictions instead of silently overriding them.

Setup is complete only when the instruction block and all three docs agree. Later phases
read these files rather than assuming a tracker, label, or domain layout.
