export const meta = {
  name: 'pxo-1-6-execute',
  description: 'Superstorm 1.6: dependency-ready execution of 56 tasks (executor opus, fresh supervisor on session model, cap 3, path mutex)',
  phases: [
    { title: 'Execute', detail: 'one executor per ready task', model: 'opus' },
    { title: 'Supervise', detail: 'fresh-context supervisor reruns the real acceptance_cmd' },
  ],
}

const REPO = '/Users/aa/workspace/myskills'
const RUN = REPO + '/docs/superpowers/runs/2026-09-18-product-experience-overhaul'
const CAP = 3
const EXECUTOR_MODEL = 'opus'
const TASKS = [
 {
  "id": "T-M1-01",
  "title": "validate_experience_design_coverage (findings + rendered pair, four blocker codes, gate registration) with host-parametrized unit tests and the project() fixture line (U7+U9; R-M1-07, R-M1-09)",
  "touched_paths": [
   "claude/meta-skill/scripts/orchestrator/validate_bootstrap.py",
   "claude/meta-skill/tests/unit/test_validate_bootstrap.py",
   "claude/meta-skill/tests/unit/test_bootstrap_scope.py"
  ],
  "acceptance_cmd": "CO=\"$(python3 -m pytest --co -q claude/meta-skill/tests/unit/test_validate_bootstrap.py)\"; echo \"$CO\" | grep -q 'test_experience_coverage_rejects_workflow_without_design_node\\[codex\\]' && echo \"$CO\" | grep -q 'test_experience_coverage_passes_with_design_node_blocking_ui_implementation\\[claude\\]' && echo \"$CO\" | grep -q 'test_experience_coverage_is_a_structural_gate_blocker' && echo \"$CO\" | grep -q 'test_app_design_flow_fixtures_raise_no_experience_findings' && test \"$(echo \"$CO\" | grep -c 'test_experience_coverage_')\" -ge 19 && python3 -m pytest -q claude/meta-skill/tests/unit/test_validate_bootstrap.py && python3 -m pytest -q claude/meta-skill/tests/unit/test_validate_unattended_readiness.py claude/meta-skill/tests/unit/test_bootstrap_scope.py claude/meta-skill/tests/unit/test_product_intent_session.py claude/meta-skill/tests/unit/test_acceptance_allocation.py claude/meta-skill/tests/unit/test_legacy_projection_authority.py claude/meta-skill/tests/unit/test_legacy_profile_authority.py claude/meta-skill/tests/unit/test_intent_review_corrections.py claude/meta-skill/tests/unit/test_product_intent_resume.py claude/meta-skill/tests/unit/test_product_retained_scope.py claude/meta-skill/tests/unit/test_planning_audit_contracts.py claude/meta-skill/tests/unit/test_freeze_idempotence.py claude/meta-skill/tests/unit/test_product_question_identity.py",
  "deps": [],
  "resources": [],
  "reality_gate": false,
  "runbook_ptr": "",
  "plan": "docs/superpowers/plans/2026-09-18-design-routing-plan.md",
  "design": "docs/superpowers/specs/2026-09-18-design-routing-design.md"
 },
 {
  "id": "T-M1-02",
  "title": "bootstrap SKILL.md: experience_priority profile schema + sole-producer rules (Step 1.2/1.6) and Step 2 item 9 forced design-knowledge load (U1+U3; R-M1-01, R-M1-03)",
  "touched_paths": [
   "claude/meta-skill/skills/bootstrap/SKILL.md"
  ],
  "acceptance_cmd": "F=claude/meta-skill/skills/bootstrap/SKILL.md; grep -qF '\"mode\": \"consumer | admin | mixed | none\"' $F && grep -qF 'Classify experience_priority (see 1.6)' $F && grep -qF 'experience_priority.mode != none' $F && grep -qF 'knowledge/capabilities/product-concept.md' $F && grep -qF 'knowledge/consumer-maturity-patterns.md' $F && grep -qF 'knowledge/journey-emotion-schema.md' $F && grep -qF 'knowledge/capabilities/app-design.md' $F && grep -qF 'knowledge/capabilities/game-design.md' $F && grep -qF 'Product routes with an interface also load item 9' $F && grep -qF 'This loads method, not a fixed node list.' $F && grep -qF 'Capabilities are REFERENCE material, not a node menu.' $F && python3 claude/meta-skill/scripts/orchestrator/validate_skills.py claude/meta-skill/skills && python3 claude/meta-skill/scripts/orchestrator/validate_meta_contracts.py",
  "deps": [],
  "resources": [],
  "reality_gate": false,
  "runbook_ptr": "",
  "plan": "docs/superpowers/plans/2026-09-18-design-routing-plan.md",
  "design": "docs/superpowers/specs/2026-09-18-design-routing-design.md"
 },
 {
  "id": "T-M1-03",
  "title": "Unify the 13 experience_priority read sites to bootstrap-profile.json experience_priority.mode; remove false source/producer claims (U2; R-M1-02)",
  "touched_paths": [
   "claude/meta-skill/knowledge/consumer-maturity-patterns.md",
   "claude/meta-skill/knowledge/experience-map-schema.md",
   "claude/meta-skill/knowledge/design-audit-dimensions.md",
   "claude/meta-skill/knowledge/capabilities/product-analysis.md",
   "claude/meta-skill/knowledge/capabilities/generate-artifacts.md",
   "claude/meta-skill/knowledge/capabilities/translate.md",
   "claude/meta-skill/knowledge/capabilities/feature-gap.md"
  ],
  "acceptance_cmd": "K=claude/meta-skill/knowledge; test -z \"$(grep -rn 'experience_priority' $K | grep -v 'experience_priority.mode' | grep -v bootstrap)\" && grep -qF 'Experience classification is not a source-summary field' $K/capabilities/product-analysis.md && grep -qF 'carried unchanged (never reclassified)' $K/capabilities/product-analysis.md && grep -qF '`bootstrap-profile.json` `experience_priority.mode` is `consumer` or `mixed`' $K/design-audit-dimensions.md && ! grep -qF '`product-map.json` contains `experience_priority`' $K/design-audit-dimensions.md && ! grep -qF 'experience_priority' $K/capabilities/generate-artifacts.md && grep -qF '`protection_level`, `audience_type`, `render_as` fields generated' $K/capabilities/generate-artifacts.md && grep -qF 'When `bootstrap-profile.json` `experience_priority.mode = consumer`' $K/consumer-maturity-patterns.md && grep -qF 'experience_priority.mode' $K/capabilities/translate.md && grep -qF 'experience_priority.mode' $K/capabilities/feature-gap.md && grep -F 'experience_priority.mode' $K/experience-map-schema.md | grep -qF 'bootstrap-profile.json' && python3 claude/meta-skill/scripts/orchestrator/validate_meta_contracts.py",
  "deps": [],
  "resources": [],
  "reality_gate": false,
  "runbook_ptr": "",
  "plan": "docs/superpowers/plans/2026-09-18-design-routing-plan.md",
  "design": "docs/superpowers/specs/2026-09-18-design-routing-design.md"
 },
 {
  "id": "T-M1-04",
  "title": "Planning law: experience design never omitted, artifact-path contract in bootstrap-planning.md; not_applicable.experience rule in product-intent-confirmation.md (U4; R-M1-04)",
  "touched_paths": [
   "claude/meta-skill/knowledge/bootstrap-planning.md",
   "claude/meta-skill/knowledge/product-intent-confirmation.md"
  ],
  "acceptance_cmd": "K=claude/meta-skill/knowledge; python3 -c \"\nimport sys, pathlib\nsys.path.insert(0, 'claude/meta-skill/scripts/orchestrator')\nimport validate_bootstrap as vb\ntext = pathlib.Path('claude/meta-skill/knowledge/bootstrap-planning.md').read_text(encoding='utf-8')\napp = tuple(vb.APP_EXPERIENCE_DESIGN_ARTIFACTS)\nassert app == ('.allforai/app-design/concept/job-story-spec.json', '.allforai/app-design/spec/user-flow-spec.json', '.allforai/app-design/spec/screen-requirements-spec.json', '.allforai/app-design/spec/permissions-notifications-settings-spec.json'), app\npaths = app + tuple(vb.GAME_EXPERIENCE_DESIGN_DOC_PATHS)\nassert len(paths) == 6\nmissing = [p for p in paths if p not in text]\nassert not missing, missing\n\" && grep -qF 'never means omitting experience design' $K/bootstrap-planning.md && grep -qF 'missing_experience_design_node' $K/bootstrap-planning.md && grep -qF 'implementation_not_blocked_by_experience_design' $K/bootstrap-planning.md && grep -qF 'the contract is the artifact path' $K/bootstrap-planning.md && grep -F 'not_applicable.experience' $K/product-intent-confirmation.md | grep -F 'experience_priority.mode' | grep -qF 'experience_not_applicable_on_ui_product' && test -z \"$(grep -n 'experience_priority' $K/product-intent-confirmation.md | grep -v 'experience_priority.mode')\" && python3 claude/meta-skill/scripts/orchestrator/validate_meta_contracts.py",
  "deps": [
   "T-M1-01"
  ],
  "resources": [],
  "reality_gate": false,
  "runbook_ptr": "",
  "plan": "docs/superpowers/plans/2026-09-18-design-routing-plan.md",
  "design": "docs/superpowers/specs/2026-09-18-design-routing-design.md"
 },
 {
  "id": "T-M1-05",
  "title": "app-design capability runs unattended: replace human_gate / Human Gate Protocol with Phase A decision_mode brainstorm + decision_inputs; fix reviewer prompt line (U5; R-M1-05)",
  "touched_paths": [
   "claude/meta-skill/knowledge/capabilities/app-design.md",
   "claude/meta-skill/tests/prompts/domain-codex.md"
  ],
  "acceptance_cmd": "A=claude/meta-skill/knowledge/capabilities/app-design.md; P=claude/meta-skill/tests/prompts/domain-codex.md; ! grep -qF '## Human Gate Protocol' $A && ! grep -qF 'requires `discipline_owner` approval' $A && ! grep -qF 'Merge all approved design JSONs' $A && grep -qF '## Decision Inputs' $A && grep -qF 'decision_mode: \"brainstorm\"' $A && grep -qF 'decision_inputs' $A && grep -qF 'No node carries `human_gate: true`' $A && grep -qF 'Merge all selected design JSONs' $A && grep -qF 'Discipline Owner' $A && ! grep -qF 'Human Gate Protocol 节是否引用' $P && grep -qF '是否已无 Human Gate Protocol 节' $P && test -z \"$(grep -n 'experience_priority' $A | grep -v 'experience_priority.mode')\" && python3 claude/meta-skill/scripts/orchestrator/validate_meta_contracts.py && python3 -m pytest --co -q claude/meta-skill/tests/unit/test_validate_bootstrap.py | grep -q 'test_app_design_flow_passes' && python3 -m pytest -q claude/meta-skill/tests/unit/test_validate_bootstrap.py -k test_app_design_flow",
  "deps": [],
  "resources": [],
  "reality_gate": false,
  "runbook_ptr": "",
  "plan": "docs/superpowers/plans/2026-09-18-design-routing-plan.md",
  "design": "docs/superpowers/specs/2026-09-18-design-routing-design.md"
 },
 {
  "id": "T-M1-06",
  "title": "bootstrap-audits.md: three-way §3.5 trigger and new blocking §3.5.0b App Design Coverage Check with seven concern rows (U6; R-M1-06)",
  "touched_paths": [
   "claude/meta-skill/knowledge/bootstrap-audits.md"
  ],
  "acceptance_cmd": "F=claude/meta-skill/knowledge/bootstrap-audits.md; grep -qF '#### 3.5.0b App Design Coverage Check' $F && grep -qF 'experience_priority.mode != none' $F && grep -qF 'App Design Coverage Check** (§3.5.0b)' $F && grep -qF 'First entry & onboarding' $F && grep -qF 'Main line, not a feature grid' $F && grep -qF 'In-progress feedback of the core loop' $F && grep -qF 'What happens after completion' $F && grep -qF 'Empty / loading / error / success states' $F && grep -qF 'Reason to return' $F && grep -qF 'Settings audience' $F && grep -qiF 'blocking' $F && test \"$(grep -n '^#### 3.5.0b' $F | head -1 | cut -d: -f1)\" -lt \"$(grep -n '^#### 3.5.1' $F | head -1 | cut -d: -f1)\" && python3 claude/meta-skill/scripts/orchestrator/validate_meta_contracts.py",
  "deps": [],
  "resources": [],
  "reality_gate": false,
  "runbook_ptr": "",
  "plan": "docs/superpowers/plans/2026-09-18-design-routing-plan.md",
  "design": "docs/superpowers/specs/2026-09-18-design-routing-design.md"
 },
 {
  "id": "T-M1-07",
  "title": "validate_meta_contracts.py: validate_experience_routing_contract pins nine routing literals, registered in main(); module closure checks (U8; R-M1-08)",
  "touched_paths": [
   "claude/meta-skill/scripts/orchestrator/validate_meta_contracts.py"
  ],
  "acceptance_cmd": "python3 claude/meta-skill/scripts/orchestrator/validate_meta_contracts.py && python3 -c \"\nimport sys, inspect\nsys.path.insert(0, 'claude/meta-skill/scripts/orchestrator')\nimport validate_meta_contracts as m\nassert 'validate_experience_routing_contract(errors)' in inspect.getsource(m.main)\nreal = []\nm.validate_experience_routing_contract(real)\nassert real == [], real\nm._bootstrap_text = lambda: ''\nerrs = []\nm.validate_experience_routing_contract(errs)\nhits = [e for e in errs if 'missing experience routing term' in e]\nassert len(hits) == 9, errs\nassert any('3.5.0b App Design Coverage Check' in e for e in hits)\nassert any('consumer | admin | mixed | none' in e for e in hits)\n\" && python3 claude/meta-skill/scripts/orchestrator/validate_skills.py claude/meta-skill/skills && test -z \"$(grep -rn 'experience_priority' claude/meta-skill/knowledge | grep -v 'experience_priority.mode' | grep -v bootstrap)\"",
  "deps": [
   "T-M1-02",
   "T-M1-03",
   "T-M1-04",
   "T-M1-05",
   "T-M1-06"
  ],
  "resources": [],
  "reality_gate": false,
  "runbook_ptr": "",
  "plan": "docs/superpowers/plans/2026-09-18-design-routing-plan.md",
  "design": "docs/superpowers/specs/2026-09-18-design-routing-design.md"
 },
 {
  "id": "T-M2-01",
  "title": "Topic experience-direction in TOPICS, test mirror, and repair of the two session tests the insertion breaks",
  "touched_paths": [
   "claude/meta-skill/scripts/orchestrator/product_intent.py",
   "claude/meta-skill/tests/unit/test_product_intent_session.py",
   "claude/meta-skill/tests/unit/test_experience_direction.py"
  ],
  "acceptance_cmd": "python3 -m pytest -q claude/meta-skill/tests/unit/test_experience_direction.py::test_topic_is_listed_before_tradeoffs_and_missing_direction_is_a_gap claude/meta-skill/tests/unit/test_product_intent_session.py claude/meta-skill/tests/unit/test_intent_review_corrections.py",
  "deps": [
   "T-M1-01"
  ],
  "resources": [],
  "reality_gate": false,
  "runbook_ptr": "",
  "plan": "docs/superpowers/plans/2026-09-18-experience-intent-plan.md",
  "design": "docs/superpowers/specs/2026-09-18-experience-intent-design.md"
 },
 {
  "id": "T-M2-02",
  "title": "Proposal storage, validation, three-namespace id uniqueness and operation propose",
  "touched_paths": [
   "claude/meta-skill/scripts/orchestrator/product_intent.py",
   "claude/meta-skill/tests/unit/test_experience_direction.py"
  ],
  "acceptance_cmd": "python3 -m pytest -q claude/meta-skill/tests/unit/test_experience_direction.py::test_propose_validates_count_recommendation_and_fields claude/meta-skill/tests/unit/test_experience_direction.py::test_proposal_identity_is_unique_across_proposals_intents_and_questions claude/meta-skill/tests/unit/test_experience_direction.py::test_proposal_cannot_be_confirmed_or_frozen claude/meta-skill/tests/unit/test_product_question_identity.py",
  "deps": [
   "T-M2-01"
  ],
  "resources": [],
  "reality_gate": false,
  "runbook_ptr": "",
  "plan": "docs/superpowers/plans/2026-09-18-experience-intent-plan.md",
  "design": "docs/superpowers/specs/2026-09-18-experience-intent-design.md"
 },
 {
  "id": "T-M2-03",
  "title": "_discussion/resume present the current proposal round; old output byte-identical",
  "touched_paths": [
   "claude/meta-skill/scripts/orchestrator/product_intent.py",
   "claude/meta-skill/tests/unit/test_experience_direction.py"
  ],
  "acceptance_cmd": "python3 -m pytest -q claude/meta-skill/tests/unit/test_experience_direction.py::test_propose_stores_rounds_without_journal_and_resume_presents_current_round claude/meta-skill/tests/unit/test_product_intent_resume.py",
  "deps": [
   "T-M2-02"
  ],
  "resources": [],
  "reality_gate": false,
  "runbook_ptr": "",
  "plan": "docs/superpowers/plans/2026-09-18-experience-intent-plan.md",
  "design": "docs/superpowers/specs/2026-09-18-experience-intent-design.md"
 },
 {
  "id": "T-M2-04",
  "title": "decide action select producing the confirmed experience-direction intent that freezes and passes the three gates",
  "touched_paths": [
   "claude/meta-skill/scripts/orchestrator/product_intent.py",
   "claude/meta-skill/tests/unit/test_experience_direction.py"
  ],
  "acceptance_cmd": "python3 -m pytest -q claude/meta-skill/tests/unit/test_experience_direction.py::test_selected_direction_freezes_and_passes_all_public_gates claude/meta-skill/tests/unit/test_experience_direction.py::test_select_then_adjust_in_one_batch_keeps_revision_lineage claude/meta-skill/tests/unit/test_experience_direction.py::test_select_needs_a_current_round_proposal_and_a_free_direction_slot",
  "deps": [
   "T-M1-02",
   "T-M2-03"
  ],
  "resources": [],
  "reality_gate": false,
  "runbook_ptr": "",
  "plan": "docs/superpowers/plans/2026-09-18-experience-intent-plan.md",
  "design": "docs/superpowers/specs/2026-09-18-experience-intent-design.md"
 },
 {
  "id": "T-M2-05",
  "title": "decide action delegate: recommended proposal, auto_decided and confirmation.delegated, refused without a current round",
  "touched_paths": [
   "claude/meta-skill/scripts/orchestrator/product_intent.py",
   "claude/meta-skill/tests/unit/test_experience_direction.py"
  ],
  "acceptance_cmd": "python3 -m pytest -q claude/meta-skill/tests/unit/test_experience_direction.py::test_delegate_records_the_recommended_proposal_as_an_auto_decision claude/meta-skill/tests/unit/test_experience_direction.py::test_delegate_and_select_need_a_current_proposal_round",
  "deps": [
   "T-M2-04"
  ],
  "resources": [],
  "reality_gate": false,
  "runbook_ptr": "",
  "plan": "docs/superpowers/plans/2026-09-18-experience-intent-plan.md",
  "design": "docs/superpowers/specs/2026-09-18-experience-intent-design.md"
 },
 {
  "id": "T-M2-06",
  "title": "Read-only disclosure: public delegations() and CLI --delegations",
  "touched_paths": [
   "claude/meta-skill/scripts/orchestrator/product_intent.py",
   "claude/meta-skill/tests/unit/test_experience_direction.py"
  ],
  "acceptance_cmd": "python3 -m pytest -q claude/meta-skill/tests/unit/test_experience_direction.py::test_delegate_records_auto_decision_and_is_disclosed",
  "deps": [
   "T-M2-05"
  ],
  "resources": [],
  "reality_gate": false,
  "runbook_ptr": "",
  "plan": "docs/superpowers/plans/2026-09-18-experience-intent-plan.md",
  "design": "docs/superpowers/specs/2026-09-18-experience-intent-design.md"
 },
 {
  "id": "T-M2-07",
  "title": "validate_scope blocker ui_product_without_experience_direction (fires for consumer/mixed, silent otherwise)",
  "touched_paths": [
   "claude/meta-skill/scripts/orchestrator/product_intent.py",
   "claude/meta-skill/tests/unit/test_experience_direction.py"
  ],
  "acceptance_cmd": "python3 -m pytest -q claude/meta-skill/tests/unit/test_experience_direction.py::test_ui_product_without_direction_is_blocked_at_every_gate claude/meta-skill/tests/unit/test_experience_direction.py::test_direction_gate_stays_silent_when_it_does_not_apply",
  "deps": [
   "T-M1-02",
   "T-M2-06"
  ],
  "resources": [],
  "reality_gate": false,
  "runbook_ptr": "",
  "plan": "docs/superpowers/plans/2026-09-18-experience-intent-plan.md",
  "design": "docs/superpowers/specs/2026-09-18-experience-intent-design.md"
 },
 {
  "id": "T-M2-08",
  "title": "run-summary and orchestrator-template Post-Completion step 0b disclose delegated decisions",
  "touched_paths": [
   "claude/meta-skill/scripts/orchestrator/summarize_run_log.py",
   "claude/meta-skill/knowledge/orchestrator-template.md",
   "claude/meta-skill/tests/unit/test_experience_direction.py"
  ],
  "acceptance_cmd": "python3 -m pytest -q claude/meta-skill/tests/unit/test_experience_direction.py::test_run_summary_and_completion_text_disclose_delegations claude/meta-skill/tests/unit/test_run_logging.py && python3 claude/meta-skill/scripts/orchestrator/validate_meta_contracts.py",
  "deps": [
   "T-M2-07"
  ],
  "resources": [],
  "reality_gate": false,
  "runbook_ptr": "",
  "plan": "docs/superpowers/plans/2026-09-18-experience-intent-plan.md",
  "design": "docs/superpowers/specs/2026-09-18-experience-intent-design.md"
 },
 {
  "id": "T-M2-09",
  "title": "Protocol text rewrite in product-intent-confirmation.md (topic, select/delegate as actions, propose entry, proposals section, --delegations)",
  "touched_paths": [
   "claude/meta-skill/knowledge/product-intent-confirmation.md",
   "claude/meta-skill/tests/unit/test_experience_direction.py"
  ],
  "acceptance_cmd": "python3 -m pytest -q claude/meta-skill/tests/unit/test_experience_direction.py::test_protocol_text_names_the_new_topic_and_actions && ! grep -n \"experience_priority\" claude/meta-skill/knowledge/product-intent-confirmation.md | grep -v \"experience_priority.mode\" | grep -q . && python3 claude/meta-skill/scripts/orchestrator/validate_meta_contracts.py",
  "deps": [
   "T-M2-08"
  ],
  "resources": [],
  "reality_gate": false,
  "runbook_ptr": "",
  "plan": "docs/superpowers/plans/2026-09-18-experience-intent-plan.md",
  "design": "docs/superpowers/specs/2026-09-18-experience-intent-design.md"
 },
 {
  "id": "T-M2-10",
  "title": "Backward-compatibility proof (pre-module concept reads without drift) and full module regression",
  "touched_paths": [
   "claude/meta-skill/tests/unit/test_experience_direction.py",
   "claude/meta-skill/scripts/orchestrator/product_intent.py"
  ],
  "acceptance_cmd": "python3 -m pytest -q claude/meta-skill/tests/unit/test_experience_direction.py::test_pre_existing_concept_and_journal_read_without_drift && python3 -m pytest -q claude/meta-skill/tests/unit/test_experience_direction.py && python3 -m pytest -q claude/meta-skill/tests/unit/test_product_intent_session.py claude/meta-skill/tests/unit/test_product_intent_resume.py claude/meta-skill/tests/unit/test_freeze_idempotence.py claude/meta-skill/tests/unit/test_product_question_identity.py claude/meta-skill/tests/unit/test_product_retained_scope.py claude/meta-skill/tests/unit/test_intent_review_corrections.py claude/meta-skill/tests/unit/test_legacy_profile_authority.py claude/meta-skill/tests/unit/test_legacy_projection_authority.py claude/meta-skill/tests/unit/test_local_reopen_scope.py claude/meta-skill/tests/unit/test_acceptance_allocation.py claude/meta-skill/tests/unit/test_run_logging.py claude/meta-skill/tests/unit/test_evidence_freshness.py::test_selected_intent_payload_drift_in_real_producer_baseline_is_stale && python3 claude/meta-skill/scripts/orchestrator/validate_meta_contracts.py",
  "deps": [
   "T-M2-09"
  ],
  "resources": [],
  "reality_gate": false,
  "runbook_ptr": "",
  "plan": "docs/superpowers/plans/2026-09-18-experience-intent-plan.md",
  "design": "docs/superpowers/specs/2026-09-18-experience-intent-design.md"
 },
 {
  "id": "T-M4-01",
  "title": "defensive-patterns.md: add Pattern I (Specification Gap Escalation) and Pattern J (Audience Isolation) with explicit #pattern-i/#pattern-j anchors",
  "touched_paths": [
   "claude/meta-skill/knowledge/defensive-patterns.md"
  ],
  "acceptance_cmd": "F=claude/meta-skill/knowledge/defensive-patterns.md; for t in '<a id=\"pattern-i\"></a>' '## Pattern I: Specification Gap Escalation' '<a id=\"pattern-j\"></a>' '## Pattern J: Audience Isolation' unspecified_user_visible_decision needed_decision blocking_intent_ids suggested_owner_artifact suspected_root_node requirement_ref '`end-user`' '`operator`' '`developer`' build-time remote-config deploy-env '.allforai/app-design/spec/permissions-notifications-settings-spec.json'; do grep -qF -- \"$t\" \"$F\" || { echo \"missing: $t\"; exit 1; }; done && ! grep -qi 'ink-scent' \"$F\" && python3 -c \"t=open('claude/meta-skill/knowledge/defensive-patterns.md',encoding='utf-8').read(); assert t.count('## Pattern H:')==1 and t.index('## Pattern H:')<t.index('## Pattern I: Specification Gap Escalation')<t.index('## Pattern J: Audience Isolation'); tail=t.split('## Pattern I: Specification Gap Escalation')[1]; assert all(tail.count(s)>=2 for s in ('**Trigger condition**:','**Protocol**:','**Key principles**:','**Example**:')), 'four-part layout incomplete'\" && python3 claude/meta-skill/scripts/orchestrator/validate_generalization_boundaries.py && python3 claude/meta-skill/scripts/orchestrator/validate_meta_contracts.py",
  "deps": [
   "T-M1-04"
  ],
  "resources": [],
  "reality_gate": false,
  "runbook_ptr": "",
  "plan": "docs/superpowers/plans/2026-09-18-spec-gap-discipline-plan.md",
  "design": "docs/superpowers/specs/2026-09-18-spec-gap-discipline-design.md"
 },
 {
  "id": "T-M4-02",
  "title": "node-spec-template.md: add '## User-visible decisions' section, Pattern I/J knowledge anchors, contract_gaps repair target",
  "touched_paths": [
   "claude/meta-skill/knowledge/node-spec-template.md"
  ],
  "acceptance_cmd": "F=claude/meta-skill/knowledge/node-spec-template.md; for t in '## User-visible decisions' 'defensive-patterns.md#pattern-i' 'defensive-patterns.md#pattern-j' contract_gaps unspecified_user_visible_decision 'Not applicable — no end-user surface' 'Source artifact path' '## Attention Contract' 'Repair targets' '## Effect Verification' '## Quality Acceptance' 'Bootstrap should spend context once' 'execute in pull mode'; do grep -qF -- \"$t\" \"$F\" || { echo \"missing: $t\"; exit 1; }; done && python3 -c \"t=open('claude/meta-skill/knowledge/node-spec-template.md',encoding='utf-8').read(); assert t.index('\\n## Guidance')<t.index('\\n## User-visible decisions')<t.index('\\n## Exit Artifacts'); assert t.count('\\n## User-visible decisions')==1\" && python3 claude/meta-skill/scripts/orchestrator/validate_meta_contracts.py && python3 claude/meta-skill/scripts/orchestrator/validate_generalization_boundaries.py",
  "deps": [
   "T-M1-04",
   "T-M4-01"
  ],
  "resources": [],
  "reality_gate": false,
  "runbook_ptr": "",
  "plan": "docs/superpowers/plans/2026-09-18-spec-gap-discipline-plan.md",
  "design": "docs/superpowers/specs/2026-09-18-spec-gap-discipline-design.md"
 },
 {
  "id": "T-M4-03",
  "title": "Settings spec and topology spec SKILL.md: settings items and service_endpoints carry audience/provisioning/surface/requirement_ref",
  "touched_paths": [
   "claude/meta-skill/skills/app-design/20-spec/permissions-notifications-settings-spec/SKILL.md",
   "claude/meta-skill/skills/app-design/20-spec/app-surface-topology-spec/SKILL.md"
  ],
  "acceptance_cmd": "S=claude/meta-skill/skills/app-design/20-spec/permissions-notifications-settings-spec/SKILL.md; T=claude/meta-skill/skills/app-design/20-spec/app-surface-topology-spec/SKILL.md; for t in 'settings_groups[].items[]' setting_id audience end-user operator developer provisioning build-time remote-config deploy-env requirement_ref admin_console operator_console 'Pattern J'; do grep -qF -- \"$t\" \"$S\" || { echo \"settings missing: $t\"; exit 1; }; done && for t in 'service_endpoints' endpoint_id consumer_surface_refs audience provisioning build-time remote-config deploy-env requirement_ref; do grep -qF -- \"$t\" \"$T\" || { echo \"topology missing: $t\"; exit 1; }; done && python3 claude/meta-skill/scripts/orchestrator/validate_skills.py claude/meta-skill/skills && python3 claude/meta-skill/scripts/orchestrator/validate_generalization_boundaries.py",
  "deps": [],
  "resources": [],
  "reality_gate": false,
  "runbook_ptr": "",
  "plan": "docs/superpowers/plans/2026-09-18-spec-gap-discipline-plan.md",
  "design": "docs/superpowers/specs/2026-09-18-spec-gap-discipline-design.md"
 },
 {
  "id": "T-M4-04",
  "title": "program-handoff-generation SKILL.md: handoff carries settings_items[] and service_endpoints[] with audience/provisioning verbatim",
  "touched_paths": [
   "claude/meta-skill/skills/app-design/30-generate/program-handoff-generation/SKILL.md"
  ],
  "acceptance_cmd": "F=claude/meta-skill/skills/app-design/30-generate/program-handoff-generation/SKILL.md; for t in 'settings_items' 'service_endpoints' setting_id audience provisioning requirement_ref end-user; do grep -qF -- \"$t\" \"$F\" || { echo \"missing: $t\"; exit 1; }; done && python3 claude/meta-skill/scripts/orchestrator/validate_skills.py claude/meta-skill/skills && python3 claude/meta-skill/scripts/orchestrator/validate_generalization_boundaries.py",
  "deps": [
   "T-M4-03"
  ],
  "resources": [],
  "reality_gate": false,
  "runbook_ptr": "",
  "plan": "docs/superpowers/plans/2026-09-18-spec-gap-discipline-plan.md",
  "design": "docs/superpowers/specs/2026-09-18-spec-gap-discipline-design.md"
 },
 {
  "id": "T-M4-05",
  "title": "app-design-closure-qa SKILL.md: Settings audience closure checks (missing_audience, non_end_user_item_in_screen_spec) -> missing_contracts + needs_revision",
  "touched_paths": [
   "claude/meta-skill/skills/app-design/40-qa/app-design-closure-qa/SKILL.md"
  ],
  "acceptance_cmd": "F=claude/meta-skill/skills/app-design/40-qa/app-design-closure-qa/SKILL.md; for t in 'Settings audience closure' missing_audience non_end_user_item_in_screen_spec missing_contracts needs_revision item_id requirement_ref 'screen-requirements-spec.json'; do grep -qF -- \"$t\" \"$F\" || { echo \"missing: $t\"; exit 1; }; done && python3 claude/meta-skill/scripts/orchestrator/validate_skills.py claude/meta-skill/skills && python3 claude/meta-skill/scripts/orchestrator/validate_generalization_boundaries.py",
  "deps": [
   "T-M4-03"
  ],
  "resources": [],
  "reality_gate": false,
  "runbook_ptr": "",
  "plan": "docs/superpowers/plans/2026-09-18-spec-gap-discipline-plan.md",
  "design": "docs/superpowers/specs/2026-09-18-spec-gap-discipline-design.md"
 },
 {
  "id": "T-M4-06",
  "title": "product-verify.md: add '### Audience Leak Check', Rule 6 Audience isolation, #pattern-j knowledge reference",
  "touched_paths": [
   "claude/meta-skill/knowledge/capabilities/product-verify.md"
  ],
  "acceptance_cmd": "F=claude/meta-skill/knowledge/capabilities/product-verify.md; for t in '### Audience Leak Check' audience_leak 'defensive-patterns.md#pattern-j' observed_audience spec_ref contract_gaps code_gaps requirement_ref '5. **Screenshot-backed UI acceptance**'; do grep -qF -- \"$t\" \"$F\" || { echo \"missing: $t\"; exit 1; }; done && grep -qE '^6\\. \\*\\*Audience isolation\\*\\*' \"$F\" && python3 -c \"t=open('claude/meta-skill/knowledge/capabilities/product-verify.md',encoding='utf-8').read(); assert t.index('### Multi-Client Feature Parity Verification')<t.index('### Audience Leak Check')<t.index('## Rules (Must Preserve)')\" && python3 claude/meta-skill/scripts/orchestrator/validate_meta_contracts.py && python3 claude/meta-skill/scripts/orchestrator/validate_generalization_boundaries.py",
  "deps": [
   "T-M4-01"
  ],
  "resources": [],
  "reality_gate": false,
  "runbook_ptr": "",
  "plan": "docs/superpowers/plans/2026-09-18-spec-gap-discipline-plan.md",
  "design": "docs/superpowers/specs/2026-09-18-spec-gap-discipline-design.md"
 },
 {
  "id": "T-M4-07",
  "title": "Characterization test: an unspecified_user_visible_decision contract gap keeps the artifact incomplete, allow-flag included",
  "touched_paths": [
   "claude/meta-skill/tests/unit/test_check_artifacts_measurement.py"
  ],
  "acceptance_cmd": "python3 -m pytest -q \"claude/meta-skill/tests/unit/test_check_artifacts_measurement.py::test_an_unspecified_user_visible_decision_gap_keeps_the_artifact_incomplete\" && python3 -m pytest -q claude/meta-skill/tests/unit/test_check_artifacts_measurement.py claude/meta-skill/tests/unit/test_check_artifacts.py",
  "deps": [],
  "resources": [],
  "reality_gate": false,
  "runbook_ptr": "",
  "plan": "docs/superpowers/plans/2026-09-18-spec-gap-discipline-plan.md",
  "design": "docs/superpowers/specs/2026-09-18-spec-gap-discipline-design.md"
 },
 {
  "id": "T-M4-08",
  "title": "validate_meta_contracts.py: add and register validate_spec_gap_discipline_contract pinning the seven-file literal table",
  "touched_paths": [
   "claude/meta-skill/scripts/orchestrator/validate_meta_contracts.py"
  ],
  "acceptance_cmd": "V=claude/meta-skill/scripts/orchestrator/validate_meta_contracts.py; [ \"$(grep -c 'validate_spec_gap_discipline_contract(errors' \"$V\")\" -ge 2 ] && for t in 'defensive-patterns.md#pattern-i' '## Pattern I: Specification Gap Escalation' '## User-visible decisions' 'settings_items' 'service_endpoints' 'non_end_user_item_in_screen_spec' 'missing_audience' '### Audience Leak Check' 'defensive-patterns.md#pattern-j' 'missing spec-gap discipline term'; do grep -qF -- \"$t\" \"$V\" || { echo \"validator lacks pin: $t\"; exit 1; }; done && python3 -c \"\nimport sys,tempfile,pathlib,shutil\nsys.path.insert(0,'claude/meta-skill/scripts/orchestrator')\nimport validate_meta_contracts as v\nsrc=pathlib.Path('claude/meta-skill'); tmp=pathlib.Path(tempfile.mkdtemp())\nv.ROOT=tmp; e=[]; v.validate_spec_gap_discipline_contract(e)\nassert len([x for x in e if x.endswith(': missing')])==7, e\nshutil.copytree(src/'knowledge', tmp/'knowledge'); shutil.copytree(src/'skills/app-design', tmp/'skills/app-design')\ne=[]; v.validate_spec_gap_discipline_contract(e); assert e==[], e\np=tmp/'knowledge/defensive-patterns.md'; p.write_text(p.read_text(encoding='utf-8').replace('## Pattern J: Audience Isolation','## Pattern J'),encoding='utf-8')\ne=[]; v.validate_spec_gap_discipline_contract(e)\nassert any('missing spec-gap discipline term' in x and 'Pattern J: Audience Isolation' in x for x in e), e\n\" && python3 claude/meta-skill/scripts/orchestrator/validate_meta_contracts.py && python3 claude/meta-skill/scripts/orchestrator/validate_skills.py claude/meta-skill/skills && python3 claude/meta-skill/scripts/orchestrator/validate_generalization_boundaries.py",
  "deps": [
   "T-M4-01",
   "T-M4-02",
   "T-M4-03",
   "T-M4-04",
   "T-M4-05",
   "T-M4-06"
  ],
  "resources": [],
  "reality_gate": false,
  "runbook_ptr": "",
  "plan": "docs/superpowers/plans/2026-09-18-spec-gap-discipline-plan.md",
  "design": "docs/superpowers/specs/2026-09-18-spec-gap-discipline-design.md"
 },
 {
  "id": "T-M3-01",
  "title": "Source-wiring validator validate_app_experience_pipeline.py with its unit test",
  "touched_paths": [
   "claude/meta-skill/scripts/orchestrator/validate_app_experience_pipeline.py",
   "claude/meta-skill/tests/unit/test_validate_app_experience_pipeline.py"
  ],
  "acceptance_cmd": "python3 -m py_compile claude/meta-skill/scripts/orchestrator/validate_app_experience_pipeline.py && [ \"$(python3 -m pytest claude/meta-skill/tests/unit/test_validate_app_experience_pipeline.py --co -q | grep -c 'test_validate_app_experience_pipeline_')\" -ge 3 ] && python3 -m pytest -q claude/meta-skill/tests/unit/test_validate_app_experience_pipeline.py claude/meta-skill/tests/unit/test_validate_game_creative_pipeline.py",
  "deps": [],
  "resources": [],
  "reality_gate": false,
  "runbook_ptr": "",
  "plan": "docs/superpowers/plans/2026-09-18-experience-gate-plan.md",
  "design": "docs/superpowers/specs/2026-09-18-experience-gate-design.md"
 },
 {
  "id": "T-M3-02",
  "title": "Child skill experience-quality-critique (report, review-doc, lens vocabulary contracts) and its PACK registration",
  "touched_paths": [
   "claude/meta-skill/skills/app-design/40-qa/experience-quality-critique/SKILL.md",
   "claude/meta-skill/skills/app-design/PACK.md",
   "claude/meta-skill/tests/unit/test_experience_quality_critique_skill.py"
  ],
  "acceptance_cmd": "python3 -m pytest -q claude/meta-skill/tests/unit/test_experience_quality_critique_skill.py claude/meta-skill/tests/unit/test_validate_skills.py && python3 claude/meta-skill/scripts/orchestrator/validate_skills.py claude/meta-skill/skills",
  "deps": [
   "T-M1-02",
   "T-M1-04",
   "T-M1-07",
   "T-M2-04",
   "T-M2-10",
   "T-M3-01",
   "T-M4-01",
   "T-M4-03",
   "T-M4-07",
   "T-M4-08"
  ],
  "resources": [],
  "reality_gate": false,
  "runbook_ptr": "",
  "plan": "docs/superpowers/plans/2026-09-18-experience-gate-plan.md",
  "design": "docs/superpowers/specs/2026-09-18-experience-gate-design.md"
 },
 {
  "id": "T-M3-03",
  "title": "Register the critique and design-repair nodes in capabilities/app-design.md",
  "touched_paths": [
   "claude/meta-skill/knowledge/capabilities/app-design.md"
  ],
  "acceptance_cmd": "F=claude/meta-skill/knowledge/capabilities/app-design.md && grep -q 'experience-critique-design' $F && grep -q 'experience-design-repair' $F && grep -q 'experience-critique-runtime' $F && grep -q 'app-design/40-qa/experience-quality-critique' $F && python3 -c 'import sys; t=open(sys.argv[1],encoding=\"utf-8\").read(); assert t.index(\"| `experience-critique-design` |\") < t.index(\"| `experience-design-repair` |\") < t.index(\"| `app-design-finalize` |\")' $F && ! grep -E 'experience-critique|experience-design-repair' $F | grep -qE 'human_gate|decision_mode' && ! grep -rn 'experience_priority' claude/meta-skill/knowledge | grep -v 'experience_priority.mode' | grep -v bootstrap | grep -q . && python3 claude/meta-skill/scripts/orchestrator/validate_skills.py claude/meta-skill/skills && python3 claude/meta-skill/scripts/orchestrator/validate_meta_contracts.py",
  "deps": [
   "T-M1-02",
   "T-M3-02"
  ],
  "resources": [],
  "reality_gate": false,
  "runbook_ptr": "",
  "plan": "docs/superpowers/plans/2026-09-18-experience-gate-plan.md",
  "design": "docs/superpowers/specs/2026-09-18-experience-gate-design.md"
 },
 {
  "id": "T-M3-04",
  "title": "check_artifacts: non-empty must_fix_* (top level or under gates{}) means the artifact is not complete",
  "touched_paths": [
   "claude/meta-skill/scripts/orchestrator/check_artifacts.py",
   "claude/meta-skill/tests/unit/test_check_artifacts.py"
  ],
  "acceptance_cmd": "[ \"$(python3 -m pytest claude/meta-skill/tests/unit/test_check_artifacts.py --co -q | grep -c 'must_fix')\" -ge 4 ] && python3 -m pytest -q claude/meta-skill/tests/unit/test_check_artifacts.py claude/meta-skill/tests/unit/test_check_artifacts_measurement.py",
  "deps": [
   "T-M1-07",
   "T-M2-10",
   "T-M4-07",
   "T-M4-08"
  ],
  "resources": [],
  "reality_gate": false,
  "runbook_ptr": "",
  "plan": "docs/superpowers/plans/2026-09-18-experience-gate-plan.md",
  "design": "docs/superpowers/specs/2026-09-18-experience-gate-design.md"
 },
 {
  "id": "T-M3-05",
  "title": "validate_experience_gate_flow in validate_bootstrap.py, registered in main(), __all__ and structural_gate_blockers",
  "touched_paths": [
   "claude/meta-skill/scripts/orchestrator/validate_bootstrap.py",
   "claude/meta-skill/tests/unit/test_validate_bootstrap.py"
  ],
  "acceptance_cmd": "python3 -m py_compile claude/meta-skill/scripts/orchestrator/validate_bootstrap.py && python3 -c 'import sys; sys.path.insert(0,\"claude/meta-skill/scripts/orchestrator\"); import validate_bootstrap as v; assert {\"validate_experience_gate_flow\",\"experience_gate_flow_findings\"} <= set(v.__all__); assert callable(v._ui_implementation_nodes)' && [ \"$(python3 -m pytest claude/meta-skill/tests/unit/test_validate_bootstrap.py --co -q | grep -c 'experience_gate')\" -ge 14 ] && python3 -m pytest -q claude/meta-skill/tests/unit/test_validate_bootstrap.py claude/meta-skill/tests/unit/test_validate_unattended_readiness.py claude/meta-skill/tests/unit/test_bootstrap_scope.py claude/meta-skill/tests/unit/test_product_intent_session.py claude/meta-skill/tests/unit/test_acceptance_allocation.py",
  "deps": [
   "T-M1-01",
   "T-M1-02",
   "T-M1-04",
   "T-M1-07",
   "T-M2-10",
   "T-M4-07",
   "T-M4-08"
  ],
  "resources": [],
  "reality_gate": false,
  "runbook_ptr": "",
  "plan": "docs/superpowers/plans/2026-09-18-experience-gate-plan.md",
  "design": "docs/superpowers/specs/2026-09-18-experience-gate-design.md"
 },
 {
  "id": "T-M3-06",
  "title": "Readiness gate accepts the Must #9 design/runtime repair-loop shape (profile-less graph) and the new gate bites at the /run boundary (product-route profile)",
  "touched_paths": [
   "claude/meta-skill/tests/unit/test_validate_unattended_readiness.py"
  ],
  "acceptance_cmd": "python3 -m pytest -q \"claude/meta-skill/tests/unit/test_validate_unattended_readiness.py::test_unattended_readiness_accepts_experience_gate_repair_loops\" \"claude/meta-skill/tests/unit/test_validate_unattended_readiness.py::test_unattended_readiness_reports_experience_gate_at_run_boundary\" && python3 -m pytest -q claude/meta-skill/tests/unit/test_validate_unattended_readiness.py",
  "deps": [
   "T-M1-02",
   "T-M1-04",
   "T-M3-05"
  ],
  "resources": [],
  "reality_gate": false,
  "runbook_ptr": "",
  "plan": "docs/superpowers/plans/2026-09-18-experience-gate-plan.md",
  "design": "docs/superpowers/specs/2026-09-18-experience-gate-design.md"
 },
 {
  "id": "T-M3-07",
  "title": "Planning law Must #9 (Experience quality gate) appended to bootstrap-planning.md",
  "touched_paths": [
   "claude/meta-skill/knowledge/bootstrap-planning.md"
  ],
  "acceptance_cmd": "F=claude/meta-skill/knowledge/bootstrap-planning.md && grep -qF '9. **Experience quality gate (products with UI).**' $F && grep -qF '8. **Creative quality gate (game projects).**' $F && grep -qF 'skills/app-design/40-qa/experience-quality-critique/SKILL.md' $F && grep -qF 'experience-quality-critique-design.json' $F && grep -qF 'experience-quality-critique-runtime.json' $F && grep -qF 'must_fix_before_implementation' $F && grep -qF 'must_fix_before_release' $F && grep -qF 'docs/experience-review/' $F && grep -qF 'required_repair_loops' $F && grep -qF 'experience_gaps' $F && grep -qF 'validate_experience_gate_flow' $F && grep -qF 'experience_priority.mode' $F && python3 claude/meta-skill/scripts/orchestrator/validate_app_experience_pipeline.py . && python3 claude/meta-skill/scripts/orchestrator/validate_meta_contracts.py",
  "deps": [
   "T-M1-02",
   "T-M3-01",
   "T-M3-02"
  ],
  "resources": [],
  "reality_gate": false,
  "runbook_ptr": "",
  "plan": "docs/superpowers/plans/2026-09-18-experience-gate-plan.md",
  "design": "docs/superpowers/specs/2026-09-18-experience-gate-design.md"
 },
 {
  "id": "T-M3-08",
  "title": "Suppress rule for experience_priority.mode = none and concept-acceptance prerequisite on the critique",
  "touched_paths": [
   "claude/meta-skill/knowledge/suppress-rules.md",
   "claude/meta-skill/knowledge/capabilities/concept-acceptance.md"
  ],
  "acceptance_cmd": "grep -qF 'experience_priority.mode = none' claude/meta-skill/knowledge/suppress-rules.md && grep -qF 'Must #9' claude/meta-skill/knowledge/suppress-rules.md && grep -qF 'creative-quality-critique' claude/meta-skill/knowledge/capabilities/concept-acceptance.md && grep -qF 'experience-quality-critique' claude/meta-skill/knowledge/capabilities/concept-acceptance.md && grep -qF 'hard_blocked_by' claude/meta-skill/knowledge/capabilities/concept-acceptance.md && ! grep -rn 'experience_priority' claude/meta-skill/knowledge | grep -v 'experience_priority.mode' | grep -v bootstrap | grep -q . && python3 claude/meta-skill/scripts/orchestrator/validate_meta_contracts.py",
  "deps": [
   "T-M1-02",
   "T-M1-07",
   "T-M2-10",
   "T-M4-07",
   "T-M4-08"
  ],
  "resources": [],
  "reality_gate": false,
  "runbook_ptr": "",
  "plan": "docs/superpowers/plans/2026-09-18-experience-gate-plan.md",
  "design": "docs/superpowers/specs/2026-09-18-experience-gate-design.md"
 },
 {
  "id": "T-M3-09",
  "title": "Pin the experience gate contract in validate_meta_contracts.py (validate_experience_gate_contract)",
  "touched_paths": [
   "claude/meta-skill/scripts/orchestrator/validate_meta_contracts.py"
  ],
  "acceptance_cmd": "[ \"$(grep -c 'validate_experience_gate_contract(errors' claude/meta-skill/scripts/orchestrator/validate_meta_contracts.py)\" -ge 2 ] && python3 -c 'import sys; sys.path.insert(0,\"claude/meta-skill/scripts/orchestrator\"); import validate_meta_contracts as m; m._bootstrap_text=lambda: \"\"; e=[]; m.validate_experience_gate_contract(e); assert len(e) >= 8, e' && python3 claude/meta-skill/scripts/orchestrator/validate_meta_contracts.py",
  "deps": [
   "T-M3-02",
   "T-M3-07",
   "T-M3-08"
  ],
  "resources": [],
  "reality_gate": false,
  "runbook_ptr": "",
  "plan": "docs/superpowers/plans/2026-09-18-experience-gate-plan.md",
  "design": "docs/superpowers/specs/2026-09-18-experience-gate-design.md"
 },
 {
  "id": "T-M3-10",
  "title": "Pre-commit wiring of the app experience pipeline validator and full module acceptance",
  "touched_paths": [
   ".githooks/pre-commit"
  ],
  "acceptance_cmd": "bash -n .githooks/pre-commit && [ \"$(grep -c 'validate_app_experience_pipeline.py \\.' .githooks/pre-commit)\" -eq 1 ] && [ \"$(grep -c 'validate_game_creative_pipeline.py \\.' .githooks/pre-commit)\" -eq 1 ] && python3 -m py_compile claude/meta-skill/scripts/orchestrator/*.py && python3 claude/meta-skill/scripts/orchestrator/validate_app_experience_pipeline.py . && python3 claude/meta-skill/scripts/orchestrator/validate_game_creative_pipeline.py . && python3 claude/meta-skill/scripts/orchestrator/validate_skills.py claude/meta-skill/skills && python3 claude/meta-skill/scripts/orchestrator/validate_meta_contracts.py && ! grep -rn 'experience_priority' claude/meta-skill/knowledge | grep -v 'experience_priority.mode' | grep -v bootstrap | grep -q . && python3 -m pytest -q claude/meta-skill/tests/unit/test_validate_bootstrap.py claude/meta-skill/tests/unit/test_validate_app_experience_pipeline.py claude/meta-skill/tests/unit/test_experience_quality_critique_skill.py claude/meta-skill/tests/unit/test_validate_game_creative_pipeline.py claude/meta-skill/tests/unit/test_check_artifacts.py claude/meta-skill/tests/unit/test_check_artifacts_measurement.py claude/meta-skill/tests/unit/test_validate_unattended_readiness.py claude/meta-skill/tests/unit/test_validate_skills.py claude/meta-skill/tests/unit/test_experience_direction.py claude/meta-skill/tests/unit/test_bootstrap_scope.py claude/meta-skill/tests/unit/test_product_intent_session.py claude/meta-skill/tests/unit/test_acceptance_allocation.py",
  "deps": [
   "T-M2-04",
   "T-M3-03",
   "T-M3-04",
   "T-M3-06",
   "T-M3-09",
   "T-M4-01",
   "T-M4-03"
  ],
  "resources": [],
  "reality_gate": false,
  "runbook_ptr": "",
  "plan": "docs/superpowers/plans/2026-09-18-experience-gate-plan.md",
  "design": "docs/superpowers/specs/2026-09-18-experience-gate-design.md"
 },
 {
  "id": "T-M6-01",
  "title": "Lens-name parity: contract test + five-lens mapping paragraph in both product-review twins (R-M6-01)",
  "touched_paths": [
   "shared/scripts/orchestrator/test_experience_lens_parity.py",
   "claude/superstorm/skills/product-review/SKILL.md",
   "codex/cross-exam-skill/product-review.md"
  ],
  "acceptance_cmd": "python3 -m pytest -q shared/scripts/orchestrator/test_experience_lens_parity.py && [ \"$(diff claude/superstorm/skills/product-review/SKILL.md codex/cross-exam-skill/product-review.md | grep -c '^[<>]')\" = \"12\" ] && python3 claude/superstorm/scripts/check_skill_refs.py",
  "deps": [
   "T-M3-02"
  ],
  "resources": [],
  "reality_gate": false,
  "runbook_ptr": "",
  "plan": "docs/superpowers/plans/2026-09-18-review-alignment-plan.md",
  "design": "docs/superpowers/specs/2026-09-18-review-alignment-design.md"
 },
 {
  "id": "T-M6-02",
  "title": "product-review adopts docs/experience-review/runtime.md as prior evidence (R-M6-02)",
  "touched_paths": [
   "claude/superstorm/skills/product-review/SKILL.md",
   "codex/cross-exam-skill/product-review.md"
  ],
  "acceptance_cmd": "for f in claude/superstorm/skills/product-review/SKILL.md codex/cross-exam-skill/product-review.md; do grep -qF '`docs/cross-exam/` and `docs/experience-review/` are readable input' \"$f\" && grep -qF 'Do not read or write that tree' \"$f\" && grep -qF 'Prior evidence — runtime experience review' \"$f\" && grep -qF 'docs/experience-review/runtime.md (<review date>, <reviewed commit>)' \"$f\" && grep -qF 'lens cells adopted' \"$f\" && grep -qF 'experience-review must-fix ids' \"$f\" && grep -qF 'not a cross-exam gap or an experience-review must-fix restated' \"$f\" && ! grep -qF 'not a cross-exam gap restated' \"$f\" && grep -qF 'Prior evidence: none' \"$f\" || exit 1; done && [ \"$(diff claude/superstorm/skills/product-review/SKILL.md codex/cross-exam-skill/product-review.md | grep -c '^[<>]')\" = \"12\" ] && python3 -m pytest -q shared/scripts/orchestrator/test_experience_lens_parity.py && python3 claude/superstorm/scripts/check_skill_refs.py",
  "deps": [
   "T-M3-02",
   "T-M6-01"
  ],
  "resources": [],
  "reality_gate": false,
  "runbook_ptr": "",
  "plan": "docs/superpowers/plans/2026-09-18-review-alignment-plan.md",
  "design": "docs/superpowers/specs/2026-09-18-review-alignment-design.md"
 },
 {
  "id": "T-M6-03",
  "title": "cross-exam §1b step 1 gains experience-direction intent and job-story candidate sources in both twins (R-M6-03)",
  "touched_paths": [
   "claude/superstorm/skills/cross-exam/SKILL.md",
   "codex/cross-exam-skill/SKILL.md"
  ],
  "acceptance_cmd": "A=claude/superstorm/skills/cross-exam/SKILL.md; B=codex/cross-exam-skill/SKILL.md; for f in \"$A\" \"$B\"; do grep -qF 'topic == \"experience-direction\"' \"$f\" && grep -qF 'status == \"confirmed\"' \"$f\" && grep -qF '.allforai/app-design/concept/job-story-spec.json' \"$f\" && grep -qF 'auto_decided: true' \"$f\" && grep -qF '此方向由模型受托选定' \"$f\" && grep -qF 'task-inventory.json` 存在也读，它只是可选数据源' \"$f\" || exit 1; done && [ \"$(grep -F -e 'experience-direction' -e 'job-story-spec' -e '受托选定' \"$A\")\" = \"$(grep -F -e 'experience-direction' -e 'job-story-spec' -e '受托选定' \"$B\")\" ] && python3 -m pytest -q claude/superstorm/scripts && python3 -m pytest -q codex/cross-exam-skill/scripts && python3 claude/superstorm/scripts/check_skill_refs.py && python3 -m pytest -q pi/cross-exam/test_contract.py",
  "deps": [
   "T-M2-04"
  ],
  "resources": [],
  "reality_gate": false,
  "runbook_ptr": "",
  "plan": "docs/superpowers/plans/2026-09-18-review-alignment-plan.md",
  "design": "docs/superpowers/specs/2026-09-18-review-alignment-design.md"
 },
 {
  "id": "T-M6-04",
  "title": "product-review question 4 audience-leak observation row + self-check example in both twins (R-M6-04)",
  "touched_paths": [
   "claude/superstorm/skills/product-review/SKILL.md",
   "codex/cross-exam-skill/product-review.md"
  ],
  "acceptance_cmd": "for f in claude/superstorm/skills/product-review/SKILL.md codex/cross-exam-skill/product-review.md; do grep -F '受众泄漏' \"$f\" | grep -q '^| 4 商业级够不够 · 受众泄漏 |' && grep -F '受众泄漏' \"$f\" | grep -qF '`end-user` / `operator` / `developer`' && grep -F '受众泄漏' \"$f\" | grep -qF 'defensive-patterns Pattern J' && grep -F 'claim: 不够商业级' \"$f\" | grep -qF '最终用户设置页里要填服务地址或访问凭证' || exit 1; done && [ \"$(diff claude/superstorm/skills/product-review/SKILL.md codex/cross-exam-skill/product-review.md | grep -c '^[<>]')\" = \"12\" ] && python3 -m pytest -q shared/scripts/orchestrator/test_experience_lens_parity.py && python3 claude/superstorm/scripts/check_skill_refs.py",
  "deps": [
   "T-M4-03",
   "T-M6-02"
  ],
  "resources": [],
  "reality_gate": false,
  "runbook_ptr": "",
  "plan": "docs/superpowers/plans/2026-09-18-review-alignment-plan.md",
  "design": "docs/superpowers/specs/2026-09-18-review-alignment-design.md"
 },
 {
  "id": "T-M6-05",
  "title": "cross-exam lenses.md (claude + codex, byte-identical): audience-leak clause in the 细节质量 row (R-M6-04)",
  "touched_paths": [
   "claude/superstorm/knowledge/cross-exam/lenses.md",
   "codex/cross-exam-skill/lenses.md"
  ],
  "acceptance_cmd": "A=claude/superstorm/knowledge/cross-exam/lenses.md; B=codex/cross-exam-skill/lenses.md; grep -F '这一项是给谁填的' \"$A\" | grep -q '^| 细节质量 ' && grep -F '这一项是给谁填的' \"$A\" | grep -qF '部署方/开发者才该碰的配置（服务地址、访问凭证、模型、环境）' && [ \"$(grep -c '^| 细节质量 ' \"$A\")\" = \"1\" ] && cmp \"$A\" \"$B\" && python3 -m pytest -q claude/superstorm/scripts && python3 -m pytest -q codex/cross-exam-skill/scripts && python3 claude/superstorm/scripts/check_skill_refs.py && python3 -m pytest -q pi/cross-exam/test_contract.py",
  "deps": [
   "T-M4-03"
  ],
  "resources": [],
  "reality_gate": false,
  "runbook_ptr": "",
  "plan": "docs/superpowers/plans/2026-09-18-review-alignment-plan.md",
  "design": "docs/superpowers/specs/2026-09-18-review-alignment-design.md"
 },
 {
  "id": "T-M5-01",
  "title": "Codex bootstrap adapter: add 0b section for experience priority, direction (propose/select/delegate) and quality gate",
  "touched_paths": [
   "codex/meta-skill/skills/bootstrap.md"
  ],
  "acceptance_cmd": "grep -q '^### 0b\\. Experience Priority, Direction and Quality Gate' codex/meta-skill/skills/bootstrap.md && for s in experience_priority experience-direction propose delegate product-intent-confirmation.md consumer-maturity-patterns.md journey-emotion-schema.md capabilities/product-concept.md; do grep -q -- \"$s\" codex/meta-skill/skills/bootstrap.md || exit 1; done && ! grep -q 'CLAUDE_PLUGIN_ROOT' codex/meta-skill/skills/bootstrap.md && python3 shared/scripts/orchestrator/check_codex_meta_skill_parity.py",
  "deps": [
   "T-M1-07",
   "T-M2-02",
   "T-M2-04",
   "T-M2-05",
   "T-M2-10",
   "T-M3-10",
   "T-M4-07",
   "T-M4-08",
   "T-M6-03",
   "T-M6-04",
   "T-M6-05"
  ],
  "resources": [],
  "reality_gate": false,
  "runbook_ptr": "",
  "plan": "docs/superpowers/plans/2026-09-18-regression-parity-plan.md",
  "design": "docs/superpowers/specs/2026-09-18-regression-parity-design.md"
 },
 {
  "id": "T-M5-02",
  "title": "Pi bootstrap adapter section 7 + Pi template delegation disclosure + Pi contract pins (tests first)",
  "touched_paths": [
   "pi/meta-skill/skills/bootstrap/SKILL.md",
   "pi/meta-skill/knowledge/orchestrator-template.md",
   "pi/meta-skill/test_contract.py"
  ],
  "acceptance_cmd": "python3 -m pytest -q \"pi/meta-skill/test_contract.py::EntryTests::test_bootstrap_carries_experience_direction\" \"pi/meta-skill/test_contract.py::TemplateTests::test_completion_discloses_delegations\" && python3 -m pytest -q pi/meta-skill/test_contract.py && grep -q '^### 7\\. 体验方向与体验质量门' pi/meta-skill/skills/bootstrap/SKILL.md && [ \"$(grep -c -- '--delegations' pi/meta-skill/knowledge/orchestrator-template.md)\" -ge 2 ] && ! grep -q '\\.claude/commands/run\\.md\\|\\.codex/commands/run\\.md' pi/meta-skill/knowledge/orchestrator-template.md",
  "deps": [
   "T-M1-07",
   "T-M2-02",
   "T-M2-04",
   "T-M2-05",
   "T-M2-06",
   "T-M2-10",
   "T-M3-10",
   "T-M4-07",
   "T-M4-08",
   "T-M6-03",
   "T-M6-04",
   "T-M6-05"
  ],
  "resources": [],
  "reality_gate": false,
  "runbook_ptr": "",
  "plan": "docs/superpowers/plans/2026-09-18-regression-parity-plan.md",
  "design": "docs/superpowers/specs/2026-09-18-regression-parity-design.md"
 },
 {
  "id": "T-M5-03",
  "title": "Codex flow driver discloses delegations in completion payload, never blocking completion (tests first)",
  "touched_paths": [
   "codex/meta-skill/knowledge/flow-template.py",
   "codex/meta-skill/test_flow.py"
  ],
  "acceptance_cmd": "python3 -m pytest -q \"codex/meta-skill/test_flow.py::test_completion_discloses_delegations\" \"codex/meta-skill/test_flow.py::test_delegation_disclosure_failure_never_blocks_completion\" && python3 -m pytest -q codex/meta-skill/test_flow.py && grep -q '^def delegation_disclosure(project_root: Path)' codex/meta-skill/knowledge/flow-template.py",
  "deps": [
   "T-M1-07",
   "T-M2-06",
   "T-M2-10",
   "T-M3-10",
   "T-M4-07",
   "T-M4-08",
   "T-M6-03",
   "T-M6-04",
   "T-M6-05"
  ],
  "resources": [],
  "reality_gate": false,
  "runbook_ptr": "",
  "plan": "docs/superpowers/plans/2026-09-18-regression-parity-plan.md",
  "design": "docs/superpowers/specs/2026-09-18-regression-parity-design.md"
 },
 {
  "id": "T-M5-04",
  "title": "Codex orchestrator template prints the delegation list at Termination and Post-Completion",
  "touched_paths": [
   "codex/meta-skill/knowledge/orchestrator-template.md"
  ],
  "acceptance_cmd": "[ \"$(grep -c -- '--delegations' codex/meta-skill/knowledge/orchestrator-template.md)\" -ge 2 ] && grep -q 'product_intent.py . --delegations' codex/meta-skill/knowledge/orchestrator-template.md && ! grep -q 'CLAUDE_PLUGIN_ROOT\\|\\.claude/commands/run\\.md' codex/meta-skill/knowledge/orchestrator-template.md && python3 shared/scripts/orchestrator/check_codex_meta_skill_parity.py",
  "deps": [
   "T-M1-07",
   "T-M2-06",
   "T-M2-10",
   "T-M3-10",
   "T-M4-07",
   "T-M4-08",
   "T-M6-03",
   "T-M6-04",
   "T-M6-05"
  ],
  "resources": [],
  "reality_gate": false,
  "runbook_ptr": "",
  "plan": "docs/superpowers/plans/2026-09-18-regression-parity-plan.md",
  "design": "docs/superpowers/specs/2026-09-18-regression-parity-design.md"
 },
 {
  "id": "T-M5-05",
  "title": "Parity script: disclose product-intent-confirmation.md and pin Codex experience-direction / --delegations text, with damage cases",
  "touched_paths": [
   "shared/scripts/orchestrator/check_codex_meta_skill_parity.py",
   "shared/scripts/orchestrator/test_codex_contract_checks.py"
  ],
  "acceptance_cmd": "python3 -m pytest --co -q shared/scripts/orchestrator/test_codex_contract_checks.py | grep -q 'experience_direction' && python3 -m pytest --co -q shared/scripts/orchestrator/test_codex_contract_checks.py | grep -q 'delegation_disclosure' && python3 -m pytest -q shared/scripts/orchestrator/test_codex_contract_checks.py && grep -q '\"product-intent-confirmation.md\"' shared/scripts/orchestrator/check_codex_meta_skill_parity.py && python3 shared/scripts/orchestrator/check_codex_meta_skill_parity.py",
  "deps": [
   "T-M5-01",
   "T-M5-03",
   "T-M5-04"
  ],
  "resources": [],
  "reality_gate": false,
  "runbook_ptr": "",
  "plan": "docs/superpowers/plans/2026-09-18-regression-parity-plan.md",
  "design": "docs/superpowers/specs/2026-09-18-regression-parity-design.md"
 },
 {
  "id": "T-M5-06",
  "title": "ink-scent-shaped bad-workflow replay fixture + test that all three public gates refuse it",
  "touched_paths": [
   "claude/meta-skill/tests/fixtures/consumer-learning-app/README.md",
   "claude/meta-skill/tests/fixtures/consumer-learning-app/bad-workflow/profile.json",
   "claude/meta-skill/tests/fixtures/consumer-learning-app/bad-workflow/dialogue.json",
   "claude/meta-skill/tests/fixtures/consumer-learning-app/bad-workflow/plan.json",
   "claude/meta-skill/tests/fixtures/consumer-learning-app/bad-workflow/readiness-spec.json",
   "claude/meta-skill/tests/unit/test_consumer_product_regression.py"
  ],
  "acceptance_cmd": "python3 -m pytest --co -q claude/meta-skill/tests/unit/test_consumer_product_regression.py | grep -q 'test_ink_scent_shaped_workflow_is_refused_at_every_public_gate\\[codex\\]' && python3 -m pytest -q claude/meta-skill/tests/unit/test_consumer_product_regression.py && python3 -c 'import json; p=json.load(open(\"claude/meta-skill/tests/fixtures/consumer-learning-app/bad-workflow/plan.json\")); s=json.dumps(p); assert \".allforai/app-design/\" not in s and \"experience-quality-critique\" not in s'",
  "deps": [
   "T-M1-01",
   "T-M1-07",
   "T-M2-10",
   "T-M3-05",
   "T-M3-10",
   "T-M4-07",
   "T-M4-08",
   "T-M6-03",
   "T-M6-04",
   "T-M6-05"
  ],
  "resources": [],
  "reality_gate": false,
  "runbook_ptr": "",
  "plan": "docs/superpowers/plans/2026-09-18-regression-parity-plan.md",
  "design": "docs/superpowers/specs/2026-09-18-regression-parity-design.md"
 },
 {
  "id": "T-M5-07",
  "title": "good-workflow replay fixture + tests: chosen direction does not excuse missing design/gate; designed and gated workflow passes every gate",
  "touched_paths": [
   "claude/meta-skill/tests/fixtures/consumer-learning-app/good-workflow/profile.json",
   "claude/meta-skill/tests/fixtures/consumer-learning-app/good-workflow/dialogue.json",
   "claude/meta-skill/tests/fixtures/consumer-learning-app/good-workflow/plan.json",
   "claude/meta-skill/tests/fixtures/consumer-learning-app/good-workflow/readiness-spec.json",
   "claude/meta-skill/tests/fixtures/consumer-learning-app/README.md",
   "claude/meta-skill/tests/unit/test_consumer_product_regression.py"
  ],
  "acceptance_cmd": "[ \"$(python3 -m pytest --co -q claude/meta-skill/tests/unit/test_consumer_product_regression.py | grep -c '::test_')\" -ge 6 ] && python3 -m pytest --co -q claude/meta-skill/tests/unit/test_consumer_product_regression.py | grep -q 'test_designed_and_gated_workflow_passes_every_public_gate\\[codex\\]' && python3 -m pytest --co -q claude/meta-skill/tests/unit/test_consumer_product_regression.py | grep -q 'test_chosen_direction_does_not_excuse_a_graph_without_design_or_gate\\[claude\\]' && python3 -m pytest -q claude/meta-skill/tests/unit/test_consumer_product_regression.py && python3 -c 'import json; s=json.dumps(json.load(open(\"claude/meta-skill/tests/fixtures/consumer-learning-app/good-workflow/plan.json\"))); assert all(k in s for k in (\"experience-quality-critique-design.json\",\"experience-quality-critique-runtime.json\",\"user-flow-spec.json\",\"screen-requirements-spec.json\"))'",
  "deps": [
   "T-M1-01",
   "T-M2-02",
   "T-M2-04",
   "T-M3-02",
   "T-M3-05",
   "T-M5-06"
  ],
  "resources": [],
  "reality_gate": false,
  "runbook_ptr": "",
  "plan": "docs/superpowers/plans/2026-09-18-regression-parity-plan.md",
  "design": "docs/superpowers/specs/2026-09-18-regression-parity-design.md"
 },
 {
  "id": "T-M5-08",
  "title": "Model-run fixture: consumer new-product prompts (claude + codex) and path-based answer keys",
  "touched_paths": [
   "claude/meta-skill/tests/prompts/new-product-consumer-app.md",
   "claude/meta-skill/tests/prompts/new-product-consumer-app-codex.md",
   "claude/meta-skill/tests/expected/new-product-consumer-app-expected.json",
   "claude/meta-skill/tests/expected/new-product-consumer-app-codex-expected.json"
  ],
  "acceptance_cmd": "python3 -c 'import json; P=\"claude/meta-skill/tests/expected/new-product-consumer-app\"; docs=[json.load(open(P+s)) for s in (\"-expected.json\",\"-codex-expected.json\")]; need={\".allforai/app-design/spec/user-flow-spec.json\",\".allforai/app-design/spec/screen-requirements-spec.json\",\".allforai/app-design/qa/experience-quality-critique-design.json\",\".allforai/app-design/qa/experience-quality-critique-runtime.json\"}; assert all(need<=set(d[\"some_node_exit_artifacts_include\"]) and d[\"profile\"][\"task_route\"]==\"new-product\" and d[\"profile\"][\"experience_priority.mode\"]==\"consumer\" and \"assert by node_id\" in d[\"forbidden\"] and set(d[\"experience_direction\"][\"user_action_in\"])=={\"select\",\"delegate\"} for d in docs)' && grep -rq --exclude-dir=tests 'experience-quality-critique-design.json' claude/meta-skill && grep -rq --exclude-dir=tests 'experience-quality-critique-runtime.json' claude/meta-skill && grep -q 'claude/meta-skill/skills/bootstrap/SKILL.md' claude/meta-skill/tests/prompts/new-product-consumer-app.md && grep -q 'codex/meta-skill/skills/bootstrap.md' claude/meta-skill/tests/prompts/new-product-consumer-app-codex.md && grep -q 'experience_priority' claude/meta-skill/tests/prompts/new-product-consumer-app.md && grep -q 'experience_priority' claude/meta-skill/tests/prompts/new-product-consumer-app-codex.md && ! grep -qi 'ink-scent' claude/meta-skill/tests/prompts/new-product-consumer-app.md claude/meta-skill/tests/prompts/new-product-consumer-app-codex.md && ! grep -q 'CLAUDE_PLUGIN_ROOT\\|AskUserQuestion' claude/meta-skill/tests/prompts/new-product-consumer-app-codex.md",
  "deps": [
   "T-M1-07",
   "T-M2-10",
   "T-M3-02",
   "T-M3-10",
   "T-M4-07",
   "T-M4-08",
   "T-M6-03",
   "T-M6-04",
   "T-M6-05"
  ],
  "resources": [],
  "reality_gate": false,
  "runbook_ptr": "",
  "plan": "docs/superpowers/plans/2026-09-18-regression-parity-plan.md",
  "design": "docs/superpowers/specs/2026-09-18-regression-parity-design.md"
 },
 {
  "id": "T-M5-09",
  "title": "Freeze thought-test criteria (E1-E9) and subject prompt before any subject runs",
  "touched_paths": [
   "fixtures/product-experience/thought-tests.json",
   "fixtures/product-experience/subject-prompt.md"
  ],
  "acceptance_cmd": "python3 -c 'import json,os; d=json.load(open(\"fixtures/product-experience/thought-tests.json\")); assert d[\"method\"] and d[\"subject_under_test\"]; c={x[\"id\"]:x for x in d[\"cases\"]}; want={\"E1\":\"claude\",\"E2\":\"codex\",\"E3\":\"claude\",\"E4\":\"claude\",\"E5\":\"codex\",\"E6\":\"claude\",\"E7\":\"codex\",\"E8\":\"claude\",\"E9\":\"pi\"}; assert {k:c[k][\"platform\"] for k in want}==want, c.keys(); assert all(x[\"situation\"] and x[\"expected\"] and x[\"skill\"] and all(os.path.isfile(p) for p in x[\"skill\"]) for x in c.values())' && grep -q 'unspecified_user_visible_decision' fixtures/product-experience/thought-tests.json && grep -q 'delegate' fixtures/product-experience/thought-tests.json && test -s fixtures/product-experience/subject-prompt.md",
  "deps": [
   "T-M2-05",
   "T-M2-06",
   "T-M4-01",
   "T-M5-01",
   "T-M5-02"
  ],
  "resources": [],
  "reality_gate": false,
  "runbook_ptr": "",
  "plan": "docs/superpowers/plans/2026-09-18-regression-parity-plan.md",
  "design": "docs/superpowers/specs/2026-09-18-regression-parity-design.md"
 },
 {
  "id": "T-M5-10",
  "title": "Run the thought-test campaign with fresh-context subagents and record evidence, responses and the validation note",
  "touched_paths": [
   "docs/validation/product-experience-thought-tests.md",
   "docs/validation/product-experience-thought-tests/evidence.json",
   "docs/validation/product-experience-thought-tests/responses.md"
  ],
  "acceptance_cmd": "python3 -c 'import json,hashlib; h=lambda p: hashlib.sha256(open(p,\"rb\").read()).hexdigest(); D=\"docs/validation/product-experience-thought-tests/\"; e=json.load(open(D+\"evidence.json\")); c={x[\"id\"]:x for x in e[\"cases\"]}; assert set(c)>={\"E%d\"%i for i in range(1,10)}, sorted(c); assert all(x[\"verdict\"] in (\"pass\",\"fail\") and len(x[\"observed_tool_calls\"])==1 and x[\"observed_tool_calls\"][0][\"name\"]==\"Read\" and x[\"platform_simulated\"] and x[\"prompt_sha256\"] for x in c.values()); f=e[\"launch\"][\"fixtures\"]; assert all(f[p]==h(p) for p in (\"fixtures/product-experience/thought-tests.json\",\"fixtures/product-experience/subject-prompt.md\")); assert e[\"responses_sha256\"]==h(D+\"responses.md\"); assert isinstance(e[\"found_defect\"],bool) and e[\"limits\"]; R=open(D+\"responses.md\",encoding=\"utf-8\").read(); assert all((\"\\n## E%d\"%i) in R for i in range(1,10)), \"responses.md needs one ## E<n> section per case\"; assert all(x[\"under_test\"] and x[\"notes\"] and x[\"resolved_model\"] for x in c.values())' && grep -q '^## 尚未验证' docs/validation/product-experience-thought-tests.md && grep -q '^## 场景判定' docs/validation/product-experience-thought-tests.md && grep -q '^## 测出的缺陷与修复' docs/validation/product-experience-thought-tests.md",
  "deps": [
   "T-M5-09"
  ],
  "resources": [],
  "reality_gate": false,
  "runbook_ptr": "",
  "plan": "docs/superpowers/plans/2026-09-18-regression-parity-plan.md",
  "design": "docs/superpowers/specs/2026-09-18-regression-parity-design.md"
 },
 {
  "id": "T-M5-11",
  "title": "Close the thought-test failure loop: fix failing skill text (and twins), pin one literal, retest as E<n>b, record failure_loop status",
  "touched_paths": [
   "docs/validation/product-experience-thought-tests.md",
   "docs/validation/product-experience-thought-tests/evidence.json",
   "docs/validation/product-experience-thought-tests/responses.md",
   "claude/meta-skill/knowledge/product-intent-confirmation.md",
   "codex/meta-skill/skills/bootstrap.md",
   "pi/meta-skill/skills/bootstrap/SKILL.md",
   "claude/meta-skill/knowledge/defensive-patterns.md",
   "claude/meta-skill/knowledge/node-spec-template.md",
   "claude/meta-skill/skills/bootstrap/SKILL.md",
   "claude/meta-skill/knowledge/bootstrap-planning.md",
   "claude/meta-skill/knowledge/suppress-rules.md",
   "claude/meta-skill/knowledge/capabilities/concept-acceptance.md",
   "codex/cross-exam-skill/product-review.md",
   "claude/superstorm/skills/product-review/SKILL.md",
   "claude/superstorm/skills/cross-exam/SKILL.md",
   "codex/cross-exam-skill/SKILL.md",
   "claude/meta-skill/scripts/orchestrator/validate_meta_contracts.py",
   "shared/scripts/orchestrator/check_codex_meta_skill_parity.py",
   "shared/scripts/orchestrator/test_codex_contract_checks.py",
   "pi/meta-skill/test_contract.py",
   "shared/scripts/orchestrator/test_experience_lens_parity.py",
   "claude/superstorm/scripts/test_superstorm_contract.py"
  ],
  "acceptance_cmd": "python3 -c 'import json,hashlib; h=lambda p: hashlib.sha256(open(p,\"rb\").read()).hexdigest(); D=\"docs/validation/product-experience-thought-tests/\"; e=json.load(open(D+\"evidence.json\")); final={}; [final.__setitem__(c[\"id\"].rstrip(\"b\"), c[\"verdict\"]) for r in [e]+e.get(\"retests\",[]) for c in r[\"cases\"]]; ids={\"E%d\"%i for i in range(1,10)}; assert set(final)>=ids and all(final[i]==\"pass\" for i in ids), final; failed=any(c[\"verdict\"]!=\"pass\" for c in e[\"cases\"]); assert e[\"failure_loop\"][\"status\"]==(\"closed\" if failed else \"not-needed\"); assert e[\"launch\"][\"fixtures\"][\"fixtures/product-experience/thought-tests.json\"]==h(\"fixtures/product-experience/thought-tests.json\"); assert e[\"responses_sha256\"]==h(D+\"responses.md\"); R=open(D+\"responses.md\",encoding=\"utf-8\").read(); fl=e[\"failure_loop\"]; bad=[c[\"id\"] for c in e[\"cases\"] if c[\"verdict\"]!=\"pass\"]; assert all((\"\\n## %sb\"%i) in R for i in bad), \"each failed case needs a ## E<n>b retest section\"; assert (not failed) or (fl[\"fixed_files\"] and fl[\"pinned\"]), \"a closed loop names the fixed files and the pinned literal\"' && python3 claude/meta-skill/scripts/orchestrator/validate_meta_contracts.py && python3 shared/scripts/orchestrator/check_codex_meta_skill_parity.py && python3 -m pytest -q pi/meta-skill/test_contract.py && python3 -m pytest -q claude/superstorm/scripts/test_superstorm_contract.py && python3 claude/superstorm/scripts/check_skill_refs.py && [ \"$(diff claude/superstorm/skills/product-review/SKILL.md codex/cross-exam-skill/product-review.md | grep -c '^[<>]')\" = \"12\" ] && python3 -m pytest -q shared/scripts/orchestrator/test_experience_lens_parity.py shared/scripts/orchestrator/test_codex_contract_checks.py && python3 claude/meta-skill/scripts/orchestrator/validate_app_experience_pipeline.py . && ! grep -rn \"experience_priority\" claude/meta-skill/knowledge | grep -v \"experience_priority.mode\" | grep -v bootstrap | grep -q .",
  "deps": [
   "T-M5-02",
   "T-M5-05",
   "T-M5-10"
  ],
  "resources": [],
  "reality_gate": false,
  "runbook_ptr": "",
  "plan": "docs/superpowers/plans/2026-09-18-regression-parity-plan.md",
  "design": "docs/superpowers/specs/2026-09-18-regression-parity-design.md"
 },
 {
  "id": "T-M5-12",
  "title": "Docs: CLAUDE.md and README.md describe experience direction, quality gate and the upgrade impact",
  "touched_paths": [
   "CLAUDE.md",
   "README.md"
  ],
  "acceptance_cmd": "grep -q 'experience_priority' CLAUDE.md && grep -q 'missing_experience_priority' CLAUDE.md && grep -q 'docs/experience-review/' CLAUDE.md && grep -q '体验质量门' CLAUDE.md && grep -q '体验方向' README.md && grep -q '体验质量门' README.md",
  "deps": [
   "T-M1-07",
   "T-M2-10",
   "T-M3-10",
   "T-M4-07",
   "T-M4-08",
   "T-M6-03",
   "T-M6-04",
   "T-M6-05"
  ],
  "resources": [],
  "reality_gate": false,
  "runbook_ptr": "",
  "plan": "docs/superpowers/plans/2026-09-18-regression-parity-plan.md",
  "design": "docs/superpowers/specs/2026-09-18-regression-parity-design.md"
 },
 {
  "id": "T-M5-13",
  "title": "Version bump in place: meta-skill 0.20.0 (codex.1 / pi.1), superstorm 0.43.0 across manifests, frontmatter and headings",
  "touched_paths": [
   ".claude-plugin/marketplace.json",
   "claude/meta-skill/.claude-plugin/plugin.json",
   "claude/meta-skill/.claude-plugin/marketplace.json",
   "claude/superstorm/.claude-plugin/plugin.json",
   "claude/superstorm/.claude-plugin/marketplace.json",
   "pi/meta-skill/package.json",
   "claude/meta-skill/SKILL.md",
   "claude/meta-skill/skills/bootstrap/SKILL.md",
   "codex/meta-skill/SKILL.md",
   "pi/cross-exam/package.json"
  ],
  "acceptance_cmd": "python3 -m pytest -q claude/superstorm/scripts/test_package_manifests.py && python3 shared/scripts/orchestrator/check_codex_meta_skill_parity.py && python3 -m pytest -q pi/meta-skill/test_contract.py && grep -q '^version: \"0.20.0\"' claude/meta-skill/SKILL.md && grep -q '^# Meta-Skill v0.20.0' claude/meta-skill/SKILL.md && grep -q '^version: \"0.20.0\"' claude/meta-skill/skills/bootstrap/SKILL.md && grep -q 'version: \"0.20.0-codex.1\"' codex/meta-skill/SKILL.md && grep -q '^# Meta-Skill v0.20.0-codex.1' codex/meta-skill/SKILL.md && grep -q '\"version\": \"0.20.0-pi.1\"' pi/meta-skill/package.json && grep -q '\"version\": \"0.20.0\"' .claude-plugin/marketplace.json && grep -q '\"version\": \"0.43.0\"' .claude-plugin/marketplace.json && grep -q '\"version\": \"0.20.0\"' claude/meta-skill/.claude-plugin/plugin.json && grep -q '\"version\": \"0.43.0\"' claude/superstorm/.claude-plugin/plugin.json && ! grep -q '0\\.19\\.[12]\\|0\\.42\\.2' .claude-plugin/marketplace.json claude/meta-skill/.claude-plugin/plugin.json claude/meta-skill/.claude-plugin/marketplace.json claude/superstorm/.claude-plugin/plugin.json claude/superstorm/.claude-plugin/marketplace.json pi/meta-skill/package.json claude/meta-skill/SKILL.md claude/meta-skill/skills/bootstrap/SKILL.md codex/meta-skill/SKILL.md",
  "deps": [
   "T-M5-11"
  ],
  "resources": [],
  "reality_gate": false,
  "runbook_ptr": "",
  "plan": "docs/superpowers/plans/2026-09-18-regression-parity-plan.md",
  "design": "docs/superpowers/specs/2026-09-18-regression-parity-design.md"
 },
 {
  "id": "T-M5-14",
  "title": "Full validation and baseline comparison: failure set must be within the four known failures; write verification-M5.md",
  "touched_paths": [
   "docs/superpowers/runs/2026-09-18-product-experience-overhaul/verification-M5.md"
  ],
  "acceptance_cmd": "python3 -c 'import subprocess,re,sys; r=subprocess.run([sys.executable,\"-m\",\"pytest\",\"-q\",\"-rfE\",\"claude/meta-skill/tests/unit\"],capture_output=True,text=True); out=r.stdout; bad={l.split()[1] for l in out.splitlines() if l.startswith((\"FAILED \",\"ERROR \"))}; U=\"claude/meta-skill/tests/unit/\"; base={U+\"test_decision_gate.py::test_a_resolved_choice_restores_readiness_only_with_fresh_evidence[claude]\",U+\"test_decision_gate.py::test_a_resolved_choice_restores_readiness_only_with_fresh_evidence[codex]\",U+\"test_evidence_freshness.py::test_fresh_contract_allows_execution_but_cannot_claim_completion[claude]\",U+\"test_evidence_freshness.py::test_fresh_contract_allows_execution_but_cannot_claim_completion[codex]\"}; m=re.search(r\"(\\d+) passed\",out); print(out[-2000:]); print(\"unexpected:\",sorted(bad-base)); sys.exit(0 if r.returncode in (0,1) and m and int(m.group(1))>=1198 and bad<=base else 1)' && python3 -m pytest -q claude/superstorm/scripts && python3 -m pytest -q codex/cross-exam-skill/scripts && python3 -m pytest -q shared/evidence-engine && python3 -m pytest -q shared/visual-acceptance && python3 -m pytest -q shared/scripts/orchestrator shared/keep-code-simple pi/cross-exam && python3 -m pytest -q pi/meta-skill/test_contract.py codex/meta-skill/test_flow.py codex/meta-skill/test_install.py && python3 shared/scripts/orchestrator/check_codex_meta_skill_parity.py && python3 claude/superstorm/scripts/check_skill_refs.py && python3 -m pytest -q claude/meta-skill/tests/unit/test_consumer_product_regression.py && python3 -m pytest -q claude/superstorm/scripts/test_package_manifests.py && python3 claude/meta-skill/scripts/orchestrator/validate_meta_contracts.py && ! grep -rn \"experience_priority\" claude/meta-skill/knowledge | grep -v \"experience_priority.mode\" | grep -v bootstrap | grep -q . && grep -q '^status: pass' docs/superpowers/runs/2026-09-18-product-experience-overhaul/verification-M5.md && grep -q '6a59fe44' docs/superpowers/runs/2026-09-18-product-experience-overhaul/verification-M5.md",
  "deps": [
   "T-M5-02",
   "T-M5-05",
   "T-M5-07",
   "T-M5-08",
   "T-M5-11",
   "T-M5-12",
   "T-M5-13"
  ],
  "resources": [],
  "reality_gate": false,
  "runbook_ptr": "",
  "plan": "docs/superpowers/plans/2026-09-18-regression-parity-plan.md",
  "design": "docs/superpowers/specs/2026-09-18-regression-parity-design.md"
 },
 {
  "id": "T-M5-15",
  "title": "Release commit message draft with verification numbers, baseline SHA and upgrade impact",
  "touched_paths": [
   "docs/superpowers/runs/2026-09-18-product-experience-overhaul/release-commit-message.txt"
  ],
  "acceptance_cmd": "F=docs/superpowers/runs/2026-09-18-product-experience-overhaul/release-commit-message.txt; head -1 \"$F\" | grep -q '^release: superstorm 0.43.0, meta-skill 0.20.0' && grep -q '6a59fe44' \"$F\" && grep -q 'missing_experience_priority' \"$F\" && grep -q 'local-change' \"$F\" && grep -q '尚未验证' \"$F\" && grep -Eq '[0-9]+ passed' \"$F\" && grep -q '^status: pass' docs/superpowers/runs/2026-09-18-product-experience-overhaul/verification-M5.md",
  "deps": [
   "T-M5-14"
  ],
  "resources": [],
  "reality_gate": false,
  "runbook_ptr": "",
  "plan": "docs/superpowers/plans/2026-09-18-regression-parity-plan.md",
  "design": "docs/superpowers/specs/2026-09-18-regression-parity-design.md"
 },
 {
  "id": "T-M5-16",
  "title": "Real-host acceptance: rerun the original ink-scent request through /bootstrap, /run, /product-review and record the three symptoms",
  "touched_paths": [
   "docs/validation/product-experience-host-run.md"
  ],
  "acceptance_cmd": "F=docs/validation/product-experience-host-run.md; grep -q '^## 症状对照' \"$F\" && grep -q '症状 1' \"$F\" && grep -q '症状 2' \"$F\" && grep -q '症状 3' \"$F\" && [ \"$(grep -c 'verdict: \\(fixed\\|not-fixed\\|partial\\)' \"$F\")\" -ge 3 ] && grep -q '^host-run: pass' \"$F\"",
  "deps": [
   "T-M5-14"
  ],
  "resources": [],
  "reality_gate": true,
  "runbook_ptr": "docs/superpowers/plans/2026-09-18-regression-parity-plan.md#runbook-real-host-bootstrap-run",
  "plan": "docs/superpowers/plans/2026-09-18-regression-parity-plan.md",
  "design": "docs/superpowers/specs/2026-09-18-regression-parity-design.md"
 }
]

const EXEC_SCHEMA = { type: 'object', required: ['status', 'task_id', 'self_reported_done'],
  properties: { status: { type: 'string', enum: ['ok', 'escalate'] }, task_id: { type: 'string' },
    acceptance_cmd: { type: 'string' }, self_reported_done: { type: 'boolean' }, notes: { type: 'string' },
    commit: { type: 'string' }, reason: { type: 'string' }, evidence: { type: 'string' },
    proposed_touched_paths: { type: 'array', items: { type: 'string' } } } }

const VERDICT_SCHEMA = { type: 'object', required: ['done', 'rerun_exit_code', 'evidence'],
  properties: { done: { type: 'boolean' }, rerun_exit_code: { type: 'integer' }, evidence: { type: 'string' },
    refutation: { type: 'string' }, vacuous: { type: 'boolean' }, reality_gated: { type: 'boolean' },
    observations: { type: 'array', items: { type: 'object', required: ['scope', 'finding', 'evidence'],
      properties: { scope: { type: 'string' }, finding: { type: 'string' }, evidence: { type: 'string' } } } } } }

function execPrompt(t, attempt, refutation, vacuous) {
  return [
    '# Executor agent — implements one task against its contract',
    '',
    'You implement ONE task. You are headless: never ask a human anything.',
    'Target repository: ' + REPO + ' (NOT your cwd — `cd` there or use absolute paths). Branch: product-experience-overhaul (already checked out; never switch branches, never reset, never stash, never push, never rebase, never amend other commits).',
    'There is NO worktree isolation: other executors are editing OTHER files in this same tree right now. Never touch, stage, revert or "fix" a file outside your touched_paths, even if it looks broken or half-written — it belongs to a running task.',
    '',
    'Task id: ' + t.id,
    'Title: ' + t.title,
    'Full task contract (interface & behaviour, test intent, acceptance, write set): read the section for ' + t.id + ' in ' + REPO + '/' + t.plan,
    'Module design (frozen requirements + Detailed design): ' + REPO + '/' + t.design,
    'touched_paths (repo-relative): ' + JSON.stringify(t.touched_paths),
    'acceptance_cmd (run with cwd = ' + REPO + '): ' + t.acceptance_cmd,
    '',
    '## Discipline',
    '1. TDD: write the failing test the task\'s test intent describes, see it fail, implement, see it pass. The interface and behaviour are fixed; the route inside touched_paths is yours. Match the surrounding code and prose style of each file.',
    '2. Touch ONLY files in touched_paths. If the change genuinely needs a file outside that set, STOP and return status:"escalate" with proposed_touched_paths (exact repo-relative files and why). Never work around it with a stub or an out-of-set edit.',
    '3. Run acceptance_cmd yourself (Bash timeout up to 600000 ms; tee long output to ' + RUN + '/logs/' + t.id + '.log). Do not claim done if it fails. If it fails ONLY because of a file outside your touched_paths that another task is mid-edit on (check `git status --short`), wait ~60s and rerun, up to 5 times, before treating it as your problem.',
    '4. Anti-vacuous: if acceptance selects tests by name/node id, those tests must exist with real assertions and the run must report a non-zero executed count.',
    '5. Divergence circuit-breaker: after 5 consecutive failed acceptance runs without a genuinely new hypothesis, return status:"escalate" with the hypothesis log (what changed, expected, actual).',
    '6. Known baseline: the full claude/meta-skill unit suite has exactly 4 pre-existing failures (test_decision_gate::test_a_resolved_choice_restores_readiness_only_with_fresh_evidence[claude|codex], test_evidence_freshness::test_fresh_contract_allows_execution_but_cannot_claim_completion[claude|codex]). Never edit or "fix" them. Never run `pytest pi/meta-skill` or `pytest codex/meta-skill` as directories.',
    '',
    '## Commit protocol (mandatory — the supervisor verifies the COMMITTED tree)',
    'When acceptance passes, commit exactly your files, serialized with the shared lock:',
    '  cd ' + REPO,
    '  until mkdir /tmp/pxo-commit.lock 2>/dev/null; do sleep 7; done',
    '  git add -- <each touched path that exists> ; git commit -m "<message>" -- <the same paths> ; rc=$? ; rmdir /tmp/pxo-commit.lock',
    'ALWAYS release the lock (rmdir) even if the commit fails. Never use --no-verify, never `git add -A` / `git add .`, never `git commit -a`.',
    'The pre-commit hook runs fast test batteries and validators over the whole working tree (~30s). If it fails because of YOUR files, fix and retry. If it fails because of another task\'s in-progress file, release the lock, wait ~60s, retry (up to 5 times).',
    'Commit message: repo convention — subject names what is now true (Chinese or English, e.g. `feat(meta-skill): …` / `test(meta-skill): …` / `docs(…): …`), mention the task id ' + t.id + ' in the body, and end the body with the trailer line:',
    '  Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>',
    'After committing, `git status --porcelain -- <touched paths>` must print nothing.',
    '',
    attempt > 1 ? ('## This is attempt ' + attempt + '. An independent supervisor REFUTED the previous attempt:\n' + (refutation || '(no refutation text)') + '\nYour earlier work may already be committed — inspect `git log --oneline -8` and the current files first, then fix what the refutation names and commit again.') : '',
    vacuous ? '## ANTI-VACUOUS: the previous acceptance passed only because ZERO tests ran. Create the named test(s) with at least one real assertion exercising your implementation and prove a non-zero executed-test count.' : '',
    '',
    '## Output',
    'Return JSON {status:"ok"|"escalate", task_id, acceptance_cmd, self_reported_done, notes, commit?, reason?, evidence?, proposed_touched_paths?}. Your self-report is NOT trusted — an independent supervisor reruns acceptance_cmd. Do not inflate.',
  ].join('\n')
}

function supPrompt(t) {
  return [
    '# Supervisor agent — anti-fake-completion verifier',
    '',
    'You independently verify ONE task that is claimed done. You are adversarial; default to disbelief. You are NOT given the executor\'s narrative. You trust reruns, not claims.',
    'Repository: ' + REPO + ' (NOT your cwd). Branch product-experience-overhaul. You are READ-ONLY: never edit, stage, commit, reset or stash anything. Other tasks are concurrently editing OTHER files in this tree.',
    '',
    'Task id: ' + t.id + ' — ' + t.title,
    'Task contract: the section for ' + t.id + ' in ' + REPO + '/' + t.plan + ' ; design: ' + REPO + '/' + t.design,
    'touched_paths: ' + JSON.stringify(t.touched_paths),
    'acceptance_cmd (cwd = ' + REPO + '): ' + t.acceptance_cmd,
    t.reality_gate ? ('This task carries reality_gate:true. Runbook: ' + t.runbook_ptr) : 'This task does NOT carry reality_gate — never set reality_gated.',
    '',
    '## Verify',
    '1. Rerun acceptance_cmd yourself from ' + REPO + ' (Bash timeout 600000 ms; tee output to ' + RUN + '/logs/' + t.id + '.supervisor.log). Capture the real exit code and output.',
    '2. done is true ONLY if exit code == 0 AND the output shows the behaviour genuinely works.',
    '3. Vacuous check: if 0 tests ran / nothing was collected / a grep-only command would have passed before this task → vacuous:true, done:false.',
    '4. Read the real diff (`git log --oneline -12`, `git show --stat`, `git diff` for the touched paths): do the changes correspond to the task\'s intent, in the right files, and ONLY there? A task that edited files outside touched_paths is refuted.',
    '5. Absence check: for each behaviour the contract promises (a blocker code emitted, a gate registered in main() AND structural_gate_blockers, a field written into the journal, a literal pinned by a validator, a twin file dual-written), trace that it is actually wired, not merely defined. Hunt for what SHOULD be present.',
    '6. Committed-tree check: `git status --porcelain -- <each touched path>` must print nothing; any modified/untracked touched path → done:false naming the dirty paths.',
    '7. If the rerun fails ONLY because of a file outside touched_paths that is currently dirty in `git status --short` (another running task mid-edit), wait ~60s and rerun, up to 4 times, before judging. Known baseline: the full claude/meta-skill unit suite has exactly 4 pre-existing failures (test_decision_gate …fresh_evidence[claude|codex], test_evidence_freshness …cannot_claim_completion[claude|codex]); they are not this task\'s defect.',
    '',
    '## Output (verdict schema)',
    '{done, rerun_exit_code, evidence:"<real captured output, trimmed>", refutation?, vacuous?, reality_gated?, observations?}. observations: anything outside THIS task ({scope:"task:<id>"|"repo", finding, evidence}). It never changes done.',
  ].join('\n')
}

const byId = {}
TASKS.forEach(t => { byId[t.id] = t })
const state = {}      // id -> {status, attempts, effective_model, first_model, last_evidence_excerpt, observations}
const running = new Map()
const observations = []
const escalations = []
const realityGated = []

function locksOf(t) { return t.touched_paths.concat((t.resources || []).map(r => 'res:' + r)) }
function conflicts(t) {
  const mine = new Set(locksOf(t))
  for (const id of running.keys()) { if (locksOf(byId[id]).some(p => mine.has(p))) return true }
  return false
}
function satisfied(id) { const s = state[id]; return s && (s.status === 'done' || s.status === 'reality_gated') }
function dead(id) { const s = state[id]; return s && (s.status === 'failed' || s.status === 'skipped') }

async function runTask(t) {
  const st = { status: 'dispatched', attempts: 0, effective_model: EXECUTOR_MODEL, first_model: null, infra_failures: 0 }
  state[t.id] = st
  let refutation = '', vacuous = false, model = EXECUTOR_MODEL, defective = 0
  while (st.attempts < 3) {
    st.attempts += 1
    let ex = await agent(execPrompt(t, st.attempts, refutation, vacuous),
      Object.assign({ label: 'exec:' + t.id + (st.attempts > 1 ? '#' + st.attempts : ''), phase: 'Execute', schema: EXEC_SCHEMA }, model ? { model } : {}))
    if (!ex) {                                   // infrastructure failure: never spends business budget
      st.infra_failures += 1; st.attempts -= 1
      defective += 1
      if (defective >= 2 && model) { st.first_model = model; model = null; st.effective_model = 'session'; log(t.id + ': executor returned null twice on ' + EXECUTOR_MODEL + ' → session model') }
      if (st.infra_failures >= 3) { st.status = 'failed'; st.last_evidence_excerpt = 'infrastructure: executor returned null 3 times'; return }
      continue
    }
    if (ex.status === 'escalate') {
      const extra = (ex.proposed_touched_paths || []).filter(p => !t.touched_paths.includes(p))
      const inRepo = extra.every(p => !p.startsWith('/') && !p.startsWith('..'))
      if (extra.length && inRepo && !st.extended) {
        const busy = extra.some(p => { for (const id of running.keys()) { if (id !== t.id && byId[id].touched_paths.includes(p)) return true } return false })
        st.extended = extra; t.touched_paths = t.touched_paths.concat(extra)
        log(t.id + ': plan defect — touched_paths extended with ' + JSON.stringify(extra) + (busy ? ' (collides with a running task; executor told to wait-and-retry)' : ''))
        st.attempts -= 1; st.status = 'redispatched'
        refutation = 'touched_paths now also includes ' + JSON.stringify(extra) + '. Resume your work-in-progress.'
        continue
      }
      st.status = 'failed'; st.last_evidence_excerpt = ('escalate: ' + (ex.reason || '') + ' | ' + (ex.evidence || '')).slice(0, 1200)
      st.proposed_touched_paths = ex.proposed_touched_paths || []
      return
    }
    const v = await agent(supPrompt(t), { label: 'sup:' + t.id + (st.attempts > 1 ? '#' + st.attempts : ''), phase: 'Supervise', schema: VERDICT_SCHEMA })
    if (!v) { st.infra_failures += 1; st.attempts -= 1; if (st.infra_failures >= 3) { st.status = 'failed'; st.last_evidence_excerpt = 'infrastructure: supervisor returned null'; return } refutation = 'The supervisor could not be reached; re-verify your committed work and report again.'; continue }
    ;(v.observations || []).forEach(o => observations.push(Object.assign({ task_id: t.id }, o)))
    st.last_evidence_excerpt = (v.evidence || '').slice(0, 1200)
    if (v.done) { st.status = 'done'; return }
    if (t.reality_gate && v.reality_gated) { st.status = 'reality_gated'; realityGated.push({ task_id: t.id, reason: (v.evidence || '').slice(0, 800), runbook_ptr: t.runbook_ptr }); return }
    if (t.reality_gate) { st.status = 'failed'; st.last_evidence_excerpt = ('reality_gate task, code defect: ' + (v.refutation || '')).slice(0, 1200); return }
    refutation = v.refutation || v.evidence || ''
    vacuous = !!v.vacuous
    st.status = 'redispatched'
    if (st.attempts === 1 && model) { /* first business failure on the downgraded executor: retry once on the same model */ }
    else if (model) { st.first_model = model; model = null; st.effective_model = 'session'; log(t.id + ': second refutation on ' + EXECUTOR_MODEL + ' → redispatch on session model') }
  }
  st.status = 'failed'
  st.last_evidence_excerpt = ('business retries exhausted. last refutation: ' + refutation).slice(0, 1200)
}

phase('Execute')
while (true) {
  let changed = true
  while (changed) {                                // transitive skip
    changed = false
    for (const t of TASKS) {
      if (state[t.id]) continue
      const blocker = t.deps.find(dead)
      if (blocker) { state[t.id] = { status: 'skipped', blocked_by: state[blocker].blocked_by || blocker, attempts: 0 }; changed = true }
    }
  }
  for (const t of TASKS) {
    if (running.size >= CAP) break
    if (state[t.id] || running.has(t.id)) continue
    if (!t.deps.every(satisfied)) continue
    if (conflicts(t)) continue
    const p = runTask(t).catch(e => { state[t.id] = Object.assign(state[t.id] || {}, { status: 'failed', last_evidence_excerpt: 'orchestrator exception: ' + String(e).slice(0, 600) }) })
      .then(() => { running.delete(t.id); const s = state[t.id]; log(t.id + ' → ' + s.status + ' (attempts ' + s.attempts + ', ' + (s.effective_model || '-') + ')'); if (s.status === 'failed') escalations.push({ task_id: t.id, reason: s.last_evidence_excerpt, retries: s.attempts, proposed_touched_paths: s.proposed_touched_paths || [] }) })
    running.set(t.id, p)
  }
  if (running.size === 0) break
  await Promise.race(Array.from(running.values()))
}
const counts = {}
TASKS.forEach(t => { const s = (state[t.id] || { status: 'never-ready' }).status; counts[s] = (counts[s] || 0) + 1 })
const unscheduled = TASKS.filter(t => !state[t.id]).map(t => t.id)
return { counts, unscheduled, state, escalations, realityGated, observations }
