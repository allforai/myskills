# UI Forge Input Contract

## Minimum Assumption

The target frontend already exists and is functionally usable.

If this assumption is false, `ui-forge` should stop and recommend returning to
normal implementation flow first.

## Preferred Inputs

When available, consume these artifacts:

1. `.allforai/ui-design/ui-design-spec.json`
2. `.allforai/ui-design/tokens.json`
3. `.allforai/ui-design/component-spec.json`
4. `.allforai/ui-design/screenshots/`
5. `.allforai/experience-map/experience-map.json`

## Behavior Without Upstream UI Artifacts

If the project has no `ui-design` output yet, `ui-forge` can still work by using:

- real code context
- local component patterns
- user request

In that case it should bias toward `polish`, not `restore`.

## Non-Goals

`ui-forge` should not:

- invent a new product direction
- refactor backend logic
- re-architect routing or state management unless necessary for a UI-only fix
- act as a replacement for complete frontend implementation
