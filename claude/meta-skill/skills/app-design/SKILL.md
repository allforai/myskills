# App Design Skill Pack

> Internal bundled sub-skill pack for app product design. Status: bundled,
> inactive, not wired.

## Purpose

App Design owns non-game product planning after concept discovery and before
UI/code implementation. It turns product concept, user goals, business
constraints, and human preferences into screen, flow, content, data,
interaction, and downstream implementation contracts.

This pack is parallel to `game-design`, but uses app product disciplines:
product, UX, content, data, growth, compliance, and engineering handoff.

## Current Children

| Layer | Child skill | Responsibility |
|---|---|---|
| `00-env` | `app-design-registry` | App design scope, selected product type, owners, required/optional nodes, and artifact index. |
| `10-concept` | `audience-positioning-spec` | Target audience, jobs, decision criteria, accessibility, business context, and user preferences. |
| `10-concept` | `job-story-spec` | Jobs-to-be-done, use cases, triggers, desired outcomes, risks, and acceptance signals. |
| `20-spec` | `information-architecture-spec` | Navigation model, screen taxonomy, hierarchy, routes, and entry points. |
| `20-spec` | `user-flow-spec` | Primary, alternate, empty, error, onboarding, and recovery flows. |
| `20-spec` | `feature-priority-spec` | MVP scope, release cuts, dependency order, non-goals, and tradeoffs. |
| `20-spec` | `screen-requirements-spec` | Per-screen purpose, data, actions, states, validation, and handoff requirements. |
| `20-spec` | `content-model-spec` | Content entities, microcopy, tone, empty/error/loading copy, and localization hooks. |
| `20-spec` | `data-model-spec` | Product entities, fields, relationships, permissions, lifecycle, and API implications. |
| `20-spec` | `interaction-pattern-spec` | Component behavior, state transitions, feedback, gestures, loading, and accessibility. |
| `20-spec` | `permissions-notifications-settings-spec` | Account, privacy, permissions, notifications, settings, consent, and preference controls. |
| `20-spec` | `monetization-subscription-spec` | Pricing, subscription, trial, paywall, entitlement, cancellation, and fairness constraints. |
| `30-generate` | `ui-input-handoff-generation` | Structured handoff for UI design: screens, flows, states, copy, tokens, and priorities. |
| `30-generate` | `program-handoff-generation` | Structured handoff for implementation nodes: data, APIs, state, permissions, and tests. |
| `40-qa` | `flow-coverage-qa` | Validate flows cover jobs, screens, errors, empty states, and recovery paths. |
| `40-qa` | `app-design-closure-qa` | Final cross-contract closure before approval and downstream implementation. |

## Canonical Invocation Paths

```text
${CLAUDE_PLUGIN_ROOT}/skills/app-design/00-env/app-design-registry/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/app-design/10-concept/audience-positioning-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/app-design/10-concept/job-story-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/app-design/20-spec/information-architecture-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/app-design/20-spec/user-flow-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/app-design/20-spec/feature-priority-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/app-design/20-spec/screen-requirements-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/app-design/20-spec/content-model-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/app-design/20-spec/data-model-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/app-design/20-spec/interaction-pattern-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/app-design/20-spec/permissions-notifications-settings-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/app-design/20-spec/monetization-subscription-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/app-design/30-generate/ui-input-handoff-generation/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/app-design/30-generate/program-handoff-generation/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/app-design/40-qa/flow-coverage-qa/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/app-design/40-qa/app-design-closure-qa/SKILL.md
```

## Boundary

App Design must not implement code, generate visual UI assets, or invent
business decisions after the concept phase. Missing decisions must route back to
product concept or the relevant app-design child skill. Downstream app UI,
frontend, backend, and QA nodes consume this pack through explicit handoff
artifacts, not conversation memory.
