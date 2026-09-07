# T9 spec review

Reviewed cumulative production diff `git diff fa2447b20199fa6f8199cdbbe2c05692e283f08c...HEAD` against ticket #9 and parent #8. HEAD remained `ed3313c7b729c4f9575968c08eaec2bfb4312e3e`; production worktree stayed clean. No Standards report read or subagents used.

## Hard blockers

**T9-SPEC-02 — malformed retained inputs still produce ready.** `claude/meta-skill/scripts/orchestrator/product_intent.py:155–157` skips retained nodes before checking their input shape; `scripts/check_decision_inputs.py:44` subsequently traverses them. Ticket `replan-2/issues/9.md:34` requires “畸形数据应明确拒绝且不能留下旧 ready 假象”. Independent temporary fixtures copied the public scripts for both adapters, added a valid completed unrelated node and matching Node-spec, and first passed all three gates. Changing only that node’s `decision_inputs` from `[]` to `42` (mirrored in its Node-spec) yielded bootstrap exit **0**, decision-input exit **1 with TypeError**, and unattended-readiness exit **0**, writing **ready** again. Both native history formats reproduced this. Validate retained-node input shapes before exemption and return structured rejection consistently.

## Judgement calls

**Pending supersession prematurely invalidates confirmed authority.** `claude/meta-skill/scripts/orchestrator/product_intent.py:148–152` treats every `supersedes` pointer as effective, without checking the replacing batch/decision’s status or source. Ticket `issues/9.md:20` says “已有确认决定按适用范围复用；新增或变化的需求明确确认后进入已有产品基准或局部需求记录”. A temporary canonical journal containing a confirmed old choice plus a pending replacement with empty `chosen` caused all three copied gates to reject the old projection as superseded. Conservatively blocking changed work may be intentional, but claiming supersession and demanding reconfirmation conflates a proposal with an accepted replacement; clarify the intended boundary.

**Interaction evidence remains limited.** `claude/meta-skill/tests/unit/test_bootstrap_scope.py:1–5,29–75` supplies preselected routes and hand-authored artifacts. Ticket `issues/9.md:24,38` asks for bootstrap behavior scenarios and says “脚本测试不冒充真实宿主测试”. These tests prove contract consumption, not actual host dialogue/routing; this review did not exercise either host. No #10–#18 implementation is requested here.

Validation: **128 scope tests passed** with bytecode/cache disabled; independent counterexamples used temporary fixtures only. No additional scope creep identified.
