# UI Design Capability

> Generate UI design specifications from product artifacts.
> Internal execution is LLM-driven — design approach adapts to project type.

## Goal

Transform experience-map + product-map into concrete UI specifications:
design tokens, per-screen layouts, component specs, and optional interactive previews.

## What LLM Must Accomplish (not how)

### Required Outputs

| Output | What |
|--------|------|
| `ui-design-spec.md` | Per-screen specification: layout, components, states, interactions |
| `tokens.json` | Design tokens: color, typography, spacing, component, animation |

### Optional Outputs

| Output | When |
|--------|------|
| `preview/*.html` | Interactive HTML previews (if user wants visual validation) |
| `art-direction.md` | For games or visually-driven products |

### Required Quality

- Every screen from experience-map has a specification
- Design tokens are binding — downstream implementation must consume them
- State completeness: every screen shows all state variants
- Consumer maturity: consumer products get production-grade spec, not wireframes

## Methodology Guidance (not steps)

- **Design tokens first**: Establish visual language before screen design
- **Per-role previews**: Each role sees different screens — design separately
- **State completeness**: Every screen includes all state variants in the spec
- **Don't over-specify**: Describe intent and constraints, not pixel coordinates
- **Component reuse**: Identify shared components across screens, define once

## Specialization Guidance

| Project Type | UI Design Differences |
|-------------|----------------------|
| Consumer mobile app | Mobile-first, touch targets, thumb zones, offline states |
| Admin dashboard | Data density, table/form patterns, multi-action pages |
| Game | Art direction replaces UI design; mood board, style guide, character design |
| SDK/Library | Documentation design replaces UI design (Diátaxis framework) |
| CLI | No UI design needed — skip entirely |

## Knowledge References

### Phase-Specific:
- experience-map-schema.md: screen definitions and component specs to design from
- consumer-maturity-patterns.md: consumer UX maturity requirements
- product-design-theory.md §Phase-6: Design System, Atomic Design, WCAG, Gestalt

## Composition Hints

### Single Node (default)
Run after experience-map is complete.

### Skip Entirely
For backend-only projects, CLI tools, or when user explicitly skips.

### Split by Role
For apps with very different role UIs (e.g., consumer app + admin dashboard).
