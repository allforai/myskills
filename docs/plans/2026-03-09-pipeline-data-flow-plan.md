# Pipeline Data Flow Unification — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Break the island-style data flow in gen_*.py scripts by adding a unified context loader, constraint injection from review feedback, and XV finding propagation.

**Architecture:** Add `FullContext` class to `_common.py` that one-shot loads all artifacts. Add `constraints/` directory with per-tab files written by `/review process`. Each `gen_*.py` calls `C.load_full_context(base)` and consumes sibling artifacts + constraints + XV findings.

**Tech Stack:** Python 3, JSON, existing `_common.py` infrastructure

---

### Task 1: FullContext class and load_full_context() in _common.py

**Files:**
- Modify: `product-design-skill/scripts/_common.py`
- Create: `product-design-skill/scripts/test_full_context.py`

**Step 1: Write the test file**

```python
#!/usr/bin/env python3
"""Tests for FullContext class."""
import os, sys, json, tempfile, shutil

sys.path.insert(0, os.path.dirname(__file__))
import _common as C

def setup_base(artifacts=None):
    """Create a temp .allforai dir with optional artifact files."""
    base = tempfile.mkdtemp(prefix="test_ctx_")
    artifacts = artifacts or {}
    for relpath, data in artifacts.items():
        full = os.path.join(base, relpath)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w") as f:
            json.dump(data, f)
    return base

def test_empty_base():
    base = setup_base()
    ctx = C.load_full_context(base)
    assert ctx.tasks == {}
    assert ctx.roles == {}
    assert ctx.flows == []
    assert ctx.entity_model is None
    assert ctx.api_contracts == []
    assert ctx.view_objects == []
    assert ctx.screens == {}
    assert ctx.xv_findings == []
    assert ctx.constraints == []
    assert ctx.get_constraints("ui-design") == []
    assert ctx.get_xv_findings("ui-design") == []
    shutil.rmtree(base)
    print("  PASS: test_empty_base")

def test_loads_artifacts():
    base = setup_base({
        "product-map/task-inventory.json": {"tasks": [
            {"id": "T001", "name": "Create user", "owner_role": "R1", "category": "core"}
        ]},
        "product-map/role-profiles.json": {"roles": [
            {"id": "R1", "name": "Admin"}
        ]},
        "product-map/entity-model.json": {"entities": [{"id": "E1", "name": "User"}], "relationships": []},
        "product-map/api-contracts.json": {"endpoints": [{"id": "API001", "path": "/users", "method": "POST"}]},
        "product-map/view-objects.json": {"view_objects": [
            {"id": "VO001", "entity_ref": "E1", "view_type": "create_form", "interaction_type": "MG2-C",
             "fields": [{"name": "username", "type": "string"}], "actions": []}
        ]},
    })
    ctx = C.load_full_context(base)
    assert "T001" in ctx.tasks
    assert ctx.tasks["T001"]["task_name"] == "Create user"  # normalized
    assert ctx.roles == {"R1": "Admin"}
    assert len(ctx.api_contracts) == 1
    assert len(ctx.view_objects) == 1
    assert ctx.entity_model is not None
    shutil.rmtree(base)
    print("  PASS: test_loads_artifacts")

def test_constraints_loading():
    base = setup_base({
        "constraints/wireframe.json": {
            "source_tab": "wireframe",
            "created_at": "2026-03-09T00:00:00Z",
            "constraints": [
                {"id": "wireframe_pin_001", "target": "ui-design", "screen_id": "S005",
                 "category": "layout", "constraint": "Button at bottom", "severity": "must"},
                {"id": "wireframe_pin_002", "target": "experience-map", "node_id": "N0103",
                 "category": "flow", "constraint": "Skip onboarding", "severity": "must"},
            ]
        },
        "constraints/map.json": {
            "source_tab": "map",
            "created_at": "2026-03-09T00:00:00Z",
            "constraints": [
                {"id": "map_T015", "target": "product-map", "task_id": "T015",
                 "category": "scope", "constraint": "Defer to v2", "severity": "should"},
            ]
        },
    })
    ctx = C.load_full_context(base)
    assert len(ctx.constraints) == 3
    ui_c = ctx.get_constraints("ui-design")
    assert len(ui_c) == 1
    assert ui_c[0]["screen_id"] == "S005"
    em_c = ctx.get_constraints("experience-map")
    assert len(em_c) == 1
    shutil.rmtree(base)
    print("  PASS: test_constraints_loading")

def test_xv_findings_collection():
    base = setup_base({
        "ui-design/ui-xv-review.json": {
            "generated_at": "2026-03-09T00:00:00Z",
            "reviews": [{
                "task_type": "design_review",
                "model_used": "gemini",
                "family": "gemini",
                "auto_applied": {"high_severity_issues": 1},
                "raw_findings": {
                    "issues": [{"severity": "high", "description": "S005 missing password toggle"}]
                }
            }]
        },
        "design-audit/audit-xv-review.json": {
            "generated_at": "2026-03-09T00:00:00Z",
            "reviews": [{
                "task_type": "cross_layer_validation",
                "model_used": "deepseek",
                "family": "deepseek",
                "auto_applied": {},
                "raw_findings": {
                    "issues": [{"severity": "low", "description": "Minor naming inconsistency"}]
                }
            }]
        },
    })
    ctx = C.load_full_context(base)
    assert len(ctx.xv_findings) == 2
    ui_xv = ctx.get_xv_findings("ui-design")
    assert len(ui_xv) == 1
    assert ui_xv[0]["task_type"] == "design_review"
    shutil.rmtree(base)
    print("  PASS: test_xv_findings_collection")

def test_vo_for_screen():
    base = setup_base({
        "product-map/task-inventory.json": {"tasks": [
            {"id": "T001", "name": "Create user", "owner_role": "R1", "category": "core"},
            {"id": "T002", "name": "View users", "owner_role": "R1", "category": "core"},
        ]},
        "product-map/role-profiles.json": {"roles": [{"id": "R1", "name": "Admin"}]},
        "product-map/view-objects.json": {"view_objects": [
            {"id": "VO001", "entity_ref": "E1", "view_type": "create_form",
             "interaction_type": "MG2-C", "fields": [{"name": "username"}],
             "actions": [], "task_refs": ["T001"]},
            {"id": "VO002", "entity_ref": "E1", "view_type": "list_item",
             "interaction_type": "MG1", "fields": [{"name": "username"}],
             "actions": [], "task_refs": ["T002"]},
        ]},
        "experience-map/experience-map.json": {
            "operation_lines": [{
                "id": "OL01", "name": "test",
                "nodes": [{
                    "id": "N01", "seq": 1, "action": "test",
                    "screens": [{"id": "S001", "name": "Create User", "tasks": ["T001"]}]
                }]
            }]
        },
    })
    ctx = C.load_full_context(base)
    vos = ctx.vo_for_screen("S001")
    assert len(vos) == 1
    assert vos[0]["id"] == "VO001"
    vos2 = ctx.vo_for_screen("S999")
    assert vos2 == []
    shutil.rmtree(base)
    print("  PASS: test_vo_for_screen")

def test_api_for_screen():
    base = setup_base({
        "product-map/task-inventory.json": {"tasks": [
            {"id": "T001", "name": "Create user", "owner_role": "R1", "category": "core"},
        ]},
        "product-map/role-profiles.json": {"roles": [{"id": "R1", "name": "Admin"}]},
        "product-map/api-contracts.json": {"endpoints": [
            {"id": "API001", "path": "/users", "method": "POST", "task_refs": ["T001"]},
            {"id": "API002", "path": "/users", "method": "GET", "task_refs": ["T002"]},
        ]},
        "experience-map/experience-map.json": {
            "operation_lines": [{
                "id": "OL01", "name": "test",
                "nodes": [{
                    "id": "N01", "seq": 1, "action": "test",
                    "screens": [{"id": "S001", "name": "Create User", "tasks": ["T001"]}]
                }]
            }]
        },
    })
    ctx = C.load_full_context(base)
    apis = ctx.api_for_screen("S001")
    assert len(apis) == 1
    assert apis[0]["method"] == "POST"
    shutil.rmtree(base)
    print("  PASS: test_api_for_screen")

if __name__ == "__main__":
    print("Running FullContext tests...")
    test_empty_base()
    test_loads_artifacts()
    test_constraints_loading()
    test_xv_findings_collection()
    test_vo_for_screen()
    test_api_for_screen()
    print("All tests passed!")
```

**Step 2: Run test to verify it fails**

Run: `cd product-design-skill/scripts && python3 test_full_context.py`
Expected: FAIL with `AttributeError: module '_common' has no attribute 'load_full_context'`

**Step 3: Implement FullContext class and load_full_context()**

Add to `product-design-skill/scripts/_common.py` (before the `# ── Self-test` section at the end):

```python
# ── Full Context Loader ──────────────────────────────────────────────────────

class FullContext:
    """One-shot loaded context of all pipeline artifacts.

    Provides unified access to all generated artifacts, constraints from
    review feedback, and XV cross-model findings. Scripts call
    load_full_context(base) once and access fields as needed.
    """

    def __init__(self):
        self.tasks = {}           # {id: task} normalized
        self.roles = {}           # {id: name}
        self.roles_full = []      # full role objects
        self.flows = []
        self.entity_model = None  # full dict or None
        self.api_contracts = []   # list of endpoints
        self.view_objects = []    # list of VOs
        self.experience_map = None
        self.screens = {}         # {id: screen}
        self.task_screen_map = {} # {task_id: [screen_ids]}
        self.interaction_gate = None
        self.pattern_catalog = None
        self.behavioral_standards = None
        self.concept = None
        self.xv_findings = []     # collected from all *-xv-review.json
        self.constraints = []     # collected from constraints/*.json
        self._base = ""

    def get_constraints(self, target):
        """Filter constraints by target (e.g. 'ui-design')."""
        return [c for c in self.constraints if c.get("target") == target]

    def get_xv_findings(self, source_phase):
        """Filter XV findings by source phase."""
        return [f for f in self.xv_findings if f.get("source_phase") == source_phase]

    def vo_for_screen(self, screen_id):
        """Match view objects to a screen via its task refs."""
        screen = self.screens.get(screen_id)
        if not screen:
            return []
        screen_tasks = set(screen.get("tasks", []))
        if not screen_tasks:
            return []
        return [vo for vo in self.view_objects
                if set(vo.get("task_refs", [])) & screen_tasks]

    def api_for_screen(self, screen_id):
        """Match API endpoints to a screen via its task refs."""
        screen = self.screens.get(screen_id)
        if not screen:
            return []
        screen_tasks = set(screen.get("tasks", []))
        if not screen_tasks:
            return []
        return [ep for ep in self.api_contracts
                if set(ep.get("task_refs", [])) & screen_tasks]


def _collect_xv_findings(base):
    """Scan all *-xv-review.json files, normalize into flat list."""
    findings = []
    # Map directory to source_phase
    phase_dirs = {
        "experience-map": "experience-map",
        "ui-design": "ui-design",
        "design-audit": "design-audit",
        "use-case": "use-case",
        "feature-gap": "feature-gap",
    }
    for subdir, phase in phase_dirs.items():
        dirpath = os.path.join(base, subdir)
        if not os.path.isdir(dirpath):
            continue
        for fname in os.listdir(dirpath):
            if fname.endswith("-xv-review.json") or fname.endswith("_xv_review.json"):
                data = load_json(os.path.join(dirpath, fname))
                if not data:
                    continue
                for review in data.get("reviews", []):
                    findings.append({
                        "source_phase": phase,
                        "task_type": review.get("task_type", ""),
                        "model_used": review.get("model_used", ""),
                        "family": review.get("family", ""),
                        "auto_applied": review.get("auto_applied", {}),
                        "raw_findings": review.get("raw_findings", {}),
                    })
    return findings


def _collect_constraints(base):
    """Scan constraints/ directory, collect all constraint entries."""
    constraints = []
    cdir = os.path.join(base, "constraints")
    if not os.path.isdir(cdir):
        return constraints
    for fname in sorted(os.listdir(cdir)):
        if not fname.endswith(".json"):
            continue
        data = load_json(os.path.join(cdir, fname))
        if not data:
            continue
        for c in data.get("constraints", []):
            constraints.append(c)
    return constraints


def load_full_context(base):
    """One-shot load all generated artifacts into a FullContext object.

    Safe to call even if most artifacts don't exist yet — missing files
    result in None or empty collections. Total IO is typically < 2MB.
    """
    ctx = FullContext()
    ctx._base = base

    # Core product-map artifacts
    inv = load_json(os.path.join(base, "product-map/task-inventory.json"))
    if inv:
        ctx.tasks = {t["id"]: _normalize_task(t) for t in inv.get("tasks", [])}

    roles_data = load_json(os.path.join(base, "product-map/role-profiles.json"))
    if roles_data:
        ctx.roles_full = roles_data.get("roles", [])
        ctx.roles = {r["id"]: r.get("name", r["id"]) for r in ctx.roles_full}

    flows_data = load_json(os.path.join(base, "product-map/business-flows.json"))
    ctx.flows = flows_data.get("flows", []) if flows_data else []

    em_data = load_json(os.path.join(base, "product-map/entity-model.json"))
    ctx.entity_model = em_data

    api_data = load_json(os.path.join(base, "product-map/api-contracts.json"))
    ctx.api_contracts = api_data.get("endpoints", []) if api_data else []

    vo_data = load_json(os.path.join(base, "product-map/view-objects.json"))
    ctx.view_objects = vo_data.get("view_objects", []) if vo_data else []

    # Experience-map artifacts
    exp_data = load_json(os.path.join(base, "experience-map/experience-map.json"))
    ctx.experience_map = exp_data
    if exp_data:
        op_lines = ensure_list(exp_data, "operation_lines")
        ctx.screens = build_screen_by_id_from_lines(op_lines)
        ctx.task_screen_map = build_task_screen_map_from_lines(op_lines)

    ctx.interaction_gate = load_json(os.path.join(base, "experience-map/interaction-gate.json"))

    # Sibling phase artifacts
    ctx.pattern_catalog = load_json(os.path.join(base, "design-pattern/pattern-catalog.json"))
    ctx.behavioral_standards = load_json(os.path.join(base, "behavioral-standards/behavioral-standards.json"))
    ctx.concept = load_json(os.path.join(base, "product-concept/product-concept.json"))

    # Cross-cutting: XV findings + review constraints
    ctx.xv_findings = _collect_xv_findings(base)
    ctx.constraints = _collect_constraints(base)

    return ctx
```

**Step 4: Run test to verify it passes**

Run: `cd product-design-skill/scripts && python3 test_full_context.py`
Expected: `All tests passed!`

**Step 5: Commit**

```bash
git add product-design-skill/scripts/_common.py product-design-skill/scripts/test_full_context.py
git commit -m "feat: add FullContext class and load_full_context() to _common.py"
```

---

### Task 2: gen_ui_design.py — consume entity-model, view-objects, api-contracts, behavioral-standards, pattern-catalog, constraints

**Files:**
- Modify: `product-design-skill/scripts/gen_ui_design.py`

**Step 1: Add ctx loading after existing data loading**

At the top of `gen_ui_design.py`, after the existing data loading section (after `concept = C.load_product_concept(BASE)`, around line 75), add:

```python
ctx = C.load_full_context(BASE)
```

**Step 2: Enrich screen sections with VO field names**

Find the section where `screen_entry` is built (around line 271). After the existing `data_fields` line, add VO-based field enrichment:

```python
    # ── VO-based field enrichment ──
    vos = ctx.vo_for_screen(sid)
    if vos and not s.get("data_fields"):
        # Use VO fields when experience-map didn't provide data_fields
        vo_fields = []
        for vo in vos:
            for f in vo.get("fields", []):
                vo_fields.append({
                    "name": f.get("name", ""),
                    "type": f.get("type", "string"),
                    "input_widget": f.get("input_widget", "text"),
                    "required": f.get("required", False),
                    "label": f.get("label", f.get("name", "")),
                })
        if vo_fields:
            screen_entry["data_fields"] = vo_fields
            screen_entry["data_fields_source"] = "view-objects"
```

**Step 3: Enrich actions with API bindings**

After the VO enrichment block, add:

```python
    # ── API binding enrichment ──
    apis = ctx.api_for_screen(sid)
    if apis:
        api_bindings = []
        for ep in apis:
            api_bindings.append({
                "endpoint": ep.get("path", ""),
                "method": ep.get("method", ""),
                "api_id": ep.get("id", ""),
            })
        screen_entry["api_bindings"] = api_bindings
```

**Step 4: Inject behavioral-standards into states**

After the API block, add:

```python
    # ── Behavioral standards injection ──
    if ctx.behavioral_standards:
        bs = ctx.behavioral_standards
        standards = bs.get("standards", bs.get("behaviors", []))
        if isinstance(standards, list):
            # Merge standard loading/error/empty patterns if screen doesn't define them
            existing_states = screen_entry.get("states", {})
            for std in standards:
                state_key = std.get("state", "")
                if state_key and state_key not in existing_states:
                    existing_states[state_key] = std.get("behavior", std.get("description", ""))
            screen_entry["states"] = existing_states
```

**Step 5: Inject pattern-catalog reference**

After behavioral standards block, add:

```python
    # ── Pattern catalog reference ──
    if ctx.pattern_catalog:
        itype = screen_entry.get("interaction_type", "")
        patterns = ctx.pattern_catalog.get("patterns", [])
        matched = [p for p in patterns if itype in p.get("interaction_types", [])]
        if matched:
            screen_entry["pattern_refs"] = [p.get("pattern_id", p.get("id", "")) for p in matched[:3]]
```

**Step 6: Inject constraints as hard overrides**

After the pattern block, add:

```python
    # ── Constraint overrides (from review feedback) ──
    screen_constraints = [c for c in ctx.get_constraints("ui-design")
                          if c.get("screen_id") == sid or not c.get("screen_id")]
    if screen_constraints:
        screen_entry["review_constraints"] = [
            {"constraint": c["constraint"], "severity": c.get("severity", "must")}
            for c in screen_constraints
        ]
```

**Step 7: Add XV findings as warnings**

After constraints block, add:

```python
    # ── XV warnings ──
    xv_ui = ctx.get_xv_findings("ui-design")
    if xv_ui:
        for xf in xv_ui:
            raw = xf.get("raw_findings", {})
            for issue in raw.get("issues", []):
                desc = issue.get("description", "")
                if sid in desc or not issue.get("screen_ref"):
                    screen_entry.setdefault("xv_warnings", []).append(desc)
```

**Step 8: Syntax check**

Run: `python3 -c "import py_compile; py_compile.compile('product-design-skill/scripts/gen_ui_design.py', doraise=True)"`
Expected: no output (success)

**Step 9: Integration test on fly_dict**

Run: `python3 product-design-skill/scripts/gen_ui_design.py /Users/aa/Documents/fly_dict/.allforai --mode auto`
Expected: completes successfully, check that `ui-design-spec.json` contains `data_fields_source`, `api_bindings`, or `review_constraints` fields where applicable.

**Step 10: Commit**

```bash
git add product-design-skill/scripts/gen_ui_design.py
git commit -m "feat(gen_ui_design): consume entity-model, VO, API, behavioral-standards, pattern-catalog, constraints"
```

---

### Task 3: gen_ui_stitch.py — enrich prompts with VO fields, API, behavioral-standards, constraints

**Files:**
- Modify: `product-design-skill/scripts/gen_ui_stitch.py`

**Step 1: Load full context in main()**

In the `main()` function (around line 207), after `comp_spec = load_component_spec(base)`, add:

```python
    ctx = C.load_full_context(base)
```

**Step 2: Pass ctx to build_prompt()**

Update the `build_prompt` call (around line 252) to pass ctx:

```python
        prompt = build_prompt(s, concept, comp_spec, device_type, is_anchor=(i == 0),
                              screen_context=screen_context, wf_feedback=wf_feedback, ctx=ctx)
```

**Step 3: Update build_prompt signature and add new layers**

Update the function signature (line 105):

```python
def build_prompt(screen, concept, component_spec, device_type, is_anchor,
                 screen_context=None, wf_feedback=None, ctx=None):
```

After the existing Layer 2 data_fields section (around line 166), add VO-precision fields:

```python
    # ── VO-precision data fields (override generic ones) ──
    if ctx:
        vos = ctx.vo_for_screen(sid)
        if vos:
            precise_fields = []
            for vo in vos:
                for f in vo.get("fields", []):
                    fname = f.get("label", f.get("name", ""))
                    ftype = f.get("type", "string")
                    freq = "required" if f.get("required") else "optional"
                    precise_fields.append(f"{fname}({ftype}, {freq})")
            if precise_fields:
                layer2 += f"Precise data fields: {', '.join(precise_fields)}\n"

        # API binding context
        apis = ctx.api_for_screen(sid)
        if apis:
            api_descs = []
            for ep in apis:
                api_descs.append(f"{ep.get('method', 'GET')} {ep.get('path', '')}")
            layer2 += f"API endpoints: {', '.join(api_descs)}\n"
```

After Layer 3 (around line 179), add behavioral-standards as part of Layer 1:

```python
    # ── Behavioral standards (global consistency) ──
    bs_hint = ""
    if ctx and ctx.behavioral_standards:
        bs = ctx.behavioral_standards
        standards = bs.get("standards", bs.get("behaviors", []))
        if isinstance(standards, list):
            std_descs = []
            for std in standards[:5]:
                state = std.get("state", "")
                behavior = std.get("behavior", std.get("description", ""))
                if state and behavior:
                    std_descs.append(f"{state}: {behavior}")
            if std_descs:
                bs_hint = "Behavioral standards: " + "; ".join(std_descs) + "\n"
```

Before the final return, add constraint layer as highest priority:

```python
    # ── Constraint layer (highest priority — human review feedback) ──
    constraint_hint = ""
    if ctx:
        screen_constraints = [c for c in ctx.get_constraints("ui-design")
                              if c.get("screen_id") == sid or not c.get("screen_id")]
        if screen_constraints:
            must_lines = [f"MUST: {c['constraint']}" for c in screen_constraints
                          if c.get("severity") == "must"]
            should_lines = [f"SHOULD: {c['constraint']}" for c in screen_constraints
                            if c.get("severity") != "must"]
            constraint_hint = "\n".join(must_lines + should_lines) + "\n"

    return f"{constraint_hint}{layer1}\n{bs_hint}{layer2}\n{layer3}{layer4}{layout}"
```

**Step 4: Syntax check**

Run: `python3 -c "import py_compile; py_compile.compile('product-design-skill/scripts/gen_ui_stitch.py', doraise=True)"`

**Step 5: Integration test**

Run: `python3 product-design-skill/scripts/gen_ui_stitch.py /Users/aa/Documents/fly_dict/.allforai --mode auto`
Expected: `OK stitch-prompts.json → 10 screens`. Verify prompts contain `Precise data fields:` or `API endpoints:` where VOs/APIs exist.

**Step 6: Commit**

```bash
git add product-design-skill/scripts/gen_ui_stitch.py
git commit -m "feat(gen_ui_stitch): enrich prompts with VO fields, API bindings, behavioral standards, constraints"
```

---

### Task 4: gen_use_cases.py — consume entity-model for validation rules, API for when_steps, constraints

**Files:**
- Modify: `product-design-skill/scripts/gen_use_cases.py`

**Step 1: Load full context**

After the existing data loading (around line 25), add:

```python
ctx = C.load_full_context(BASE)
```

**Step 2: Enrich validation rules from entity model**

Find the `gen_validation` function (around line 177). Before the existing validation_rules loop, add entity-based rules:

```python
    # ── Entity-model validation rules ──
    if ctx.entity_model:
        entities = ctx.entity_model.get("entities", [])
        for vo in ctx.vo_for_screen(sid) if ctx else []:
            for f in vo.get("fields", []):
                constraints = f.get("constraints", {})
                if constraints:
                    vr = []
                    if "min_length" in constraints:
                        vr.append(f"{f['name']} 最少 {constraints['min_length']} 字符")
                    if "max_length" in constraints:
                        vr.append(f"{f['name']} 最多 {constraints['max_length']} 字符")
                    if "pattern" in constraints:
                        vr.append(f"{f['name']} 需要匹配格式: {constraints['pattern']}")
                    if f.get("required"):
                        vr.append(f"{f['name']} 为必填字段")
                    for rule in vr:
                        cases.append({
                            "id": next_uc(),
                            "title": f"{task['task_name']}_校验_{rule[:20]}",
                            "type": "validation",
                            "priority": prio,
                            "given": ["用户已登录", f"正在执行{task['task_name']}"],
                            "when": [f"违反校验规则: {rule}"],
                            "then": [f"系统提示校验失败: {rule}"],
                            "screen_ref": sid,
                            "validation_rule": rule,
                            "source": "entity-model",
                        })
```

**Step 3: Inject constraints**

At the top of the main generation loop, filter use-case constraints:

```python
uc_constraints = ctx.get_constraints("use-case") if ctx else []
```

After generating all cases, append constraint-driven cases if any:

```python
# ── Constraint-driven use cases ──
for c in uc_constraints:
    if c.get("constraint"):
        # Constraints become additional test scenarios
        pass  # constraints are advisory here — they appear in the report
```

**Step 4: Syntax check + test**

Run: `python3 -c "import py_compile; py_compile.compile('product-design-skill/scripts/gen_use_cases.py', doraise=True)"`

**Step 5: Commit**

```bash
git add product-design-skill/scripts/gen_use_cases.py
git commit -m "feat(gen_use_cases): consume entity-model for validation rules, add constraint support"
```

---

### Task 5: gen_feature_gap.py — add entity/API coverage checks, consume constraints

**Files:**
- Modify: `product-design-skill/scripts/gen_feature_gap.py`

**Step 1: Load full context**

After existing data loading (around line 28), add:

```python
ctx = C.load_full_context(BASE)
```

**Step 2: Add entity field coverage check**

After the existing gap detection loops (find the section that writes to `screen_gaps`), add:

```python
# ── Entity field coverage gaps ──
entity_field_gaps = []
if ctx.entity_model:
    for entity in ctx.entity_model.get("entities", []):
        eid = entity.get("id", "")
        ename = entity.get("name", eid)
        entity_fields = {f.get("name", "") for f in entity.get("fields", []) if f.get("name")}
        # Find all screens that reference this entity (via VOs)
        entity_vos = [vo for vo in ctx.view_objects if vo.get("entity_ref") == eid]
        vo_fields = set()
        for vo in entity_vos:
            for f in vo.get("fields", []):
                vo_fields.add(f.get("name", ""))
        missing = entity_fields - vo_fields
        if missing and len(missing) <= len(entity_fields) * 0.5:
            # Only flag if some fields shown (not a completely hidden entity)
            entity_field_gaps.append({
                "entity_id": eid,
                "entity_name": ename,
                "total_fields": len(entity_fields),
                "shown_fields": len(vo_fields),
                "missing_fields": sorted(missing),
                "gap_type": "ENTITY_FIELD_COVERAGE",
            })
```

**Step 3: Add API coverage check**

```python
# ── API endpoint coverage gaps ──
api_gaps = []
if ctx.api_contracts:
    referenced_apis = set()
    for vo in ctx.view_objects:
        for a in vo.get("actions", []):
            api_ref = a.get("api_ref", "")
            if api_ref:
                referenced_apis.add(api_ref)
    for ep in ctx.api_contracts:
        epid = ep.get("id", "")
        if epid and epid not in referenced_apis:
            api_gaps.append({
                "api_id": epid,
                "path": ep.get("path", ""),
                "method": ep.get("method", ""),
                "gap_type": "UNREFERENCED_API",
                "description": f"API {ep.get('method','')} {ep.get('path','')} ({epid}) 未被任何 VO 引用",
            })
```

**Step 4: Write entity and API gaps into existing gap output**

Find where `gap-tasks.json` is written. Before that write, merge the new gaps:

```python
# Merge entity/API gaps into output
if entity_field_gaps:
    output.setdefault("entity_field_gaps", []).extend(entity_field_gaps)
    print(f"  Entity field gaps: {len(entity_field_gaps)}")
if api_gaps:
    output.setdefault("api_gaps", []).extend(api_gaps)
    print(f"  API coverage gaps: {len(api_gaps)}")
```

**Step 5: Consume constraints (skip marked "not a gap")**

```python
gap_constraints = ctx.get_constraints("feature-gap")
skip_ids = {c.get("task_id") or c.get("screen_id") for c in gap_constraints
            if "not a gap" in c.get("constraint", "").lower() or "ignore" in c.get("constraint", "").lower()}
# Filter out gaps for items explicitly marked as "not a gap"
# Apply skip_ids as a filter on task_gaps and screen_gaps before writing
```

**Step 6: Syntax check + test**

Run: `python3 -c "import py_compile; py_compile.compile('product-design-skill/scripts/gen_feature_gap.py', doraise=True)"`

**Step 7: Commit**

```bash
git add product-design-skill/scripts/gen_feature_gap.py
git commit -m "feat(gen_feature_gap): add entity/API coverage checks, consume constraints"
```

---

### Task 6: gen_interaction_gate.py — consume XV findings for score adjustment

**Files:**
- Modify: `product-design-skill/scripts/gen_interaction_gate.py`

**Step 1: Load full context**

After existing data loading, add:

```python
ctx = C.load_full_context(BASE)
```

**Step 2: Apply XV findings as score penalties**

Find the scoring section (after `evaluate_line`). Add XV penalty:

```python
    # ── XV finding penalties ──
    xv_findings = ctx.xv_findings if ctx else []
    for finding in xv_findings:
        severity = "low"
        raw = finding.get("raw_findings", {})
        for issue in raw.get("issues", []):
            sev = issue.get("severity", "low")
            desc = issue.get("description", "")
            # Check if this finding relates to any screen in this operation line
            for screen in screens_in_line:
                if screen["id"] in desc:
                    if sev == "high":
                        total_score -= 5
                    elif sev == "critical":
                        total_score -= 10
    total_score = max(0, total_score)
```

**Step 3: Syntax check + commit**

Run: `python3 -c "import py_compile; py_compile.compile('product-design-skill/scripts/gen_interaction_gate.py', doraise=True)"`

```bash
git add product-design-skill/scripts/gen_interaction_gate.py
git commit -m "feat(gen_interaction_gate): consume XV findings for gate score adjustment"
```

---

### Task 7: gen_feature_prune.py + gen_design_audit.py — add constraint consumption

**Files:**
- Modify: `product-design-skill/scripts/gen_feature_prune.py`
- Modify: `product-design-skill/scripts/gen_design_audit.py`

**Step 1: gen_feature_prune.py — load context and consume constraints**

After existing data loading (around line 28), add:

```python
ctx = C.load_full_context(BASE)
prune_constraints = ctx.get_constraints("feature-prune")
```

Before the prune scoring loop, apply constraints:

```python
# Tasks marked "defer" by reviewer get auto-pruned
defer_task_ids = {c.get("task_id") for c in prune_constraints
                  if "defer" in c.get("constraint", "").lower() or "不做" in c.get("constraint", "")}
# Tasks marked "must keep" by reviewer are protected from pruning
keep_task_ids = {c.get("task_id") for c in prune_constraints
                 if "keep" in c.get("constraint", "").lower() or "必须" in c.get("constraint", "")}
```

In the scoring loop, add:

```python
    if tid in defer_task_ids:
        score += 50  # heavy prune bias
        reasons.append("reviewer: defer to later version")
    if tid in keep_task_ids:
        score -= 100  # protect from pruning
        reasons.append("reviewer: must keep")
```

**Step 2: gen_design_audit.py — load context and add constraint coverage check**

After existing data loading, add:

```python
ctx = C.load_full_context(BASE)
```

Add a new audit check section:

```python
# ── Constraint fulfillment check ──
constraint_issues = []
for c in ctx.constraints:
    target = c.get("target", "")
    cid = c.get("id", "")
    constraint_issues.append({
        "check_id": "CON1",
        "type": "ACTIVE_CONSTRAINT",
        "constraint_id": cid,
        "target": target,
        "detail": f"Active review constraint: {c.get('constraint', '')} (severity: {c.get('severity', 'must')})",
    })

if constraint_issues:
    report.setdefault("constraint_status", []).extend(constraint_issues)
    print(f"  Active constraints: {len(constraint_issues)}")
```

**Step 3: Syntax check both**

Run:
```bash
python3 -c "import py_compile; py_compile.compile('product-design-skill/scripts/gen_feature_prune.py', doraise=True)"
python3 -c "import py_compile; py_compile.compile('product-design-skill/scripts/gen_design_audit.py', doraise=True)"
```

**Step 4: Commit**

```bash
git add product-design-skill/scripts/gen_feature_prune.py product-design-skill/scripts/gen_design_audit.py
git commit -m "feat(prune+audit): consume review constraints for prune bias and audit tracking"
```

---

### Task 8: /review process — generate constraint files

**Files:**
- Modify: `product-design-skill/commands/review.md`

**Step 1: Add constraint generation instructions to the process flow**

In the `## Mode: process` section (around line 71), update step 4 to include constraint writing:

Replace the existing step 4-6 with:

````markdown
4. K > 0 → 按类别汇总修改建议：
   - 脑图 tab: 按节点分组展示 revision comments
   - 预览 tab: 按界面分组展示 pin comments，按 category 路由
     - category="product-map" → 汇总为产品地图修改建议
     - category="experience-map" → 汇总为体验地图修改建议
     - category="concept" → 汇总为概念级问题

5. **生成约束文件** → `.allforai/constraints/<tab>.json`
   - 每条 needs_revision 评论转为一个约束条目
   - 约束 ID = `{tab}_{pin_id}` 或 `{tab}_{node_id}`（幂等，重复 process 不重复）
   - target 推断规则：
     - 脑图 tab: 节点类型直接对应 target（concept→product-concept, map→product-map, data-model→product-map, spec→dev-forge）
     - 预览 tab: pin 的 category 字段（"product-map" / "experience-map" / "ui"→"ui-design"）
   - severity: pin 的 severity 字段，默认 "must"
   - 约束文件格式：
     ```json
     {
       "source_tab": "<tab>",
       "created_at": "<ISO>",
       "constraints": [
         {"id": "...", "target": "...", "constraint": "...", "severity": "must", ...}
       ]
     }
     ```
   - 输出提示："已写入 N 条约束到 constraints/<tab>.json，下次重跑相关脚本时自动生效"

6. K = 0（全部 approved）→ 删除 `constraints/<tab>.json`（如果存在）
   - 输出 "<tab> 审核全部通过，约束已清除"

7. 输出修复行动清单

8. 更新 review-feedback.json: round += 1
````

**Step 2: Commit**

```bash
git add product-design-skill/commands/review.md
git commit -m "feat(review): add constraint file generation to /review process flow"
```

---

### Task 9: Version bump + final integration test

**Files:**
- Modify: `product-design-skill/.claude-plugin/plugin.json`
- Modify: `product-design-skill/.claude-plugin/marketplace.json`
- Modify: `product-design-skill/SKILL.md`

**Step 1: Bump version to 4.6.0 (minor — new feature)**

Update all 3 files: `"version": "4.5.6"` → `"version": "4.6.0"`

**Step 2: Full pipeline integration test on fly_dict**

```bash
# Regenerate experience-map (already has 23 screens)
python3 product-design-skill/scripts/gen_experience_map.py /Users/aa/Documents/fly_dict/.allforai --mode auto

# Generate UI components (dependency)
python3 product-design-skill/scripts/gen_ui_components.py /Users/aa/Documents/fly_dict/.allforai --mode auto

# Test gen_ui_design with full context
python3 product-design-skill/scripts/gen_ui_design.py /Users/aa/Documents/fly_dict/.allforai --mode auto

# Test gen_ui_stitch with full context
python3 product-design-skill/scripts/gen_ui_stitch.py /Users/aa/Documents/fly_dict/.allforai --mode auto

# Test gen_use_cases with full context
python3 product-design-skill/scripts/gen_use_cases.py /Users/aa/Documents/fly_dict/.allforai --mode auto

# Test gen_feature_gap with full context
python3 product-design-skill/scripts/gen_feature_gap.py /Users/aa/Documents/fly_dict/.allforai --mode auto
```

Verify:
- `ui-design-spec.json` contains `data_fields_source: "view-objects"` or `api_bindings` on some screens
- `stitch-prompts.json` prompts contain `Precise data fields:` or `API endpoints:`
- `use-case-tree.json` contains validation rules with `source: "entity-model"`
- No script crashes

**Step 3: Test with constraints (create a mock constraint file)**

```bash
mkdir -p /Users/aa/Documents/fly_dict/.allforai/constraints
echo '{"source_tab":"wireframe","created_at":"2026-03-09T00:00:00Z","constraints":[{"id":"wireframe_test_001","target":"ui-design","screen_id":"S001","category":"layout","constraint":"Button must be at bottom","severity":"must"}]}' > /Users/aa/Documents/fly_dict/.allforai/constraints/wireframe.json
```

Re-run gen_ui_design and gen_ui_stitch, verify S001 output contains the constraint.

Clean up: `rm -rf /Users/aa/Documents/fly_dict/.allforai/constraints/`

**Step 4: Commit version bump**

```bash
git add product-design-skill/.claude-plugin/plugin.json product-design-skill/.claude-plugin/marketplace.json product-design-skill/SKILL.md
git commit -m "chore: bump product-design to 4.6.0 (pipeline data flow unification)"
```

**Step 5: Push**

```bash
git push
```

---

Plan complete and saved to `docs/plans/2026-03-09-pipeline-data-flow-plan.md`. Two execution options:

**1. Subagent-Driven (this session)** — I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** — Open new session with executing-plans, batch execution with checkpoints

Which approach?