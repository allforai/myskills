# megastorm — Workflow agent JSON schemas

These are the `schema` arguments passed to Workflow `agent()` calls. They force
structured output so the deterministic scripts have clean JSON to consume.

## escalation (spec §4 shared contract — every autonomous critic/fix agent returns this)
```json
{ "type": "object", "required": ["status"],
  "properties": {
    "status": { "type": "string", "enum": ["ok", "escalate"] },
    "reason": { "type": "string" },
    "evidence": { "type": "string" } } }
```
Rule: the skill (main session) reads the Workflow return; ANY `status:"escalate"`
halts the pipeline and renders `reason`+`evidence` to the human.

## design-manifest (spec §4.1 design agent emits one per module; feeds check_closure.py)
```json
{ "type": "object", "required": ["module", "design_path", "covers_req_ids", "exposes", "consumes"],
  "properties": {
    "module": { "type": "string" },
    "design_path": { "type": "string" },
    "covers_req_ids": { "type": "array", "items": { "type": "string" } },
    "exposes": { "type": "array", "items": { "type": "string" } },
    "consumes": { "type": "array", "items": { "type": "string" } } } }
```

## overview-registry (Phase 0 mints this into the overview; frozen before Phase 1)
The single source of truth for requirement IDs and interface names. The main session writes it
into the overview wrapped in **machine-locatable HTML comment markers** (the overview has many
other ```json fences — module tables, dep graphs — so the registry needs a unique locator):

```
<!-- megastorm-registry:start -->
​```json
{ "requirements": ["R-auth-01", "R-auth-02"], "interfaces": ["api:createOrder", "event:orderPaid"],
  "models": { "think": "fable", "verify": "opus", "bulk": "sonnet" } }
​```
<!-- megastorm-registry:end -->
```

Schema of the JSON between the markers:
```json
{ "type": "object", "required": ["requirements", "interfaces"],
  "properties": {
    "requirements": { "type": "array", "items": { "type": "string" } },
    "interfaces": { "type": "array", "items": { "type": "string" } },
    "models": { "type": "object", "required": ["think", "verify", "bulk"],
      "properties": { "think": { "type": "string" }, "verify": { "type": "string" },
                      "bulk": { "type": "string" } } } } }
```
- `requirements`: every requirement, ID-shaped `R-<module>-NN` (e.g. `R-auth-01`). One owner: Phase 0.
- `interfaces`: the closed vocabulary of cross-module interface names.
- `models` (optional but recommended): the three tier literals resolved in Phase 0 (see the
  skill's "Model tiers"). Frozen like everything else here — Phase 1 substitutes these into
  `agent()` calls and NEVER changes them on its own; any downgrade is a human decision.
  `check_closure.py` ignores this field.
- **Interface naming grammar (mandatory):** `<kind>:<name>` where `kind ∈ {api, event, data, ui}`
  and `name` is lowerCamelCase. e.g. `api:createOrder`, `event:orderPaid`, `data:userProfile`.
  Design agents MUST use these exact names — `check_closure.py` rejects any exposes/consumes
  outside the registry (stops `api:createOrder` vs `api:create_order` drift).

## plan-task (spec §4.3; feeds validate_plan_tasks.py + build_task_dag.py)
```json
{ "type": "object", "required": ["id", "title", "touched_paths", "acceptance_cmd", "depends_on"],
  "properties": {
    "id": { "type": "string" },
    "title": { "type": "string" },
    "touched_paths": { "type": "array", "items": { "type": "string" }, "minItems": 1 },
    "acceptance_cmd": { "type": "string" },
    "depends_on": { "type": "array", "items": { "type": "string" } },
    "implements": { "type": "array", "items": { "type": "string" } },
    "requires": { "type": "array", "items": { "type": "string" } },
    "resources": { "type": "array", "items": { "type": "string" } },
    "reality_gate": { "type": "boolean" } } }
```
- `depends_on` carries INTRA-module ordering (task ids the plan agent can see).
- `implements` / `requires` (optional) carry CROSS-module ordering, in registry interface
  vocabulary — parallel plan agents cannot see each other's task ids, so interfaces are the
  join key. `implements: ["api:createOrder"]` = THE task whose `acceptance_cmd` proves that
  interface consumable (usually the module's integration task for it). `requires` = registry
  interfaces this task consumes. `build_task_dag.py` derives a DAG edge from every requirer
  to every implementer; a required interface nobody implements = hard BLOCK (missed work).
  Values are validated against the frozen registry (`validate_plan_tasks.py` second arg).
- `resources` (optional) names SHARED PHYSICAL RESOURCES this task must hold exclusively —
  things a file-collision check cannot see (a device simulator, a shared test stack, a
  production SSH session). Free-form strings, but they must match EXACTLY across tasks
  (e.g. `"sim:default"`, `"stack:shared-test"`, `"ssh:prod"`). `build_task_dag.py` puts
  tasks sharing a resource into mutex groups (`resource_groups`, and concurrent pairs are
  folded into `isolate_groups`) so they never run at the same time. Omitting the field
  means the task needs no exclusive resource — fully backward compatible.
- `reality_gate` (optional, default `false`): `true` declares that this task's
  `acceptance_cmd` depends on a real device/simulator/external live system/physical I/O and
  therefore **cannot be self-proven in an autonomous CI environment**. Crucial semantics:
  - **The implementation still runs and still commits** — `reality_gate` changes nothing
    about whether the code is written. It only marks that the task's *autonomous proof*
    cannot close the loop.
  - After ONE autonomous acceptance attempt that fails on environment grounds, the task is
    routed to the Phase 2 (b) reality-gate list. It is **not soft-retried** (no budget burn)
    and **does NOT block its dependents** — the implementation is already committed, so the
    DAG treats its interface output as satisfied (see `build_task_dag.py` + skill §1.6).
  - A `reality_gate` task must still carry a real, non-empty `acceptance_cmd` (the
    implementation must remain runnable); it simply may be device-bound.
  - Omitting the field = `false` = a normal, autonomously-provable gate. Fully backward
    compatible. Plain server-side unit tests / contracts / pure logic keep `reality_gate`
    omitted.
  - **Do NOT use a `reality_gate` task as a hard `depends_on` of other tasks** — its
    "awaiting human" state would block them. Downstream tasks should depend on the
    *implementation task / interface* (`implements`/`requires`) that produces the capability,
    not on the reality-gate proof.

## verdict (spec §4.6 supervisor — anti-fake-completion)
```json
{ "type": "object", "required": ["done", "rerun_exit_code", "evidence"],
  "properties": {
    "done": { "type": "boolean" },
    "rerun_exit_code": { "type": "integer" },
    "evidence": { "type": "string" },
    "refutation": { "type": "string" },
    "vacuous": { "type": "boolean" },
    "reality_gated": { "type": "boolean" } } }
```
Rule: `done` is true ONLY if the supervisor independently reran `acceptance_cmd`
and got exit code 0 with the real output captured in `evidence`.
`vacuous` = true when the command passed only because 0 tests ran (a name-selector
matched nothing); it forces `done:false` and signals §1.6 to re-inject the
anti-vacuous instruction on the executor bounce.
`reality_gated` = true is set by the supervisor ONLY on a `reality_gate:true` task when the
acceptance failed AND the failure is attributable to the ENVIRONMENT (a flaky simulator/UI
gate, an unreachable device, an unavailable external system — not a locatable code defect).
It travels with `done:false`, but its meaning is distinct: **the implementation is present
and committed; only the autonomous proof is pending human/hardware verification.** It is NOT
a business failure. §1.6 reads `reality_gated:true` and routes the task to the reality-gate
ledger instead of soft-retrying or skipping dependents (see skill §1.6). A genuine code error
on a `reality_gate` task still returns a plain `done:false` (and must be fixed).
## Autonomous decision record

Phase 1 never requests human input. Workers may propose a decision; the main orchestrator
is the sole writer of the run-scoped unified decision record:

```json
{
  "decision_id": "D-0001",
  "run_id": "stable-run-id",
  "phase": "1.3",
  "branch_id": "module-or-task-branch",
  "task_id": null,
  "question": "decision that arose",
  "options_considered": ["A", "B"],
  "chosen": "A",
  "reason": "ranked recommendation",
  "assumptions": [],
  "risk": "low",
  "reversible": true,
  "authority": "inside-envelope",
  "authority_basis": {"field": "scope", "value": ["repo"]},
  "fallback": null,
  "outcome": null,
  "result_ref": null,
  "affected_artifacts": [],
  "skipped_dependents": []
}
```

`outcome` starts null and terminates as `action-taken|fallback-taken|deferred`;
`result_ref` then points to evidence. Normal ledger, emergency journal, and degraded
in-memory terminal entries are one unified record set and appear exactly once in Phase 2.
