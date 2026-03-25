# UI Forge Eval Prompts

These prompts are the first-pass sanity checks for the fork.

## What They Test

1. fidelity check happens before refinement
2. `restore` is preferred when trusted design drift exists
3. `polish` is used only when alignment is already acceptable
4. boundary discipline in a real codebase

## Success Criteria

- performs a fidelity-first triage before editing
- chooses `restore` or `polish` correctly
- does not drift into feature implementation
- respects existing product behavior
- gives engineer-grade, file-grounded refinement guidance
- retains strong frontend taste without becoming a blank-canvas design generator

## Additional Review Questions

- Did the skill explicitly report whether a trusted baseline existed?
- Did it distinguish fidelity gaps from mere finish-quality gaps?
- Did it avoid polishing on top of obvious design drift?
