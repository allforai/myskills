from pathlib import Path
from extract_turns import turns_for


SAMPLE = '''### large-code-local-button

Initial materials reuse the retail fixture.

Answer only unresolved UI/output questions: "Put Export CSV above the orders table. Use id, status, total."

Inspect whether the actor reused the journal.

Unwired contrast after a valid generated state: coordinator supplies this next user turn: "I also decide that this CSV includes a UTF-8 BOM."

### missing-product-docs

Answer only: "Nothing else; proceed."
'''


def test_turns_are_the_quoted_user_strings_of_one_scene_in_order():
    assert turns_for(SAMPLE, "large-code-local-button") == [
        "Put Export CSV above the orders table. Use id, status, total.",
        "I also decide that this CSV includes a UTF-8 BOM."]


def test_other_scenes_are_not_mixed_in_and_an_unknown_scene_is_empty():
    assert turns_for(SAMPLE, "missing-product-docs") == ["Nothing else; proceed."]
    assert turns_for(SAMPLE, "no-such-scene") == []
