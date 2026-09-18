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
# The two codes that stay when the direction question is answered: choosing what the
# product should feel like is not designing it, and neither is reviewing what was built.
DESIGNLESS = {"missing_experience_design_node", "missing_experience_gate"}
# The local-change seed the shared fixture leaves behind; a new product starts from nothing.
LOCAL_LEFTOVERS = ("orders.py", ".allforai/bootstrap/local-requirements.json")
CODE_LINE = re.compile(r"^\s+- (\w+):")
BASELINE = ".allforai/product-concept/concept-baseline.json"
EXPERIENCE_TOPIC = "experience-direction"
# The direction the good dialogue's `select` turns into an intent of its own.
CHOSEN = EXPERIENCE_TOPIC + "-steady-drip"


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

    `plan` is a fixture path, or the request itself when a case replays a stored graph with
    one field changed — the second case below crosses one dialogue with the other's plan.
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

    request = plan if isinstance(plan, dict) else _fixture(plan)
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
    is a refusal and an empty one is a pass. The statuses are returned beside the codes so
    each case states the exit it expects of each gate instead of inferring it. The three
    shapes differ because the gates are three separate entries, not one renamed: the
    bootstrap validator prints rendered `code: message` errors as JSON, the decision-wiring
    gate prints an indented list, and the readiness entry writes a typed report.

    A verdict is output, not a fault: all three gates print a refusal on stdout exactly as
    they print a pass, so stderr stays empty on every run here, refused or not. Anything
    on it is a traceback or a warning, and either one is a defect in the gate.
    """
    reported, exits = {}, {}
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
        assert not result.stderr, (name, result.stderr)
        reported[name] = found
        exits[name] = result.returncode
    return reported, exits


@pytest.mark.parametrize("host", ["claude", "codex"])
def test_ink_scent_shaped_workflow_is_refused_at_every_public_gate(tmp_path, host):
    """The graph that shipped: screens planned, none designed, none reviewed, no direction."""
    workflow = build(tmp_path, host, dialogue="bad-workflow/dialogue.json",
                     plan="bad-workflow/plan.json", readiness="bad-workflow/readiness-spec.json",
                     force_past_front_door=True)
    reported, exits = codes(tmp_path)
    # Refused three times over: each gate exits 1, and each names what it refused.
    assert exits == {"validate_bootstrap.py": 1, "check_decision_inputs.py": 1,
                     "validate_unattended_readiness.py": 1}, exits
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


@pytest.mark.parametrize("host", ["claude", "codex"])
def test_chosen_direction_does_not_excuse_a_graph_without_design_or_gate(tmp_path, host):
    """Choosing a direction answers the scope question, and leaves the graph as it was.

    A clean scope is what makes this case worth having: the front door opens, so nothing
    short-circuits and `validate_bootstrap.py` reaches the cross-node rules on its own
    rather than reporting the scope fault and stopping. The direction reaches every node
    because the stage law holds per frozen intent — a new intent consumed only by the
    nodes that build screens would leave the product, technical, documentation and
    verification stages uncovered, and `plan` would refuse the graph for the wrong reason.
    """
    request = _fixture("bad-workflow/plan.json")
    for node in request["nodes"]:
        node["intent_ids"].append(CHOSEN)
        # A new product has no code to read yet, and saying so is a declaration: without it
        # the validator stops at the shape rule and never reaches the graph it is here for.
        node["source_inputs"] = []
    workflow = build(tmp_path, host, dialogue="good-workflow/dialogue.json", plan=request,
                     readiness="bad-workflow/readiness-spec.json")
    assert [node["node_id"] for node in workflow["nodes"]] == [
        node["node_id"] for node in request["nodes"]]

    reported, exits = codes(tmp_path)
    # The decision-wiring gate has nothing left to ask, so it passes; the two that read the
    # graph still refuse it.
    assert exits == {"validate_bootstrap.py": 1, "check_decision_inputs.py": 0,
                     "validate_unattended_readiness.py": 1}, exits
    assert DIRECTION not in set().union(*reported.values()), reported
    assert DESIGNLESS <= reported["validate_bootstrap.py"], reported


@pytest.mark.parametrize("host", ["claude", "codex"])
def test_designed_and_gated_workflow_passes_every_public_gate(tmp_path, host):
    """The graph it should have shipped: the gates are a shape, not a blanket refusal."""
    workflow = build(tmp_path, host, dialogue="good-workflow/dialogue.json",
                     plan="good-workflow/plan.json",
                     readiness="good-workflow/readiness-spec.json")
    artifacts = {str(path) for node in workflow["nodes"] for path in node["exit_artifacts"]}
    assert {".allforai/app-design/spec/user-flow-spec.json",
            ".allforai/app-design/spec/screen-requirements-spec.json",
            ".allforai/app-design/qa/experience-quality-critique-design.json",
            ".allforai/app-design/qa/experience-quality-critique-runtime.json"} <= artifacts

    # The user picked one of the model's three offers, so the frozen scope carries exactly
    # one direction, and it is the model's proposal rather than a topic the user typed.
    frozen = json.loads((tmp_path / BASELINE).read_text(encoding="utf-8"))["intent_baseline"]
    chosen = [intent for intent in frozen["intents"] if intent["topic"] == EXPERIENCE_TOPIC]
    assert [intent["id"] for intent in chosen] == [CHOSEN], frozen["intents"]
    assert chosen[0]["origin"] == "model-proposal", chosen[0]

    reported, exits = codes(tmp_path)
    assert exits == {"validate_bootstrap.py": 0, "check_decision_inputs.py": 0,
                     "validate_unattended_readiness.py": 0}, exits
    assert not any(reported.values()), reported
    report = json.loads((tmp_path / READINESS_REPORT).read_text(encoding="utf-8"))
    assert report["status"] == "ready", report

    # A gate reads the project and says what it found; asked again, without the report
    # written on request above, it leaves every byte of the project as it was and says
    # nothing on stderr either.
    before = {path: path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()}
    for name in GATES:
        result = gate(tmp_path, name)
        assert result.returncode == 0, (name, result.stdout, result.stderr)
        assert not result.stderr, (name, result.stderr)
    after = {path: path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()}
    assert after == before
