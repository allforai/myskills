# proof tasks

Spec revision2; task revision1. Outcome and boundaries: ../modules/proof-spec.md and ../program-spec.md. Authoritative criteria remain source issues; local detail refines execution, not scope. Public seam: bootstrap/resume, its generated artifacts and current readiness/completion.

Workflow projection revision2: required scenarios are the union of parent #8 Testing Decisions and each child ticket, frozen in scenario-matrix.json. T15 includes the parent-required new-product case in addition to its six child scenarios (7x2 cells). T16=7x2, T17=8x2, T18=8x2; total60. Existing criteria remain intact. The evaluator must implement the full matrix at its existing scenario directory and evidence gate. dispatch-contract.md/controller.py bind criteria to evaluator/reviewer packets and reserve subject capacity; no oracle is sent to subjects.

## T15: meta-skill 思维测试：任务分流与需求确认反例

- Status: pending
- Source: ../sources/issue-15.json (read full body and comments as the builder/evaluator, NOT as a thought-test subject).
- Depends on: T9, T10
- Requirements: R01, R02, R03, R04, R05, R06, R07, R08, R09, R10, R11, R12, R13, R14, R15, R16, R17, R18, R19, R29, R30
- Purpose chain: user_confirmed issue8 O3; preserve desired intent/scope and reject false completion.
- Interfaces: implements none; requires I-scope, I-intent
- Exclusive resources: none with isolated fixture paths; controller must add a discovered actual mutex before use.
- Acceptance command: `python3 -m pytest claude/meta-skill/tests/scenarios/T15/test_evidence.py -q`
- Validation level: task; blast radius module because shared contracts/host consumers or candidate-bound proof.
- Expected evidence: nonzero test count, raw command exit/output, exact input/candidate hashes; actual per-scenario Claude and Codex dialogue/tool/artifact comparisons, complete required denominator.
- Runtime check: execute every required scenario from the ticket on both actual hosts; controller dispatches fresh subjects on evaluator request.
- Failure contract: typed visible pending/stale/invalid/conflict/error, no empty/default success. Preserve old authority/history and unrelated work, repair through the owning task then rerun. Apply declared failure-ledger cases through existing seams; do not add a production subsystem per case.
- Review gate: fresh supervisor plus independent Standards and Spec; controller-owned post-merge acceptance.

### Allowed touched paths

- claude/meta-skill/tests/scenarios/T15/**

### Steps

1. Read source ticket as evaluator; keep oracle/criteria outside subject context. Prepare unique synthetic fixtures and per-scenario raw briefs referencing candidate Skill paths.
2. Ask root coordinator to launch actual fresh Claude/Codex subjects via Orca; provide only raw scenario and current user turn. Subject does not receive this document or source ticket. Keep each scenario on a fixed candidate input manifest; no installed update.
3. Capture actual dialogue/tool output and resulting artifacts; preserve candidate paths/hashes, provider/version/dispatch identity, source state changes and evaluator comparisons. Missing decisive evidence is unverified, not self-attested pass.
4. Write scenario-local pytest evidence assertions and results under this task directory; assert all required scenario/host cells, actual output behavior, loaded-candidate binding and current applicability. No blanket skip or reused other-host result. Prove installed/candidate mismatch and changed-candidate rejection through this evaluator boundary.
5. Failed cases retain a minimal reproduction and owning implementation ticket link; request owner repair, then fresh-context affected retest. Do not edit production or manufacture a pass. Unresolved or unavailable cells keep this task unverified.
6. Run focused acceptance, return evidence to supervisor, and only commit own declared paths as directed. No shared new framework dependency across thought tickets.

### Evidence

Pending real execution. Required test output file: claude/meta-skill/tests/scenarios/T15/test_evidence.py. Never mark verified from this document.

## T16: meta-skill 思维测试：中断反悔与旧资料冲突

- Status: pending
- Source: ../sources/issue-16.json (read full body and comments as the builder/evaluator, NOT as a thought-test subject).
- Depends on: T11
- Requirements: R01, R02, R03, R04, R05, R06, R07, R08, R09, R10, R11, R12, R13, R14, R15, R16, R17, R18, R19, R29, R30
- Purpose chain: user_confirmed issue8 O3; preserve desired intent/scope and reject false completion.
- Interfaces: implements none; requires I-resume
- Exclusive resources: none with isolated fixture paths; controller must add a discovered actual mutex before use.
- Acceptance command: `python3 -m pytest claude/meta-skill/tests/scenarios/T16/test_evidence.py -q`
- Validation level: task; blast radius module because shared contracts/host consumers or candidate-bound proof.
- Expected evidence: nonzero test count, raw command exit/output, exact input/candidate hashes; actual per-scenario Claude and Codex dialogue/tool/artifact comparisons, complete required denominator.
- Runtime check: execute every required scenario from the ticket on both actual hosts; controller dispatches fresh subjects on evaluator request.
- Failure contract: typed visible pending/stale/invalid/conflict/error, no empty/default success. Preserve old authority/history and unrelated work, repair through the owning task then rerun. Apply declared failure-ledger cases through existing seams; do not add a production subsystem per case.
- Review gate: fresh supervisor plus independent Standards and Spec; controller-owned post-merge acceptance.

### Allowed touched paths

- claude/meta-skill/tests/scenarios/T16/**

### Steps

1. Read source ticket as evaluator; keep oracle/criteria outside subject context. Prepare unique synthetic fixtures and per-scenario raw briefs referencing candidate Skill paths.
2. Ask root coordinator to launch actual fresh Claude/Codex subjects via Orca; provide only raw scenario and current user turn. Subject does not receive this document or source ticket. Keep each scenario on a fixed candidate input manifest; no installed update.
3. Capture actual dialogue/tool output and resulting artifacts; preserve candidate paths/hashes, provider/version/dispatch identity, source state changes and evaluator comparisons. Missing decisive evidence is unverified, not self-attested pass.
4. Write scenario-local pytest evidence assertions and results under this task directory; assert all required scenario/host cells, actual output behavior, loaded-candidate binding and current applicability. No blanket skip or reused other-host result. Prove installed/candidate mismatch and changed-candidate rejection through this evaluator boundary.
5. Failed cases retain a minimal reproduction and owning implementation ticket link; request owner repair, then fresh-context affected retest. Do not edit production or manufacture a pass. Unresolved or unavailable cells keep this task unverified.
6. Run focused acceptance, return evidence to supervisor, and only commit own declared paths as directed. No shared new framework dependency across thought tickets.

### Evidence

Pending real execution. Required test output file: claude/meta-skill/tests/scenarios/T16/test_evidence.py. Never mark verified from this document.

## T17: meta-skill 思维测试：增量同步与假完成压力

- Status: pending
- Source: ../sources/issue-17.json (read full body and comments as the builder/evaluator, NOT as a thought-test subject).
- Depends on: T12, T13
- Requirements: R20, R21, R22, R23, R24, R25, R26, R27, R28, R29, R30
- Purpose chain: user_confirmed issue8 O3; preserve desired intent/scope and reject false completion.
- Interfaces: implements none; requires I-freshness, I-sync
- Exclusive resources: none with isolated fixture paths; controller must add a discovered actual mutex before use.
- Acceptance command: `python3 -m pytest claude/meta-skill/tests/scenarios/T17/test_evidence.py -q`
- Validation level: task; blast radius module because shared contracts/host consumers or candidate-bound proof.
- Expected evidence: nonzero test count, raw command exit/output, exact input/candidate hashes; actual per-scenario Claude and Codex dialogue/tool/artifact comparisons, complete required denominator.
- Runtime check: execute every required scenario from the ticket on both actual hosts; controller dispatches fresh subjects on evaluator request.
- Failure contract: typed visible pending/stale/invalid/conflict/error, no empty/default success. Preserve old authority/history and unrelated work, repair through the owning task then rerun. Apply declared failure-ledger cases through existing seams; do not add a production subsystem per case.
- Review gate: fresh supervisor plus independent Standards and Spec; controller-owned post-merge acceptance.

### Allowed touched paths

- claude/meta-skill/tests/scenarios/T17/**

### Steps

1. Read source ticket as evaluator; keep oracle/criteria outside subject context. Prepare unique synthetic fixtures and per-scenario raw briefs referencing candidate Skill paths.
2. Ask root coordinator to launch actual fresh Claude/Codex subjects via Orca; provide only raw scenario and current user turn. Subject does not receive this document or source ticket. Keep each scenario on a fixed candidate input manifest; no installed update.
3. Capture actual dialogue/tool output and resulting artifacts; preserve candidate paths/hashes, provider/version/dispatch identity, source state changes and evaluator comparisons. Missing decisive evidence is unverified, not self-attested pass.
4. Write scenario-local pytest evidence assertions and results under this task directory; assert all required scenario/host cells, actual output behavior, loaded-candidate binding and current applicability. No blanket skip or reused other-host result. Prove installed/candidate mismatch and changed-candidate rejection through this evaluator boundary.
5. Failed cases retain a minimal reproduction and owning implementation ticket link; request owner repair, then fresh-context affected retest. Do not edit production or manufacture a pass. Unresolved or unavailable cells keep this task unverified.
6. Run focused acceptance, return evidence to supervisor, and only commit own declared paths as directed. No shared new framework dependency across thought tickets.

### Evidence

Pending real execution. Required test output file: claude/meta-skill/tests/scenarios/T17/test_evidence.py. Never mark verified from this document.

## T18: meta-skill 思维测试：外部漂移的完整恢复路径

- Status: pending
- Source: ../sources/issue-18.json (read full body and comments as the builder/evaluator, NOT as a thought-test subject).
- Depends on: T14
- Requirements: R20, R21, R22, R23, R24, R25, R26, R27, R28, R29, R30
- Purpose chain: user_confirmed issue8 O3; preserve desired intent/scope and reject false completion.
- Interfaces: implements none; requires I-drift
- Exclusive resources: none with isolated fixture paths; controller must add a discovered actual mutex before use.
- Acceptance command: `python3 -m pytest claude/meta-skill/tests/scenarios/T18/test_evidence.py -q`
- Validation level: task; blast radius module because shared contracts/host consumers or candidate-bound proof.
- Expected evidence: nonzero test count, raw command exit/output, exact input/candidate hashes; actual per-scenario Claude and Codex dialogue/tool/artifact comparisons, complete required denominator.
- Runtime check: execute every required scenario from the ticket on both actual hosts; controller dispatches fresh subjects on evaluator request.
- Failure contract: typed visible pending/stale/invalid/conflict/error, no empty/default success. Preserve old authority/history and unrelated work, repair through the owning task then rerun. Apply declared failure-ledger cases through existing seams; do not add a production subsystem per case.
- Review gate: fresh supervisor plus independent Standards and Spec; controller-owned post-merge acceptance.

### Allowed touched paths

- claude/meta-skill/tests/scenarios/T18/**

### Steps

1. Read source ticket as evaluator; keep oracle/criteria outside subject context. Prepare unique synthetic fixtures and per-scenario raw briefs referencing candidate Skill paths.
2. Ask root coordinator to launch actual fresh Claude/Codex subjects via Orca; provide only raw scenario and current user turn. Subject does not receive this document or source ticket. Keep each scenario on a fixed candidate input manifest; no installed update.
3. Capture actual dialogue/tool output and resulting artifacts; preserve candidate paths/hashes, provider/version/dispatch identity, source state changes and evaluator comparisons. Missing decisive evidence is unverified, not self-attested pass.
4. Write scenario-local pytest evidence assertions and results under this task directory; assert all required scenario/host cells, actual output behavior, loaded-candidate binding and current applicability. No blanket skip or reused other-host result. Prove installed/candidate mismatch and changed-candidate rejection through this evaluator boundary.
5. Failed cases retain a minimal reproduction and owning implementation ticket link; request owner repair, then fresh-context affected retest. Do not edit production or manufacture a pass. Unresolved or unavailable cells keep this task unverified.
6. Run focused acceptance, return evidence to supervisor, and only commit own declared paths as directed. No shared new framework dependency across thought tickets.

### Evidence

Pending real execution. Required test output file: claude/meta-skill/tests/scenarios/T18/test_evidence.py. Never mark verified from this document.
