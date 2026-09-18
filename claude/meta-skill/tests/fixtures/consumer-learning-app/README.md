# consumer-learning-app

The shape of the ink-scent new-product run of 2026-09-14~16 — a consumer language-learning
app with an Expo mobile client and a Node service — replayed as bootstrap dialogue, not a
copy of that project's content: every goal, rule and acceptance line here is written for
this fixture.

These are explicit artifacts, not a substitute semantic planner: the files hold the
`product_intent.py` requests a host would have typed, and the tests replay them through the
CLI copied into a generated project, so the gates judge a workflow the real code produced.

## bad-workflow

The graph that shipped: a consumer product whose six intents never name the experience the
product gives people, and whose thirteen nodes write `experience` into their own
`responsibilities` instead of designing one. It exists to be refused, so nothing in it may
be repaired into shape — no node produces `.allforai/app-design/**` and no node names
`experience-quality-critique`.

`profile.json` is merged into the generated `bootstrap-profile.json` after the dialogue has
run, because `draft` and `freeze` own `task_route` and `task_scope`; `dialogue.json` is the
ordered request list; `plan.json` is the single `plan` request; `readiness-spec.json`
replaces `unattended-run-readiness-spec.json` for the `/run` entry gate.
