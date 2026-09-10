"""Recorded Run Policy at the copied bootstrap/run boundary, no real host proof."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from .test_bootstrap_scope import project, gate, publish_contract
from .test_product_intent_session import invoke
from .test_bootstrap_scope import write

POLICY = {"on_repeated_failure": "continue", "on_needs_iteration": "accept", "on_safety_warning": "halt"}
ACCEPTANCE = [sys.executable, "-c",
              "import json; assert json.load(open('.allforai/bootstrap/export-report.json'))['status'] == 'passed'"]


def publish_evidence(root):
    """Stand in for the executor's acceptance publication required by input-freshness.md."""
    return publish_contract(root, kind="evidence", verification_command=ACCEPTANCE)


@pytest.mark.parametrize("host", ["claude", "codex"])
def test_policy_is_collected_once_reused_and_never_confirms_product_requirements(tmp_path, host):
    project(tmp_path, host=host)
    required = invoke(tmp_path, {"operation": "run-policy"})
    assert required.returncode == 1
    assert json.loads(required.stdout)["status"] == "needs_run_policy"
    before = (tmp_path / ".allforai/bootstrap/local-requirements.json").read_bytes()
    saved = invoke(tmp_path, {"operation": "run-policy", "answers": POLICY, "user_reference": "run entry user turn"})
    assert saved.returncode == 0, saved.stdout
    policy_bytes = (tmp_path / ".allforai/bootstrap/run-policy.json").read_bytes()
    resumed = invoke(tmp_path, {"operation": "run-policy"})
    assert resumed.returncode == 0
    assert json.loads(resumed.stdout)["policy"] == POLICY
    assert json.loads(resumed.stdout)["questions"] == []
    for event, action in [("on_repeated_failure", "continue"), ("on_needs_iteration", "accept"), ("on_safety_warning", "halt")]:
        result = invoke(tmp_path, {"operation": "run-event", "event": event})
        assert result.returncode == 0, result.stdout
        assert json.loads(result.stdout)["action"] == action
    assert (tmp_path / ".allforai/bootstrap/run-policy.json").read_bytes() == policy_bytes
    assert (tmp_path / ".allforai/bootstrap/local-requirements.json").read_bytes() == before
    assert not (tmp_path / ".allforai/product-concept/decision-journal.json").exists()
    for name in ("validate_bootstrap.py", "check_decision_inputs.py", "validate_unattended_readiness.py"):
        result = gate(tmp_path, name)
        assert result.returncode == 1 and "pending_requirement" in result.stdout


@pytest.mark.parametrize("choice,expected", [("continue", 2), ("halt", 3)])
def test_generated_driver_requires_policy_and_consumes_repeated_failure_choice(tmp_path, choice, expected):
    project(tmp_path, confirmed=True, host="codex")
    driver = tmp_path / ".allforai/codex/flow.py"
    driver.parent.mkdir(parents=True)
    shutil.copy2(Path(__file__).resolve().parents[4] / "codex/meta-skill/knowledge/flow-template.py", driver)
    path = ".allforai/bootstrap/workflow.json"
    workflow = json.loads((tmp_path / path).read_text())
    workflow["expanders"] = []
    workflow["transition_log"] = [{"node": "deliver-export", "status": "failed", "artifacts_created": []}] * 3
    write(tmp_path, path, workflow)
    # Only the external host process is substituted; the generated driver and all gates are real.
    # The substitute and its call log live outside the project so they are not product source.
    bin_dir = tmp_path.parent / (tmp_path.name + "-host")
    bin_dir.mkdir()
    host = bin_dir / "codex"
    host.write_text("#!" + sys.executable + "\nfrom pathlib import Path\nimport sys\n"
                    "p=Path(__file__).with_name('host-calls.txt')\np.write_text((p.read_text() if p.exists() else '') + sys.argv[-1] + '\\n')\n"
                    "print('diagnosis: retry the scoped work')\nsys.exit(1)\n")
    host.chmod(0o755)
    env = dict(os.environ, PATH=str(bin_dir) + os.pathsep + os.environ["PATH"])
    def run():
        return subprocess.run([sys.executable, str(driver), "Deliver export", "1"], cwd=tmp_path,
                              env=env, text=True, capture_output=True)
    blocked = run()
    assert blocked.returncode == 6, (blocked.stdout, blocked.stderr)
    assert not (bin_dir / "host-calls.txt").exists()
    assert invoke(tmp_path, {"operation": "run-policy", "answers": dict(POLICY, on_repeated_failure=choice),
                             "user_reference": "Run entry choice"}).returncode == 0
    result = run()
    assert result.returncode == expected, (result.stdout, result.stderr)
    calls = (bin_dir / "host-calls.txt").read_text()
    assert ("Selected node: deliver-export" in calls) == (choice == "continue")


# concept-acceptance is a coverage gate (ADR 0008): its report names the behaviour mappings
# without evidence and renders no score or verdict. With no declared repair loop naming the
# gate, auto_fix_once has nothing it may charge: the repair is unauthorized and halts.
MISSING_MAPPINGS = [{"mapping_id": "bm-1", "behaviour": "CSV labels follow the account locale",
                     "expected_evidence": "export fixture in the second locale"}]


@pytest.mark.parametrize("choice,expected", [("halt_with_report", 5), ("accept", 0), ("auto_fix_once", 6)])
@pytest.mark.parametrize("declared", [False, True])
def test_generated_driver_consumes_iteration_policy_without_new_interviews(tmp_path, choice, expected, declared):
    project(tmp_path, confirmed=True, host="codex")
    driver = tmp_path / ".allforai/codex/flow.py"
    driver.parent.mkdir(parents=True)
    shutil.copy2(Path(__file__).resolve().parents[4] / "codex/meta-skill/knowledge/flow-template.py", driver)
    workflow = json.loads((tmp_path / ".allforai/bootstrap/workflow.json").read_text())
    workflow["expanders"] = []
    if declared:
        workflow["nodes"][0]["exit_artifacts"].append(".allforai/concept-acceptance/acceptance-report.json")
        spec_path = tmp_path / ".allforai/bootstrap/node-specs/deliver-export.md"
        body = spec_path.read_text().split("---", 2)[2]
        spec_path.write_text("---\n" + json.dumps(workflow["nodes"][0]) + "\n---" + body)
    write(tmp_path, ".allforai/bootstrap/workflow.json", workflow)
    write(tmp_path, ".allforai/bootstrap/export-report.json", {"status": "passed"})
    write(tmp_path, ".allforai/concept-acceptance/acceptance-report.json",
          {"gate": "concept-acceptance", "missing_mappings": MISSING_MAPPINGS})
    publish_evidence(tmp_path)  # Declared evidence is verified and published before the policy branch is exercised.
    assert invoke(tmp_path, {"operation": "run-policy", "answers": dict(POLICY, on_needs_iteration=choice),
                             "user_reference": "Run entry"}).returncode == 0
    bin_dir = tmp_path.parent / (tmp_path.name + "-host")
    bin_dir.mkdir()
    host = bin_dir / "codex"
    host.write_text("#!" + sys.executable + "\nfrom pathlib import Path\np=Path(__file__).with_name('repair-count')\np.write_text(str(int(p.read_text())+1) if p.exists() else '1')\n")
    host.chmod(0o755)
    env = dict(os.environ, PATH=str(bin_dir) + os.pathsep + os.environ["PATH"])
    for _ in range(2):
        result = subprocess.run([sys.executable, str(driver), "Export orders", "1"], cwd=tmp_path,
                                env=env, text=True, capture_output=True)
        assert result.returncode == expected, (result.stdout, result.stderr)
        if choice == "accept":
            assert json.loads(result.stderr)["passed"] is False
            assert json.loads(result.stderr)["done"] is False
    assert not (bin_dir / "repair-count").exists(), "no repair runs outside a ledger-authorized dispatch"
    if choice == "accept":
        assert "accepted_with_gaps" in (tmp_path / ".allforai/bootstrap/assumed-decisions.json").read_text()
    else:
        summary = (tmp_path / ".allforai/concept-acceptance/acceptance-report.md").read_text()
        assert "bm-1" in summary and "score" not in summary.lower()
    if choice == "auto_fix_once":
        assert "no declared repair loop names the concept-acceptance gate" in result.stderr


def test_generated_driver_refuses_a_scored_acceptance_report_by_name(tmp_path):
    project(tmp_path, confirmed=True, host="codex")
    driver = tmp_path / ".allforai/codex/flow.py"
    driver.parent.mkdir(parents=True)
    shutil.copy2(Path(__file__).resolve().parents[4] / "codex/meta-skill/knowledge/flow-template.py", driver)
    workflow = json.loads((tmp_path / ".allforai/bootstrap/workflow.json").read_text())
    workflow["expanders"] = []
    write(tmp_path, ".allforai/bootstrap/workflow.json", workflow)
    write(tmp_path, ".allforai/bootstrap/export-report.json", {"status": "passed"})
    write(tmp_path, ".allforai/concept-acceptance/acceptance-report.json",
          {"verdict": "pass", "overall_score": 91, "pass_threshold": 80, "missing_mappings": []})
    publish_evidence(tmp_path)
    assert invoke(tmp_path, {"operation": "run-policy", "answers": dict(POLICY, on_needs_iteration="halt_with_report"),
                             "user_reference": "Run entry"}).returncode == 0
    result = subprocess.run([sys.executable, str(driver), "Export orders", "1"], cwd=tmp_path,
                            text=True, capture_output=True)
    assert result.returncode == 5, (result.stdout, result.stderr)
    summary = (tmp_path / ".allforai/concept-acceptance/acceptance-report.md").read_text()
    assert "refused" in summary and "verdict" in summary, "a scored report is not read as either answer"


@pytest.mark.parametrize("choice,count", [("halt", 3), ("continue", 4)])
def test_public_claude_workflow_shell_loads_real_policy_and_routes_retries(tmp_path, choice, count):
    project(tmp_path, confirmed=True)
    shell = Path(__file__).resolve().parents[2] / "knowledge/run-engine/run-engine.workflow.js"
    runner = tmp_path / "shell-test.cjs"
    runner.write_text(r'''
const fs = require('node:fs'); const cp = require('node:child_process');
const source = fs.readFileSync(process.argv[2], 'utf8').replace('export const meta', 'const meta');
const AsyncFunction = Object.getPrototypeOf(async function(){}).constructor;
let count=0;
const agent = async (prompt, opts) => {
 if(opts.label === 'run-policy') {
   const r=cp.spawnSync(process.argv[3], ['.allforai/bootstrap/scripts/product_intent.py', '.', '--run-policy'], {encoding:'utf8'});
   return JSON.parse(r.stdout);
 }
 if(opts.label === 'load-dag') return {nodes:[{node_id:'export',soft_retry_max:2,hard_blocked_by:[],exit_artifacts:[]}],completed:[]};
 if(opts.label === 'export') {count++; return {node_id:'export',outcome:count===4?'passed':'soft_fail',blocking_findings:[],artifacts_written:[]};}
 if(opts.label === 'verify:export') return {node_id:'export',status:'passed',blocking_findings:[]};
 return {};
};
const pipeline=async (items,...steps)=>Promise.all(items.map(async x=>{for(const step of steps)x=await step(x);return x;}));
(async()=>{const result=await new AsyncFunction('agent','pipeline','log','phase',source)(agent,pipeline,()=>{},()=>{});console.log(JSON.stringify({result,count}));})();
''')
    def run():
        result = subprocess.run(["node", str(runner), str(shell), sys.executable], cwd=tmp_path, text=True, capture_output=True)
        assert result.returncode == 0, result.stderr
        return json.loads(result.stdout)
    assert run()["count"] == 0
    assert invoke(tmp_path, {"operation": "run-policy", "answers": dict(POLICY, on_repeated_failure=choice), "user_reference": "run entry"}).returncode == 0
    result = run()
    assert result["count"] == count
    assert result["result"]["status"] == ("complete" if choice == "continue" else "needs_diagnosis")


# The Claude shell reads the gate's missing-mapping list: a named mapping fires the
# recorded policy, an empty list proceeds. With no declared repair loop, auto_fix_once has
# no route it may charge, so nothing is repaired in-node and the run stops. The
# ledger-authorized route itself is covered in run-engine/tests/repair-loop.test.js.
@pytest.mark.parametrize("event,choice,status,attempts,gate", [
    ("on_safety_warning", "halt", "needs_diagnosis", 1, "covered"),
    ("on_safety_warning", "continue", "complete", 1, "covered"),
    ("on_needs_iteration", "halt_with_report", "needs_diagnosis", 1, "named"),
    ("on_needs_iteration", "accept", "accepted_with_gaps", 1, "named"),
    ("on_needs_iteration", "auto_fix_once", "needs_diagnosis", 1, "named"),
    ("on_needs_iteration", "auto_fix_once", "complete", 1, "covered"),
])
def test_claude_shell_routes_safety_and_iteration_without_committing_unverified_acceptance(tmp_path, event, choice, status, attempts, gate):
    project(tmp_path, confirmed=True)
    assert invoke(tmp_path, {"operation": "run-policy", "answers": dict(POLICY, **{event: choice}), "user_reference": "run entry"}).returncode == 0
    shell = Path(__file__).resolve().parents[2] / "knowledge/run-engine/run-engine.workflow.js"
    runner = tmp_path / "events.cjs"
    runner.write_text(r'''
const fs=require('node:fs'),cp=require('node:child_process');
const source=fs.readFileSync(process.argv[2],'utf8').replace('export const meta','const meta');
const AsyncFunction=Object.getPrototypeOf(async function(){}).constructor;
let count=0,commits=0;
const agent=async(prompt,opts)=>{
 if(opts.label==='run-policy'||opts.label==='policy:on_needs_iteration'){
  const args=opts.label==='run-policy'?['--run-policy']:['--policy-event','on_needs_iteration'];
  return JSON.parse(cp.spawnSync(process.argv[3],['.allforai/bootstrap/scripts/product_intent.py','.',...args],{encoding:'utf8'}).stdout);
 }
 if(opts.label==='load-dag')return {nodes:[{node_id:'export',hard_blocked_by:[],exit_artifacts:[]}],completed:[]};
 if(opts.label==='export'){count++;return {node_id:'export',outcome:'passed',blocking_findings:[],artifacts_written:['.allforai/concept-acceptance/acceptance-report.json'],
  ...(process.argv[4]==='on_safety_warning'?{safety_warnings:['Slow external API']}:{}),
  missing_mappings:process.argv[5]==='named'?[{mapping_id:'bm-1',behaviour:'CSV labels follow the account locale'}]:[]};}
 if(opts.label==='verify:export')return {node_id:'export',status:'passed',blocking_findings:[]};
 if(opts.label==='commit:export')commits++;
 return {};
};
const pipeline=async(items,...steps)=>Promise.all(items.map(async x=>{for(const step of steps)x=await step(x);return x;}));
(async()=>{const result=await new AsyncFunction('agent','pipeline','log','phase',source)(agent,pipeline,()=>{},()=>{});console.log(JSON.stringify({result,count,commits}));})();
''')
    result = subprocess.run(["node", str(runner), str(shell), sys.executable, event, gate], cwd=tmp_path, text=True, capture_output=True)
    assert result.returncode == 0, result.stderr
    output = json.loads(result.stdout)
    assert output["result"]["status"] == status
    assert output["count"] == attempts, "no in-node repair reruns the gate outside a ledger-authorized dispatch"
    assert output["commits"] == (1 if status == "complete" else 0)


@pytest.mark.parametrize("choice,expected", [("halt", 4), ("continue", 0)])
def test_codex_driver_consumes_recorded_nonblocking_safety_warning(tmp_path, choice, expected):
    project(tmp_path, confirmed=True, host="codex")
    driver = tmp_path / ".allforai/codex/flow.py"
    driver.parent.mkdir(parents=True)
    shutil.copy2(Path(__file__).resolve().parents[4] / "codex/meta-skill/knowledge/flow-template.py", driver)
    workflow = json.loads((tmp_path / ".allforai/bootstrap/workflow.json").read_text())
    workflow["expanders"] = []
    write(tmp_path, ".allforai/bootstrap/workflow.json", workflow)
    write(tmp_path, ".allforai/bootstrap/export-report.json", {"status": "passed"})
    publish_evidence(tmp_path)
    write(tmp_path, ".allforai/bootstrap/run-warnings.json", {"warnings": ["Slow staging API"]})
    assert invoke(tmp_path, {"operation": "run-policy", "answers": dict(POLICY, on_safety_warning=choice), "user_reference": "run entry"}).returncode == 0
    result = subprocess.run([sys.executable, str(driver), "Export orders", "1"], cwd=tmp_path, text=True, capture_output=True)
    assert result.returncode == expected, (result.stdout, result.stderr)
