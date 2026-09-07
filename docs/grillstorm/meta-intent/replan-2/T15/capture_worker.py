"""Record bounded Orca worker pages without grading or launching actors."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dispatch")
    parser.add_argument("output", type=Path)
    parser.add_argument("--orca", default="orca", help="Exact session-selected Orca executable")
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--pages", type=int, default=20)
    parser.add_argument("--after", type=Path, help="Continue only from this prior capture.json")
    args = parser.parse_args()
    if not 1 <= args.pages <= 100 or not 1 <= args.limit <= 1000:
        parser.error("pages must be 1..100 and limit 1..1000")
    args.output.mkdir(parents=True, exist_ok=False)
    report = {"dispatchId": args.dispatch, "pages": [], "cursor": None,
              "semantic_verdict": "not-evaluated", "full_dialogue_proven": False,
              "history_boundary": "initial read is a bounded window; corroborate earlier history",
              "limitations": []}
    if args.after:
        previous = json.loads(args.after.read_text())
        if previous.get("dispatchId") != args.dispatch or not previous.get("cursor"):
            parser.error("prior capture must belong to this dispatch and contain its returned cursor")
        if "source-changed" in previous.get("limitations", []):
            parser.error("source changed; start a fresh capture without --after")
        report.update({key: previous.get(key) for key in ("cursor", "source", "sourceIdentity", "provider")})
        report["previous_capture"] = str(args.after.resolve())
        report["previous_capture_sha256"] = hashlib.sha256(args.after.read_bytes()).hexdigest()
        report["history_boundary"] = "continuation from prior capture; full history still needs corroboration"
    for number in range(1, args.pages + 1):
        command = [args.orca, "orchestration", "worker-read", "--dispatch", args.dispatch,
                   "--source", "auto", "--limit", str(args.limit), "--json"]
        if report["cursor"]:
            command += ["--cursor", report["cursor"]]
        prefix = args.output / f"page-{number:04d}"
        try:
            captured = subprocess.run(command, capture_output=True, timeout=55)
        except subprocess.TimeoutExpired as error:
            captured = subprocess.CompletedProcess(command, 124, error.stdout or b"", error.stderr or b"")
            report["limitations"].append("command-timeout")
        except OSError as error:
            captured = subprocess.CompletedProcess(command, 127, b"", str(error).encode())
            report["limitations"].append("command-failed")
        prefix.with_suffix(".stdout.json").write_bytes(captured.stdout)
        prefix.with_suffix(".stderr.txt").write_bytes(captured.stderr)
        metadata = {"command": command, "exit_code": captured.returncode,
                    "stdout_sha256": hashlib.sha256(captured.stdout).hexdigest(),
                    "stderr_sha256": hashlib.sha256(captured.stderr).hexdigest()}
        write(prefix.with_suffix(".command.json"), metadata)
        report["pages"].append({"prefix": str(prefix.resolve()), **metadata})
        try:
            response = json.loads(captured.stdout)
        except (ValueError, UnicodeError):
            report["limitations"].append("invalid-runtime-json")
            break
        if captured.returncode or not isinstance(response, dict) or response.get("ok") is not True:
            report["limitations"].append("runtime-error")
            if isinstance(response, dict) and "source_changed" in json.dumps(response.get("error")):
                report["limitations"].append("source-changed")
            break
        result = response["result"]
        identity = {key: result.get(key) for key in ("source", "sourceIdentity", "provider")}
        report["pages"][-1].update({**identity, "warnings": result.get("warnings", []),
                                    "fallbackReason": result.get("fallbackReason"),
                                    "transcript": {key: (result.get("transcript") or {}).get(key)
                                                   for key in ("limited", "returnedMessageCount")}})
        if result.get("warnings"):
            report["limitations"].append("runtime-warnings")
        if number == 1 and not args.after:
            report.update(identity)
        elif any(identity[key] != report.get(key) for key in identity):
            report["limitations"].append("source-changed")
            break
        if result.get("dispatchId") != args.dispatch:
            report["limitations"].append("dispatch-mismatch")
            break
        if identity["source"] != "transcript":
            report["limitations"].append("terminal-fallback")
        if not identity["sourceIdentity"]:
            report["limitations"].append("missing-source-identity")
        if number == 1 and not args.after and (result.get("transcript") or {}).get("limited"):
            report["limitations"].append("initial-window-limited")
        cursor = result.get("cursor")
        if not cursor or cursor == report["cursor"]:
            break
        report["cursor"] = cursor
    else:
        report["limitations"].append("page-budget-reached")
    report["limitations"] = sorted(set(report["limitations"]))
    write(args.output / "capture.json", report)
    print(json.dumps({"report": str((args.output / "capture.json").resolve()),
                      "pages": len(report["pages"]), "semantic_verdict": "not-evaluated"}))
    return 1 if report["limitations"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
