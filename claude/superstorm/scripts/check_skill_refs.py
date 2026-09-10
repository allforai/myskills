#!/usr/bin/env python3
"""Integration self-check: every script + prompt the superstorm skill relies on must
exist on disk. Run after editing the skill or moving files (run-engine sync-check spirit)."""
import os
import sys

# The files skills/superstorm/SKILL.md references via $ROOT/...
REQUIRED = [
    "knowledge/execution-playbook.md",
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
    "skills/superstorm/SKILL.md",
    # cross-exam (bundled skill) — files skills/cross-exam/SKILL.md references via $ROOT/...
    "skills/cross-exam/SKILL.md",
    "knowledge/cross-exam/lenses.md",
    "knowledge/cross-exam/prompts/prober.md",
    "knowledge/cross-exam/schemas.md",
    "scripts/render_report.py",
    "knowledge/cross-exam/visual/visual-acceptance.md",
    "knowledge/cross-exam/visual/validation.py",
    "knowledge/cross-exam/visual/matrix.py",
    "knowledge/cross-exam/visual/requirements.txt",
    "knowledge/cross-exam/visual/swiftui/baseline-guide.md",
    "knowledge/cross-exam/visual/swiftui/review-criteria.md",
    "knowledge/cross-exam/visual/swiftui/brand-spec-template.md",
    "knowledge/cross-exam/visual/swiftui/UPSTREAM.md",
    "knowledge/cross-exam/visual/platforms/swiftui.md",
    "knowledge/cross-exam/visual/platforms/web.md",
    "knowledge/cross-exam/visual/prompts/visual-reviewer.md",
    "knowledge/cross-exam/visual/swiftui/LICENSE",
    # keep-code-simple — independent advisory protocol, installed without shared/.
    "skills/keep-code-simple/SKILL.md",
    "knowledge/keep-code-simple/protocol.md",
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
