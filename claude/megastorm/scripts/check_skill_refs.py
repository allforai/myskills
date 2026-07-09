#!/usr/bin/env python3
"""Integration self-check: every script + prompt the megastorm skill relies on must
exist on disk. Run after editing the skill or moving files (run-engine sync-check spirit)."""
import os
import sys

# The files skills/megastorm.md references via $ROOT/...
REQUIRED = [
    "knowledge/schemas.md",
    "knowledge/prompts/design-agent.md",
    "knowledge/prompts/plan-agent.md",
    "knowledge/prompts/closure-critic.md",
    "knowledge/prompts/reverse-critic.md",
    "knowledge/prompts/executor.md",
    "knowledge/prompts/supervisor.md",
    "scripts/validate_plan_tasks.py",
    "scripts/build_task_dag.py",
    "scripts/check_closure.py",
    "skills/megastorm.md",
    "commands/megastorm.md",
    # cross-exam (bundled skill) — files skills/cross-exam.md references via $ROOT/...
    "skills/cross-exam.md",
    "commands/cross-exam.md",
    "knowledge/cross-exam/lenses.md",
    "knowledge/cross-exam/prompts/prober.md",
    "knowledge/cross-exam/schemas.md",
    "scripts/render_report.py",
    ".claude-plugin/plugin.json",
    ".claude-plugin/marketplace.json",
]


def check_refs(plugin_root, extra_required=None):
    required = REQUIRED + list(extra_required or [])
    missing = [rel for rel in required if not os.path.isfile(os.path.join(plugin_root, rel))]
    return {"ok": len(missing) == 0, "missing": missing}


def main(argv):
    root = argv[1] if len(argv) > 1 else os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    r = check_refs(root)
    if r["ok"]:
        print(f"OK: all {len(REQUIRED)} referenced files present")
        return 0
    print("BLOCKED: skill references missing files:")
    for m in r["missing"]:
        print(f"  - {m}")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
