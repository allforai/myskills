"""Shared validation of explicit bootstrap scope; never infers user decisions."""
from pathlib import Path
import json
from typing import Any


def validate_scope(project_root, workflow, *, consumed_sources=None):
    """Return typed blockers for the scope consumed by a generated workflow.

    Profiles without the scope contract remain legacy inputs. Their existence is
    not evidence of approval; bootstrap must capture scope before generating new work.
    If supplied, consumed_sources collects journal paths reached through scoped
    requirements; callers may use them only when the returned blockers are empty.
    """
    root = Path(project_root)
    path = root / ".allforai/bootstrap/bootstrap-profile.json"
    try:
        if not isinstance(workflow, dict):
            raise ValueError("workflow.json must be an object")
        nodes = workflow.get("nodes", [])
        if not isinstance(nodes, list):
            raise ValueError("workflow.json nodes must be a list")
        if any(not isinstance(node, dict) for node in nodes):
            raise ValueError("workflow.json nodes must contain objects")
        for node in nodes:
            inputs = node.get("decision_inputs", [])
            if not isinstance(inputs, list) or any(
                    not isinstance(value, str) or not value.strip() for value in inputs):
                raise ValueError("decision_inputs must be an array of non-empty paths, including retained nodes")
        history = workflow.get("transition_log", [])
        if not isinstance(history, list):
            raise ValueError("workflow.json transition_log must be a list")
        for index, event in enumerate(history):
            if not isinstance(event, dict):
                raise ValueError(f"transition_log[{index}] must be an object")
            node_id = event.get("node_id", event.get("node"))
            if not isinstance(node_id, str) or not node_id.strip():
                raise ValueError(f"transition_log[{index}] needs a non-empty node_id or node")
            if "node_id" in event and "node" in event and event["node"] != node_id:
                raise ValueError(f"transition_log[{index}] has conflicting node_id and node")
            if not isinstance(event.get("status"), str) or not event["status"].strip():
                raise ValueError(f"transition_log[{index}] needs a non-empty status")
        scoped_nodes = any("requirement_refs" in node for node in nodes)
        if not path.exists():
            return ([{"code": "invalid_scope", "message": "Scoped nodes require bootstrap-profile.json"}]
                    if scoped_nodes else [])
        profile = json.loads(path.read_text(encoding="utf-8"))
        scope = profile.get("task_scope")
        if "task_scope" not in profile and "task_route" not in profile:
            if scoped_nodes:
                raise ValueError("Scoped nodes require task_route and task_scope")
            return []
        if profile.get("task_route") not in (
                "local-change", "product-reconstruction", "new-product"):
            return [{"code": "pending_task_route", "message":
                     "Clarify the user's goal at interactive bootstrap; file presence cannot choose the route"}]
        if not isinstance(profile.get("task_goal"), str) or not profile["task_goal"].strip():
            raise ValueError("task_goal must be a non-empty user goal")
        if (not isinstance(scope, dict) or not isinstance(scope.get("areas"), list)
                or not scope["areas"] or any(not isinstance(area, str) or not area.strip()
                                             for area in scope["areas"])
                or not isinstance(scope.get("requirement_refs"), list)):
            raise ValueError("task_scope needs non-empty areas and a requirement_refs array")
        for ref in scope["requirement_refs"]:
            if (not isinstance(ref, dict)
                    or any(not isinstance(ref.get(key), str) or not ref[key].strip()
                           for key in ("path", "id"))
                    or type(ref.get("revision")) is not int or ref["revision"] < 1):
                raise ValueError("requirement_refs need path, id and a positive integer revision")
            requirement_path = Path(ref["path"])
            if (requirement_path.is_absolute()
                    or not (root / requirement_path).resolve().is_relative_to(root.resolve())):
                raise ValueError("requirement paths must stay inside the project")
        # A retained completed branch is historical work, not approval for this
        # request. Reconciliation still owns whether its evidence is reusable.
        # Claude records node_id; the native Codex producer records node.
        # Fold both histories together in log order so reopened work is not retained.
        retained = _retained_nodes(workflow, scope["requirement_refs"])
        blockers = []
        if profile.get("intent_session_path") == LOCAL and scope["requirement_refs"]:
            blockers.extend(_local_contract(root, workflow, profile, retained=retained))
        if profile["task_route"] in ("product-reconstruction", "new-product") and scope["requirement_refs"]:
            blockers.extend(_product_contract(root, workflow, profile, retained=retained))
        if profile["task_route"] != "product-reconstruction":
            for node in workflow.get("nodes", []):
                if node.get("capability") == "reverse-concept" and node.get("node_id") not in retained:
                    blockers.append({"code": "scope_route_conflict", "node_id": node.get("node_id"),
                                     "message": "reverse-concept requires a product-reconstruction goal"})
        if not scope.get("requirement_refs"):
            code = ("pending_requirement" if profile["task_route"] == "local-change"
                    else "pending_product_confirmation")
            blockers.append({"code": code, "message": "No confirmed requirements in the selected scope; return to bootstrap"})
        for ref in scope.get("requirement_refs", []):
            data = json.loads((root / ref["path"]).read_text(encoding="utf-8"))
            related = [item for item in data["requirements"] if item["id"] == ref["id"]]
            revisions = [item["revision"] for item in related]
            consumers = _consumers(workflow, ref)
            if any(type(revision) is not int or revision < 1 for revision in revisions):
                raise ValueError(f"{ref['id']}: invalid requirement revision")
            if not revisions or max(revisions) != ref["revision"]:
                _scoped(blockers, "stale_requirement",
                        f"{ref['id']}: reference does not select the current requirement revision", consumers)
                continue
            if len(revisions) != len(set(revisions)):
                _scoped(blockers, "invalid_requirement", f"{ref['id']}: duplicate requirement revisions", consumers)
                continue
            for item in related:
                if item["id"] == ref["id"] and item["revision"] == ref["revision"]:
                    if (not isinstance(item.get("goal"), str) or not item["goal"].strip()
                            or any(not isinstance(item.get(key), list) or not item[key]
                                   or any(not isinstance(value, str) or not value.strip()
                                          for value in item[key])
                                   for key in ("business_rules", "acceptance", "scope"))):
                        _scoped(blockers, "invalid_requirement",
                                f"{ref['id']}: goal, scope, business_rules and acceptance must be non-empty", consumers)
                    if not set(item.get("scope", [])).intersection(scope.get("areas", [])):
                        _scoped(blockers, "requirement_scope_conflict",
                                f"{ref['id']}: confirmed decision does not apply to this task scope", consumers)
                    confirmation = item.get("confirmation") or {}
                    if (item.get("status") != "confirmed"
                            or confirmation.get("source") != "user"
                            or any(not isinstance(confirmation.get(key), str)
                                   or not confirmation[key].strip()
                                   for key in ("reference", "decision_id", "reason"))):
                        _scoped(blockers, "pending_requirement",
                                f"{ref['id']}: return to interactive bootstrap for confirmation", consumers)
                    else:
                        source, separator, fragment = confirmation["reference"].partition("#")
                        if Path(source).name == "decision-journal.json":
                            if (Path(source).is_absolute() or not separator
                                    or not (root / source).resolve().is_relative_to(root.resolve())):
                                raise ValueError("Journal reference needs a project-local path and decision fragment")
                            journal = json.loads((root / source).read_text(encoding="utf-8"))
                            if journal.get("schema_version") != "1.0" or not isinstance(journal.get("batches"), list):
                                raise ValueError("Journal must use schema 1.0 batches")
                            batch_id, marker, index = fragment.split("/")
                            batches = [batch for batch in journal["batches"]
                                       if batch["batch_id"] == batch_id]
                            if marker != "decisions" or len(batches) != 1:
                                raise ValueError("Journal reference must select one decision")
                            batch = batches[0]
                            if (batch.get("source") != "user_session"
                                    or batch.get("status", "confirmed") != "confirmed"
                                    or not isinstance(batch.get("decisions"), list)):
                                raise ValueError("Journal reference needs a confirmed user-session batch")
                            if not index.isdecimal() or int(index) >= len(batch["decisions"]):
                                raise ValueError("Journal decision index is invalid")
                            decision = batch["decisions"][int(index)]
                            if (decision.get("status", "confirmed") != "confirmed"
                                    or any(not isinstance(decision.get(key), str) or not decision[key].strip()
                                           for key in ("question", "chosen"))):
                                raise ValueError("Journal reference needs an explicit user choice")
                            for recorded_batch in journal["batches"]:
                                for recorded in recorded_batch["decisions"]:
                                    if recorded.get("supersedes") in (
                                            fragment, confirmation["reference"]):
                                        raise ValueError("Journal decision was superseded; reconfirm the current requirement")
                            if consumed_sources is not None:
                                consumed_sources.add(source)
        for node in workflow.get("nodes", []):
            if node.get("node_id") in retained:
                continue
            refs = node.get("requirement_refs")
            if not isinstance(refs, list) or not refs:
                blockers.append({"code": "scope_requirement_unwired", "node_id": node.get("node_id"),
                                 "message": f"{node.get('node_id')}: new scoped work needs non-empty requirement_refs"})
                continue
            for ref in refs:
                if ref not in scope["requirement_refs"] or ref["path"] not in node.get("decision_inputs", []):
                    blockers.append({"code": "scope_requirement_unwired", "node_id": node.get("node_id"),
                                     "message": "Node requirement must be in task_scope and consumed through decision_inputs"})
        if profile["task_route"] == "local-change":
            for ref in scope.get("requirement_refs", []):
                responsibilities = set()
                for node in workflow.get("nodes", []):
                    if ref in node.get("requirement_refs", []):
                        responsibilities.update(node.get("responsibilities", []))
                missing = {"implementation", "documentation", "verification"} - responsibilities
                if missing:
                    blockers.append({"code": "missing_scope_responsibility", "message":
                                     f"{ref['id']}: missing {', '.join(sorted(missing))} responsibility"})
        return blockers
    except (OSError, ValueError, TypeError, KeyError, AttributeError, IndexError) as exc:
        return [{"code": "invalid_scope", "message": f"{path}: {exc}"}]


CONCEPT = ".allforai/product-concept/product-concept.json"
JOURNAL = ".allforai/product-concept/decision-journal.json"
BASELINE = ".allforai/product-concept/concept-baseline.json"
PROFILE = ".allforai/bootstrap/bootstrap-profile.json"
LOCAL = ".allforai/bootstrap/local-requirements.json"
TOPICS = ("target-users", "scenarios", "core-problem", "value-proposition", "business-loop", "tradeoffs")
RUN_POLICY = ".allforai/bootstrap/run-policy.json"
RUN_POLICY_REPAIRS = ".allforai/bootstrap/run-policy-repairs.json"
POLICY_OPTIONS = {
    "on_repeated_failure": ["continue", "halt"],
    "on_needs_iteration": ["halt_with_report", "auto_fix_once", "accept"],
    "on_safety_warning": ["continue", "halt"],
}


def _policy_invalid(policy):
    return not isinstance(policy, dict) or any(policy.get(k) not in options for k, options in POLICY_OPTIONS.items())


def _recorded_policy(root):
    """Return (policy, previous content, problem); an unusable file is reported, never trusted."""
    target = root / RUN_POLICY
    if not target.exists():
        return None, None, None
    previous = target.read_text(encoding="utf-8")
    try:
        policy = json.loads(previous)
    except ValueError as exc:
        return None, previous, f"Recorded Run Policy is not JSON: {exc}"
    if _policy_invalid(policy):
        return None, policy, "Recorded Run Policy has missing or unknown choices"
    return policy, policy, None


def run_policy(root, request):
    """Run choices are separate from the product journal and never approve intent.

    Only the interactive run entry collects or repairs a policy, with explicit
    answers and an actual user reference. A repair records the invalid prior
    content in an audit file; unattended events never rewrite the policy.
    """
    policy, previous, problem = _recorded_policy(root)
    if policy is None:
        if request["operation"] != "run-policy":
            if problem:
                raise ValueError(f"Invalid Run Policy; repair it at the interactive entry without guessing answers ({problem})")
            if "answers" in request:
                raise ValueError("Run events consume a recorded Run Policy; they never collect or repair one")
        if "answers" not in request:
            result = {"status": "needs_run_policy", "questions": POLICY_OPTIONS,
                      "return_to": "interactive run entry before the first node"}
            if problem:
                result["invalid_policy"] = f"{problem}; repair it at the interactive entry without guessing answers"
            return result
        if not _text(request.get("user_reference")):
            raise ValueError("Run Policy requires an actual user response")
        policy = request["answers"]
        if _policy_invalid(policy):
            raise ValueError("Invalid Run Policy; repair it at the interactive entry without guessing answers")
        if problem:
            repairs = _read(root, RUN_POLICY_REPAIRS, [])
            if not isinstance(repairs, list):
                raise ValueError("Run Policy repair audit must stay a list")
            repairs.append({"previous": previous, "reason": problem, "answers": policy,
                            "user_reference": request["user_reference"]})
            _write(root, RUN_POLICY_REPAIRS, repairs)
        _write(root, RUN_POLICY, policy)
    if request["operation"] == "run-event":
        event = request["event"]
        if event not in POLICY_OPTIONS:
            raise ValueError("Unknown run event requires a report, never a new unattended interview")
        action = policy[event]
        if event == "on_needs_iteration" and action == "auto_fix_once" and request.get("consume") is True:
            state_path = ".allforai/bootstrap/run-policy-state.json"
            state = _read(root, state_path, {})
            if state.get("iteration_policy_consumed"):
                action = "halt_with_report"
            else:
                state["iteration_policy_consumed"] = True
                _write(root, state_path, state)
        return {"status": "policy_action", "event": event, "action": action, "questions": []}
    return {"status": "run_policy_ready", "policy": policy, "questions": []}


def _read(root, path, default=None):
    target = root / path
    return json.loads(target.read_text(encoding="utf-8")) if target.exists() else default


def _write(root, path, data):
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _text(value):
    return isinstance(value, str) and bool(value.strip())


def _item(item):
    if not isinstance(item, dict) or any(not _text(item.get(key)) for key in ("id", "goal", "topic")):
        raise ValueError("Intent needs id, topic and goal")
    for key in ("scope", "business_rules", "acceptance"):
        if not isinstance(item.get(key), list) or not item[key] or not all(_text(v) for v in item[key]):
            raise ValueError(f"Intent needs non-empty {key}")


def _latest(concept):
    latest: dict[str, Any] = {}
    for item in concept.get("requirements", []):
        if item["id"] not in latest or latest[item["id"]]["revision"] < item["revision"]:
            latest[item["id"]] = item
    return latest


def _confirmed(root, item, *, statuses=("confirmed",)):
    """Product projections must equal the journal's explicit decision payload."""
    reference = item.get("confirmation", {}).get("reference", "")
    source, separator, fragment = reference.partition("#")
    if source != JOURNAL or not separator:
        raise ValueError("Product confirmation needs canonical journal provenance")
    batch_id, marker, index = fragment.split("/")
    journal = _read(root, JOURNAL, {})
    matches = [b for b in journal["batches"] if b["batch_id"] == batch_id]
    if journal["schema_version"] != "1.0" or len(matches) != 1 or marker != "decisions" or not index.isdecimal():
        raise ValueError("Invalid product journal reference")
    batch = matches[0]
    decision = batch["decisions"][int(index)]
    confirmation = item.get("confirmation", {})
    # Legacy schema-1.0 choices have no intent payload. The recorded choice and
    # rationale evidence the goal only; scope, business rules and acceptance are
    # still the model's projection until the user confirms them explicitly.
    matches_payload = (decision["intent"] == item if "intent" in decision else
                       decision.get("chosen") == item.get("goal")
                       and decision.get("rationale") == confirmation.get("reason")
                       and _text(decision.get("rationale")))
    if (batch.get("source") != "user_session" or batch.get("status", "confirmed") != "confirmed"
            or decision.get("status", "confirmed") != "confirmed" or not matches_payload
            or item.get("status") not in statuses or confirmation.get("source") != "user"
            or not _text(confirmation.get("decision_id")) or not _text(confirmation.get("reason"))):
        raise ValueError("Product projection differs from confirmed journal decision")
    if any(d.get("supersedes") in (fragment, reference) for b in journal["batches"] for d in b["decisions"]):
        raise ValueError("Product decision is superseded")
    if "intent" not in decision:
        raise LegacyProjection(reference)


class LegacyProjection(ValueError):
    """A journal choice evidences the goal only; the remaining projection needs the user."""

    EVIDENCED = ["goal"]
    UNCONFIRMED = ["scope", "business_rules", "acceptance"]

    def __init__(self, reference):
        self.reference = reference
        super().__init__("Legacy journal choice evidences the goal only; confirm scope, business_rules and "
                         "acceptance at interactive bootstrap")

    def expose(self, item):
        item["status"] = "pending"
        item["pending_reason"] = str(self)
        item["legacy_reuse"] = {"reference": self.reference, "evidenced": list(self.EVIDENCED),
                                "unconfirmed": list(self.UNCONFIRMED)}


def _consumers(workflow, ref):
    """Current nodes that consume one scoped requirement reference."""
    return [node.get("node_id") for node in workflow.get("nodes", []) if ref in node.get("requirement_refs", [])]


def _scoped(blockers, code, message, node_ids):
    """Bind a requirement blocker to its consumers so unrelated work stays executable.

    A requirement nobody consumes still blocks globally; silence is not approval.
    """
    if not node_ids:
        blockers.append({"code": code, "message": message})
    for node_id in node_ids:
        blockers.append({"code": code, "node_id": node_id, "message": f"{node_id}: {message}"})


def _reuse_legacy_choice(root, item):
    """Keep a confirmed legacy intent only when its journal choice verifies; else it is pending."""
    revision = item.setdefault("revision", 1)
    if type(revision) is not int or revision < 1:
        raise ValueError("Legacy intent revision must be a positive integer")
    try:
        _confirmed(root, item)
    except LegacyProjection as exc:
        exc.expose(item)
    except (OSError, ValueError, TypeError, KeyError, AttributeError, IndexError):
        item["status"] = "pending"
        item["pending_reason"] = "Legacy intent needs user verification"


def _retained_nodes(workflow, refs):
    """Consume reconciled history, folding both native formats in log order."""
    last_status = {event.get("node_id", event.get("node")): event.get("status")
                   for event in workflow.get("transition_log", [])}
    return {node.get("node_id") for node in workflow.get("nodes", [])
            if last_status.get(node.get("node_id")) == "completed"
            and not any(ref in refs for ref in node.get("requirement_refs", []))}


def _product_contract(root, workflow, profile, *, retained=()):
    """Verify the frozen product scope; bind per-intent drift to the nodes that consume it.

    Freeze-level problems (provenance, scope, workflow baseline, plan shape) raise and
    block globally. One reopened, adjusted, removed or unverifiable intent, or an
    unresolved decision it depends on, returns blockers only for its consumers.
    """
    concept = _read(root, CONCEPT)
    _validate_question_ids(concept)
    baseline = _read(root, BASELINE, {}).get("intent_baseline")
    if not isinstance(baseline, dict):
        raise ValueError("Product work needs a frozen product baseline")
    source, fragment = baseline["confirmation"].split("#")
    batch_id, marker, index = fragment.split("/")
    journal = _read(root, JOURNAL)
    matches = [b for b in journal["batches"] if b["batch_id"] == batch_id]
    if (source != JOURNAL or marker != "decisions" or not index.isdecimal() or len(matches) != 1
            or journal.get("schema_version") != "1.0"):
        raise ValueError("Product scope has invalid journal provenance")
    batch = matches[0]
    decision = batch["decisions"][int(index)]
    if (batch.get("source") != "user_session" or not _text(batch.get("user_reference"))
            or batch.get("status", "confirmed") != "confirmed" or decision.get("status", "confirmed") != "confirmed"
            or decision.get("baseline") != baseline
            or any(d.get("supersedes") in (fragment, baseline["confirmation"])
                   for b in journal["batches"] for d in b["decisions"])):
        raise ValueError("Product baseline differs from confirmed scope")
    refs = baseline["requirement_refs"]
    if refs != profile["task_scope"]["requirement_refs"]:
        raise ValueError("Product task scope differs from frozen baseline")
    frozen = baseline.get("intents")
    if not isinstance(frozen, list) or len(frozen) != len(refs):
        raise ValueError("Product baseline intents must match its requirement refs")
    if workflow.get("product_baseline") != baseline:
        raise ValueError("Product workflow must consume current frozen baseline")
    stages = {"product", "experience", "technical", "implementation", "documentation", "verification"}
    omitted = workflow.get("not_applicable", {})
    if not isinstance(omitted, dict) or set(omitted) - {"experience", "technical"} or not all(_text(v) for v in omitted.values()):
        raise ValueError("Product stage applicability needs explicit planning reasons")
    for ref in refs:
        consumers = [n for n in workflow["nodes"] if ref in n.get("requirement_refs", [])]
        covered = {r for n in consumers for r in n.get("responsibilities", [])}
        if stages - covered - omitted.keys():
            raise ValueError("Product plan lacks applicable full-process responsibilities")
    return _intent_drift(root, workflow, concept, refs, frozen, label="Product", path=CONCEPT, retained=retained)


def _local_contract(root, workflow, profile, *, retained=()):
    """Verify the frozen local scope; bind per-intent drift to the nodes that consume it.

    The same two levels as the product route: unverifiable journal provenance of the
    frozen scope, a task scope differing from the frozen refs, or a malformed scope
    raise and block globally; one reopened, adjusted or unverifiable local intent, or
    an unresolved decision it depends on, returns blockers only for its consumers.
    """
    local = _read(root, LOCAL)
    _validate_question_ids(local)
    _discussion(root, local)  # Verify the journal-backed frozen local scope.
    baseline = profile["intent_scope"]
    refs = baseline["requirement_refs"]
    if refs != profile["task_scope"]["requirement_refs"]:
        raise ValueError("Local task scope differs from the frozen scope")
    frozen = baseline.get("intents")
    if not isinstance(frozen, list) or len(frozen) != len(refs):
        raise ValueError("Local scope intents must match its requirement refs")
    return _intent_drift(root, workflow, local, refs, frozen, label="Local", path=LOCAL, retained=retained)


def _intent_drift(root, workflow, concept, refs, frozen, *, label, path, retained=()):
    """Bind each frozen intent's drift to the current nodes that consume it.

    A reopened intent (latest revision pending) is pending work; an adjusted, removed,
    restored or silently changed one is stale; a journal choice that no longer verifies
    is pending with its reason; a pending question an intent depends on names the
    unresolved decision. Node projections are then checked against the confirmed
    intent so unrelated nodes keep their validity.
    """
    latest = _latest(concept)
    blockers: list[dict] = []
    drifted = set()
    for ref, intent in zip(refs, frozen):
        item = latest.get(ref["id"])
        consumers = _consumers(workflow, ref)
        if item is None or item != intent or ref["path"] != path or ref["revision"] != item["revision"]:
            drifted.add(ref["id"])
            if item is not None and item.get("status") == "pending":
                _scoped(blockers, "pending_requirement", f"{label} intent {ref['id']} was reopened after the freeze; "
                        "confirm it at interactive bootstrap, then refreeze and replan", consumers)
            else:
                _scoped(blockers, "stale_requirement", f"{label} intent {ref['id']} differs from the frozen "
                        "user-confirmed scope; refreeze and replan the affected work", consumers)
            continue
        try:
            _confirmed(root, item)
        except (OSError, ValueError, TypeError, KeyError, AttributeError, IndexError) as exc:
            drifted.add(ref["id"])
            _scoped(blockers, "pending_requirement",
                    f"{label} intent {ref['id']}: {exc}; return to interactive bootstrap", consumers)
    for question in concept.get("intent_questions", []):
        if not _question_pending(root, question):
            continue
        for ref in refs:
            if ref["id"] in set(question.get("depends_on", [])):
                _scoped(blockers, "pending_requirement", f"{label} intent {ref['id']} depends on unresolved decision "
                        f"{question['id']}; answer it at interactive bootstrap, then refreeze and replan",
                        _consumers(workflow, ref))
    for node in workflow["nodes"]:
        node_id = node.get("node_id")
        if node_id in retained:
            continue
        node_refs = node.get("requirement_refs", [])
        if not node_refs or any(ref not in refs for ref in node_refs):
            _scoped(blockers, "scope_requirement_unwired", f"{label} node consumes excluded or unconfirmed intent", [node_id])
            continue
        if any(ref["id"] in drifted for ref in node_refs):
            continue
        expected = [latest[r["id"]] for r in node_refs]
        if (node.get("product_goals") != [i["goal"] for i in expected]
                or node.get("acceptance") != [a for i in expected for a in i["acceptance"]]):
            _scoped(blockers, "stale_requirement", f"{label} goals and acceptance differ from confirmed intent", [node_id])
    return blockers


def _validate_question_ids(concept):
    intent_ids = set(_latest(concept))
    question_ids = set()
    for question in concept.get("intent_questions", []):
        identity = question.get("id")
        if not _text(identity) or identity in intent_ids or identity in question_ids:
            raise ValueError("Question identities must be unique and separate from intent identities")
        question_ids.add(identity)


def _question_pending(root, question):
    if question.get("status", "pending") != "resolved":
        return True
    try:
        reference = question["confirmation"]["reference"]
        source, fragment = reference.split("#")
        batch_id, marker, index = fragment.split("/")
        journal = _read(root, JOURNAL)
        batches = [b for b in journal["batches"] if b["batch_id"] == batch_id]
        return (source != JOURNAL or marker != "decisions" or not index.isdecimal()
                or journal.get("schema_version") != "1.0" or len(batches) != 1
                or batches[0].get("source") != "user_session"
                or batches[0].get("status", "confirmed") != "confirmed"
                or batches[0]["decisions"][int(index)].get("intent") != question
                or batches[0]["decisions"][int(index)].get("status", "confirmed") != "confirmed"
                or any(d.get("supersedes") in (reference, fragment)
                       for b in journal["batches"] for d in b["decisions"]))
    except (OSError, ValueError, TypeError, KeyError, AttributeError, IndexError):
        return True


def _frozen_scope_batch(root, baseline):
    """Return the journal and batch identity that still confirm a frozen scope, else raise."""
    source, fragment = baseline["confirmation"].split("#")
    batch_id, marker, index = fragment.split("/")
    journal = _read(root, JOURNAL, {})
    batches = [b for b in journal.get("batches", []) if b["batch_id"] == batch_id]
    if (source != JOURNAL or marker != "decisions" or not index.isdecimal()
            or journal.get("schema_version") != "1.0"
            or len(batches) != 1 or batches[0].get("source") != "user_session"
            or batches[0].get("status", "confirmed") != "confirmed"
            or batches[0]["decisions"][int(index)].get("status", "confirmed") != "confirmed"
            or batches[0]["decisions"][int(index)].get("baseline") != baseline
            or any(d.get("supersedes") in (fragment, baseline["confirmation"])
                   for b in journal["batches"] for d in b["decisions"])):
        raise ValueError("Cannot resume unverified scope exclusions")
    return journal, batch_id


def _same_selection(previous, refs, exclude, intents):
    """True when a verified previous scope already binds exactly this confirmed selection."""
    by_id = lambda values: {v["id"]: v for v in values}  # noqa: E731
    return (isinstance(previous, dict)
            and by_id(previous.get("requirement_refs", [])) == by_id(refs)
            and previous.get("excluded") == exclude
            and by_id(previous.get("intents", [])) == by_id(intents))


def _discussion(root, concept):
    import copy
    concept = copy.deepcopy(concept)
    profile = _read(root, PROFILE, {})
    baseline = (profile.get("intent_scope", {}) if profile.get("intent_session_path") == LOCAL
                else _read(root, BASELINE, {}).get("intent_baseline", {}))
    excluded = {}
    if baseline:
        journal, batch_id = _frozen_scope_batch(root, baseline)
        excluded = dict(baseline["excluded"])
        # A later explicit reconsideration replaces only that exclusion. The
        # frozen baseline remains historical until the user freezes a new scope.
        after_scope = False
        reopened = set()
        for batch in journal["batches"]:
            if batch["batch_id"] == batch_id:
                after_scope = True
                continue
            if (not after_scope or batch.get("source") != "user_session"
                    or batch.get("status", "confirmed") != "confirmed"):
                continue
            for decision in batch["decisions"]:
                if decision.get("operation") == "reopen" and decision.get("status", "confirmed") == "confirmed":
                    identity = decision["intent"]["id"]
                    excluded.pop(identity, None)
                    reopened.add(identity)
        for question in concept.get("intent_questions", []):
            if set(question.get("depends_on", [])) & reopened:
                excluded.pop(question["id"], None)
    for item in _latest(concept).values():
        if item.get("status") in ("confirmed", "removed"):
            try:
                _confirmed(root, item, statuses=("confirmed", "removed"))
            except LegacyProjection as exc:
                exc.expose(item)
            except (OSError, ValueError, TypeError, KeyError, AttributeError, IndexError):
                item["status"] = "pending"
                item["pending_reason"] = "Missing or invalid user confirmation provenance"
    topics = []
    for topic in dict.fromkeys([*TOPICS, *(i["topic"] for i in _latest(concept).values())]):
        items = [i for i in _latest(concept).values() if i["topic"] == topic and i["status"] == "pending" and i["id"] not in excluded]
        questions = [dict(q, status="pending") for q in concept.get("intent_questions", [])
                     if q["topic"] == topic and _question_pending(root, q) and q["id"] not in excluded]
        if items or questions:
            topics.append({"topic": topic, "items": items, "questions": questions})
    return {"status": "discussion", "topics": topics, "history": concept.get("requirements", []),
            "excluded": excluded, "questions": concept.get("intent_questions", [])}


def session(root, request):
    """Apply explicit interactive bootstrap input; never called by unattended run."""
    if request.get("operation") in ("run-policy", "run-event"):
        return run_policy(root, request)
    profile = _read(root, PROFILE, {})
    concept_path = LOCAL if profile.get("intent_session_path") == LOCAL else CONCEPT
    concept = _read(root, concept_path, {})
    _validate_question_ids(concept)
    operation = request["operation"]
    if operation == "admit":
        import copy
        if (request.get("route") != "local-change" or not _text(request.get("goal"))
                or not isinstance(request.get("areas"), list) or not request["areas"]
                or not all(_text(a) for a in request["areas"])):
            raise ValueError("Legacy admission needs the explicit local goal and areas")
        if _read(root, LOCAL, {}).get("requirements"):
            raise ValueError("Existing local history must be resumed, not overwritten")
        items = copy.deepcopy(request["items"])
        if not isinstance(items, list) or not items:
            raise ValueError("Supply only relevant legacy projections and missing local requirements")
        for item in items:
            _item(item)
            if not set(item["scope"]) & set(request["areas"]):
                raise ValueError("Legacy projection is outside the requested local scope")
            _reuse_legacy_choice(root, item)
        if len({i["id"] for i in items}) != len(items):
            raise ValueError("Legacy projection identities must be unique")
        concept = {"requirements": items, "intent_questions": request.get("questions", [])}
        _validate_question_ids(concept)
        profile.update(task_route="local-change", task_goal=request["goal"], intent_session_path=LOCAL,
                       task_scope={"areas": request["areas"], "requirement_refs": []})
        profile.pop("intent_scope", None)
        _write(root, LOCAL, concept)
        _write(root, PROFILE, profile)
        return _discussion(root, concept)
    if operation == "resume":
        return _discussion(root, concept)
    if operation == "plan":
        import copy
        import re
        baseline = (profile["intent_scope"] if concept_path == LOCAL
                    else _read(root, BASELINE, {})["intent_baseline"])
        latest = _latest(concept)
        refs_by_id = {r["id"]: r for r in baseline["requirement_refs"]}
        workflow = copy.deepcopy(request)
        workflow.pop("operation")
        if concept_path == CONCEPT:
            workflow["product_baseline"] = baseline
        workflow.setdefault("transition_log", [])
        for node in workflow["nodes"]:
            if "intent_ids" in node:
                node["requirement_refs"] = [refs_by_id[i] for i in node.pop("intent_ids")]
        retained = _retained_nodes(workflow, baseline["requirement_refs"])
        bodies = {}
        for node in workflow["nodes"]:
            identity = node["node_id"]
            if not isinstance(identity, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", identity) or identity in bodies:
                raise ValueError("Node identity must be unique and filename-safe")
            bodies[identity] = node.pop("body", None)
            if identity in retained:
                if not (root / ".allforai/bootstrap/node-specs" / (identity + ".md")).is_file() and not _text(bodies[identity]):
                    raise ValueError("Retained node needs its historical Node-spec or task brief")
                continue
            if not _text(bodies[identity]):
                raise ValueError("Node needs a project-specific task brief")
            scope_inputs = [LOCAL] if concept_path == LOCAL else [CONCEPT, BASELINE]
            node["decision_inputs"] = list(dict.fromkeys([*node.get("decision_inputs", []), *scope_inputs]))
            selected = [latest[r["id"]] for r in node["requirement_refs"]]
            node["product_goals"] = [i["goal"] for i in selected]
            node["acceptance"] = [a for i in selected for a in i["acceptance"]]
        blockers = validate_scope(root, workflow)
        if blockers:
            raise ValueError(json.dumps(blockers))
        for node in workflow["nodes"]:
            path = root / ".allforai/bootstrap/node-specs" / (node["node_id"] + ".md")
            if node["node_id"] in retained:
                if not path.exists():
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text("---\n" + json.dumps(node, ensure_ascii=False) + "\n---\n" + bodies[node["node_id"]], encoding="utf-8")
                continue
            body = bodies[node["node_id"]] + "\n\nConfirmed product goals:\n" + "\n".join("- " + v for v in node["product_goals"])
            body += "\n\nAcceptance:\n" + "\n".join("- " + v for v in node["acceptance"]) + "\n"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("---\n" + json.dumps(node, ensure_ascii=False) + "\n---\n" + body, encoding="utf-8")
        for path in (root / ".allforai/bootstrap/node-specs").glob("*.md"):
            if path.stem not in bodies:
                path.unlink()
        _write(root, ".allforai/bootstrap/workflow.json", workflow)
        return {"status": "planned", "workflow": workflow}
    if operation == "freeze":
        include, exclude = request["include"], request["exclude"]
        if (not isinstance(include, list) or not include or not all(_text(i) for i in include)
                or len(include) != len(set(include)) or not isinstance(exclude, dict)
                or not all(_text(k) and _text(v) for k, v in exclude.items())):
            raise ValueError("Freeze needs explicit included identities and exclusion reasons")
        latest = _latest(concept)
        questions = concept.get("intent_questions", [])
        pending = {q["id"] for q in questions if _question_pending(root, q)}
        if (set(include) - latest.keys() or set(include) & exclude.keys()
                or (latest.keys() | pending) - (set(include) | exclude.keys())
                or exclude.keys() - (latest.keys() | pending)):
            raise ValueError("Freeze needs explicit scope for every intent and unresolved question")
        for q in questions:
            if q["id"] in pending and set(q.get("depends_on", [])) & set(include):
                raise ValueError("Included work depends on an unresolved decision")
        for identity in include:
            _confirmed(root, latest[identity])
        if any(not _text(request.get(k)) for k in ("batch_id", "user_reference", "reason")):
            raise ValueError("Scope needs explicit user reference and reason")
        journal = _read(root, JOURNAL)
        baseline = _read(root, BASELINE, {})
        refs = [{"path": concept_path, "id": i, "revision": latest[i]["revision"]} for i in include]
        previous_scope = profile.get("intent_scope", {}) if concept_path == LOCAL else baseline.get("intent_baseline", {})
        # The same confirmed selection re-frozen converges: no new decision, version or
        # replan. A changed selection, a new revision, any user decision recorded after
        # the scope batch, or an unverifiable previous scope freezes a new version.
        if (_same_selection(previous_scope, refs, exclude, [latest[i] for i in include])
                and profile.get("task_scope", {}).get("requirement_refs") == previous_scope["requirement_refs"]):
            try:
                _, scope_batch = _frozen_scope_batch(root, previous_scope)
            except (OSError, ValueError, TypeError, KeyError, AttributeError, IndexError):
                pass
            else:
                if journal["batches"][-1]["batch_id"] == scope_batch:
                    return {"status": "frozen", "baseline": previous_scope, "unchanged": True}
        if any(b["batch_id"] == request["batch_id"] for b in journal["batches"]):
            raise ValueError("Scope batch identity already exists")
        contract = {"version": previous_scope.get("version", 0) + 1,
                    "requirement_refs": refs, "excluded": exclude,
                    "intents": [latest[i] for i in include],
                    "confirmation": JOURNAL + "#" + request["batch_id"] + "/decisions/0"}
        journal["batches"].append({"batch_id": request["batch_id"], "topic": "Product baseline scope",
                                   "source": "user_session", "user_reference": request["user_reference"],
                                   "decisions": [{"question": "Freeze this product scope?", "chosen": "Freeze explicit scope",
                                                  "rationale": request["reason"], "baseline": contract}]})
        baseline["intent_baseline"] = contract
        profile = _read(root, PROFILE, {})
        profile["task_scope"] = {"areas": sorted({a for i in include for a in latest[i]["scope"]}), "requirement_refs": refs}
        _write(root, JOURNAL, journal)
        if concept_path == LOCAL:
            profile["intent_scope"] = contract
        else:
            _write(root, BASELINE, baseline)
        _write(root, PROFILE, profile)
        return {"status": "frozen", "baseline": contract}
    if operation == "decide":
        import copy
        actions = request["actions"]
        if not isinstance(actions, list):
            raise ValueError("actions must be an explicit array")
        if not actions:
            return _discussion(root, concept)
        if any(not _text(request.get(k)) for k in ("batch_id", "topic", "user_reference")):
            raise ValueError("User decisions need batch identity, topic and actual user reference")
        journal = _read(root, JOURNAL, {"schema_version": "1.0", "batches": []})
        if journal.get("schema_version") != "1.0" or not isinstance(journal.get("batches"), list):
            raise ValueError("Preserve canonical schema 1.0 journal batches")
        if any(b["batch_id"] == request["batch_id"] for b in journal["batches"]):
            raise ValueError("Batch identity already exists; resume before submitting new decisions")
        batch = {"batch_id": request["batch_id"], "topic": request["topic"], "source": "user_session",
                 "user_reference": request["user_reference"], "decisions": []}
        for action in actions:
            op = action["operation"]
            if not _text(action.get("reason")):
                raise ValueError("Every explicit decision needs its reason")
            reference = JOURNAL + "#" + request["batch_id"] + "/decisions/" + str(len(batch["decisions"]))
            confirmation = {"source": "user", "reference": reference, "decision_id": reference.split("#")[1],
                            "reason": action["reason"], "user_reference": request["user_reference"]}
            previous = None
            if op == "add":
                item = copy.deepcopy(action["item"])
                _item(item)
                if item["id"] in _latest(concept):
                    raise ValueError("Added intent needs an unused stable identity")
                item.update(revision=1, origin="user-request", evidence=[], status="confirmed", confirmation=confirmation)
                concept.setdefault("requirements", []).append(item)
            elif op in ("confirm", "adjust", "remove", "restore") or (op == "reopen" and action["id"] in _latest(concept)):
                item = _latest(concept)[action["id"]]
                previous = item.get("confirmation", {}).get("reference")
                if item["status"] == "removed" and op != "restore":
                    try:
                        _confirmed(root, item, statuses=("removed",))
                    except (OSError, ValueError, TypeError, KeyError, AttributeError, IndexError):
                        if op != "confirm":
                            raise ValueError("Unverified legacy removal needs explicit confirmation")
                    else:
                        raise ValueError("Removed intent cannot be silently restored")
                if op == "restore" and item["status"] != "removed":
                    raise ValueError("Restore requires a removed intention")
                if op == "adjust":
                    replacement = copy.deepcopy(item)
                    changes = action["changes"]
                    if not changes or set(changes) - {"goal", "scope", "business_rules", "acceptance", "topic"}:
                        raise ValueError("Adjust only product meaning; identity and authority are immutable")
                    replacement.update(changes)
                    _item(replacement)
                    replacement.update(revision=item["revision"] + 1, supersedes={"id": item["id"], "revision": item["revision"]})
                    item["status"] = "superseded"
                    concept["requirements"].append(replacement)
                    item = replacement
                elif op in ("remove", "restore", "reopen") and item.get("confirmation"):
                    replacement = copy.deepcopy(item)
                    replacement.update(revision=item["revision"] + 1,
                                       supersedes={"id": item["id"], "revision": item["revision"]})
                    if item["status"] != "removed":
                        item["status"] = "superseded"
                    concept["requirements"].append(replacement)
                    item = replacement
                elif op == "confirm" and item["status"] != "pending":
                    try:
                        _confirmed(root, item)
                    except (OSError, ValueError, TypeError, KeyError, AttributeError, IndexError):
                        item["prior_confirmation"] = item.get("confirmation")
                    else:
                        raise ValueError("Reuse recorded confirmation; do not reconfirm it")
                elif op == "confirm" and item.get("confirmation"):
                    # Keep the historical goal-only or unverified provenance for context.
                    item["prior_confirmation"] = item["confirmation"]
                for stale in ("pending_reason", "legacy_reuse"):
                    item.pop(stale, None)
                item.update(status="removed" if op == "remove" else "pending" if op == "reopen" else "confirmed",
                            confirmation=confirmation)
            elif op in ("answer", "reopen"):
                item = next(q for q in concept["intent_questions"] if q["id"] == action["id"])
                previous = item.get("confirmation", {}).get("reference")
                if op == "answer" and not _text(action.get("answer")):
                    raise ValueError("Unanswered question remains pending")
                if op == "answer":
                    item.update(status="resolved", answer=action["answer"], confirmation=confirmation)
                else:
                    item.pop("answer", None)
                    item.update(status="pending", confirmation=confirmation)
            else:
                raise ValueError("Only explicit confirm/add/adjust/remove/answer/reopen/restore operations are supported")
            batch["decisions"].append({"question": action.get("id", item["id"]),
                                       "chosen": item.get("goal", item.get("answer", "Reopen decision")),
                                       "rationale": action["reason"], "operation": op,
                                       "supersedes": previous, "intent": copy.deepcopy(item)})
        _validate_question_ids(concept)
        journal["batches"].append(batch)
        _write(root, JOURNAL, journal)
        _write(root, concept_path, concept)
        return _discussion(root, concept)
    if operation == "draft":
        if request.get("route") not in ("product-reconstruction", "new-product") or not _text(request.get("goal")):
            raise ValueError("Product discussion needs an explicit product goal and route")
        if concept.get("requirements"):
            raise ValueError("Existing intent history must be resumed, not overwritten")
        items = request["items"]
        if not isinstance(items, list):
            raise ValueError("items must be an array")
        ids = set()
        for item in items:
            _item(item)
            if item["id"] in ids:
                raise ValueError("Duplicate intent identity")
            ids.add(item["id"])
            if item.get("origin") not in ("inference", "unknown", "user-request"):
                raise ValueError("Draft origin must distinguish inference, unknown or user-request")
            if item["origin"] == "inference" and (not item.get("evidence") or not _text(item.get("uncertainty"))):
                raise ValueError("Inference needs evidence and uncertainty")
            if request["route"] == "new-product" and item["origin"] == "inference":
                raise ValueError("New products start from user intent, not reverse inference")
            if item.get("status") == "confirmed" or "confirmation" in item:
                # A legacy confirmed projection is reused only with canonical journal
                # provenance; the draft never strips or invents confirmation.
                _reuse_legacy_choice(root, item)
            else:
                item.update(revision=1, status="pending")
        facts = request.get("facts", [])
        for evidence in [*facts, *(e for i in items for e in i.get("evidence", []))]:
            path = Path(evidence["path"])
            if path.is_absolute() or not (root / path).resolve().is_relative_to(root.resolve()):
                raise ValueError("Evidence must be project-local")
            if not _text(evidence.get("quote")) or evidence["quote"] not in (root / path).read_text(encoding="utf-8"):
                raise ValueError("Evidence quote is absent from source")
        questions = request.get("questions", [])
        for q in questions:
            if any(not _text(q.get(k)) for k in ("id", "topic", "question")):
                raise ValueError("Questions need identity, topic and question")
            q["status"] = "pending"
        for topic in TOPICS:
            if not any(i["topic"] == topic for i in items):
                questions.append({"id": "gap-" + topic, "topic": topic, "kind": "gap",
                                  "question": "What is the desired " + topic + "?", "status": "pending", "depends_on": []})
        concept.update(requirements=items, intent_facts=facts, intent_questions=questions)
        _validate_question_ids(concept)
        profile = _read(root, PROFILE, {})
        profile.update(task_goal=request["goal"], task_route=request["route"],
                       task_scope={"areas": sorted({a for i in items for a in i["scope"]}) or ["product"], "requirement_refs": []})
        _write(root, CONCEPT, concept)
        _write(root, PROFILE, profile)
        return _discussion(root, concept)
    raise ValueError("Unknown interactive operation")


if __name__ == "__main__":
    import sys
    try:
        request = ({"operation": "run-policy"} if sys.argv[2:] == ["--run-policy"] else
                   {"operation": "run-event", "event": sys.argv[3], "consume": True} if len(sys.argv) == 4 and sys.argv[2] == "--policy-event"
                   else json.load(sys.stdin))
        result = session(Path(sys.argv[1]).resolve(), request)
        print(json.dumps(result, ensure_ascii=False))
        if result.get("status") == "needs_run_policy":
            sys.exit(1)
    except (OSError, ValueError, TypeError, KeyError, AttributeError, IndexError, StopIteration) as exc:
        print(json.dumps({"status": "blocked", "error": str(exc)}))
        sys.exit(1)
