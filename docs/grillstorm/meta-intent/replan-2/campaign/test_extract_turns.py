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


def test_a_scene_that_borrows_another_scenes_answers_gets_them():
    """T15/new-product says: "Answer relevant questions with the reshape scenario's ... choices ...
    approve the named directions and release scope as in reshape." The turns are reshape's, by
    instruction — not invented here and not left empty."""
    sample = '''### reshape-business-model

Answer: "I approve these named directions together."

Then: "Only verified members of the same group can see requests."

### new-product

Answer relevant questions with the reshape scenario's choices. After a matching summary, explicitly
approve the named directions and release scope as in reshape.
'''
    assert turns_for(sample, "new-product", batch="T15") == [
        "I approve these named directions together.",
        "Only verified members of the same group can see requests."]
    # the borrow is scoped: without the batch it stays empty rather than guessing
    assert turns_for(sample, "new-product") == []
