"""Recorded Run Policy at the copied bootstrap/run boundary, no real host proof."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from .test_bootstrap_scope import project, gate
from .test_product_intent_session import invoke
from .test_bootstrap_scope import write

POLICY = {"on_repeated_failure": "continue", "on_needs_iteration": "accept", "on_safety_warning": "halt"}


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
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    host = bin_dir / "codex"
    host.write_text("#!" + sys.executable + "\nfrom pathlib import Path\nimport sys\n"
                    "p=Path('host-calls.txt')\np.write_text((p.read_text() if p.exists() else '') + sys.argv[-1] + '\\n')\n"
                    "print('diagnosis: retry the scoped work')\nsys.exit(1)\n")
    host.chmod(0o755)
    env = dict(os.environ, PATH=str(bin_dir) + os.pathsep + os.environ["PATH"])
    def run():
        return subprocess.run([sys.executable, str(driver), "Deliver export", "1"], cwd=tmp_path,
                              env=env, text=True, capture_output=True)
    blocked = run()
    assert blocked.returncode == 6, (blocked.stdout, blocked.stderr)
    assert not (tmp_path / "host-calls.txt").exists()
    assert invoke(tmp_path, {"operation": "run-policy", "answers": dict(POLICY, on_repeated_failure=choice),
                             "user_reference": "Run entry choice"}).returncode == 0
    result = run()
    assert result.returncode == expected, (result.stdout, result.stderr)
    calls = (tmp_path / "host-calls.txt").read_text()
    assert ("Selected node: deliver-export" in calls) == (choice == "continue")


@pytest.mark.parametrize("choice,expected", [("halt_with_report", 5), ("accept", 0), ("auto_fix_once", 5)])
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
    write(tmp_path, ".allforai/concept-acceptance/acceptance-report.json", {"verdict": "needs_iteration", "gaps": ["CSV labels need improvement"]})
    assert invoke(tmp_path, {"operation": "run-policy", "answers": dict(POLICY, on_needs_iteration=choice),
                             "user_reference": "Run entry"}).returncode == 0
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    host = bin_dir / "codex"
    host.write_text("#!" + sys.executable + "\nfrom pathlib import Path\np=Path('repair-count')\np.write_text(str(int(p.read_text())+1) if p.exists() else '1')\n")
    host.chmod(0o755)
    env = dict(os.environ, PATH=str(bin_dir) + os.pathsep + os.environ["PATH"])
    for _ in range(2):
        result = subprocess.run([sys.executable, str(driver), "Export orders", "1"], cwd=tmp_path,
                                env=env, text=True, capture_output=True)
        assert result.returncode == expected, (result.stdout, result.stderr)
        if choice == "accept":
            assert json.loads(result.stderr)["passed"] is False
            assert json.loads(result.stderr)["done"] is False
    if choice == "auto_fix_once":
        assert (tmp_path / "repair-count").read_text() == "1"
    else:
        assert not (tmp_path / "repair-count").exists()
    if choice == "accept":
        assert "accepted_with_gaps" in (tmp_path / ".allforai/bootstrap/assumed-decisions.json").read_text()
    else:
        assert (tmp_path / ".allforai/concept-acceptance/acceptance-report.md").exists()


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


@pytest.mark.parametrize("event,choice,status,attempts,repaired", [
    ("on_safety_warning", "halt", "needs_diagnosis", 1, False),
    ("on_safety_warning", "continue", "complete", 1, False),
    ("on_needs_iteration", "halt_with_report", "needs_diagnosis", 1, False),
    ("on_needs_iteration", "accept", "accepted_with_gaps", 1, False),
    ("on_needs_iteration", "auto_fix_once", "needs_diagnosis", 2, False),
    ("on_needs_iteration", "auto_fix_once", "iteration_repair_stopped", 2, True),
])
def test_claude_shell_routes_safety_and_iteration_without_committing_unverified_acceptance(tmp_path, event, choice, status, attempts, repaired):
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
 if(opts.label==='export'){count++;return {node_id:'export',outcome:'passed',blocking_findings:[],artifacts_written:[],
  ...(process.argv[4]==='on_safety_warning'?{safety_warnings:['Slow external API']}:{acceptance_verdict:process.argv[5]==='yes'&&count>1?'passed':'needs_iteration'})};}
 if(opts.label==='verify:export')return {node_id:'export',status:'passed',blocking_findings:[]};
 if(opts.label==='commit:export')commits++;
 return {};
};
const pipeline=async(items,...steps)=>Promise.all(items.map(async x=>{for(const step of steps)x=await step(x);return x;}));
(async()=>{const result=await new AsyncFunction('agent','pipeline','log','phase',source)(agent,pipeline,()=>{},()=>{});console.log(JSON.stringify({result,count,commits}));})();
''')
    result = subprocess.run(["node", str(runner), str(shell), sys.executable, event, "yes" if repaired else "no"], cwd=tmp_path, text=True, capture_output=True)
    assert result.returncode == 0, result.stderr
    output = json.loads(result.stdout)
    assert output["result"]["status"] == status
    assert output["count"] == attempts
    assert output["commits"] == (1 if status == "complete" or repaired else 0)


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
    write(tmp_path, ".allforai/bootstrap/run-warnings.json", {"warnings": ["Slow staging API"]})
    assert invoke(tmp_path, {"operation": "run-policy", "answers": dict(POLICY, on_safety_warning=choice), "user_reference": "run entry"}).returncode == 0
    result = subprocess.run([sys.executable, str(driver), "Export orders", "1"], cwd=tmp_path, text=True, capture_output=True)
    assert result.returncode == expected, (result.stdout, result.stderr)
