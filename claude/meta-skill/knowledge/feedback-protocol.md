# Anonymous Feedback Protocol

> After experience extraction, propose universally useful findings as
> anonymous GitHub Issues on the myskills repository.

## When to Trigger

After learning extraction (learning-protocol.md), if any extracted items
are classified as universally useful (not project-specific):

- Mapping gaps in preset mapping files → useful for all users of that stack pair
- Discovery blind spots → useful for all projects
- Convergence issues → useful for meta-skill improvement
- Safety gaps → critical for all users

Project-specific items (e.g., "this project's auth is unusual") stay local only.

## Privacy Rules (MANDATORY)

Before proposing any Issue, verify the content contains:
- Tech stack names (React, SwiftUI, Go, Gin)
- Abstract pattern descriptions ("CRUD completeness check", "handler directory coverage")
- Threshold/config suggestions ("coverage 50% → 80%")
- NO project names, company names, domain-specific terms
- NO file paths from the user's project
- NO code snippets from the user's project
- NO user identity (name, email, username)
- NO business logic descriptions

## User Confirmation Flow

```
Orchestrator presents:

"本次执行发现了 {N} 条可能对 meta-skill 有改进价值的经验：
{numbered list of deidentified findings}

是否愿意匿名提交到 myskills GitHub Issues？(y/n/选择部分提交)"
```

- User says yes → submit all
- User says no → skip, keep local only
- User selects specific items → submit only those

## Issue Creation

For each approved item:

```bash
gh issue create \
  --repo <myskills-repo> \
  --title "[Auto Feedback] {tech_stack_pair} — {one_line_description}" \
  --body "$(cat <<'EOF'
## [Auto Feedback] {tech_stack_pair} — {description}

**Source**: meta-skill automatic feedback (anonymous)
**Tech Stack**: {source} → {target}
**Category**: {mapping-gap | discovery-blind-spot | convergence | safety}

### Description
{deidentified improvement suggestion}

### Suggested Change
{which knowledge file to modify and what to add/change}
EOF
)" \
  --label "feedback/auto,{tech_stack_label}"
```

## Fallback

If `gh` CLI is not available or not authenticated:
- Log the Issue content to `.allforai/bootstrap/pending-feedback.md`
- Inform user: "gh CLI 不可用，反馈已保存到 pending-feedback.md，您可以稍后手动提交"
