"""Scripted bootstrap artifacts exercised through the generated-project CLI gates.

The agent chooses the route and graph; these tests supply its explicit artifacts,
not a substitute semantic planner. Actual host dialogue proof belongs to T15.

The artifacts here are one product replayed twice: the graph the ink-scent run actually
shipped, which every public gate must refuse, and the graph it should have shipped.
"""
import json
from pathlib import Path
import re

import pytest

from .test_bootstrap_scope import confirm_plan, gate, project, publish_contract, write
from .test_product_intent_session import invoke

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures/consumer-learning-app"
GATES = ("validate_bootstrap.py", "check_decision_inputs.py", "validate_unattended_readiness.py")
PROFILE = ".allforai/bootstrap/bootstrap-profile.json"
READINESS_SPEC = ".allforai/bootstrap/unattended-run-readiness-spec.json"
READINESS_REPORT = ".allforai/bootstrap/unattended-run-readiness.json"
WORKFLOW = ".allforai/bootstrap/workflow.json"
# The three codes the incident is made of: nobody designed the journeys, nobody reviewed
# what was built from them, and the frozen scope never said what living with it feels like.
REFUSED = {"missing_experience_design_node", "missing_experience_gate",
           "ui_product_without_experience_direction"}
DIRECTION = "ui_product_without_experience_direction"
# The local-change seed the shared fixture leaves behind; a new product starts from nothing.
LOCAL_LEFTOVERS = ("orders.py", ".allforai/bootstrap/local-requirements.json")
CODE_LINE = re.compile(r"^\s+- (\w+):")


def _fixture(name):
    return json.loads((FIXTURE / name).read_text(encoding="utf-8"))


def build(root, host, *, dialogue, plan, readiness, force_past_front_door=False):
    """Replay one scripted bootstrap session through the copied CLI; return its workflow.

    `profile.json` sits beside the dialogue and is merged after it, because `draft` and
    `freeze` own `task_route` and `task_scope` and would overwrite anything written first.

    `force_past_front_door` is the whole reason a refused graph can be built at all:
    `plan` runs the scope contract before it writes, so a consumer product without a
    confirmed direction cannot be planned through the public CLI. The refusal is asserted
    first — the front door is closed too — and only then is the classification held back
    for the one call that writes the graph, so the gates judge the graph the incident had.
    """
    project(root, host=host, source_inputs=None)
    for leftover in LOCAL_LEFTOVERS:
        (root / leftover).unlink()
    for request in _fixture(dialogue):
        recorded = invoke(root, request)
        assert recorded.returncode == 0, (request["operation"], recorded.stdout, recorded.stderr)
    profile = json.loads((root / PROFILE).read_text(encoding="utf-8"))
    profile.update(_fixture(str(Path(dialogue).parent / "profile.json")))
    write(root, PROFILE, profile)
    write(root, READINESS_SPEC, _fixture(readiness))

    request = _fixture(plan)
    if force_past_front_door:
        refused = invoke(root, request)
        assert refused.returncode == 1, (refused.stdout, refused.stderr)
        assert DIRECTION in refused.stdout, refused.stdout
        held = dict(profile, experience_priority={
            "mode": "none", "reason": "Held back so the refused graph can be written at all"})
        write(root, PROFILE, held)
    planned = invoke(root, request)
    assert planned.returncode == 0, (planned.stdout, planned.stderr)
    if force_past_front_door:
        write(root, PROFILE, profile)

    confirm_plan(root, stage="plan-projection", reason="Presented the projected plan")
    workflow = json.loads((root / WORKFLOW).read_text(encoding="utf-8"))
    for node in workflow["nodes"]:
        if node.get("source_inputs"):
            publish_contract(root, node["node_id"])
    return workflow


def codes(root):
    """Every blocking code each public gate reports, read from its own output shape.

    One run per gate, and each run's exit status is held to what it reported: a gate that
    names a blocker exits 1 and a gate that names none exits 0, so a non-empty set below
    is a refusal and an empty one is a pass. The three shapes differ because the gates are
    three separate entries, not one renamed: the bootstrap validator prints rendered
    `code: message` errors as JSON, the decision-wiring gate prints an indented list, and
    the readiness entry writes a typed report.
    """
    reported = {}
    for name in GATES:
        options = ("--write-report",) if name == "validate_unattended_readiness.py" else ()
        result = gate(root, name, *options)
        if name == "validate_bootstrap.py":
            found = {error.split(":")[0] for error in json.loads(result.stdout)["errors"]}
        elif name == "check_decision_inputs.py":
            found = {match.group(1) for match in map(CODE_LINE.match, result.stdout.splitlines())
                     if match}
        else:
            report = json.loads((root / READINESS_REPORT).read_text(encoding="utf-8"))
            found = {blocker["code"] for blocker in report["blockers"]}
        assert result.returncode == (1 if found else 0), (name, result.stdout, result.stderr)
        reported[name] = found
    return reported


@pytest.mark.parametrize("host", ["claude", "codex"])
def test_ink_scent_shaped_workflow_is_refused_at_every_public_gate(tmp_path, host):
    """The graph that shipped: screens planned, none designed, none reviewed, no direction."""
    workflow = build(tmp_path, host, dialogue="bad-workflow/dialogue.json",
                     plan="bad-workflow/plan.json", readiness="bad-workflow/readiness-spec.json",
                     force_past_front_door=True)
    reported = codes(tmp_path)
    # codes() ties each gate's exit status to what it reported, so a named blocker is a
    # refusal: all three gates exited 1.
    assert all(reported[name] for name in GATES), reported
    assert REFUSED <= set().union(*reported.values()), reported
    # Only the readiness entry runs the scope contract and the structural gates side by
    # side; the other two stop at the first refusal, which is why the union is the claim.
    assert REFUSED <= reported["validate_unattended_readiness.py"], reported
    assert DIRECTION in reported["check_decision_inputs.py"], reported

    # The fixture's own shape, so a later edit cannot repair the graph into passing.
    assert len(workflow["nodes"]) == 13, [node["node_id"] for node in workflow["nodes"]]
    artifacts = [str(path) for node in workflow["nodes"] for path in node["exit_artifacts"]]
    assert not [path for path in artifacts if path.startswith(".allforai/app-design/")], artifacts
