# UI Forge Eval Prompts

These prompts are the first-pass sanity checks for the fork.

## What They Test

1. `polish` mode selection
2. `restore` mode selection
3. boundary discipline in a real codebase

## Success Criteria

- chooses `polish` or `restore` correctly
- does not drift into feature implementation
- respects existing product behavior
- gives engineer-grade, file-grounded refinement guidance
- retains strong frontend taste without becoming a blank-canvas design generator
