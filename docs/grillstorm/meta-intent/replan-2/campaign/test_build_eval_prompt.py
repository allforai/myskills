"""The builder must never hand an evaluator a shortened set of criteria."""
import importlib.util
from pathlib import Path

import pytest

HERE = Path(__file__).parent
PRIVATE = HERE.parent / "T15" / "evaluator-private.md"
TEMPLATE = HERE / "evaluate_cell.md"


def load():
    spec = importlib.util.spec_from_file_location("bep", HERE / "build_eval_prompt.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_every_scene_builds_a_complete_block():
    m = load()
    text = PRIVATE.read_text()
    scenes = [s for s in m.sections(text) if "-" in s]
    assert len(scenes) == 7, f"expected the seven T15 scenarios, got {scenes}"
    for scene in scenes:
        block = m.criteria_block(text, scene)
        assert m.assert_complete(block, text, scene)


def test_the_admission_drill_rules_survive_into_the_block():
    """The regression that motivated this module: these two sentences were truncated away."""
    m = load()
    block = m.criteria_block(PRIVATE.read_text(), "missing-product-docs")
    assert "exercise evidence rejection with a mismatched loaded path/hash" in block
    assert "count toward zero host cells" in block
    assert "a self-authored receipt alone is insufficient" in block


def test_a_truncated_block_is_rejected():
    m = load()
    text = PRIVATE.read_text()
    good = m.criteria_block(text, "missing-product-docs")
    with pytest.raises(ValueError, match="truncated|lost a paragraph"):
        m.assert_complete(good[:2372], text, "missing-product-docs")


def test_a_block_missing_an_interior_paragraph_is_rejected():
    m = load()
    text = text_ = PRIVATE.read_text()
    good = m.criteria_block(text, "missing-product-docs")
    paras = good.split("\n\n")
    maimed = "\n\n".join(paras[:3] + paras[4:])
    with pytest.raises(ValueError, match="lost a paragraph"):
        m.assert_complete(maimed, text_, "missing-product-docs")


def test_render_fills_every_placeholder_and_leaves_none():
    m = load()
    out = m.render(TEMPLATE.read_text(), "CRIT", "/t/path", "/r/path")
    assert "CRIT" in out and "/t/path" in out and "/r/path" in out
    assert "{{" not in out


def test_render_refuses_a_template_missing_a_placeholder():
    m = load()
    with pytest.raises(KeyError):
        m.render("no placeholders here", "CRIT", "/t", "/r")


def test_unknown_scene_is_an_error_not_an_empty_block():
    m = load()
    with pytest.raises(KeyError):
        m.criteria_block(PRIVATE.read_text(), "no-such-scene")
