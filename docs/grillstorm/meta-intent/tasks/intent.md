# intent tasks

Spec revision2; task revision1. Outcome and boundaries: ../modules/intent-spec.md and ../program-spec.md. Authoritative criteria remain source issues; local detail refines execution, not scope. Public seam: bootstrap/resume, its generated artifacts and current readiness/completion.

## T9: meta-skill：局部需求确认后进入范围匹配的工作流

- Status: pending
- Source: ../sources/issue-9.json (read full body and comments as the builder/evaluator, NOT as a thought-test subject).
- Depends on: none
- Requirements: R01, R02, R17, R18, R30
- Purpose chain: user_confirmed issue8 O1; preserve desired intent/scope and reject false completion.
- Interfaces: implements I-scope; requires none
- Exclusive resources: none with isolated fixture paths; controller must add a discovered actual mutex before use.
- Acceptance command: `python3 -m pytest claude/meta-skill/tests/unit/test_bootstrap_scope.py -q`
- Validation level: task; blast radius integration because shared contracts/host consumers or candidate-bound proof.
- Expected evidence: nonzero test count, raw command exit/output, exact input/candidate hashes; failing behavior then passing public-boundary tests and runnable fixture path.
- Runtime check: exercise the produced bootstrap/resume contract through real CLI/gates using scripted fixture inputs; cross-host extended adversarial proof is separately owned by T15–T18, not waived.
- Failure contract: typed visible pending/stale/invalid/conflict/error, no empty/default success. Preserve old authority/history and unrelated work, repair through the owning task then rerun. Apply declared failure-ledger cases through existing seams; do not add a production subsystem per case.
- Review gate: fresh supervisor plus independent Standards and Spec; controller-owned post-merge acceptance.

### Allowed touched paths

- claude/meta-skill/skills/bootstrap/SKILL.md
- claude/meta-skill/knowledge/bootstrap-planning.md
- claude/meta-skill/knowledge/bootstrap-audits.md
- claude/meta-skill/knowledge/node-spec-template.md
- claude/meta-skill/scripts/check_decision_inputs.py
- claude/meta-skill/scripts/orchestrator/product_intent.py
- claude/meta-skill/scripts/orchestrator/validate_bootstrap.py
- claude/meta-skill/scripts/orchestrator/validate_unattended_readiness.py
- codex/meta-skill/skills/bootstrap.md
- codex/meta-skill/knowledge/product-inference.md
- claude/meta-skill/tests/unit/test_validate_bootstrap.py
- claude/meta-skill/tests/unit/test_validate_unattended_readiness.py
- claude/meta-skill/tests/unit/test_check_artifacts.py
- claude/meta-skill/tests/unit/test_reconcile_bootstrap_workflow.py
- claude/meta-skill/tests/unit/test_bootstrap_scope.py

### Steps

1. Read approved source ticket and relevant contracts, canonical Skill/adapter instructions, ADRs and existing helpers. Load official TDD and skill-creator.
2. Write one failing public bootstrap/resume behavior test in the named acceptance file; demonstrate expected failure against actual current path.
3. Implement the smallest complete vertical path, including shared helper/contract consumption, canonical Skill guidance, affected host adapter integration and necessary fixture assertions. Do not stop at a classifier or unused helper. Existing product_intent.py/input_freshness.py names are the planned invariant owners only where needed; extend previously delivered helpers rather than create competing logic.
4. Iterate red -> green per behavior; retain compatibility and declared authority. Both product-concept and concept-baseline projections and journal wrappers must agree where affected. Reuse reset_closure for transitive graph impact; readiness/summary/engines cannot keep competing acceptance semantics.
5. Run focused acceptance and directly affected existing checks. Preserve red/green evidence. Do not run all suites in a task merely for reassurance; module/global scheduling is root-owned.
6. Submit exact changed-path list and candidate commit to independent supervisor/review. No marker, merge, tracker mutation, main edits or push by builder. Repair only own feedback, then root serializes integration.

### Evidence

Pending real execution. Required test output file: claude/meta-skill/tests/unit/test_bootstrap_scope.py. Never mark verified from this document.

## T10: meta-skill：产品意图初稿经用户重塑后驱动完整流程

- Status: pending
- Source: ../sources/issue-10.json (read full body and comments as the builder/evaluator, NOT as a thought-test subject).
- Depends on: T9
- Requirements: R03, R04, R05, R06, R07, R08, R09, R10, R11, R12, R13, R14, R16, R19, R22, R30
- Purpose chain: user_confirmed issue8 O1; preserve desired intent/scope and reject false completion.
- Interfaces: implements I-intent; requires I-scope
- Exclusive resources: none with isolated fixture paths; controller must add a discovered actual mutex before use.
- Acceptance command: `python3 -m pytest claude/meta-skill/tests/unit/test_bootstrap_confirmation.py -q`
- Validation level: task; blast radius integration because shared contracts/host consumers or candidate-bound proof.
- Expected evidence: nonzero test count, raw command exit/output, exact input/candidate hashes; failing behavior then passing public-boundary tests and runnable fixture path.
- Runtime check: exercise the produced bootstrap/resume contract through real CLI/gates using scripted fixture inputs; cross-host extended adversarial proof is separately owned by T15–T18, not waived.
- Failure contract: typed visible pending/stale/invalid/conflict/error, no empty/default success. Preserve old authority/history and unrelated work, repair through the owning task then rerun. Apply declared failure-ledger cases through existing seams; do not add a production subsystem per case.
- Review gate: fresh supervisor plus independent Standards and Spec; controller-owned post-merge acceptance.

### Allowed touched paths

- claude/meta-skill/skills/bootstrap/SKILL.md
- claude/meta-skill/knowledge/bootstrap-planning.md
- claude/meta-skill/knowledge/bootstrap-audits.md
- claude/meta-skill/knowledge/node-spec-template.md
- claude/meta-skill/scripts/check_decision_inputs.py
- claude/meta-skill/scripts/orchestrator/product_intent.py
- claude/meta-skill/scripts/orchestrator/validate_bootstrap.py
- claude/meta-skill/scripts/orchestrator/validate_unattended_readiness.py
- codex/meta-skill/skills/bootstrap.md
- codex/meta-skill/knowledge/product-inference.md
- claude/meta-skill/tests/unit/test_validate_bootstrap.py
- claude/meta-skill/tests/unit/test_validate_unattended_readiness.py
- claude/meta-skill/tests/unit/test_check_artifacts.py
- claude/meta-skill/tests/unit/test_reconcile_bootstrap_workflow.py
- claude/meta-skill/tests/unit/test_bootstrap_confirmation.py
- claude/meta-skill/internal/commands/journal.md
- claude/meta-skill/internal/commands/journal-merge.md
- claude/meta-skill/knowledge/capabilities/reverse-concept.md
- claude/meta-skill/knowledge/capabilities/product-concept.md
- claude/meta-skill/knowledge/cross-phase-protocols.md
- codex/meta-skill/commands/journal.md
- codex/meta-skill/commands/journal-merge.md

### Steps

1. Read approved source ticket and relevant contracts, canonical Skill/adapter instructions, ADRs and existing helpers. Load official TDD and skill-creator.
2. Write one failing public bootstrap/resume behavior test in the named acceptance file; demonstrate expected failure against actual current path.
3. Implement the smallest complete vertical path, including shared helper/contract consumption, canonical Skill guidance, affected host adapter integration and necessary fixture assertions. Do not stop at a classifier or unused helper. Existing product_intent.py/input_freshness.py names are the planned invariant owners only where needed; extend previously delivered helpers rather than create competing logic.
4. Iterate red -> green per behavior; retain compatibility and declared authority. Both product-concept and concept-baseline projections and journal wrappers must agree where affected. Reuse reset_closure for transitive graph impact; readiness/summary/engines cannot keep competing acceptance semantics.
5. Run focused acceptance and directly affected existing checks. Preserve red/green evidence. Do not run all suites in a task merely for reassurance; module/global scheduling is root-owned.
6. Submit exact changed-path list and candidate commit to independent supervisor/review. No marker, merge, tracker mutation, main edits or push by builder. Repair only own feedback, then root serializes integration.

### Evidence

Pending real execution. Required test output file: claude/meta-skill/tests/unit/test_bootstrap_confirmation.py. Never mark verified from this document.

## T11: meta-skill：产品决定中断续接与旧基准安全接入

- Status: pending
- Source: ../sources/issue-11.json (read full body and comments as the builder/evaluator, NOT as a thought-test subject).
- Depends on: T10
- Requirements: R14, R15, R29, R30
- Purpose chain: user_confirmed issue8 O1; preserve desired intent/scope and reject false completion.
- Interfaces: implements I-resume; requires I-intent
- Exclusive resources: none with isolated fixture paths; controller must add a discovered actual mutex before use.
- Acceptance command: `python3 -m pytest claude/meta-skill/tests/unit/test_bootstrap_resume.py -q`
- Validation level: task; blast radius integration because shared contracts/host consumers or candidate-bound proof.
- Expected evidence: nonzero test count, raw command exit/output, exact input/candidate hashes; failing behavior then passing public-boundary tests and runnable fixture path.
- Runtime check: exercise the produced bootstrap/resume contract through real CLI/gates using scripted fixture inputs; cross-host extended adversarial proof is separately owned by T15–T18, not waived.
- Failure contract: typed visible pending/stale/invalid/conflict/error, no empty/default success. Preserve old authority/history and unrelated work, repair through the owning task then rerun. Apply declared failure-ledger cases through existing seams; do not add a production subsystem per case.
- Review gate: fresh supervisor plus independent Standards and Spec; controller-owned post-merge acceptance.

### Allowed touched paths

- claude/meta-skill/skills/bootstrap/SKILL.md
- claude/meta-skill/knowledge/bootstrap-planning.md
- claude/meta-skill/knowledge/bootstrap-audits.md
- claude/meta-skill/knowledge/node-spec-template.md
- claude/meta-skill/scripts/check_decision_inputs.py
- claude/meta-skill/scripts/orchestrator/product_intent.py
- claude/meta-skill/scripts/orchestrator/validate_bootstrap.py
- claude/meta-skill/scripts/orchestrator/validate_unattended_readiness.py
- codex/meta-skill/skills/bootstrap.md
- codex/meta-skill/knowledge/product-inference.md
- claude/meta-skill/tests/unit/test_validate_bootstrap.py
- claude/meta-skill/tests/unit/test_validate_unattended_readiness.py
- claude/meta-skill/tests/unit/test_check_artifacts.py
- claude/meta-skill/tests/unit/test_reconcile_bootstrap_workflow.py
- claude/meta-skill/tests/unit/test_bootstrap_resume.py
- claude/meta-skill/internal/commands/journal.md
- claude/meta-skill/internal/commands/journal-merge.md
- claude/meta-skill/knowledge/capabilities/reverse-concept.md
- claude/meta-skill/knowledge/capabilities/product-concept.md
- claude/meta-skill/knowledge/cross-phase-protocols.md
- claude/meta-skill/knowledge/orchestrator-template.md
- claude/meta-skill/knowledge/run-engine/engine-core.js
- claude/meta-skill/knowledge/run-engine/run-engine.workflow.js
- claude/meta-skill/knowledge/run-engine/tests/engine-core.test.js
- claude/meta-skill/knowledge/run-engine/tests/engine-integration.test.js
- codex/meta-skill/knowledge/orchestrator-template.md
- codex/meta-skill/knowledge/flow-template.py
- codex/meta-skill/test_flow.py
- codex/meta-skill/commands/journal.md
- codex/meta-skill/commands/journal-merge.md
- claude/meta-skill/scripts/compute_reset_closure.py

### Steps

1. Read approved source ticket and relevant contracts, canonical Skill/adapter instructions, ADRs and existing helpers. Load official TDD and skill-creator.
2. Write one failing public bootstrap/resume behavior test in the named acceptance file; demonstrate expected failure against actual current path.
3. Implement the smallest complete vertical path, including shared helper/contract consumption, canonical Skill guidance, affected host adapter integration and necessary fixture assertions. Do not stop at a classifier or unused helper. Existing product_intent.py/input_freshness.py names are the planned invariant owners only where needed; extend previously delivered helpers rather than create competing logic.
4. Iterate red -> green per behavior; retain compatibility and declared authority. Both product-concept and concept-baseline projections and journal wrappers must agree where affected. Reuse reset_closure for transitive graph impact; readiness/summary/engines cannot keep competing acceptance semantics.
5. Run focused acceptance and directly affected existing checks. Preserve red/green evidence. Do not run all suites in a task merely for reassurance; module/global scheduling is root-owned.
6. Submit exact changed-path list and candidate commit to independent supervisor/review. No marker, merge, tracker mutation, main edits or push by builder. Repair only own feedback, then root serializes integration.

### Evidence

Pending real execution. Required test output file: claude/meta-skill/tests/unit/test_bootstrap_resume.py. Never mark verified from this document.
