## Spec

Reviewed cumulative `git diff cadac5525abf2407fdcd0588252336cba8f60a01...HEAD`, with HEAD fixed at `459022e02f5bf1dc98e37d3b40d38c69c59513e3`, against issue #9 body and comments (empty), relevant parent #8, and frozen I-scope/T9 boundaries.

**1 blocking finding; 0 judgement findings.**

- **Preserved decision history blocks the new local-confirmation path.** `claude/meta-skill/scripts/check_decision_inputs.py:43–46` still treats every project-wide `decision-*.json` as a newly gathered input requiring direct workflow wiring. The new local projection contract in `claude/meta-skill/knowledge/bootstrap-planning.md:31–36` retains the original journal reference in confirmation provenance, while nodes consume the local requirement JSON. The newly mandated three-gate validation therefore rejects the existing `decision-journal.json` as an orphan even when the local requirement legitimately reuses its decision. Historical, unrelated decision artifacts have the same problem.

  Authoritative requirement: issue #9 Acceptance criteria says “已有确认决定按适用范围复用” and “并保留无关产品方向和既有工作”; parent #8 says “Do not silently rewrite legacy artifacts or require a full interview for a local feature.” This is a partial T9 integration requirement, not a request for later I-resume functionality.

  Reproduction: use the candidate's confirmed, documented local-export fixture; preserve a journal in the native `schema_version/batches/source:user_session/decisions` format; point the requirement's confirmation reference at its decision; retain the documented local requirement path in node `decision_inputs`. On both Claude and Codex asset paths, bootstrap validation exits 0, readiness exits 0, but decision-input validation exits 1 with `orphan (unwired): .allforai/product-concept/decision-journal.json`. All fixture bytes remain unchanged. Scope orphan checking to newly gathered applicable decisions and account for provenance references without requiring unrelated history to become execution inputs.

Validation: focused acceptance passed **106 tests** (bytecode/cache writes disabled); additional public-CLI reproduction above independently confirmed the finding. No source changes or candidate movement. Actual host dialogue and later T10–T18 delivery are not claimed by this review.

**Spec total: 1 blocking, 0 judgement; worst issue: legitimate journal-backed local work is rejected by the mandatory decision-input gate.**
