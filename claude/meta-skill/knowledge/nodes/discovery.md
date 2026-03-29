# Discovery Node Template

> How to scan and understand an existing project. Used by bootstrap to generate
> project-specific discovery node-specs.

## Purpose

Scan source project to build a complete understanding: file structure, module boundaries,
tech stack, infrastructure, abstractions, cross-cutting concerns, visual assets.

## Phases

### Phase A: Structure Discovery

| Step | Output | What |
|------|--------|------|
| Scan root | discovery-profile.json | LLM reads root dir, generates module discovery rules |
| File scan | source-summary.json skeleton | Script scans files per discovery-profile |
| Key file reading | source-summary.json | LLM reads key_files per module, generates file cards |
| Coverage check | coverage report | Modules <50% coverage get supplementary header scans |
| Knowledge base | file-catalog.json + code-index.json | Aggregate file cards, build cross-reference index |
| Archetype | project_archetype | LLM identifies project core value type |

### Phase B: Runtime Foundation Discovery

| Step | Output | What |
|------|--------|------|
| Infrastructure | infrastructure-profile.json | Custom/proprietary components, substitution risk |
| Environment | env-inventory.json | Environment variable catalog |
| Third-party | third-party-services.json | External service dependencies |
| Cron | cron-inventory.json | Scheduled tasks |
| Error codes | error-catalog.json | Error code system |

### Phase C: Resource Discovery

| Step | Output | What |
|------|--------|------|
| Assets | asset-inventory.json | Frontend static resources |
| Seed data | seed-data-inventory.json | Backend base data |
| Abstractions | abstractions + cross_cutting | Reuse patterns + middleware/interceptors |
| Role-view matrix | role-view-matrix.json | Per-role UI differences |
| Interactions | interaction-recordings.json | End-to-end user journeys |
| Screenshots | visual/source/ | Multi-role screenshots + dynamic recordings |

### Phase D: Confirmation

User reviews discovery results. Last human interaction point before silent execution.

## Rules (Bootstrap Must Preserve)

1. **File coverage >= 50%** per module. Unread files get header scan (definition + method signatures).
2. **Quiz validation** per file card: 3-question self-check, re-read on inconsistency (max 2 retries).
3. **Infrastructure before business**: Phase B completes before Phase 3 generation.
4. **Config-as-code**: nginx.conf, routes.yaml, OpenAPI spec, rbac.yaml may contain business logic. Include in sources.
5. **Cannot-substitute flag**: Custom/proprietary infra components (encryption, custom protocols, native SDKs) must be flagged.
6. **Protocol structurization**: Custom protocols output protocol_spec (frame format + state machine + test vectors).
7. **Never skip files by name**: LLM cannot guess importance from filename. Sample-read first.
8. **code-index resident**: Phase 3 LLM calls load source-summary + code-index as global context.
9. **UI-driven closure**: Screenshots/recordings from Phase C feed into Phase 3 generation for completeness validation.
10. **Infrastructure 3-question probe**: For each infra component ask — (a) what does the user see if this is missing? (b) does it have periodic/background behaviors? (c) what does it do at each app lifecycle stage (start / foreground / background / shutdown)?
11. **Event bus inventory**: If source has EventBus/EventDispatcher/MessageBus, list all event types + publishers + subscribers. Events are cross-module coupling pipes — missing events = silent functional breakage.
12. **Implicit behaviors explicit**: mixin/decorator/annotation-driven behaviors (auto-CRUD, auto-sync, auto-persist) must be documented as explicit capabilities. Record what capability is implicitly gained and what must be hand-implemented in a target stack without the equivalent mechanism.

## Scripts Referenced

- `cr_discover.py --profile <discovery-profile>`: File scanning + module detection
- Output: source-summary.json, file-catalog.json, code-index.json

## What Bootstrap Specializes

When generating a project-specific discovery node-spec, bootstrap fills in:
- Module paths and boundaries (from bootstrap-profile.json)
- Which Phase B/C steps are relevant (backend-only projects skip assets/screenshots)
- Specific file patterns to scan (from detected tech stack)
- Coverage thresholds (may be adjusted per project complexity)
