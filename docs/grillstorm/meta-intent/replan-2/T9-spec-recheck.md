# T9 corrective spec recheck

Reviewed only `git diff ed3313c7b729c4f9575968c08eaec2bfb4312e3e...HEAD`, commit `ea046abc` (`fix(meta-skill): reject malformed retained decision inputs (#9)`), against revised `replan-2/issues/9.md` and parent `sources/issue-8.json`. Read only the historical Spec report; no Standards report or subagents.

**Verdict: T9-SPEC-02 repaired; no new spec blocker or scope creep found in this delta.**

Ticket #9 requires “保留已完成节点和两端原生 history 格式；畸形数据应明确拒绝且不能留下旧 ready 假象” and “真实生成/复制后的三个公开 gate 一起验证，不只测共享 helper”. At `claude/meta-skill/scripts/orchestrator/product_intent.py:24–28`, validation now rejects malformed `decision_inputs` on every node before the retained-node exemption. Both adapter paths copy this shared helper; rejection prevents unsafe downstream traversal.

Independent temporary fixtures copied `validate_bootstrap.py`, `check_decision_inputs.py`, and `validate_unattended_readiness.py` from each adapter path. All three rejected 13 malformed variants, including scalar/null/object values, blank strings, nested arrays and mixed valid/invalid entries, with exit 1, `invalid_scope`, and empty stderr. Each mutation followed a passing baseline; readiness with `--write-report` replaced `ready` with `not_ready`, then returned to `ready` after correction. Omitted, empty and valid nonempty inputs passed. Completed unrelated nodes and native histories remained unchanged; the Codex fixture used its native transition producer. Total: **246 independent copied CLI invocations**.

Regression evidence: **142 scope tests and 34 existing bootstrap/readiness tests passed**. Coverage retains trusted journal projection, forged/pending authority rejection, orphan detection and rejection of new unscoped work. No missing or incorrectly implemented corrective requirement identified.

**Separate historical judgement:** pending supersession handling remains unchanged. Ticket #9 says “新增或变化的需求明确确认后进入已有产品基准或局部需求记录”; whether a pending replacement should invalidate earlier authority remains a product judgement, not the repaired malformed-input blocker.

Actual host dialogue remains **#15**. These copied-script checks do not establish host interaction, consistent with “脚本测试不冒充真实宿主测试”.

Production HEAD remained `ea046abc8e0a479d736d332e5e5d15514d3ff294`; production worktree remained clean. Only temporary fixtures and this report were written; no commits.
