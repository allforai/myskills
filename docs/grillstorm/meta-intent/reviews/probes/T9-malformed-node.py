"""Red-capable public CLI regression: malformed nodes must replace prior ready."""
import json
from pathlib import Path
import sys
import tempfile

candidate = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(candidate / "claude/meta-skill/tests"))
from unit.test_bootstrap_scope import project, gate, write

fixture = Path(tempfile.mkdtemp(prefix="t9-malformed-feedback-"))
project(fixture, confirmed=True)
report = fixture / ".allforai/bootstrap/unattended-run-readiness.json"
before = gate(fixture, "validate_unattended_readiness.py", "--write-report")
assert before.returncode == 0 and json.loads(report.read_text())["status"] == "ready"
original = (fixture / ".allforai/bootstrap/workflow.json").read_bytes()
malformed = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {"nodes": [None]}
write(fixture, ".allforai/bootstrap/workflow.json", malformed)
results = []
for name in ("validate_bootstrap.py", "check_decision_inputs.py", "validate_unattended_readiness.py"):
    args = ("--write-report",) if name == "validate_unattended_readiness.py" else ()
    result = gate(fixture, name, *args)
    results.append({"gate": name, "exit": result.returncode,
                    "stdout": result.stdout, "stderr": result.stderr})
stale_ready = json.loads(report.read_text())["status"] == "ready"
(fixture / ".allforai/bootstrap/workflow.json").write_bytes(original)
restored = gate(fixture, "validate_unattended_readiness.py", "--write-report")
passed = (not stale_ready and all(r["exit"] == 1 and r["stdout"] and
          "Traceback" not in r["stderr"] for r in results) and restored.returncode == 0)
print(json.dumps({"fixture": str(fixture), "passed": bool(passed),
                  "prior_ready_retained": stale_ready, "results": results,
                  "restored_exit": restored.returncode}, indent=2))
sys.exit(0 if passed else 1)
