"""Independent controller probe at the copied bootstrap CLI seam."""
import json
from pathlib import Path
import sys
import tempfile

candidate = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(candidate / "claude/meta-skill/tests"))
from unit.test_bootstrap_scope import project, gate, write, ATTENTION_CONTRACT_BODY

root = Path(tempfile.mkdtemp(prefix="meta-intent-t9-unscoped-"))
project(root, confirmed=True)
workflow_path = root / ".allforai/bootstrap/workflow.json"
workflow = json.loads(workflow_path.read_text())
unrelated = {
    "node_id": "replace-warehouse", "goal": "Replace the unrelated warehouse workflow",
    "capability": "implement", "exit_artifacts": [".allforai/warehouse/report.json"],
}
workflow["nodes"].append(unrelated)
write(root, ".allforai/bootstrap/workflow.json", workflow)
(root / ".allforai/bootstrap/node-specs/replace-warehouse.md").write_text(
    "---\n" + json.dumps(unrelated) + "\n---\n" + ATTENTION_CONTRACT_BODY)
results = []
for name in ("validate_bootstrap.py", "validate_unattended_readiness.py", "check_decision_inputs.py"):
    result = gate(root, name)
    results.append({"command": [str(root / ".allforai/bootstrap/scripts" / name)],
                    "exit_code": result.returncode, "stdout": result.stdout, "stderr": result.stderr})
print(json.dumps({"fixture": str(root), "expected": "new work without any scoped requirement is rejected",
                  "unscoped_work_accepted": all(r["exit_code"] == 0 for r in results),
                  "results": results}, indent=2))
