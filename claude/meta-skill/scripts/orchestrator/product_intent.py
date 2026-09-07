"""Shared validation of explicit bootstrap scope; never infers user decisions."""
from pathlib import Path
import json


def validate_scope(project_root, workflow):
    """Return typed blockers for the scope consumed by a generated workflow.

    Profiles without the scope contract remain legacy inputs. Their existence is
    not evidence of approval; bootstrap must capture scope before generating new work.
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
        last_status = {event.get("node_id", event.get("node")): event.get("status")
                       for event in history}
        retained = {node.get("node_id") for node in workflow.get("nodes", [])
                    if last_status.get(node.get("node_id")) == "completed"
                    and not any(ref in scope["requirement_refs"]
                                for ref in node.get("requirement_refs", []))}
        blockers = []
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
            if any(type(revision) is not int or revision < 1 for revision in revisions):
                raise ValueError(f"{ref['id']}: invalid requirement revision")
            if not revisions or max(revisions) != ref["revision"]:
                blockers.append({"code": "stale_requirement", "message":
                                 f"{ref['id']}: reference does not select the current requirement revision"})
                continue
            if len(revisions) != len(set(revisions)):
                blockers.append({"code": "invalid_requirement", "message":
                                 f"{ref['id']}: duplicate requirement revisions"})
                continue
            for item in related:
                if item["id"] == ref["id"] and item["revision"] == ref["revision"]:
                    if (not isinstance(item.get("goal"), str) or not item["goal"].strip()
                            or any(not isinstance(item.get(key), list) or not item[key]
                                   or any(not isinstance(value, str) or not value.strip()
                                          for value in item[key])
                                   for key in ("business_rules", "acceptance", "scope"))):
                        blockers.append({"code": "invalid_requirement", "message":
                                         f"{ref['id']}: goal, scope, business_rules and acceptance must be non-empty"})
                    if not set(item.get("scope", [])).intersection(scope.get("areas", [])):
                        blockers.append({"code": "requirement_scope_conflict", "message":
                                         f"{ref['id']}: confirmed decision does not apply to this task scope"})
                    confirmation = item.get("confirmation") or {}
                    if (item.get("status") != "confirmed"
                            or confirmation.get("source") != "user"
                            or any(not isinstance(confirmation.get(key), str)
                                   or not confirmation[key].strip()
                                   for key in ("reference", "decision_id", "reason"))):
                        blockers.append({"code": "pending_requirement", "message":
                                         f"{ref['id']}: return to interactive bootstrap for confirmation"})
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
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
        return [{"code": "invalid_scope", "message": f"{path}: {exc}"}]
