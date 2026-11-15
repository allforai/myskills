## Anonymous Meta-Skill Feedback

Category: freshness / run-cycle hygiene
Meta-skill version: 0.25.0

### Failure Pattern

1. After re-bootstrap and a new run cycle, artifacts of not-yet-run downstream nodes from the previous cycle remain on disk. An early-scheduled node read them; freshness recorded those nodes as its upstream; they had not published this cycle, so its publish was refused with stale_upstream_evidence. With suspected_root_node set, the engine treated it as hard_fail and the branch stalled.
2. When the engine is aborted mid-run, in-flight nodes leave observed reads and evidence publish records; readiness then reports dependency_outside_graph or transition_log_missing_for_delivered_nodes until cleaned by hand.
3. Same-wave siblings reading each other's artifacts also yield dependency_outside_graph.

### Suggested Fix

- On a new cycle, quarantine stale artifacts of incomplete nodes, or let freshness distinguish artifacts published this cycle from leftovers.
- On engine abort, clear the in-flight nodes' observed reads and publish records automatically.
