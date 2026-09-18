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

## good-workflow

The same product, the same four file names, the graph it should have shipped. The dialogue
adds the two turns the incident never had: `propose` puts three experience directions on the
table with one recommended, and `decide` records the user's `select` of `steady-drip`
followed by the `answer` that closes `gap-experience-direction` — a selection does not close
the question by itself. `freeze` then carries the derived intent
`experience-direction-steady-drip` alongside the six topics, and every node consumes it,
because the full-process stage law is applied per frozen intent: a direction consumed only by
the nodes that build screens would leave the product, technical, documentation and
verification stages uncovered and `plan` would refuse the graph.

The twelve nodes are the shape both experience gates ask for, expressed in artifacts rather
than in names: `design-learner-journeys` produces the four app-design specifications,
`review-experience-design` and `review-experience-runtime` produce the two stages of
`experience-quality-critique` report (each with its `.html` and its `docs/experience-review/`
companion), the implementation nodes are `hard_blocked_by` the design review and its repair
node, and `close-launch-readiness` takes `capability: pipeline-closure-verify` so
`closure_not_blocked_by_experience_gate` is a check this graph actually walks through rather
than one it skips. No node takes `capability: app-design` or an id from
`APP_DESIGN_REQUIRED_NODES`, and no node id contains `product-review` or `cross-exam`: the
contract under test is the artifact path, never the node name.

`verify-learner-flows-on-device` is there for a gate that predates this one: an Expo module
in `profile.json` makes `validate_mobile_ui_coverage` demand a React Native UI automation
node with runner evidence, so that node names `detox` and the report it keeps. Every node
declares `source_inputs: []` — a new product has no code to read yet, and saying so is the
declaration evidence freshness requires; without it the bootstrap validator stops at the
shape rule before it reaches the cross-node experience rules.

`readiness-spec.json` declares one repair loop per review node, which is what
`experience_gate_without_repair_loop` asks of any graph that reviews an experience: the
design loop sends findings to `repair-experience-design` and holds both implementation nodes,
the runtime loop sends them to `repair-runtime-experience` and holds the closure node. Each
closure node is `hard_blocked_by` its repair node and its QA node, so it waits for the rerun
that proves the repair rather than for the repair alone.
