# UI Design Capability

> Generate UI design specifications and interactive HTML previews from product artifacts.

## Purpose

Transform experience-map + product-map into concrete UI specifications:
per-screen layout, component hierarchy, design tokens, and interactive HTML previews
that stakeholders can review in a browser.

## Protocol

### Design Token Generation
From experience-map screens and detected patterns:
- Color palette, typography scale, spacing system
- Component tokens (button variants, input styles, card layouts)
- Output: `tokens.json`

### Per-Screen Specification
For each screen in experience-map:
- Layout structure (header/content/footer, sidebar, grid)
- Component hierarchy (which components, nesting, data flow)
- State variants (empty/loading/error/success visual treatment)
- Micro-interactions (hover, focus, transition, loading animation)

### HTML Preview Generation
For each role in role-profiles:
- Generate a standalone HTML file showing that role's screens
- Use design tokens for consistent styling
- Interactive: clickable navigation between screens
- Output: `.allforai/ui-design/preview/{role-id}.html`

Output: `.allforai/ui-design/ui-design-spec.md` + `tokens.json` + `preview/*.html`

## Rules (Must Preserve)

1. **Design tokens are binding**: Downstream implementation must consume tokens.json.
2. **Per-role previews**: Each role sees different screens — generate separate previews.
3. **State completeness**: Every screen preview includes all state variants.
4. **Consumer maturity**: If experience_priority = consumer, previews must show production-grade UI, not wireframes.

## Composition Hints

### Single Node (default)
Run after experience-map is complete.

### Skip Entirely
For backend-only projects, CLI tools, or when user explicitly skips UI design.

### Split by Role
For apps with very different role UIs (e.g., consumer app + admin dashboard): one node per role.
