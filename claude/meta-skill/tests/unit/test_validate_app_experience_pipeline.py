from ..module_isolation import load

validate_app_experience_pipeline = load(
    "validate_app_experience_pipeline"
).validate_app_experience_pipeline


def _write(root, rel, text):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


def _minimal_repo(tmp_path):
    _write(
        tmp_path,
        "claude/meta-skill/knowledge/bootstrap-planning.md",
        "9. Experience quality gate: "
        "${CLAUDE_PLUGIN_ROOT}/skills/app-design/40-qa/experience-quality-critique/SKILL.md\n",
    )
    _write(
        tmp_path,
        "claude/meta-skill/skills/app-design/PACK.md",
        """${CLAUDE_PLUGIN_ROOT}/skills/app-design/40-qa/experience-quality-critique/SKILL.md
experience-quality-critique
contract_defect
evidence_based_critique
llm_judgment
insufficient_evidence
.allforai/app-design/qa/
docs/experience-review/
""",
    )
    _write(
        tmp_path,
        "claude/meta-skill/skills/app-design/40-qa/experience-quality-critique/SKILL.md",
        """.allforai/app-design/qa/experience-quality-critique-design.json
.allforai/app-design/qa/experience-quality-critique-design.html
.allforai/app-design/qa/experience-quality-critique-runtime.json
.allforai/app-design/qa/experience-quality-critique-runtime.html
docs/experience-review/
onboarding
process_feedback
next_step
state_consistency
return_reason
mainline
direction_fidelity
audience_leak
contract_defect
evidence_based_critique
llm_judgment
insufficient_evidence
must_fix_before_implementation
must_fix_before_release
recommended_iterations
experience_gaps
review_language
zh-CN
repair_route
counterexample_or_comparison
rerun_from_node_id
fresh-context
""",
    )


def test_validate_app_experience_pipeline_accepts_minimal_graph(tmp_path):
    _minimal_repo(tmp_path)

    assert validate_app_experience_pipeline(str(tmp_path)) == []


def test_validate_app_experience_pipeline_rejects_unlisted_child(tmp_path):
    _minimal_repo(tmp_path)
    _write(
        tmp_path,
        "claude/meta-skill/skills/app-design/40-qa/new-critique/SKILL.md",
        "---\nname: y\ndescription: y\n---\n",
    )

    errors = validate_app_experience_pipeline(str(tmp_path))

    assert any("missing canonical child path" in error for error in errors)


def test_validate_app_experience_pipeline_rejects_missing_term(tmp_path):
    _minimal_repo(tmp_path)
    critique = (
        tmp_path
        / "claude/meta-skill/skills/app-design/40-qa/experience-quality-critique/SKILL.md"
    )
    critique.write_text(
        "".join(
            line
            for line in critique.read_text().splitlines(keepends=True)
            if line.strip() != "audience_leak"
        )
    )

    errors = validate_app_experience_pipeline(str(tmp_path))

    assert any("missing required term audience_leak" in error for error in errors)


def test_validate_app_experience_pipeline_rejects_unwired_bootstrap_corpus(tmp_path):
    _minimal_repo(tmp_path)
    _write(
        tmp_path,
        "claude/meta-skill/knowledge/bootstrap-planning.md",
        "9. Experience quality gate: planned, path not named\n",
    )

    errors = validate_app_experience_pipeline(str(tmp_path))

    assert len(errors) == 1, errors
    assert errors[0].startswith("bootstrap corpus: ")
    assert "skills/app-design/40-qa/experience-quality-critique/SKILL.md" in errors[0]


def test_validate_app_experience_pipeline_returns_early_on_missing_required_file(
    tmp_path,
):
    _minimal_repo(tmp_path)
    critique = (
        tmp_path
        / "claude/meta-skill/skills/app-design/40-qa/experience-quality-critique/SKILL.md"
    )
    critique.unlink()
    # Also unwire the corpus: an early return reports the missing file and nothing else.
    _write(tmp_path, "claude/meta-skill/knowledge/bootstrap-planning.md", "unwired\n")

    errors = validate_app_experience_pipeline(str(tmp_path))

    assert errors == [f"{critique}: required app-design pipeline file missing"]
