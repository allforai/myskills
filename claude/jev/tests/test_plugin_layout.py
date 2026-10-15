import json
import re
from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[1]


def frontmatter(path):
    text = path.read_text(encoding="utf-8")
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    assert m, f"{path} has no frontmatter"
    out = {}
    for line in m.group(1).splitlines():
        key, _, value = line.partition(":")
        out[key.strip()] = value.strip()
    return out


def test_manifests_agree():
    plugin = json.loads((PLUGIN / ".claude-plugin/plugin.json").read_text())
    market = json.loads((PLUGIN / ".claude-plugin/marketplace.json").read_text())
    assert plugin["name"] == market["name"] == market["plugins"][0]["name"] == "jev"
    assert plugin["version"] == market["plugins"][0]["version"] == "0.1.0"


def test_hooks_point_at_existing_scripts_with_timeouts():
    hooks = json.loads((PLUGIN / "hooks/hooks.json").read_text())["hooks"]
    prompt = hooks["UserPromptSubmit"][0]["hooks"][0]
    assert "scripts/route.py" in prompt["command"] and prompt["timeout"] == 5
    post = hooks["PostToolUse"][0]
    assert post["matcher"] == "Agent|Task" and "scripts/delegate_seen.py" in post["hooks"][0]["command"]
    assert (PLUGIN / "scripts/route.py").exists() and (PLUGIN / "scripts/delegate_seen.py").exists()


def test_every_skill_has_matching_name_and_description():
    skills = list((PLUGIN / "skills").iterdir())
    assert skills
    for skill in skills:
        fm = frontmatter(skill / "SKILL.md")
        assert fm["name"] == skill.name and fm["description"]


def test_jev_command_is_user_only():
    assert frontmatter(PLUGIN / "commands/jev.md")["disable-model-invocation"] == "true"


def test_route_question_has_three_tiers():
    q = json.loads((PLUGIN / "scripts/route_question.json").read_text())["tier"]
    assert q["type"] == "choice" and list(q["criteria"]) == ["light", "standard", "heavy"]


def test_classify_skill_states_its_contract():
    text = (PLUGIN / "skills/classify/SKILL.md").read_text(encoding="utf-8")
    for needle in ["--sample", "approve", "rebucket", "resolve", "save-set", "--source", "review",
                   "allow.json", "jev_batch.py", "curl"]:
        assert needle in text, needle


def test_code_scan_skill_states_its_contract():
    text = (PLUGIN / "skills/code-scan/SKILL.md").read_text(encoding="utf-8")
    for needle in ["code_chunks.py", "hits", "resolve", "false_positive", "save-set", "--source", "误报",
                   "allow.json", "curl"]:
        assert needle in text, needle
