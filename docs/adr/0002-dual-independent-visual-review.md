# Visual review is two independent reviewers; blockers are the union

Every screenshot or art gate runs two visual reviews of the same evidence: Codex CLI and Claude Code each open the images and write their own report (`codex-*-visual-review.*`, `claude-code-visual-review.*`). Neither reads the other's report before writing its own, and neither is skipped to save tokens. A reconciliation step (`*-reconciliation.json`) merges findings; a blocker or major finding from either reviewer blocks, agreement is not required, and a contradiction resolves in favour of the blocking claim. Repair reruns both reviewers. Closure audit runs after reconciliation and never replaces a review.

This reverses the earlier rule that Claude Code only audits closure and must not re-score images. That rule existed to save tokens; visual defects are the class a single reviewer misses, so the saving was not worth it. The wording is enforced by `validate_art_pipeline.py` and `validate_game_frontend_pipeline.py`; changing it back requires changing the validators.

Companion decisions in the same pass: `experience-map.json.screens[]` is the only screen inventory, `interaction-design.json` the only component-state author, `visual-style-tokens.json` the only token author on game projects, and `ui-forge` (design spec reference) precedes `visual-verify` (source-app reference).
