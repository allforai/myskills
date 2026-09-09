# T10 independent spec review

Reviewed `git diff 54ba9127a07506024700fde12ddd273f3690b963...HEAD`; sole commit and verified production HEAD: `b5c66303ce62618bd587ffa0ec705b8af61a6336`. Read both adapter entries, canonical protocol, persistence/plan implementation and public consumers. No production edits; root-owned `execution.json` untouched; other-axis report not read.

## Hard blockers

1. **P1 — An unanswered question can silently enter frozen scope.** Requirement: “未决问题不能通过沉默自动确认，排除范围必须显式决定” (`issues/10.md:22`, relative to this directory). `claude/meta-skill/scripts/orchestrator/product_intent.py:511–518` accepts question IDs colliding with intent IDs. At `:379–386`, freeze unions both identity sets, so including an intent also satisfies coverage for its unanswered namesake question without an answer or exclusion. Independently reproduced through each adapter’s copied CLI: six intents, pending question `id=tradeoffs`, `depends_on=[]`, confirm all intents, freeze with all six IDs and `exclude={}`, then plan. Results: `frozen`, `planned`, all three public gates exit 0, unattended readiness `ready`; the question remains pending. Separate question/intent scope identities or reject collisions before persistence.

2. **P2 — Product planning rejects retained, unrelated completed work.** Parent requirement: “preserve unaffected results with their provenance” (`docs/grillstorm/meta-intent/sources/issue-8.json:1`, Implementation Decisions / Incremental impact). `claude/meta-skill/scripts/orchestrator/product_intent.py:298–301` requires every node to consume current baseline intent, overriding the existing retained-completion exemption at `:74–83,163–165`. Independently reproduced on both copied CLIs: append an unrelated completed node with empty intent references and its completion transition to an otherwise accepted plan; `plan` exits 1, “Product node consumes excluded or unconfirmed intent.” Preserve the already-reconciled historical node without granting it new scope. This is a regression in consuming supplied history, not a request to implement later reconciliation tickets.

## Coverage and optional judgments

Current scripted suite: **22 passed**. Four operations, user-only additions, revision history, normal pending-dependency blocking, explicit freeze and goal/acceptance projection are present. No additional scope creep or optional judgment findings. Actual-host semantic/dialogue proofs remain #15; scripted adapter results do not establish them. Temporary synthetic projects were removed; no target product was modified.
