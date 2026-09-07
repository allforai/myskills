"""Controller diagnostic: journal-backed local requirements at copied public gates."""
import json
from pathlib import Path
import sys
import tempfile

candidate = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(candidate / "claude/meta-skill/tests"))
from unit.test_bootstrap_scope import project, gate, write, REQUIREMENTS

root = Path(tempfile.mkdtemp(prefix="T9-journal-provenance-"))
results = []
for host in ("claude", "codex"):
    fixture = root / host
    requirement = project(fixture, confirmed=True, documents=True, host=host)
    journal_path = ".allforai/product-concept/decision-journal.json"
    write(fixture, journal_path, {"schema_version": "1.0", "batches": [{
        "batch_id": "export-choice", "source": "user_session", "topic": "Order export",
        "decisions": [{"question": "Which orders may be exported?",
                       "chosen": "Only the signed-in account's orders",
                       "rationale": "Account isolation is required", "supersedes": None}]
    }]})
    requirement["confirmation"]["reference"] = journal_path + "#export-choice/decisions/0"
    write(fixture, REQUIREMENTS, {"requirements": [requirement]})
    protected = [fixture / journal_path, fixture / REQUIREMENTS, fixture / "orders.py",
                 fixture / ".allforai/bootstrap/workflow.json"]
    before = {str(p): p.read_bytes() for p in protected}
    for name in ("validate_bootstrap.py", "validate_unattended_readiness.py", "check_decision_inputs.py"):
        result = gate(fixture, name)
        results.append({"host": host, "gate": name, "exit": result.returncode,
                        "stdout": result.stdout, "stderr": result.stderr,
                        "expected_exit": 0,
                        "protected_unchanged": all(p.read_bytes() == before[str(p)] for p in protected)})
passed = all(r["exit"] == r["expected_exit"] and r["protected_unchanged"] for r in results)
print(json.dumps({"candidate": str(candidate), "fixture": str(root), "passed": passed,
                  "results": results}, indent=2))
sys.exit(0 if passed else 1)
