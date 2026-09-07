"""Materialize blind T15 input packets; does not run actors or score behavior."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

SOURCE = Path(__file__).resolve().parents[5]
COMMIT = "88e7becaf30522ef29dd2fa168b62045affcb782"
PRODUCER = "3f66d7acc367cdb39ee12ae10827c8d81298ae0a"
SCENES = {
    "large-code-local-button": "Add an Export CSV button to the merchant orders page. Use the recorded export decisions. Bootstrap the work for this feature.",
    "missing-product-docs": "Bootstrap a change to add an Export CSV button to the merchant orders page.",
    "reshape-business-model": "Bootstrap a redesign of this product direction. I want to replace merchant subscriptions with a free service for neighborhood mutual-aid groups. The old charging model should go. Help me settle the new product direction and plan it.",
    "add-unimplemented-need": "Bootstrap a product update for unreliable connectivity: volunteers must be able to queue supply requests offline and submit them once connectivity returns. There is no offline code yet. Help me establish the direction and plan the work.",
    "deny-inferred-intent": "Bootstrap a review of the product direction inferred from this repository. Show me what you think the product is for so we can decide its future.",
    "interrupted-confirmation": "Bootstrap a redesign of the product for neighborhood mutual-aid groups. I have not decided who can see requests or how we will fund it. Help me settle the direction.",
    "new-product": "Bootstrap a new product for neighborhood mutual-aid groups to coordinate supply requests. There is no implementation. Help me establish the product direction and plan the work.",
}


def put(root, path, value):
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(value if isinstance(value, str) else json.dumps(value, indent=2) + "\n")


def fingerprint(root):
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob("*")) if p.is_file() and not p.is_symlink()}


def candidate(destination):
    paths = subprocess.check_output(["git", "ls-tree", "-r", "--name-only", COMMIT,
        "claude/meta-skill", "codex/meta-skill", "docs/adr"], cwd=SOURCE, text=True).splitlines()
    for path in paths:
        if "/tests/" in path or path.endswith("/tests"):
            continue
        entry = subprocess.check_output(["git", "ls-tree", COMMIT, path], cwd=SOURCE, text=True)
        data = subprocess.check_output(["git", "show", f"{COMMIT}:{path}"], cwd=SOURCE)
        target = destination / path
        target.parent.mkdir(parents=True, exist_ok=True)
        if entry.startswith("120000"):
            target.symlink_to(data.decode())
        else:
            target.write_bytes(data)
    hashes = fingerprint(destination)
    links = {str(p.relative_to(destination)): str(p.readlink())
             for p in sorted(destination.rglob("*")) if p.is_symlink()}
    return {"source_commit": COMMIT, "production_commit": PRODUCER,
            "sha256": hashes, "symlinks": links,
            "tree_sha256": hashlib.sha256(json.dumps({"files": hashes, "links": links},
                sort_keys=True, separators=(",", ":")).encode()).hexdigest()}


def fixture(root, scene):
    if scene == "new-product":
        put(root, "README.md", "# Neighborhood Supply\nEmpty project workspace.\n")
        return
    shutil.copytree(SOURCE / "claude/meta-skill/tests/fixtures/retail-sphere", root,
                    dirs_exist_ok=True)
    put(root, "services/api/orders.py", '''ORDERS = [
    {"id": "a-1", "account": "alice", "status": "open", "total": 12},
    {"id": "b-1", "account": "bob", "status": "open", "total": 24},
    {"id": "a-2", "account": "alice", "status": "archived", "total": 9},
]

def list_orders(account, status=None):
    return [order for order in ORDERS if order["account"] == account
            and (status is None or order["status"] == status)]
''')
    put(root, "apps/merchant-web/app/orders/page.tsx", '''export default function OrdersPage({orders}) {
  return <main><h1>Orders</h1><table><tbody>{orders.map(order =>
    <tr key={order.id}><td>{order.id}</td><td>{order.status}</td><td>{order.total}</td></tr>
  )}</tbody></table></main>;
}
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
    if scene == "deny-inferred-intent":
        put(root, "archive/sales-notes.txt", "Former contractor notes, unreviewed: perhaps maximize high-revenue merchant subscriptions. No owner sign-off recorded.\n")
    if scene == "large-code-local-button":
        # Expand the existing multi-platform retail fixture with unrelated domains.
        for domain in ("warehouse", "shipping", "catalog", "returns", "loyalty", "staff",
                       "tax", "procurement", "inventory", "campaigns", "analytics", "suppliers"):
            for number in range(20):
                put(root, f"services/api/{domain}/records_{number}.py", f'''"""{domain} record storage view {number}."""
def visible_records(records, tenant_id):
    return [row for row in records if row["tenant_id"] == tenant_id]

def active_records(records):
    return [row for row in records if not row.get("archived", False)]

def find_record(records, record_id):
    return next((row for row in records if row["id"] == record_id), None)

def summarize(records):
    return {{"count": len(records), "active": len(active_records(records))}}
''')
        journal = ".allforai/product-concept/decision-journal.json"
        put(root, "history/export-discussion.txt", "Owner, 2026-09-01: Export only the signed-in merchant account. Export the currently filtered order rows; include id, status and total. This prevents cross-account disclosure.\n")
        put(root, journal, {"schema_version": "1.0", "batches": [{"batch_id": "export-choice",
            "source": "user_session", "topic": "Order export", "decisions": [{
                "question": "Which orders and columns can be exported?",
                "chosen": "Only signed-in merchant account, current filters, id/status/total columns",
                "rationale": "Prevent cross-account disclosure", "supersedes": None}]}]})
        put(root, ".allforai/bootstrap/local-requirements.json", {"requirements": [{
            "id": "export", "revision": 1, "scope": ["orders"],
            "goal": "Export the currently filtered merchant orders as CSV",
            "business_rules": ["Only signed-in account orders", "Honor current filters", "Columns: id, status, total"],
            "acceptance": ["Other accounts never appear", "CSV rows match current filters"],
            "status": "confirmed", "confirmation": {"source": "user",
                "reference": journal + "#export-choice/decisions/0", "decision_id": "confirm-export-1",
                "reason": "Prevent cross-account disclosure"}}]})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    destination = args.destination.resolve()
    destination.mkdir(parents=True, exist_ok=False)
    manifest = candidate(destination / "candidate")
    put(destination, "candidate-manifest.json", manifest)
    for host in ("claude", "codex"):
        for scene, request in SCENES.items():
            cell = destination / host / scene
            fixture(cell / "project", scene)
            put(cell, "source-before.json", fingerprint(cell / "project"))
            entry = ("claude/meta-skill/skills/bootstrap/SKILL.md" if host == "claude"
                     else "codex/meta-skill/SKILL.md")
            put(cell, "actor-input.md", f'''Use this exact candidate for the explicitly requested bootstrap: {destination / "candidate" / entry}.
The candidate source root is {destination / "candidate"}; resolve canonical and adapter references there, without installing anything.
Your project is {cell / "project"}. Read only this project's raw materials and candidate skill assets, not other scenario folders, reports, test sources, or evaluator materials.
Follow the candidate entry and its references normally. Do not implement the target product; the requested deliverable is bootstrap discussion and generated planning artifacts.
Record actual loaded entry/reference paths and SHA-256 values with your host and independent session identity in {cell / "receipt.json"}; preserve tool output and the raw dialog in the host transcript. Never invent session identity or successful tool results; report unavailable metadata explicitly.
If you need user input, ask the coordinator through your dispatch ask command and wait. Work only from the delivered user turn, not hypothetical future replies.

User request:
{request}
''')
    print(json.dumps({"packets": str(destination), "candidate_tree_sha256": manifest["tree_sha256"],
                      "cells": 14, "executed": 0}, indent=2))


if __name__ == "__main__":
    main()
