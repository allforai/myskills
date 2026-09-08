"""Materialize blind T16 input packets; does not run actors or score behavior.

T16 covers interruption, reversal, conflicting legacy material and repeated
reverse-inference. Every resume-shaped cell receives only the persisted state it
would legitimately have, never the evaluator oracle or the expected outcome.
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


def _shared():
    """Reuse the T15 explicit-candidate exporter rather than start a second framework."""
    path = HERE.parent / "T15" / "prepare_packets.py"
    spec = importlib.util.spec_from_file_location("t15_prepare_packets", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_T15 = _shared()
candidate = _T15.candidate
fingerprint = _T15.fingerprint
put = _T15.put


SCENES = {
    "no-answer": "Bootstrap a product reshape for this repository. I want to move away from paid merchant subscriptions toward free neighborhood mutual-aid groups. Help me settle the product direction.",
    "partial-resume": "Continue the bootstrap for this product.",
    "reverse-prior-decision": "I have changed my mind about who can see a supply request. Earlier I settled that every volunteer in the group can see every request; I now want only the requester and the group coordinators to see it. Take that into account and plan the work.",
    "legacy-provenance": "Bootstrap a product reshape toward free neighborhood mutual aid. Reuse whatever I have already settled and do not make me repeat decisions I have already made.",
    "removed-not-resurrected": "Re-derive the product direction from the current code and plan the next iteration.",
    "discussion-preserves-source": "Drop paid lead ranking from the product; we are not doing revenue-ranked sales targeting any more. I also have not decided how the service will be funded. Take both into account and plan the work.",
    "unattended-pending": "Execute the generated workflow to completion. I am not available for the duration of this run, so do not wait on me.",
}

PHASE_TWO = {
    "no-answer": "Continue the bootstrap for this product.",
    "unattended-pending": "Resume the generated workflow and carry it to completion. I am still unavailable.",
}

TOPICS = ["target-users", "scenarios", "core-problem", "value-proposition", "business-loop", "tradeoffs"]

GOALS = {
    "target-users": "Serve neighborhood mutual-aid volunteers and requesters",
    "scenarios": "A neighbor posts a supply request and a volunteer fulfils it",
    "core-problem": "Neighbors cannot see which supply requests still need help",
    "value-proposition": "Free coordination for a neighborhood supply network",
    "business-loop": "Charge merchants a monthly subscription for access",
    "tradeoffs": "Reach versus requester privacy",
}


def base_code(root, scene):
    """The shared synthetic product source. Never scenario-specific beyond stated code facts."""
    shutil.copytree(SOURCE / "claude/meta-skill/tests/fixtures/retail-sphere", root, dirs_exist_ok=True)
    put(root, "services/api/requests.py", '''REQUESTS = [
    {"id": "r-1", "requester": "ana", "group": "oakwood", "item": "baby formula", "status": "open"},
    {"id": "r-2", "requester": "boris", "group": "oakwood", "item": "blankets", "status": "filled"},
]

def visible_requests(group):
    """Every volunteer in the group currently sees every request in it."""
    return [row for row in REQUESTS if row["group"] == group]
''')
    put(root, "services/api/billing.py", '''MONTHLY_MERCHANT_FEE = 49

def may_use_service(merchant):
    return merchant["subscription_status"] == "paid"

def renewal_invoice(merchant):
    return {"merchant": merchant["id"], "amount": MONTHLY_MERCHANT_FEE}
''')
    put(root, "services/api/acquisition.py", '''def rank_leads(leads):
    return sorted(leads, key=lambda lead: lead.get("monthly_revenue", 0), reverse=True)

def outreach_segment(lead):
    return "premium" if lead.get("monthly_revenue", 0) > 10000 else "standard"
''')
    put(root, "README.md", "# Neighborhood Supply\nSupply-request coordination service.\n")


def copy_gates(root, host, candidate_root):
    """Copy the candidate's public gate CLIs into the project, as the protocol requires."""
    scripts = root / ".allforai/bootstrap/scripts"
    scripts.mkdir(parents=True, exist_ok=True)
    orchestrator = (candidate_root / ("claude/meta-skill" if host == "claude" else "codex/meta-skill")
                    / "scripts" / "orchestrator")
    top = orchestrator.parent
    for name in ("check_artifacts.py", "validate_bootstrap.py", "validate_unattended_readiness.py",
                 "product_intent.py", "evidence_freshness.py", "reconcile_bootstrap_workflow.py"):
        shutil.copy2(orchestrator / name, scripts / name)
    shutil.copy2(top / "check_decision_inputs.py", scripts / "check_decision_inputs.py")


def invoke(root, request):
    done = subprocess.run([sys.executable, str(root / ".allforai/bootstrap/scripts/product_intent.py"), str(root)],
                          input=json.dumps(request), text=True, capture_output=True, cwd=root)
    if done.returncode != 0:
        raise RuntimeError(f"seeding request {request['operation']} failed: {done.stdout}{done.stderr}")
    return json.loads(done.stdout) if done.stdout.strip() else {}


def draft_request(questions):
    return {"operation": "draft", "route": "product-reconstruction",
            "goal": "Reshape the neighborhood supply service",
            "items": [{"id": topic, "topic": topic, "scope": ["requests"], "goal": GOALS[topic],
                       "business_rules": ["Requests belong to one group"],
                       "acceptance": ["A request is visible to its group"],
                       "origin": "inference",
                       "evidence": [{"path": "services/api/requests.py", "quote": "def visible_requests"}],
                       "uncertainty": "Implementation cannot establish the desired direction"}
                      for topic in TOPICS],
            "facts": [{"path": "services/api/requests.py", "quote": "def visible_requests"},
                      {"path": "services/api/billing.py", "quote": "MONTHLY_MERCHANT_FEE = 49"},
                      {"path": "services/api/acquisition.py", "quote": "def rank_leads"}],
            "questions": questions}


FUNDING_QUESTION = {"id": "funding-choice", "topic": "business-loop",
                    "question": "How will the free service be funded?", "kind": "gap",
                    "depends_on": ["business-loop"]}
VISIBILITY_QUESTION = {"id": "visibility-choice", "topic": "tradeoffs",
                       "question": "Who may see an open supply request?", "kind": "contradiction",
                       "depends_on": ["tradeoffs"]}


def seed(root, scene, host, candidate_root):
    """Persist only the state this scenario would legitimately already have."""
    if scene == "no-answer":
        return {"persisted": "none"}
    copy_gates(root, host, candidate_root)
    if scene == "partial-resume":
        invoke(root, draft_request([FUNDING_QUESTION, VISIBILITY_QUESTION]))
        invoke(root, {"operation": "decide", "batch_id": "settled-1", "topic": "Product direction",
                      "user_reference": "bootstrap user turn 2",
                      "actions": [{"operation": "confirm", "id": topic,
                                   "reason": "Settled with the owner in the first session"}
                                  for topic in ("target-users", "scenarios", "core-problem")]
                                 + [{"operation": "answer", "id": "visibility-choice",
                                     "answer": "Every volunteer in the group may see an open request",
                                     "reason": "Volunteers must find work to do"}]})
        return {"persisted": "three confirmed topics; three topics and the funding question pending"}
    if scene == "unattended-pending":
        invoke(root, draft_request([FUNDING_QUESTION]))
        invoke(root, {"operation": "decide", "batch_id": "settled-1", "topic": "Product direction",
                      "user_reference": "bootstrap user turn 2",
                      "actions": [{"operation": "confirm", "id": topic, "reason": "Settled with the owner"}
                                  for topic in TOPICS if topic != "business-loop"]})
        return {"persisted": "five confirmed topics; business-loop and the funding question pending; no run policy"}
    invoke(root, draft_request([FUNDING_QUESTION]))
    if scene == "reverse-prior-decision":
        invoke(root, {"operation": "decide", "batch_id": "settled-1", "topic": "Product direction",
                      "user_reference": "bootstrap user turn 2",
                      "actions": [{"operation": "confirm", "id": topic, "reason": "Settled with the owner"}
                                  for topic in TOPICS if topic != "business-loop"]
                                 + [{"operation": "adjust", "id": "tradeoffs",
                                     "changes": {"goal": "Every volunteer in the group may see every request"},
                                     "reason": "Volunteers must be able to find work to do"}]})
        return {"persisted": "confirmed visibility decision recorded in the journal"}
    if scene == "removed-not-resurrected":
        invoke(root, {"operation": "decide", "batch_id": "settled-1", "topic": "Product direction",
                      "user_reference": "bootstrap user turn 2",
                      "actions": [{"operation": "confirm", "id": topic, "reason": "Settled with the owner"}
                                  for topic in TOPICS if topic != "business-loop"]
                                 + [{"operation": "remove", "id": "business-loop",
                                     "reason": "Mutual aid must stay free; subscription billing is not wanted"}]})
        return {"persisted": "confirmed removal of the subscription business loop; billing code still present"}
    if scene == "discussion-preserves-source":
        invoke(root, {"operation": "decide", "batch_id": "settled-1", "topic": "Product direction",
                      "user_reference": "bootstrap user turn 2",
                      "actions": [{"operation": "confirm", "id": topic, "reason": "Settled with the owner"}
                                  for topic in ("target-users", "scenarios", "core-problem")]})
        return {"persisted": "three confirmed topics; the funding question pending"}
    if scene == "legacy-provenance":
        invoke(root, {"operation": "decide", "batch_id": "settled-1", "topic": "Product direction",
                      "user_reference": "bootstrap user turn 2",
                      "actions": [{"operation": "confirm", "id": topic,
                                   "reason": "Settled with the owner in an earlier session"}
                                  for topic in ("target-users", "scenarios", "core-problem")]})
        concept_path = root / ".allforai/product-concept/product-concept.json"
        concept = json.loads(concept_path.read_text())
        concept.setdefault("requirements", []).append({
            "id": "legacy-subscription-growth", "revision": 1, "scope": ["billing"],
            "goal": "Maximize recurring merchant subscription revenue",
            "business_rules": ["Rank outreach by monthly revenue"],
            "acceptance": ["Subscription revenue grows month over month"],
            "origin": "inference", "status": "confirmed",
            "evidence": [{"path": "services/api/billing.py", "quote": "MONTHLY_MERCHANT_FEE = 49"}]})
        concept_path.write_text(json.dumps(concept, ensure_ascii=False, indent=2) + "\n")
        return {"persisted": "one journal-backed confirmed set plus one legacy concept entry with no confirmation provenance"}
    raise ValueError(f"unknown scene {scene}")


def prompt(destination, cell, host, scene, request):
    entry = ("claude/meta-skill/skills/bootstrap/SKILL.md" if host == "claude"
             else "codex/meta-skill/SKILL.md")
    return f'''Use this exact candidate for the explicitly requested work: {destination / "candidate" / entry}.
The candidate source root is {destination / "candidate"}; resolve canonical and adapter references there, without installing anything.
Your project is {cell / "project"}. Read only this project's raw materials and candidate skill assets, not other scenario folders, reports, test sources, or evaluator materials.
Follow the candidate entry and its references normally. Do not implement the target product; the requested deliverable is the discussion and the generated planning artifacts.
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
            base_code(cell / "project", scene)
            seeded[f"{host}/{scene}"] = seed(cell / "project", scene, host, destination / "candidate")
            put(cell, "source-before.json", fingerprint(cell / "project"))
            put(cell, "actor-input.md", prompt(destination, cell, host, scene, request))
            if scene in PHASE_TWO:
                put(cell, "actor-input-phase2.md",
                    prompt(destination, cell, host, scene, PHASE_TWO[scene]))
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
    print(json.dumps({"packets": str(destination), "candidate_tree_sha256": manifest["tree_sha256"]},
                     indent=2))


if __name__ == "__main__":
    main()
