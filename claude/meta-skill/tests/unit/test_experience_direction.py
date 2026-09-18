"""Experience direction through the copied product-intent CLI and gates; no host proof.

The user picks the product's experience direction from the model's proposals.
These tests drive that choice through the generated project's own scripts, so
both host copies (the Codex tests directory is a symlink to this one) prove the
same seams.
"""
import importlib.util
import json

import pytest

from .test_bootstrap_scope import project
from .test_product_intent_session import TOPICS, draft, invoke

EXPERIENCE_TOPIC = "experience-direction"


def script(root):
    """The copied CLI as a module, to read the constants the generated project really ships."""
    path = root / ".allforai/bootstrap/scripts/product_intent.py"
    spec = importlib.util.spec_from_file_location("copied_product_intent", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def new_product_draft():
    """`draft()` for a product without source and without a proposed experience direction."""
    request = draft()
    request.update(route="new-product", facts=[], questions=[],
                   items=[dict(item, origin="user-request", evidence=[])
                          for item in request["items"] if item["topic"] != EXPERIENCE_TOPIC])
    return request


@pytest.mark.parametrize("host", ["claude", "codex"])
def test_topic_is_listed_before_tradeoffs_and_missing_direction_is_a_gap(tmp_path, host):
    project(tmp_path, host=host)
    module = script(tmp_path)
    assert list(module.TOPICS) == TOPICS
    assert module.EXPERIENCE_TOPIC == EXPERIENCE_TOPIC
    assert TOPICS[TOPICS.index("tradeoffs") - 1] == EXPERIENCE_TOPIC
    (tmp_path / "orders.py").unlink()
    result = invoke(tmp_path, new_product_draft())
    assert result.returncode == 0, (result.stdout, result.stderr)
    output = json.loads(result.stdout)
    presented = [topic["topic"] for topic in output["topics"]]
    assert presented.index(EXPERIENCE_TOPIC) == presented.index("tradeoffs") - 1
    gaps = [question["id"] for topic in output["topics"] for question in topic["questions"]
            if question["kind"] == "gap"]
    assert "gap-" + EXPERIENCE_TOPIC in gaps
