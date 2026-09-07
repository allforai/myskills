# The second visual reviewer is any independent context, not a named tool

Amends ADR-0002. The invariant stays: every screenshot or art gate runs two visual reviews of the same evidence, each written in a context that has not read the other's report, blockers are the union, agreement is not required, repair reruns both, closure audit never replaces a review.

What changes is reviewer identity. ADR-0002 named the two reviewers as Codex CLI and Claude Code and made a missing Codex CLI a hard block (`blocked_by_missing_codex_cli`). That naming was scaffolding for the model tier of the time; it is now the single point where a whole `/run` fails on an unrelated CLI being absent, and on Codex hosts the file name `claude-code-visual-review.json` is simply wrong. From this decision:

- Reviewer one is the session's own fresh-context visual reviewer (a sub-agent that has not produced the images and does not read the other report).
- Reviewer two is, in order of preference, the other platform's CLI (Codex CLI on Claude hosts, `claude -p` on Codex hosts) when it is installed and can actually open images, otherwise a second fresh-context sub-agent on the current platform. Both are recorded in the visual-model-routing report with a `reviewer` field naming what actually ran.
- A missing cross-platform CLI is a warning recorded in the routing report, not a blocker. `blocked_by_missing_codex_cli` is retired; the only visual blockers are "no reviewer could open the images" and "fewer than two independent reports exist".
- Report file names are reviewer-neutral (`visual-review-1.json`, `visual-review-2.json`, plus `visual-review-reconciliation.json`); the reviewer identity lives inside the report.
- Neither reviewer may be the context that generated the images. Same-context self-review remains a downgrade, exactly as ADR-0002 and verification-protocol.md require.

Enforced by `validate_art_pipeline.py` and `validate_game_frontend_pipeline.py`, which must be updated in the same change as the skill text; changing this back requires changing the validators.
