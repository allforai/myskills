"""Normalize an actor's own receipt into the bounded admission shape, preserving the original.

The private file permits this: "the coordinator may normalize actual raw actor records into this
shape while preserving originals." Actors write richer, host-specific receipts; `admit_evidence.py`
reads a fixed set of fields. Normalizing by hand was how a receipt first reached admission with no
identity binding at all, so this does it by rule and refuses to invent anything.

What it will NOT do: fabricate a field. The Orca process incarnation comes from the coordinator's own
launch record, never from the actor, and the actor's independently reported dispatch id and terminal
handle are CHECKED against that record rather than trusted.

Usage: normalize_receipt.py <cell-dir> --candidate-root <path> --raw-dialogue <path> [--out <path>]
"""
import argparse
import hashlib
import json
from pathlib import Path

# Key names that record what the actor did NOT read. Harvesting these would turn a declared
# non-read into a claimed read, which is the one lie normalization must never introduce.
DENY = ("not_used", "not_loaded", "deliberately_not", "unavailable", "missing", "absent", "skipped")
PATH_FIELDS = ("abs_path", "resolved_path", "path", "requested_entry_path")

HOSTS = {"codex": "codex", "claude": "claude"}


def host_value(receipt):
    """The host, wherever this receipt put it and whatever it called the key.

    Three actors have now used three shapes: a plain string `host`, a nested `session_identity.host`,
    and a dict `host` keyed on `harness`. Chasing key names one at a time under-reports the next
    variant, so this searches structurally: any key that looks like a host or harness field whose
    string value names a known host. Ambiguity is still refused by normalize_host rather than guessed.
    """
    found = []

    def walk(node, key_path=""):
        if isinstance(node, dict):
            for key, value in node.items():
                walk(value, f"{key_path}.{key}" if key_path else key)
        elif isinstance(node, str) and node:
            leaf = key_path.lower()
            if not any(token in leaf for token in ("host", "harness", "agent", "product")):
                return
            # A host name is a short identifier, not prose and not a path. Without this, a sentence
            # under host.note that merely mentioned "~/.codex" read as a second host declaration and
            # the receipt was refused as naming two hosts.
            if len(node) > 60 or "/" in node or node.count(" ") > 6:
                return
            if any(h in node.lower() for h in HOSTS):
                found.append(node)

    walk(receipt)
    if not found:
        return None
    # Collapse to the set of hosts actually named; a single host named many ways is not ambiguous.
    named = {h for token, h in HOSTS.items() for value in found if token in value.lower()}
    if len(named) == 1:
        return named.pop()
    return found[0] if len(found) == 1 else " and ".join(sorted(named))


def normalize_host(value):
    """'Codex inside Orca' and 'Claude Code' must land on the admission vocabulary, or fail loudly."""
    if isinstance(value, dict):
        value = value.get("product") or value.get("name") or ""
    text = str(value).lower()
    hits = [canonical for token, canonical in HOSTS.items() if token in text]
    if len(hits) != 1:
        raise ValueError(f"cannot determine a single host from {value!r}")
    return hits[0]


def session_id(receipt):
    """The one session identity the receipt reports, or a refusal.

    Hosts name this differently — CODEX_SESSION_ID, claude_code_session_id, claude_code_session_uuid —
    so the search is structural: any key naming a session id or uuid. If two such keys disagree the
    receipt is refused rather than resolved by search order: silently preferring whichever key was
    checked first is how a record starts describing a session that never ran.
    """
    direct = receipt.get("session_id")
    if isinstance(direct, str) and direct:
        return direct
    found = {}

    def walk(node, key_path=""):
        if isinstance(node, dict):
            for key, value in node.items():
                walk(value, f"{key_path}.{key}" if key_path else key)
        elif isinstance(node, str) and node:
            leaf = key_path.lower().rsplit(".", 1)[-1]
            if "session" in leaf and ("id" in leaf or "uuid" in leaf or "thread" in leaf):
                found[key_path] = node

    walk(receipt)
    # A reference URL and the bare id it contains are the same identity, not a conflict.
    distinct = {v for v in found.values()}
    if not distinct:
        raise ValueError("receipt carries no session identity to normalize")
    if len(distinct) > 1:
        shortest = min(distinct, key=len)
        if all(shortest in v or v in shortest for v in distinct):
            return shortest
        raise ValueError(f"receipt reports conflicting session identities: {found}")
    return distinct.pop()


def loaded_files(receipt, candidate_root):
    """Every candidate asset the receipt records as actually read, at any depth.

    Four actors have used four shapes: `loaded_assets`, `references_loaded_in_full` plus
    `references_loaded_in_part`, a single `candidate_entry`, and a nested `candidate.loaded[]`. A
    top-level-only scan found nothing in the fourth and reported zero reads, so discovery walks the
    whole record and keys on structure — anything carrying a sha256 and a path.

    Two guards keep that from over-reporting. Any key ANYWHERE on the path that names a non-read is
    refused, so a declared skip can never become a claimed read. And every path must resolve inside
    the pinned candidate, which drops project files, host skill stubs and installed-but-unused copies.
    """
    root = Path(candidate_root).resolve()
    out, seen = [], set()

    def harvest(node, key_path=""):
        if any(token in key_path.lower() for token in DENY):
            return
        if isinstance(node, dict):
            digest = node.get("sha256")
            raw = next((node[f] for f in PATH_FIELDS if node.get(f)), None)
            if digest and raw:
                candidate = Path(raw)
                path = (candidate if candidate.is_absolute() else root / candidate).resolve()
                if path.is_relative_to(root) and path.is_file() and str(path) not in seen:
                    seen.add(str(path))
                    out.append({"path": str(path), "sha256": digest})
            for key, value in node.items():
                harvest(value, f"{key_path}.{key}" if key_path else key)
        elif isinstance(node, list):
            for item in node:
                harvest(item, key_path)

    harvest(receipt)
    return sorted(out, key=lambda f: f["path"])


# Field names hosts use for the Orca ids, mapped to the coordinator record they must agree with.
# Hosts nest these differently: one wrote them at top level, another under session_identity.orca.
IDENTITY_ALIASES = {
    "dispatch_id": ("dispatch_id", "dispatchId"),
    "terminal_handle": ("terminal_handle", "worker_terminal_handle", "agent_terminal_handle"),
    "task_id": ("task_id", "taskId"),
}


def claimed_identity(receipt):
    """Every Orca id the receipt states, found at any depth.

    Looking only at the top level discarded real corroboration: one host recorded its dispatch id,
    terminal handle and task id under session_identity.orca, and a shallow read saw none of them, so
    the strongest available agreement evidence was silently dropped.
    """
    found = {}

    def walk(node):
        if isinstance(node, dict):
            for key, value in node.items():
                for field, aliases in IDENTITY_ALIASES.items():
                    if key in aliases and isinstance(value, str) and value:
                        found.setdefault(field, value)
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(receipt)
    return found


def identity_binding(receipt, coordinator_identity):
    """Bind to what the coordinator observed, and verify every id the actor independently stated."""
    orca_side = coordinator_identity.get("orca_side") or {}
    incarnation = (orca_side.get("dispatch_prompt_processIncarnation")
                   or orca_side.get("terminal_incarnationId"))
    dispatch = coordinator_identity.get("dispatch_id")
    if not dispatch or not incarnation:
        raise ValueError("coordinator identity record is incomplete; cannot bind")
    observed = {"dispatch_id": dispatch,
                "terminal_handle": orca_side.get("terminal_handle"),
                "task_id": coordinator_identity.get("task_id")}
    claimed = claimed_identity(receipt)
    disagreements, agreed = [], []
    for field, seen in observed.items():
        said = claimed.get(field)
        if not said or not seen:
            continue
        if said != seen:
            disagreements.append({"field": field, "actor_said": said, "coordinator_saw": seen})
        else:
            agreed.append(field)
    return ({"dispatch_id": dispatch, "process_incarnation": incarnation,
             "actor_agreed_on": sorted(agreed)}, disagreements)


def actor_receipt_path(cell):
    """Always normalize from the actor's own words.

    Once receipt.json has been normalized it no longer carries the actor's own dispatch id and
    terminal handle, so re-reading it silently loses the actor-agreement evidence that makes the
    identity binding worth anything. Prefer the preserved original whenever it exists, which also
    makes normalization idempotent.
    """
    cell = Path(cell)
    original = cell / "receipt.actor-original.json"
    return original if original.is_file() else cell / "receipt.json"


def build(cell, candidate_root, raw_dialogue):
    cell = Path(cell)
    receipt = json.loads(actor_receipt_path(cell).read_text())
    identity_file = cell / "capture" / "coordinator-identity.json"
    coordinator = json.loads(identity_file.read_text())
    binding, disagreements = identity_binding(receipt, coordinator)
    if disagreements:
        raise ValueError(f"actor identity contradicts the coordinator record: {disagreements}")
    raw = Path(raw_dialogue).resolve()
    return {
        "host": normalize_host(host_value(receipt)),
        "session_id": session_id(receipt),
        "orca_identity": binding,
        "source_root": str(Path(candidate_root).resolve()),
        "loaded_files": loaded_files(receipt, candidate_root),
        "raw_dialogue": {"path": str(raw),
                         "sha256": hashlib.sha256(raw.read_bytes()).hexdigest()},
        "normalized_by": ("coordinator; the actor's own record is preserved at "
                          "receipt.actor-original.json. process_incarnation comes from the "
                          "coordinator's launch record, never from the actor; the actor's own "
                          "dispatch_id and terminal_handle were checked against it and agreed."),
    }


def certified_guard(cell, ledger=None, allow=False):
    """Refuse to rewrite the receipt of a cell already recorded as passed.

    A certified cell's artifacts are what an evaluator judged. Re-normalizing one under improved
    tooling changed a certified receipt's bytes and the as-evaluated artifact could not be restored,
    which is an audit-trail loss even though the change only added corroboration. Freeze instead.
    """
    if allow:
        return
    ledger = Path(ledger) if ledger else (Path(__file__).parent.parent / "T15" / "results.json")
    if not ledger.is_file():
        return
    try:
        cells = json.loads(ledger.read_text()).get("cells") or []
    except ValueError:
        return
    target = str(Path(cell).resolve())
    for entry in cells:
        if entry.get("status") != "passed":
            continue
        for attempt in entry.get("attempts") or []:
            receipt = attempt.get("receipt") or ""
            if receipt and str(Path(receipt).parent.resolve()) == target:
                raise SystemExit(
                    f"refusing to rewrite the receipt of a certified cell ({entry.get('scenario')} "
                    f"{entry.get('host')}); its artifacts are what the evaluator judged. Pass "
                    f"--allow-certified only to deliberately re-open it, and re-evaluate afterwards.")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("cell")
    ap.add_argument("--candidate-root", required=True)
    ap.add_argument("--raw-dialogue", required=True)
    ap.add_argument("--out")
    ap.add_argument("--ledger")
    ap.add_argument("--allow-certified", action="store_true",
                    help="deliberately re-open a certified cell; its evaluation must then be redone")
    a = ap.parse_args(argv)
    cell = Path(a.cell)
    if not a.out:
        certified_guard(cell, a.ledger, a.allow_certified)
    record = build(cell, a.candidate_root, a.raw_dialogue)
    original = cell / "receipt.actor-original.json"
    if not original.exists():
        original.write_text((cell / "receipt.json").read_text())
    out = Path(a.out) if a.out else cell / "receipt.json"
    out.write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps({"written": str(out), "preserved": str(original),
                      "loaded_files": len(record["loaded_files"]),
                      "actor_agreed_on": record["orca_identity"]["actor_agreed_on"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
