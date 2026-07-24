# Conditional Supporting Disciplines

Load and apply only the section whose trigger is present.

## Research

When a decision waits on facts outside the repository, investigate primary sources such as
official documentation, standards, source code, or first-party APIs. Capture findings in one
cited Markdown file using the repository's existing notes convention. Keep grilling or
planning independent branches moving while research runs when the host supports background
work.

## Prototype

A prototype is throwaway code that answers one design question.

- Logic/state question: build a tiny interactive terminal artifact that exposes state.
- UI question: build several radically different variants selectable from one route.
- Mark it clearly as a prototype and provide one run command.
- Use in-memory state unless persistence is the question.
- Skip production polish, tests, and abstractions.
- Fold the validated decision into the specs; keep prototype code off the main delivery
  branch and leave a context pointer to its captured throwaway branch.

## Codebase design

Design deep modules: substantial behavior behind a small interface, located at a clean seam
and tested through that interface.

Use these terms precisely:

- **Module**: interface plus implementation.
- **Interface**: everything callers must know, including invariants and error modes.
- **Implementation**: code hidden behind the interface.
- **Seam**: where behavior can vary and where the interface lives.
- **Adapter**: a concrete implementation occupying a seam.
- **Depth**: caller leverage per unit of interface.

Prefer fewer methods and parameters, hide complexity, accept dependencies rather than
constructing them, and return results rather than exposing internal side effects. Do not
invent a seam for a hypothetical second adapter.

## Merge conflicts

For an actual merge or rebase conflict:

1. Inspect history, operation state, and conflicting files.
2. Trace each side to commits, issues, specs, and the intent that produced it.
3. Resolve each hunk while preserving both intents where compatible; otherwise select the
   intent matching the current goal and record the tradeoff.
4. Never invent unrelated behavior and never abort merely to avoid resolution.
5. Run typechecks, tests, and formatting required by the repository.
6. Stage resolved files and finish the merge/rebase through all remaining commits.
