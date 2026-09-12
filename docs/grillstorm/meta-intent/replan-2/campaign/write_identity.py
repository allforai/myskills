"""Write the coordinator-observed identity record that admission binds a receipt against.

A receipt's own session id is self-authored; `admit_evidence.py` used to accept any non-empty value,
so a host could name itself and pass. These fields come from Orca at launch, before the actor can
report anything, which is what makes them usable as corroboration.

Usage: write_identity.py <cell-dir> <dispatch.json> <run.json> <worker-show.json>
"""
import argparse
import datetime
import json
from pathlib import Path


def read(path):
    try:
        return json.loads(Path(path).read_text()).get("result") or {}
    except (OSError, ValueError):
        return {}


def build(dispatch, run, worker_show):
    terminal = worker_show.get("terminal") or {}
    prompt = dispatch.get("prompt") or {}
    return {
        "captured_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "captured_by": "coordinator at launch, before the actor produced any output",
        "dispatch_id": dispatch.get("dispatchId"),
        "run_id": dispatch.get("runId") or ((run.get("run") or {}).get("id")),
        "task_id": dispatch.get("taskId"),
        "orca_side": {
            "dispatch_prompt_processIncarnation": prompt.get("processIncarnation"),
            "terminal_incarnationId": terminal.get("incarnationId"),
            "terminal_agentIdentity": terminal.get("agentIdentity"),
            "dispatch_prompt_provider": prompt.get("provider"),
            "launch_effective_agent": ((dispatch.get("launch") or {}).get("effective") or {}).get("agent"),
            "terminal_handle": next((e.get("id") for e in dispatch.get("effects") or []
                                     if e.get("kind") == "terminal"), None),
        },
    }


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("cell"); ap.add_argument("dispatch"); ap.add_argument("run")
    ap.add_argument("worker_show")
    a = ap.parse_args(argv)
    record = build(read(a.dispatch), read(a.run), read(a.worker_show))
    missing = [k for k in ("dispatch_id",) if not record.get(k)]
    if not record["orca_side"]["dispatch_prompt_processIncarnation"] and \
       not record["orca_side"]["terminal_incarnationId"]:
        missing.append("process_incarnation")
    out = Path(a.cell) / "capture" / "coordinator-identity.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps({"written": str(out), "missing": missing}))
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
