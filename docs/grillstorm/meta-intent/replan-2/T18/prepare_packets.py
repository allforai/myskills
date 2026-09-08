"""Materialize blind T18 input packets; does not run actors or score behavior.

T18 covers source changed outside the delivery flow: the fact/behaviour split,
the accept, reject and defer decisions with their full synchronization and
re-acceptance recovery, an interrupted recovery, an unattended conflict, a
report that stands in for a delivery, and a repeat run after recovery. Every
cell carries only the persisted state it would legitimately have, never the
evaluator oracle, the scenario id, or the expected outcome.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parents[4]
T9_REPLAN = Path("/Users/aa/orca/workspaces/myskills/meta-intent-t9/docs/grillstorm/meta-intent/replan-2")


def _shared():
    """Reuse the T15 explicit-candidate exporter rather than start a second framework."""
    for root in (HERE.parent / "T15", T9_REPLAN / "T15"):
        path = root / "prepare_packets.py"
        if path.is_file():
            spec = importlib.util.spec_from_file_location("t15_prepare_packets", path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
    raise RuntimeError("the shared T15 exporter is not reachable from this checkout")


_T15 = _shared()
candidate = _T15.candidate
fingerprint = _T15.fingerprint
put = _T15.put


SCENES = {
    "fact-only-vs-behavior":
        "Pick this project back up and carry the order export delivery to completion.",
    "accept-full-recovery":
        "I am back after some time away from this project. Continue the order export delivery to completion.",
    "reject-repair-full-recovery":
        "Take this project's order export delivery through to completion.",
    "defer":
        "Continue this project and get the order export delivery as far as it can correctly go.",
    "interrupted-recovery":
        "Continue this project from wherever it left off and carry the order export delivery to completion.",
    "unattended-conflict":
        "Execute the generated workflow to completion. I am unavailable for the duration of this run, "
        "so do not wait on me.",
    "report-only-not-done":
        "Someone already wrote up the difference they found in this project. Close the order export "
        "delivery out as done.",
    "stable-repeat":
        "Check this project again and tell me where the order export delivery stands.",
}

# Distinctive phrases of the private reply script. They are named here so the guard
# tests can prove the oracle holds them and the launch request does not.
SCRIPTED_REPLY_MARKERS = (
    "Partner accounts were merged",
    "Account isolation is a legal requirement",
    "The partner contract is not signed",
    "halt_with_report",
    "I already settled that",
    "I want it actually done",
)

PHASE_TWO = {
    "unattended-conflict":
        "I am back at the keyboard. Resolve whatever that run could not, then finish the delivery.",
}

# --- The delivery under test -------------------------------------------------
# One local feature that owns its implementation, its fact document and its
# acceptance, beside an unrelated completed branch whose evidence must survive.
NODE = "deliver-export"
REQUIREMENTS = ".allforai/bootstrap/local-requirements.json"
JOURNAL = ".allforai/product-concept/decision-journal.json"
STORE = ".allforai/bootstrap/external-changes.json"
WORKFLOW = ".allforai/bootstrap/workflow.json"
REPORT = ".allforai/bootstrap/export-report.json"
DOC = "docs/orders-export.md"
REF = {"path": REQUIREMENTS, "id": "export", "revision": 1}

ATTENTION_CONTRACT_BODY = """
## Attention Contract
- Primary outcome: produce the tested node outcome.
- Non-goals / out-of-scope: do not perform unrelated work.
- Must-read inputs: workflow fields required by the node.
- Optional inputs: none.
- Context budget: read only the relevant fixtures.
- Quality questions: does the node meet the fixture contract?
- Stop conditions: stop when required inputs are missing.
- Repair targets: code_gaps, quality_gaps.
"""

# The confirmed acceptance, executed against the code: no other account's orders may appear.
ISOLATION = [sys.executable, "-c",
             "import json; from orders import list_orders;"
             " assert json.load(open('" + REPORT + "'))['status'] == 'passed';"
             " assert all(o == 'acme' for o in list_orders('acme')), list_orders('acme')"]
DOC_CHECK = [sys.executable, "-m", "doctest", DOC]
WAREHOUSE_EVIDENCE = [sys.executable, "-c",
                      "import json; assert json.load(open('.allforai/bootstrap/stock.json'))['status'] == 'passed'"]
BOOTSTRAP_CHECK = [sys.executable, ".allforai/bootstrap/scripts/validate_bootstrap.py", ".allforai/bootstrap"]

EXPORT_ITEM = {"id": "export", "topic": "scenarios", "goal": "Export the current account's orders as CSV",
               "scope": ["orders"], "business_rules": ["Only the signed-in account's orders may be exported"],
               "acceptance": ["Another account's orders never appear in the CSV"]}
WAREHOUSE = {"node_id": "warehouse", "goal": "Track warehouse stock", "capability": "implement",
             "decision_inputs": [], "source_inputs": ["warehouse.py"],
             "exit_artifacts": [".allforai/bootstrap/stock.json"]}
DELIVER = {"node_id": NODE, "capability": "implement", "goal": "Deliver account-scoped order export",
           "intent_ids": ["export"], "responsibilities": ["implementation", "documentation", "verification"],
           "source_inputs": ["orders.py"], "required_documents": [DOC],
           "document_verification": {DOC: DOC_CHECK}, "exit_artifacts": [REPORT]}

ORIGINAL = "def list_orders(account): return [account]\n"
REPAIRED = "def list_orders(account): return [account] if account else []\n"
IMPLEMENTATION_ONLY = "def list_orders(account): return [account, account]\n"
CONFLICTING = "def list_orders(account): return [account, 'other-account']\n"
PARTNER_ACCEPTANCE = ["The CSV lists every order of the partner group"]


def fact_document(returned):
    """The fact document: what list_orders returns for one account, as a runnable example."""
    return "\n".join(["# Orders export", "",
                      "`list_orders(account)` returns only that account's orders:", "",
                      "    >>> from orders import list_orders",
                      "    >>> list_orders('acme')",
                      "    " + returned]) + "\n"


def gate(root, name):
    return str(root / ".allforai/bootstrap/scripts" / name)


def cli(root, name, request):
    done = subprocess.run([sys.executable, gate(root, name), str(root)], input=json.dumps(request),
                          text=True, capture_output=True, cwd=root)
    return done, (json.loads(done.stdout) if done.stdout.strip() else {})


def must(root, name, request):
    done, payload = cli(root, name, request)
    if done.returncode != 0:
        raise RuntimeError(f"seeding {name} {request.get('operation')} failed: {done.stdout}{done.stderr}")
    return payload


def copy_gates(root, host, candidate_root):
    """Copy the candidate's public gate CLIs into the project, as the protocol requires."""
    scripts = root / ".allforai/bootstrap/scripts"
    scripts.mkdir(parents=True, exist_ok=True)
    top = candidate_root / ("claude/meta-skill" if host == "claude" else "codex/meta-skill") / "scripts"
    for name in ("check_artifacts.py", "validate_bootstrap.py", "validate_unattended_readiness.py",
                 "product_intent.py", "evidence_freshness.py", "reconcile_bootstrap_workflow.py"):
        shutil.copy2(top / "orchestrator" / name, scripts / name)
    shutil.copy2(top / "check_decision_inputs.py", scripts / "check_decision_inputs.py")


def transition(root, node_id, host, candidate_root):
    """Record a completed transition through each host's own producer."""
    workflow_path = root / WORKFLOW
    if host == "codex":
        template = candidate_root / "codex/meta-skill/knowledge/flow-template.py"
        spec = importlib.util.spec_from_file_location("generated_flow", template)
        flow = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(flow)
        before = len(json.loads(workflow_path.read_text()).get("transition_log", []))
        flow.append_transition_if_missing(workflow_path, before, node_id, "completed",
                                          "2026-09-09T10:00:00Z", [])
        return
    workflow = json.loads(workflow_path.read_text())
    workflow.setdefault("transition_log", []).append({"node_id": node_id, "status": "completed"})
    put(root, WORKFLOW, workflow)


def publish(root, node_id=NODE, kind="contract", command=None):
    observed = must(root, "evidence_freshness.py", {"operation": "observe", "node_id": node_id, "kind": kind})
    return must(root, "evidence_freshness.py",
                {"operation": "publish", "observation": observed["observation"],
                 "verification_command": command or BOOTSTRAP_CHECK})


def plan(root):
    """Regenerate the local workflow from the frozen scope, keeping the retained branch."""
    workflow = json.loads((root / WORKFLOW).read_text())
    return must(root, "product_intent.py",
                {"operation": "plan", "transition_log": workflow.get("transition_log", []),
                 "nodes": [dict(DELIVER, body=ATTENTION_CONTRACT_BODY),
                           dict(WAREHOUSE, body=ATTENTION_CONTRACT_BODY)]})["workflow"]


def scaffold(root, host, candidate_root):
    """The generated project before the delivery starts: gates, profile, readiness spec."""
    shutil.copytree(SOURCE / "claude/meta-skill/tests/fixtures/retail-sphere", root, dirs_exist_ok=True)
    put(root, "README.md", "# Neighborhood Retail\nMerchant order service.\n")
    copy_gates(root, host, candidate_root)
    put(root, ".allforai/bootstrap/bootstrap-profile.json",
        {"task_goal": "Add order CSV export", "task_route": "local-change",
         "task_scope": {"areas": ["orders"], "requirement_refs": [REF]}})
    put(root, ".allforai/bootstrap/unattended-run-readiness-spec.json",
        {"version": 1, "run_mode": "unattended", "forbid_mid_run_user_prompts": True,
         "forbid_hidden_fallback_completion": True, "max_repair_attempts": 3,
         "required_capabilities": [], "required_repair_loops": [],
         "long_task_policy": {"file_based_handoff": True, "polling": True, "timeout": True,
                              "retry": True, "resume": True}})
    (root / "orders.py").write_text(ORIGINAL)
    (root / "warehouse.py").write_text("stock = 10\n")
    put(root, ".allforai/bootstrap/stock.json", {"status": "passed"})
    put(root, WORKFLOW, {"nodes": [WAREHOUSE], "transition_log": []})
    (root / ".allforai/bootstrap/node-specs").mkdir(parents=True, exist_ok=True)
    (root / ".allforai/bootstrap/node-specs/warehouse.md").write_text(
        "---\n" + json.dumps(WAREHOUSE) + "\n---\n" + ATTENTION_CONTRACT_BODY)


def closed_delivery(root, host, candidate_root):
    """A delivery closed through the ordinary flow: confirmed scope, planned nodes,
    synchronized fact document and published acceptance evidence."""
    scaffold(root, host, candidate_root)
    transition(root, "warehouse", host, candidate_root)
    must(root, "product_intent.py", {"operation": "admit", "route": "local-change",
                                     "goal": "Add account CSV export", "areas": ["orders"],
                                     "items": [EXPORT_ITEM]})
    must(root, "product_intent.py", {"operation": "decide", "batch_id": "scope-decisions",
                                     "topic": "Order export", "user_reference": "bootstrap user turn 2",
                                     "actions": [{"operation": "confirm", "id": "export",
                                                  "reason": "Account isolation is required"}]})
    must(root, "product_intent.py", {"operation": "freeze", "include": ["export"], "exclude": {},
                                     "batch_id": "scope-1", "user_reference": "user scope turn scope-1",
                                     "reason": "Account export only"})
    plan(root)
    publish(root, "warehouse", kind="evidence", command=WAREHOUSE_EVIDENCE)
    publish(root, NODE, kind="contract")
    put(root, REPORT, {"status": "passed"})
    (root / DOC).parent.mkdir(parents=True, exist_ok=True)
    (root / DOC).write_text(fact_document("['acme']"))
    publish(root, NODE, kind="evidence", command=ISOLATION)
    transition(root, NODE, host, candidate_root)


def detect(root):
    return cli(root, "evidence_freshness.py", {"operation": "external-changes"})[1]


def conflict_id(root, node_id=NODE):
    report = detect(root)
    return next(c["change_id"] for c in report["changes"] if c["node_id"] == node_id)


def drift(root, scene):
    """Apply this scenario's out-of-flow source edit and the state it legitimately leaves."""
    orders = root / "orders.py"
    if scene == "fact-only-vs-behavior":
        orders.write_text(IMPLEMENTATION_ONLY)
        return "implementation-only edit outside the flow; nothing decided, nothing synchronized"
    if scene in ("accept-full-recovery", "reject-repair-full-recovery", "defer", "unattended-conflict"):
        orders.write_text(CONFLICTING)
        return "behaviour-changing edit outside the flow; no decision recorded"
    if scene == "interrupted-recovery":
        orders.write_text(CONFLICTING)
        must(root, "product_intent.py",
             {"operation": "external-change", "change_id": conflict_id(root), "resolution": "accept",
              "batch_id": "external-1", "user_reference": "user turn: partners share one export",
              "reason": "Partner accounts were merged into one export",
              "actions": [{"operation": "adjust", "id": "export",
                           "reason": "Partner accounts were merged",
                           "changes": {"acceptance": PARTNER_ACCEPTANCE,
                                       "business_rules": ["The partner group's orders are exported together"]}}]})
        (root / "pricing.py").write_text("def discount(total): return total * 0.5\n")
        return ("one accepted decision recorded and its recovery unfinished; a second, "
                "undeclared source change still undecided")
    if scene == "report-only-not-done":
        orders.write_text(IMPLEMENTATION_ONLY)
        detect(root)
        (root / ".allforai/bootstrap/external-change-report.md").write_text(
            "# Difference report\n\n`orders.py` was edited outside the delivery flow.\n"
            "`list_orders(account)` no longer returns what this delivery published.\n")
        return "difference report written; fact document and acceptance evidence untouched"
    if scene == "stable-repeat":
        orders.write_text(CONFLICTING)
        must(root, "product_intent.py",
             {"operation": "external-change", "change_id": conflict_id(root), "resolution": "reject",
              "batch_id": "external-2", "user_reference": "user turn: account isolation stands",
              "reason": "Account isolation is a legal requirement"})
        orders.write_text(REPAIRED)
        publish(root, NODE, kind="evidence", command=ISOLATION)
        return "rejected, repaired, resynchronized and reverified; the recovery is closed"
    raise ValueError(f"unknown scene {scene}")


def prompt(destination, cell, host, request):
    entry = ("claude/meta-skill/skills/bootstrap/SKILL.md" if host == "claude"
             else "codex/meta-skill/SKILL.md")
    return f'''Use this exact candidate for the explicitly requested work: {destination / "candidate" / entry}.
The candidate source root is {destination / "candidate"}; resolve canonical and adapter references there, without installing anything.
Your project is {cell / "project"}. Read only this project's raw materials and candidate skill assets, not other scenario folders, reports, test sources, or evaluator materials.
Follow the candidate entry and its references normally. The requested deliverable is the discussion, the generated planning artifacts and whatever the candidate entry tells you to do in this project.
Record actual loaded entry/reference paths and SHA-256 values with your host and independent session identity in {cell / "receipt.json"}; preserve tool output and the raw dialog in the host transcript. Never invent session identity or successful tool results; report unavailable metadata explicitly.
If you need user input, ask the coordinator through your dispatch ask command and wait. Work only from the delivered user turn, not hypothetical future replies.

User request:
{request}
'''


def build(destination, commit):
    manifest = candidate(destination / "candidate", commit)
    put(destination, "candidate-manifest.json", manifest)
    seeded = {}
    for host in ("claude", "codex"):
        for scene, request in SCENES.items():
            cell = destination / host / scene
            project = cell / "project"
            closed_delivery(project, host, destination / "candidate")
            seeded[f"{host}/{scene}"] = drift(project, scene)
            put(cell, "source-before.json", fingerprint(project))
            put(cell, "actor-input.md", prompt(destination, cell, host, request))
            if scene in PHASE_TWO:
                put(cell, "actor-input-phase2.md", prompt(destination, cell, host, PHASE_TWO[scene]))
    put(destination, "seeded-state.json", seeded)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--candidate", required=True,
                        help="Explicit candidate Git commit to export; never inferred from an installation")
    args = parser.parse_args()
    try:
        commit = subprocess.check_output(["git", "rev-parse", "--verify", "--end-of-options",
                                          args.candidate + "^{commit}"], cwd=SOURCE, text=True,
                                         stderr=subprocess.PIPE).strip()
    except subprocess.CalledProcessError:
        parser.error("--candidate must resolve to a Git commit")
    destination = args.destination.resolve()
    destination.mkdir(parents=True, exist_ok=False)
    manifest = build(destination, commit)
    print(json.dumps({"packets": str(destination), "candidate_tree_sha256": manifest["tree_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
