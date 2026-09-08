# T13 Spec review (candidate 000c9242, base ed430dfc)

Reviewed `git diff ed430dfc...000c9242` against GitHub #13 (v2, unchanged) and
`replan-2/issues/13.md`. `T13-delivery-closure.md` was treated as claims. HEAD
verified equal to `000c92420d2ef97b777eaf1aef534fb8382bba82`. I re-ran
`test_delivery_closure.py`, the two edited #12 fixtures and `codex/meta-skill/test_flow.py`
from a clean env: 84 passed. These are copied-CLI runs; host evidence remains 0/60.

## Verdict

No hard breach found. Every acceptance line has an observable contract in the
shared gate CLIs, and the two v2 increments (accepted_with_gaps distinction, SG01
across implement→sync→re-accept) are implemented. Two partial items and several
observations follow.

## Requirement coverage (spec quoted → evidence)

- "任一不一致时…不能标记完成，即使…测试局部通过": `publish` returns `inconsistent`
  for missing documents and `failed_verification` when a retained document's
  declared check fails after a passing acceptance command; `check_artifacts`
  reports `all_exist=false`. Verified in the decisive negative of the closure test.
- "明确差异与修复责任…不能只写一条警告": `diff` + `repair` on `check`, artifact gate,
  readiness `stale_evidence` message, reconciliation `invalidate` items. Met.
- "不重复询问已有…决定 / 不能由无人值守补造": `adjust` → `stale_requirement` →
  owner `interactive-bootstrap` (`replan`); `resume` topics empty; `reopen` →
  `pending_requirement` blocks readiness while Run Policy `accept` still returns
  `accept`. Reuses `validate_scope`; no new interview/retry mechanism. Met.
- "新证据绑定当前输入并恢复…无关工作保持有效": warehouse branch stays valid at every
  step; only the affected record changes; repeated `check` byte-identical. Met.
- "accepted_with_gaps…不能转为 verified/completed": blocking status in
  `check_artifacts` and reconciliation; flow.py `first_pending_node` and completion
  both route through `independent_artifact_gate`. Met at the authoritative gate.
- "复核当前输入，覆盖 SG01": inputs rechecked after the acceptance command (existing)
  and again after the last document check, including `source_snapshot` and outputs;
  own-source and upstream-source mutating checkers return `stale` and publish nothing.
  Checker argv tokens naming project files must be consumed inputs. Met.
- Root correction 000c9242: register absent → legacy short circuit kept; register
  present and corrupt → falls through to `evaluate`, which raises → all nodes
  `invalid`, file left in place (test confirms). Fail-closed behaviour preserved.

## Partial (should be closed, not blocking)

1. **Host parity of the status rule** ("Claude 与 Codex…消费同一权威规则").
   `codex/meta-skill/knowledge/flow-template.py:25` `BLOCKING_STATUS_VALUES`, the
   generated run.md guidance at `flow-template.py:531`, and
   `codex/meta-skill/knowledge/orchestrator-template.md:116` still omit
   `accepted_with_gaps`. Completion is decided by `check_artifacts`, so no node
   completes, but flow's own `artifact_ready`/`status_error` report fields would
   call such an artifact ready, and the Codex worker text does not list it.
2. **"Mirror all four in the Node-spec frontmatter"** (SKILL.md, bootstrap.md).
   `validate_bootstrap.py:1073` parity-checks only three fields;
   `knowledge/node-spec-template.md:9` was not updated to name
   `document_verification`. Planning from that template can omit it and be refused
   only later by every gate (which is the documented behaviour, so not a breach).

## Optional observations

- `plan` itself does not run `input_declaration_errors`; a required document
  without a check is written and refused by `validate_bootstrap`/readiness. Fine.
- Checker identity tracks only argv tokens that are existing project files;
  `-m module`, directory arguments and `-c` strings are untracked. Consistent with
  the stated host-supplied trust boundary; documented.
- Document checks run inside the publication lock (up to 300 s each); the lock
  waits only 3 s, so a concurrent publisher fails with "locked" rather than waiting.
- `repair_responsibility` names the node when both own and upstream diffs exist;
  the doc says producers repair first. Minor ordering ambiguity.
- Standalone legacy copy with a register present but no `evidence_freshness.py`
  raises `ModuleNotFoundError` (nonzero exit, traceback, no report). Unlikely,
  since only that helper writes the register.
- Contract-kind publication no longer binds `required_documents` (`outputs()`);
  intentional per ticket ("contract permits execution, cannot prove completion").
- #12 fixture edits only add a `document_verification` entry; no assertion
  weakened. The `test_dynamic_input_dependencies` check is a status-field read on
  a JSON report, which the new docs call "not a check"; harmless in a fixture.
- No #11 C1′ behaviour was attributed to this diff. No scope creep beyond the
  ticket-authorised corrupt-register detection.
